"""Live order queue for kitchen/bar staff. Auto-refreshes."""
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from lib.auth import require_admin
from lib.db import query, execute
from lib.utils import format_ugx, STATUS_LABELS

st.set_page_config(page_title="Orders", page_icon="🔥", layout="wide")
require_admin()

st.title("🔥 Live Orders")

# manual refresh (Streamlit reruns naturally on interaction; avoids
# fighting the platform with forced auto-refresh loops)
if st.button("🔄 Refresh"):
    st.rerun()

STATUS_FLOW = ["pending", "confirmed", "preparing", "ready", "served", "paid"]

active_orders = query(
    """select o.*, t.label as table_label
       from orders o left join tables t on o.table_id = t.id
       where o.status != 'paid' and o.status != 'cancelled'
       order by o.created_at asc"""
)

if not active_orders:
    st.info("No active orders right now.")
else:
    cols = st.columns(3)
    for i, order in enumerate(active_orders):
        items = query("select * from order_items where order_id = %s", (order["id"],))
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{order['order_number']}** — {order['table_label'] or 'N/A'}")
                st.caption(STATUS_LABELS.get(order["status"], order["status"]))
                for it in items:
                    st.write(f"{it['quantity']}x {it['item_name']}")
                st.write(f"**{format_ugx(float(order['total']))}**")
                if order.get("notes"):
                    st.caption(f"📝 {order['notes']}")

                current_idx = STATUS_FLOW.index(order["status"]) if order["status"] in STATUS_FLOW else 0
                next_status = STATUS_FLOW[min(current_idx + 1, len(STATUS_FLOW) - 1)]

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if order["status"] != "paid":
                        if st.button(f"→ {next_status}", key=f"next_{order['id']}"):
                            execute(
                                "update orders set status = %s, updated_at = now() where id = %s",
                                (next_status, order["id"]),
                            )
                            st.rerun()
                with btn_col2:
                    if st.button("Cancel", key=f"cancel_{order['id']}"):
                        execute(
                            "update orders set status = 'cancelled', updated_at = now() where id = %s",
                            (order["id"],),
                        )
                        st.rerun()
