"""Staff list, shift schedule, and PIN management for staff self-service login.
PINs are always visible to the manager here (not just at creation) so they
can be relayed to staff verbally at any time, including if a staff member
forgets theirs."""
import streamlit as st
from datetime import date, timedelta
import random
from lib.db import query, execute

st.title("👥 Staff & Schedule")

tab1, tab2 = st.tabs(["📅 This Week's Schedule", "🧑 Staff List"])

with tab1:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    shifts = query(
        """select sh.*, s.name as staff_name from shifts sh
           join staff s on sh.staff_id = s.id
           where sh.shift_date between %s and %s
           order by sh.shift_date, sh.start_time""",
        (week_dates[0], week_dates[-1]),
    )

    for d in week_dates:
        day_shifts = [s for s in shifts if s["shift_date"] == d]
        st.subheader(d.strftime("%A, %d %b"))
        if day_shifts:
            for s in day_shifts:
                st.write(f"🕐 {s['start_time']}–{s['end_time']} — **{s['staff_name']}** ({s['role_on_shift'] or ''})")
        else:
            st.caption("No shifts scheduled")
        st.divider()

    st.subheader("➕ Add a shift")
    staff_list = query("select * from staff where is_active = true order by name")
    if staff_list:
        staff_options = {s["name"]: s["id"] for s in staff_list}
        col1, col2, col3 = st.columns(3)
        with col1:
            staff_name = st.selectbox("Staff", list(staff_options.keys()))
            shift_date = st.date_input("Date", value=today)
        with col2:
            start_time = st.time_input("Start")
            end_time = st.time_input("End")
        with col3:
            role_on_shift = st.text_input("Role for this shift (optional)")
        if st.button("Add shift"):
            execute(
                """insert into shifts (staff_id, shift_date, start_time, end_time, role_on_shift)
                   values (%s, %s, %s, %s, %s)""",
                (staff_options[staff_name], shift_date, start_time, end_time, role_on_shift),
            )
            st.success("Shift added")
            st.rerun()
    else:
        st.info("Add staff members in the Staff List tab first.")

with tab2:
    st.caption("PINs are shown here so you can tell staff their login PIN for **My Tips & Shifts** at any time — including if they forget it.")
    staff_all = query("select * from staff order by name")
    for s in staff_all:
        status = "🟢" if s["is_active"] else "⚪"
        with st.container(border=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"{status} **{s['name']}** — {s['role']} — {s.get('phone') or '—'}")
            with col2:
                if s.get("pin"):
                    st.markdown(f"**PIN: `{s['pin']}`**")
                else:
                    st.caption("No PIN set")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if not s.get("pin"):
                    if st.button(f"Generate PIN", key=f"genpin_{s['id']}"):
                        new_pin = str(random.randint(1000, 9999))
                        execute("update staff set pin = %s where id = %s", (new_pin, s["id"]))
                        st.rerun()
            with btn_col2:
                if s.get("pin"):
                    if st.button(f"Reset PIN", key=f"resetpin_{s['id']}"):
                        new_pin = str(random.randint(1000, 9999))
                        execute("update staff set pin = %s where id = %s", (new_pin, s["id"]))
                        st.rerun()

    st.divider()
    st.subheader("➕ Add staff member")
    name = st.text_input("Name")
    role = st.selectbox("Role", ["waiter", "bartender", "chef", "cashier", "manager", "owner"])
    phone = st.text_input("Phone (optional)")
    if st.button("Add staff"):
        if name:
            pin = str(random.randint(1000, 9999))
            execute("insert into staff (name, role, phone, pin) values (%s, %s, %s, %s)", (name, role, phone, pin))
            st.success(f"Added {name} — PIN: **{pin}** (also visible above anytime)")
            st.rerun()
