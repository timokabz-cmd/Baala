"""Premium guest-facing menu + cart + WhatsApp checkout for El Nivel.
Cart and checkout now live INLINE on the main page (tap the cart banner
to expand it) instead of only in the sidebar, so it's reachable without
needing to know the sidebar exists. Same DB logic, same WhatsApp flow,
same tip-to-waiter linking as before. Menu/table/staff lookups are now
cached briefly so tapping a quantity doesn't re-hit the database (and
the network round-trip to Supabase) on every single interaction.
"""
import streamlit as st
from lib.db import query, execute
from lib.theme import inject_theme
from lib.utils import format_ugx, generate_order_number, build_whatsapp_order_link

BUSINESS_NAME = "El Nivel Bar & Lounge"
WHATSAPP_NUMBER = st.secrets.get("whatsapp_number", "256700000000")

inject_theme()

if "cart" not in st.session_state:
    st.session_state.cart = {}
if "order_number_last" not in st.session_state:
    st.session_state.order_number_last = None
if "show_checkout" not in st.session_state:
    st.session_state.show_checkout = False


@st.cache_data(ttl=60)
def get_table_by_slug(slug):
    """Cached -- table info almost never changes mid-session."""
    rows = query("select * from tables where qr_slug = %s and is_active = true", (slug,))
    return rows[0] if rows else None


@st.cache_data(ttl=30)
def get_waiter_staff():
    """Cached -- avoids a DB round-trip every time the tip checkbox area re-renders."""
    return query(
        "select * from staff where is_active = true and role in ('waiter','bartender') order by name"
    )


@st.cache_data(ttl=30)
def get_menu_items(category):
    """Cached for 30s -- the menu rarely changes mid-session, and without
    this, every tap on a quantity +/- button re-queries Supabase over the
    network (Uganda -> Frankfurt), which is what caused the ~20s lag
    guests were seeing after tapping an item."""
    return query(
        "select * from menu_items where category = %s and is_available = true order by subcategory, name",
        (category,),
    )


table_slug = st.query_params.get("table", None)
current_table = get_table_by_slug(table_slug) if table_slug else None


def render_sidebar_note():
    """Sidebar now just confirms cart status and points to the on-page
    checkout -- the full checkout flow lives inline on the main page
    (tap the cart banner) so it's reachable without opening the sidebar."""
    with st.sidebar:
        st.markdown("### Your Order")
        st.markdown("<hr class='gold-rule'>", unsafe_allow_html=True)
        cart = st.session_state.cart
        if not cart:
            st.caption("Your order is empty - tap + on any dish or drink.")
        else:
            count = sum(c["quantity"] for c in cart.values())
            subtotal = sum(c["price"] * c["quantity"] for c in cart.values())
            st.metric("Items", count)
            st.metric("Subtotal", format_ugx(subtotal))
            st.caption("Tap the 🛒 banner on the main page to review and checkout.")


def render_checkout_panel():
    """Full checkout flow -- cart items, service type, optional tip with
    waiter selection, WhatsApp send button. Rendered INLINE on the main
    page when the cart banner is tapped open."""
    cart = st.session_state.cart
    if not cart:
        return

    subtotal = 0
    cart_items = []
    max_wait = 0
    for c in cart.values():
        line_total = c["price"] * c["quantity"]
        subtotal += line_total
        max_wait = max(max_wait, c["estimated_minutes"])
        cart_items.append(
            {"name": c["name"], "quantity": c["quantity"], "unit_price": c["price"], "line_total": line_total}
        )

    st.markdown("<div class='checkout-panel'>", unsafe_allow_html=True)
    st.markdown("#### Your Order")
    for c in cart_items:
        st.write(f"{c['quantity']} × {c['name']} — {format_ugx(c['line_total'])}")

    st.markdown("<hr class='gold-rule'>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-family:Playfair Display,serif;color:#e6c87a;font-size:1.15rem;'>"
        f"Subtotal &nbsp;·&nbsp; {format_ugx(subtotal)}</p>",
        unsafe_allow_html=True,
    )
    st.caption(f"Estimated wait ~{max_wait} min")

    service_type = st.radio("Served as", ["Dine-in", "Takeaway"], horizontal=True, key="ck_service_type")

    table_number = None
    if service_type == "Dine-in":
        table_number = current_table["label"] if current_table else st.text_input(
            "Table number", key="ck_table_number"
        )

    st.markdown("<hr class='gold-rule'>", unsafe_allow_html=True)
    st.caption("ADD A TIP (OPTIONAL)")
    add_tip = st.checkbox("Add a tip for your server", key="ck_add_tip")
    tip_amount = 0
    waiter_id = None
    if add_tip:
        tip_amount = st.number_input("Tip amount (UGX)", min_value=0, step=1000, key="ck_tip_amount")
        staff = get_waiter_staff()
        if staff:
            staff_options = {s["name"]: s["id"] for s in staff}
            waiter_name = st.selectbox("Who served you?", list(staff_options.keys()), key="ck_waiter")
            waiter_id = staff_options.get(waiter_name)
        else:
            st.caption("Tip will be recorded without a specific server.")

    total = subtotal + tip_amount
    if tip_amount:
        st.markdown(
            f"<p style='font-family:Playfair Display,serif;color:#e6c87a;font-size:1.1rem;'>"
            f"Total incl. tip &nbsp;·&nbsp; {format_ugx(total)}</p>",
            unsafe_allow_html=True,
        )

    notes = st.text_input("Notes for kitchen / bar (optional)", key="ck_notes")

    if st.button("SEND ORDER VIA WHATSAPP", type="primary", use_container_width=True, key="ck_send"):
        order_number = generate_order_number()
        table_id = current_table["id"] if current_table else None
        service_key = "dine_in" if service_type == "Dine-in" else "takeaway"

        order_row = execute(
            """insert into orders (order_number, table_id, service_type, status, subtotal, tip_amount, total, notes, waiter_id)
               values (%s, %s, %s, 'pending', %s, %s, %s, %s, %s) returning id""",
            (order_number, table_id, service_key, subtotal, tip_amount, total, notes, waiter_id),
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

        if tip_amount > 0 and waiter_id:
            execute(
                "insert into tips (order_id, staff_id, amount, method) values (%s, %s, %s, 'added_to_bill')",
                (order_id, waiter_id, tip_amount),
            )

        label = table_number or "Takeaway"
        link = build_whatsapp_order_link(WHATSAPP_NUMBER, order_number, label, cart_items, total, notes)
        st.session_state.order_number_last = order_number
        st.session_state.cart = {}
        st.session_state.show_checkout = False
        st.success(f"Order {order_number} placed!")
        st.link_button("Open WhatsApp", link, use_container_width=True)
        st.caption("Track it under My Order Status.")

    st.markdown("</div>", unsafe_allow_html=True)


render_sidebar_note()

st.markdown("<p class='hero-eyebrow'>Kiwatule · Kampala</p>", unsafe_allow_html=True)
st.markdown(
    "<h1 class='hero-title'>El Nivel<br>Bar &amp; Lounge</h1>",
    unsafe_allow_html=True,
)
st.markdown("<p class='hero-sub'>Scan · Order · Sip</p>", unsafe_allow_html=True)
if current_table:
    st.markdown(f"<span class='table-badge'>Table {current_table['label']}</span>", unsafe_allow_html=True)
st.markdown("<hr class='gold-rule'>", unsafe_allow_html=True)

category = st.radio("Browse", ["Restaurant", "Bar"], horizontal=True, label_visibility="collapsed")
cat_key = "restaurant" if category == "Restaurant" else "bar"

# ---------- tappable cart banner -- opens checkout INLINE on this page ----------
if st.session_state.cart:
    _count = sum(c["quantity"] for c in st.session_state.cart.values())
    _subtotal = sum(c["price"] * c["quantity"] for c in st.session_state.cart.values())
    _label = "🛒  Hide checkout ▲" if st.session_state.show_checkout else f"🛒 {_count} item{'s' if _count != 1 else ''} · {format_ugx(_subtotal)} — tap to checkout ▼"
    if st.button(_label, key="cart_toggle", use_container_width=True):
        st.session_state.show_checkout = not st.session_state.show_checkout
        st.rerun()

    if st.session_state.show_checkout:
        render_checkout_panel()
    st.markdown("<hr class='gold-rule'>", unsafe_allow_html=True)

items = get_menu_items(cat_key)

if not items:
    st.info("This menu is being refreshed - please ask our team for today's selection.")
else:
    groups = {}
    for it in items:
        groups.setdefault(it.get("subcategory") or "Menu", []).append(it)

    for group_name, group_items in groups.items():
        st.markdown(f"<p class='premium-label'>{group_name}</p>", unsafe_allow_html=True)
        for it in group_items:
            wait = it.get("estimated_minutes") or 5
            desc = it.get("description") or ""
            desc_html = f"<div class='item-desc'>{desc}</div>" if desc else ""

            col_card, col_qty = st.columns([3.2, 1])
            with col_card:
                st.markdown(
                    "<div class='menu-card'>"
                    f"<div class='item-name'>{it['name']}</div>"
                    f"{desc_html}"
                    f"<div class='item-price'>{format_ugx(float(it['price']))} &nbsp;·&nbsp; ~{wait} min</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            with col_qty:
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
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
