"""Mark an order paid, capture payment method and tip, attributed to the waiter."""
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from lib.auth import require_admin
from lib.db import query, execute
from lib.utils import format_ugx

st.set_page_config(page_title="Payments & Tips", page_icon="💰", layout="centered")
require_admin()

st.title("💰 Payments & Tips")

served_orders = query(
    """select o.*, t.label as table_label
       from orders o left join tables t on o.table_id = t.id
       where o.status = 'served'
       order by o.created_at asc"""
)

if not served_orders:
    st.info("No served orders awaiting payment.")
else:
    staff = query("select * from staff where is_active = true and role in ('waiter','bartender') order by name")
    staff_options = {s["name"]: s["id"] for s in staff}

    for order in served_orders:
        with st.container(border=True):
            st.subheader(f"{order['order_number']} — {order['table_label']}")
            st.write(f"Subtotal: {format_ugx(float(order['subtotal']))}")

            waiter_name = st.selectbox(
                "Served by", list(staff_options.keys()) or ["(no staff added yet)"], key=f"waiter_{order['id']}"
            )
            tip = st.number_input("Tip amount (UGX)", min_value=0, step=1000, key=f"tip_{order['id']}")
            payment_method = st.selectbox(
                "Payment method", ["cash", "mobile_money", "card"], key=f"pay_{order['id']}"
            )

            total = float(order["subtotal"]) + tip

            if st.button(f"Confirm Payment — {format_ugx(total)}", key=f"confirm_{order['id']}", type="primary"):
                execute(
                    """update orders set status = 'paid', tip_amount = %s, total = %s,
                       payment_method = %s, waiter_id = %s, updated_at = now() where id = %s""",
                    (tip, total, payment_method, staff_options.get(waiter_name), order["id"]),
                )
                if tip > 0 and staff_options.get(waiter_name):
                    execute(
                        """insert into tips (order_id, staff_id, amount, method)
                           values (%s, %s, %s, %s)""",
                        (order["id"], staff_options[waiter_name], tip, "added_to_bill"),
                    )
                st.success(f"Payment recorded for {order['order_number']}")
                st.rerun()

st.divider()
st.subheader("📊 Tips summary (this week)")
tip_summary = query(
    """select s.name, sum(t.amount) as total_tips, count(*) as tip_count
       from tips t join staff s on t.staff_id = s.id
       where t.created_at >= now() - interval '7 days'
       group by s.name order by total_tips desc"""
)
if tip_summary:
    for row in tip_summary:
        st.write(f"**{row['name']}** — {format_ugx(float(row['total_tips']))} across {row['tip_count']} orders")
else:
    st.caption("No tips recorded yet this week.")
