"""Staff self-service: view own upcoming shifts. Uses the same PIN session
as My Tips -- if already logged in there, no need to log in again here."""
import streamlit as st
from datetime import date
from lib.db import query

st.title("📅 My Shifts")

if "staff_id" not in st.session_state:
    st.session_state.staff_id = None

if not st.session_state.staff_id:
    pin = st.text_input("Enter your PIN", type="password", max_chars=4)
    if st.button("Login"):
        staff = query("select * from staff where pin = %s and is_active = true", (pin,), fetch="one")
        if staff:
            st.session_state.staff_id = staff["id"]
            st.session_state.staff_name = staff["name"]
            st.rerun()
        else:
            st.error("PIN not recognized. Ask your manager if you don't have one yet.")
    st.stop()

st.success(f"Welcome, {st.session_state.staff_name}")
if st.button("Log out"):
    st.session_state.staff_id = None
    st.rerun()

st.divider()

shifts = query(
    """select * from shifts where staff_id = %s and shift_date >= %s order by shift_date, start_time limit 14""",
    (st.session_state.staff_id, date.today()),
)
if shifts:
    for s in shifts:
        st.write(f"**{s['shift_date'].strftime('%a, %d %b')}** — {s['start_time']}–{s['end_time']}")
        if s.get("role_on_shift"):
            st.caption(s["role_on_shift"])
else:
    st.caption("No upcoming shifts scheduled.")
