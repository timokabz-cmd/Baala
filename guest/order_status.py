"""Lets a guest check their order status by order number, without needing
any login. No sensitive data exposed -- just status and items for that
one order number, which only the guest who placed it would know."""
import streamlit as st
from lib.db import query
from lib.utils import format_ugx, STATUS_LABELS

st.title("🔔 My Order Status")

default_order = st.session_state.get("order_number_last", "")
order_number = st.text_input("Enter your order number (e.g. ORD-4471)", value=default_order)

if order_number:
    order = query("select * from orders where order_number = %s", (order_number.strip(),), fetch="one")
    if not order:
        st.error("No order found with that number.")
    else:
        st.subheader(f"Order {order['order_number']}")
        st.markdown(f"**Status: {STATUS_LABELS.get(order['status'], order['status'])}**")

        items = query("select * from order_items where order_id = %s", (order["id"],))
        for it in items:
            st.write(f"{it['quantity']}x {it['item_name']}")

        st.write(f"**Total: {format_ugx(float(order['total']))}**")

        if order["status"] == "pending":
            st.caption("We've received your order and will confirm shortly.")
        elif order["status"] == "confirmed":
            st.caption("Your order is confirmed and will start preparing soon.")
        elif order["status"] == "preparing":
            st.caption("Your order is being prepared.")
        elif order["status"] == "ready":
            st.success("Your order is ready!")
        elif order["status"] == "served":
            st.caption("Enjoy! Let a staff member know when you're ready to settle the bill.")
        elif order["status"] == "paid":
            st.success("Payment received. Thank you for visiting!")
        elif order["status"] == "cancelled":
            st.error("This order was cancelled. Please speak to a staff member.")

        if st.button("🔄 Refresh status"):
            st.rerun()
