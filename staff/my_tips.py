"""Staff view: own tips only. Login happens via the Staff/Admin sidebar
expander (lib/nav.py) -- this page just reads the resulting session state."""
import streamlit as st
from lib.db import query
from lib.utils import format_ugx

st.title("🧾 My Tips")

if not st.session_state.get("staff_id"):
    st.warning("Please log in with your PIN using the **Staff / Admin** panel in the sidebar.")
    st.stop()

st.success(f"Welcome, {st.session_state.staff_name}")

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
