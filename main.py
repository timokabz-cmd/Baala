"""
Main entry point. Uses st.navigation so admin pages are genuinely absent
from the sidebar for guests -- not just password-gated after being visible.

IMPORTANT: with st.navigation, individual page files under pages/ are no
longer auto-registered by Streamlit's old magic folder behavior. This file
is now what should be set as the app's main file in Streamlit Cloud.
"""
import streamlit as st
from lib.nav import is_admin, admin_login_widget

st.set_page_config(page_title="El Nivel Bar & Lounge", page_icon="🍹", layout="centered")

guest_pages = [
    st.Page("guest/home.py", title="Menu & Order", icon="🍹", default=True),
    st.Page("guest/order_status.py", title="My Order Status", icon="🔔"),
]

admin_pages = [
    st.Page("admin/orders.py", title="Live Orders", icon="🔥"),
    st.Page("admin/payments_tips.py", title="Payments & Tips", icon="💰"),
    st.Page("admin/inventory.py", title="Inventory", icon="📦"),
    st.Page("admin/staff_schedule.py", title="Staff & Schedule", icon="👥"),
    st.Page("admin/analytics.py", title="Analytics", icon="📊"),
    st.Page("admin/menu_manager.py", title="Menu Manager", icon="🍽️"),
    st.Page("admin/tables_qr.py", title="Tables & QR", icon="🔗"),
]

staff_pages = [
    st.Page("staff/my_tips.py", title="My Tips & Shifts", icon="🧾"),
]

# Guests only ever see guest_pages. Admin pages appear ONLY once logged in.
pages_to_show = list(guest_pages)
if is_admin():
    pages_to_show += admin_pages
pages_to_show += staff_pages  # staff PIN login happens inside that page itself

pg = st.navigation(pages_to_show, position="sidebar")

admin_login_widget()

pg.run()
