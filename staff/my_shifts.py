"""Staff view: own upcoming shifts. Login happens via the Staff/Admin
sidebar expander (lib/nav.py) -- this page just reads session state."""
import streamlit as st
from datetime import date
from lib.db import query

st.title("📅 My Shifts")

if not st.session_state.get("staff_id"):
    st.warning("Please log in with your PIN using the **Staff / Admin** panel in the sidebar.")
    st.stop()

st.success(f"Welcome, {st.session_state.staff_name}")

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
