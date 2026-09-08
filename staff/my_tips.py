"""
Staff self-service: enter your PIN, see ONLY your own tips.
Shifts are on a separate page (my_shifts.py) so this stays focused.
"""
import streamlit as st
from lib.db import query
from lib.utils import format_ugx

st.title("🧾 My Tips")

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

period = st.selectbox("Period", ["This week", "This month", "All time"])
interval = {"This week": "7 days", "This month": "30 days", "All time": "50 years"}[period]

tips = query(
    f"""select t.amount, t.method, t.created_at, o.order_number
        from tips t join orders o on t.order_id = o.id
        where t.staff_id = %s and t.created_at >= now() - interval '{interval}'
        order by t.created_at desc""",
    (st.session_state.staff_id,),
)

total = sum(float(t["amount"]) for t in tips)
st.metric(f"Total tips ({period.lower()})", format_ugx(total))

if tips:
    for t in tips:
        st.write(f"{t['created_at'].strftime('%d %b, %H:%M')} — {format_ugx(float(t['amount']))} ({t['order_number']})")
else:
    st.caption("No tips recorded for this period yet.")
