"""Guest-facing menu + cart + WhatsApp checkout. Styled with El Nivel's
actual brand palette; includes a persistent sidebar cart summary."""
import streamlit as st
from lib.db import query, execute
from lib.utils import format_ugx, generate_order_number, build_whatsapp_order_link

BUSINESS_NAME = "El Nivel Bar & Lounge"
WHATSAPP_NUMBER = st.secrets.get("whatsapp_number", "256700000000")

st.markdown(
    """
    <style>
    .stApp { background-color: #1a1512; }
    section[data-testid="stSidebar"] { background-color: #120e0c; }

    h1, h2, h3 {
        color: #e8c77a !important;
        font-family: Georgia, 'Times New Roman', serif;
    }
    p, span, label, .stMarkdown, .stCaption, div[data-testid="stCaptionContainer"] {
        color: #f0e6d2 !important;
    }
    .item-name { color: #e8c77a !important; font-weight: 700; font-size: 1.05rem; }
    .item-price { color: #d4a94a !important; }

    div[role="radiogroup"] label, div[role="radiogroup"] p {
        color: #f0e6d2 !important;
    }
    div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
        border-color: #d4a94a !important;
    }

    .stButton>button {
        background-color: #d4a94a; color: #1a1512; border-radius: 8px;
        border: none; font-weight: 600;
    }
    .stButton>button:hover { background-color: #e8c77a; color: #1a1512; }

    div[data-testid="stNumberInput"] input { color: #1a1512 !important; }

    hr { border-color: #3a2e24 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "cart" not in st.session_state:
    st.session_state.cart = {}
if "order_number_last" not in st.session_state:
    st.session_state.order_number_last = None


def render_sidebar_cart():
    """Always-visible cart summary in the sidebar, so guests don't have to
    scroll through the whole menu to reach checkout -- it's pinned no
    matter where they are on the page."""
    cart = st.session_state.cart
    with st.sidebar:
        st.markdown("### 🛒 Your Order")
        if not cart:
            st.caption("Cart is empty — add items to get started.")
        else:
            subtotal = 0
            count = 0
            for c in cart.values():
                subtotal += c["price"] * c["quantity"]
                count += c["quantity"]
            st.metric("Items", count)
            st.metric("Subtotal", format_ugx(subtotal))
            st.caption("Scroll down to review and checkout ⬇️")


render_sidebar_cart()

table_slug = st.query_params.get("table", None)
current_table = None
if table_slug:
    rows = query("select * from tables where qr_slug = %s and is_active = true", (table_slug,))
    if rows:
        current_table = rows[0]

st.title(f"🍹 {BUSINESS_NAME}")
st.caption("Kiwatule, Kampala")
if current_table:
    st.info(f"📍 {current_table['label']}")

category = st.radio("Browse", ["🍽️ Restaurant", "🍸 Bar"], horizontal=True, label_visibility="collapsed")
cat_key = "restaurant" if "Restaurant" in category else "bar"

items = query(
    "select * from menu_items where category = %s and is_available = true order by subcategory, name",
    (cat_key,),
)

if not items:
    st.info("No items available in this category right now.")
else:
    groups = {}
    for it in items:
        groups.setdefault(it.get("subcategory") or "Menu", []).append(it)

    for group_name, group_items in groups.items():
        st.subheader(group_name.title())
        for it in group_items:
            wait = it.get("estimated_minutes") or 5
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<span class='item-name'>{it['name']}</span>", unsafe_allow_html=True)
                st.markdown(
                    f"<span class='item-price'>{format_ugx(float(it['price']))} · ~{wait} min</span>",
                    unsafe_allow_html=True,
                )
                if it.get("description"):
                    st.caption(it["description"])
            with col2:
                qty = st.number_input(
                    "Qty", min_value=0, max_value=20, value=0, key=f"qty_{it['id']}", label_visibility="collapsed"
                )
            if qty > 0:
                st.session_state.cart[it["id"]] = {
                    "name": it["name"],
                    "price": float(it["price"]),
                    "quantity": qty,
                    "estimated_minutes": wait,
                }
            elif it["id"] in st.session_state.cart:
                del st.session_state.cart[it["id"]]
            st.divider()

cart = st.session_state.cart
if cart:
    st.subheader("🛒 Your Order")
    subtotal = 0
    cart_items = []
    max_wait = 0
    for item_id, c in cart.items():
        line_total = c["price"] * c["quantity"]
        subtotal += line_total
        max_wait = max(max_wait, c["estimated_minutes"])
        cart_items.append(
            {"name": c["name"], "quantity": c["quantity"], "unit_price": c["price"], "line_total": line_total}
        )
        st.write(f"{c['quantity']}x {c['name']} — {format_ugx(line_total)}")

    st.write(f"**Subtotal: {format_ugx(subtotal)}**")
    st.caption(f"⏱️ Estimated wait: ~{max_wait} min")

    service_type = st.radio("How would you like this served?", ["Dine-in", "Takeaway"], horizontal=True)

    table_number = None
    if service_type == "Dine-in":
        table_number = current_table["label"] if current_table else st.text_input("Table number (if known)")

    notes = st.text_input("Any notes for the kitchen/bar? (optional)")

    if st.button("📲 Send Order via WhatsApp", type="primary", use_container_width=True):
        order_number = generate_order_number()
        table_id = current_table["id"] if current_table else None
        service_key = "dine_in" if service_type == "Dine-in" else "takeaway"

        order_row = execute(
            """insert into orders (order_number, table_id, service_type, status, subtotal, total, notes)
               values (%s, %s, %s, 'pending', %s, %s, %s) returning id""",
            (order_number, table_id, service_key, subtotal, subtotal, notes),
            returning=True,
        )
        order_id = order_row["id"]

        for item_id, c in cart.items():
            execute(
                """insert into order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total)
                   values (%s, %s, %s, %s, %s, %s)""",
                (order_id, item_id, c["name"], c["price"], c["quantity"], c["price"] * c["quantity"]),
            )
            menu_row = query("select inventory_id from menu_items where id = %s", (item_id,), fetch="one")
            if menu_row and menu_row.get("inventory_id"):
                execute(
                    "update inventory set quantity_on_hand = quantity_on_hand - %s, updated_at = now() where id = %s",
                    (c["quantity"], menu_row["inventory_id"]),
                )
                execute(
                    "insert into inventory_movements (inventory_id, change_qty, reason) values (%s, %s, 'sale')",
                    (menu_row["inventory_id"], -c["quantity"]),
                )

        label = table_number or "Takeaway"
        link = build_whatsapp_order_link(WHATSAPP_NUMBER, order_number, label, cart_items, subtotal, notes)
        st.session_state.order_number_last = order_number
        st.success(f"Order {order_number} placed! Tap below to notify us on WhatsApp.")
        st.link_button("Open WhatsApp", link, use_container_width=True)
        st.caption("Track your order status in the **My Order Status** page (sidebar).")
        st.session_state.cart = {}
else:
    st.info("Add items above to build your order.")
