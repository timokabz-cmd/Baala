"""
Central navigation + auth gate.
Guests only ever see the guest-facing pages. Admin pages are not even
listed in the sidebar until the correct admin password is entered here --
this is different from just password-protecting each page individually,
which still let the page names/sidebar leak to guests.
"""
import streamlit as st


def is_admin():
    return st.session_state.get("is_admin", False)


def is_staff():
    return st.session_state.get("staff_id") is not None


def admin_login_widget():
    """Render a small admin login control. Call from the guest-side pages
    (e.g. in a sidebar expander) so staff can get to admin without guests
    ever seeing page names they shouldn't."""
    with st.sidebar:
        with st.expander("Staff / Admin"):
            if is_admin():
                st.success("Admin mode active")
                if st.button("Log out"):
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
