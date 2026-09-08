"""
Central navigation + auth gate.
Guests only ever see the guest-facing pages. Admin pages appear only
after the admin password is entered; staff pages appear only after a
staff PIN is entered. Both logins live in the same sidebar expander so
guests never see "My Tips" / "My Shifts" / admin page names at all.
"""
import streamlit as st
from lib.db import query


def is_admin():
    return st.session_state.get("is_admin", False)


def is_staff():
    return st.session_state.get("staff_id") is not None


def staff_login_widget():
    """Renders inside the same Staff/Admin expander as admin login.
    On success, sets staff_id/staff_name in session state so staff
    pages (my_tips.py, my_shifts.py) can use them directly."""
    if is_staff():
        st.success(f"Logged in as {st.session_state.get('staff_name', 'staff')}")
        if st.button("Log out (staff)"):
            st.session_state.staff_id = None
            st.session_state.staff_name = None
            st.rerun()
    else:
        pin = st.text_input("Staff PIN", type="password", max_chars=4, key="staff_pin_input")
        if st.button("Login with PIN"):
            staff = query("select * from staff where pin = %s and is_active = true", (pin,), fetch="one")
            if staff:
                st.session_state.staff_id = staff["id"]
                st.session_state.staff_name = staff["name"]
                st.rerun()
            else:
                st.error("PIN not recognized.")


def admin_login_widget():
    """Renders BOTH admin password login and staff PIN login inside one
    sidebar expander, so guests only ever see a single generic
    'Staff / Admin' entry point -- never separate page names."""
    with st.sidebar:
        with st.expander("Staff / Admin"):
            tab1, tab2 = st.tabs(["Admin", "Staff"])

            with tab1:
                if is_admin():
                    st.success("Admin mode active")
                    if st.button("Log out (admin)"):
                        st.session_state.is_admin = False
                        st.rerun()
                else:
                    pwd = st.text_input("Admin password", type="password", key="admin_pwd_input")
                    if st.button("Login as admin"):
                        if pwd == st.secrets.get("admin_password", ""):
                            st.session_state.is_admin = True
                            st.rerun()
                        else:
                            st.error("Incorrect password")

            with tab2:
                staff_login_widget()
