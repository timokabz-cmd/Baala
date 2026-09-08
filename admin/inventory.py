"""Inventory: stock levels, low-stock alerts, restocking, menu item linking."""
import streamlit as st
from lib.db import query, execute

st.title("📦 Inventory")

items = query("select * from inventory order by item_name")

low_stock = [i for i in items if float(i["quantity_on_hand"]) <= float(i["reorder_level"])]
if low_stock:
    st.warning(f"⚠️ {len(low_stock)} item(s) at or below reorder level: " + ", ".join(i["item_name"] for i in low_stock))

st.subheader("Current Stock")
for it in items:
    is_low = float(it["quantity_on_hand"]) <= float(it["reorder_level"])
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            label = f"⚠️ **{it['item_name']}**" if is_low else f"**{it['item_name']}**"
            st.write(label)
            st.caption(f"Supplier: {it.get('supplier') or '—'}")
        with col2:
            st.metric("On hand", f"{it['quantity_on_hand']} {it['unit']}")
        with col3:
            adjustment = st.number_input(
                "Adjust (+/-)", value=0.0, step=1.0, key=f"adj_{it['id']}", label_visibility="collapsed"
            )
            if st.button("Apply", key=f"apply_{it['id']}"):
                if adjustment != 0:
                    new_qty = float(it["quantity_on_hand"]) + adjustment
                    execute(
                        "update inventory set quantity_on_hand = %s, updated_at = now() where id = %s",
                        (new_qty, it["id"]),
                    )
                    reason = "restock" if adjustment > 0 else "manual adjustment"
                    execute(
                        "insert into inventory_movements (inventory_id, change_qty, reason) values (%s, %s, %s)",
                        (it["id"], adjustment, reason),
                    )
                    st.rerun()

st.divider()
with st.expander("➕ Add new inventory item"):
    name = st.text_input("Item name")
    unit = st.selectbox("Unit", ["bottle", "crate", "litre", "kg", "piece"])
    qty = st.number_input("Starting quantity", min_value=0.0, step=1.0)
    reorder = st.number_input("Reorder level (alert when at/below this)", min_value=0.0, step=1.0)
    supplier = st.text_input("Supplier (optional)")
    if st.button("Add item"):
        if name:
            execute(
                """insert into inventory (item_name, unit, quantity_on_hand, reorder_level, supplier)
                   values (%s, %s, %s, %s, %s)""",
                (name, unit, qty, reorder, supplier),
            )
            st.success(f"Added {name}")
            st.rerun()

st.divider()
st.subheader("🔗 Link menu items to inventory")
st.caption("So stock auto-depletes when that item sells. Optional — only link items you want tracked (e.g. bottled spirits, beer).")
menu_items = query("select * from menu_items where category = 'bar' order by name")
inv_options = {i["item_name"]: i["id"] for i in items}
inv_options["(none)"] = None

for mi in menu_items:
    current_link = next((k for k, v in inv_options.items() if v == mi.get("inventory_id")), "(none)")
    choice = st.selectbox(
        mi["name"], list(inv_options.keys()), index=list(inv_options.keys()).index(current_link), key=f"link_{mi['id']}"
    )
    if inv_options[choice] != mi.get("inventory_id"):
        execute("update menu_items set inventory_id = %s where id = %s", (inv_options[choice], mi["id"]))
        st.rerun()
