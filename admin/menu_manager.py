"""Add, edit, and toggle availability of menu items. Includes wait-time estimate."""
import streamlit as st
from lib.db import query, execute
from lib.utils import format_ugx

st.title("🍽️ Menu Manager")

tab1, tab2 = st.tabs(["📋 Current Menu", "➕ Add Item"])

with tab1:
    items = query("select * from menu_items order by category, subcategory, name")
    for it in items:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{it['name']}** ({it['category']}/{it.get('subcategory') or '—'})")
                st.caption(it.get("description") or "")
            with col2:
                st.write(format_ugx(float(it["price"])))
                wait = st.number_input(
                    "Wait (min)", min_value=1, max_value=120, value=it.get("estimated_minutes") or 5,
                    key=f"wait_{it['id']}", label_visibility="collapsed"
                )
                if wait != it.get("estimated_minutes"):
                    execute("update menu_items set estimated_minutes = %s where id = %s", (wait, it["id"]))
            with col3:
                available = st.toggle("Available", value=it["is_available"], key=f"avail_{it['id']}")
                if available != it["is_available"]:
                    execute(
                        "update menu_items set is_available = %s, updated_at = now() where id = %s",
                        (available, it["id"]),
                    )
                    st.rerun()

with tab2:
    name = st.text_input("Item name")
    description = st.text_area("Description (optional)")
    category = st.selectbox("Category", ["bar", "restaurant"])
    subcategory = st.text_input("Subcategory (e.g. spirits, grills, starters)")
    price = st.number_input("Price (UGX)", min_value=0, step=500)
    wait_minutes = st.number_input("Estimated wait time (minutes)", min_value=1, max_value=120, value=5)
    if st.button("Add item", type="primary"):
        if name and price:
            execute(
                """insert into menu_items (name, description, category, subcategory, price, estimated_minutes)
                   values (%s, %s, %s, %s, %s, %s)""",
                (name, description, category, subcategory, price, wait_minutes),
            )
            st.success(f"Added {name}")
            st.rerun()
        else:
            st.error("Name and price are required.")
