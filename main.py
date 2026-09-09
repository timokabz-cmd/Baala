"""
Main entry point. Uses st.navigation so admin AND staff pages are
genuinely absent from the sidebar until the correct login happens --
guests only ever see Home / Menu & Order / My Order Status.
"""
import streamlit as st
from lib.nav import is_admin, is_staff, admin_login_widget

st.set_page_config(page_title="El Nivel Bar & Lounge", page_icon="🍹", layout="centered")

guest_pages = [
    st.Page("guest/landing.py", title="El Nivel", icon="🍸", default=True),
    st.Page("guest/home.py", title="Menu & Order", icon="🍹"),
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
    st.Page("staff/my_tips.py", title="My Tips", icon="🧾"),
    st.Page("staff/my_shifts.py", title="My Shifts", icon="📅"),
]

pages_to_show = list(guest_pages)
if is_admin():
    pages_to_show += admin_pages
if is_staff():
    pages_to_show += staff_pages

pg = st.navigation(pages_to_show, position="sidebar")

admin_login_widget()

pg.run()
