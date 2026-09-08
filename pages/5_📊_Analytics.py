"""Basic analytics: today's sales, top items, tips, order volume trend."""
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from lib.auth import require_admin
from lib.db import query
from lib.utils import format_ugx

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
require_admin()

st.title("📊 Analytics")

period = st.selectbox("Period", ["Today", "Last 7 days", "Last 30 days"])
interval = {"Today": "1 day", "Last 7 days": "7 days", "Last 30 days": "30 days"}[period]

# ---------- Top-line numbers ----------
summary = query(
    f"""select
            count(*) as order_count,
            coalesce(sum(total), 0) as revenue,
            coalesce(sum(tip_amount), 0) as tips
        from orders
        where status = 'paid' and created_at >= now() - interval '{interval}'"""
)[0]

col1, col2, col3 = st.columns(3)
col1.metric("Orders", summary["order_count"])
col2.metric("Revenue", format_ugx(float(summary["revenue"])))
col3.metric("Tips", format_ugx(float(summary["tips"])))

st.divider()

# ---------- Top items ----------
st.subheader("🏆 Top-selling items")
top_items = query(
    f"""select oi.item_name, sum(oi.quantity) as qty_sold, sum(oi.line_total) as revenue
        from order_items oi
        join orders o on oi.order_id = o.id
        where o.status = 'paid' and o.created_at >= now() - interval '{interval}'
        group by oi.item_name
        order by qty_sold desc
        limit 10"""
)
if top_items:
    for it in top_items:
        st.write(f"**{it['item_name']}** — {it['qty_sold']} sold — {format_ugx(float(it['revenue']))}")
else:
    st.caption("No paid orders in this period yet.")

st.divider()

# ---------- Bar vs Restaurant split ----------
st.subheader("🍹 Bar vs 🍽️ Restaurant")
split = query(
    f"""select mi.category, sum(oi.line_total) as revenue
        from order_items oi
        join orders o on oi.order_id = o.id
        join menu_items mi on oi.menu_item_id = mi.id
        where o.status = 'paid' and o.created_at >= now() - interval '{interval}'
        group by mi.category"""
)
if split:
    for row in split:
        st.write(f"{row['category'].title()}: {format_ugx(float(row['revenue']))}")
else:
    st.caption("No data yet.")

st.divider()

# ---------- Peak hours ----------
st.subheader("⏰ Peak hours")
peak = query(
    f"""select extract(hour from created_at) as hour, count(*) as order_count
        from orders
        where status = 'paid' and created_at >= now() - interval '{interval}'
        group by hour order by hour"""
)
if peak:
    chart_data = {int(row["hour"]): row["order_count"] for row in peak}
    st.bar_chart(chart_data)
else:
    st.caption("No data yet.")
