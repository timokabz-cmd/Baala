"""
Bar & Restaurant — QR Menu + WhatsApp Ordering
Guest scans a table QR -> lands here with ?table=<slug> -> browses menu ->
builds a cart -> sends order via WhatsApp.
"""
import streamlit as st
from lib.db import query, execute
from lib.utils import format_ugx, generate_order_number, build_whatsapp_order_link

BUSINESS_NAME = "Baala"
WHATSAPP_NUMBER = st.secrets.get("whatsapp_number", "256700000000")

st.set_page_config(page_title=BUSINESS_NAME, page_icon="🍹", layout="centered")

# ---------- Resolve table from QR link ----------
table_slug = st.query_params.get("table", None)
current_table = None
if table_slug:
    rows = query("select * from tables where qr_slug = %s and is_active = true", (table_slug,))
    if rows:
        current_table = rows[0]

if "cart" not in st.session_state:
    st.session_state.cart = {}  # menu_item_id -> {name, price, quantity}

# ---------- Header ----------
st.title(f"🍹 {BUSINESS_NAME}")
if current_table:
    st.caption(f"📍 {current_table['label']}")
else:
    st.warning("No table detected — scan the QR code at your table, or select one below.")
    tables = query("select * from tables where is_active = true order by label")
    if tables:
        labels = {t["label"]: t for t in tables}
        chosen = st.selectbox("Select your table", list(labels.keys()))
        current_table = labels[chosen]

st.divider()

# ---------- Category toggle ----------
category = st.radio("Browse", ["🍽️ Restaurant", "🍸 Bar"], horizontal=True, label_visibility="collapsed")
cat_key = "restaurant" if "Restaurant" in category else "bar"

items = query(
    "select * from menu_items where category = %s and is_available = true order by subcategory, name",
    (cat_key,),
)

if not items:
    st.info("No items available in this category right now.")
else:
    # group by subcategory
    groups = {}
    for it in items:
        groups.setdefault(it.get("subcategory") or "Menu", []).append(it)

    for group_name, group_items in groups.items():
        st.subheader(group_name.title())
        for it in group_items:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{it['name']}**")
                if it.get("description"):
                    st.caption(it["description"])
                st.write(format_ugx(float(it["price"])))
            with col2:
                qty = st.number_input(
                    "Qty", min_value=0, max_value=20, value=0, key=f"qty_{it['id']}", label_visibility="collapsed"
                )
            with col3:
                if qty > 0:
                    st.session_state.cart[it["id"]] = {
                        "name": it["name"],
                        "price": float(it["price"]),
                        "quantity": qty,
                    }
                elif it["id"] in st.session_state.cart:
                    del st.session_state.cart[it["id"]]
            st.divider()

# ---------- Cart / Checkout ----------
cart = st.session_state.cart
if cart:
    st.subheader("🛒 Your Order")
    subtotal = 0
    cart_items = []
    for item_id, c in cart.items():
        line_total = c["price"] * c["quantity"]
        subtotal += line_total
        cart_items.append(
            {"name": c["name"], "quantity": c["quantity"], "unit_price": c["price"], "line_total": line_total}
        )
        st.write(f"{c['quantity']}x {c['name']} — {format_ugx(line_total)}")

    st.write(f"**Subtotal: {format_ugx(subtotal)}**")

    notes = st.text_input("Any notes for the kitchen/bar? (optional)")

    if st.button("📲 Send Order via WhatsApp", type="primary", use_container_width=True):
        if not current_table:
            st.error("Please select a table before ordering.")
        else:
            order_number = generate_order_number()
            order_row = execute(
                """insert into orders (order_number, table_id, service_type, status, subtotal, total, notes)
                   values (%s, %s, 'dine_in', 'pending', %s, %s, %s) returning id""",
                (order_number, current_table["id"], subtotal, subtotal, notes),
                returning=True,
            )
            order_id = order_row["id"]
            for item_id, c in cart.items():
                execute(
                    """insert into order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total)
                       values (%s, %s, %s, %s, %s, %s)""",
                    (order_id, item_id, c["name"], c["price"], c["quantity"], c["price"] * c["quantity"]),
                )

            link = build_whatsapp_order_link(
                WHATSAPP_NUMBER, order_number, current_table["label"], cart_items, subtotal, notes
            )
            st.success(f"Order {order_number} placed! Tap below to notify us on WhatsApp.")
            st.link_button("Open WhatsApp", link, use_container_width=True)
            st.session_state.cart = {}
else:
    st.info("Add items above to build your order.")
