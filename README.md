# El Nivel Bar & Lounge — QR Menu, Ordering, Inventory, Tips & Staff

Streamlit app: guests scan a table QR, browse the real El Nivel menu, and
send orders via WhatsApp. Staff manage orders, payments/tips, inventory,
schedules, and analytics from admin pages — genuinely hidden from guests
until an admin password is entered (using st.navigation, not just a
per-page password check).

## Structure

- `main.py` — entry point, controls which pages are visible to whom
- `guest/` — menu browsing, cart, WhatsApp checkout, order status lookup
- `admin/` — orders queue, payments/tips, inventory, staff/schedule,
  analytics, menu manager, tables/QR — only visible after admin login
- `staff/` — PIN-based self-service page for staff to see their own tips
  and upcoming shifts, without needing the shared admin password
- `lib/` — database connection, shared utilities, schema, nav/auth logic

## Setup

1. Run `lib/schema.sql` then `lib/schema_v2.sql` in Supabase SQL Editor
2. Run `seed_el_nivel.sql` to load the real menu and starter tables
3. Set Streamlit Cloud **Main file path** to `main.py`
4. Set secrets in **Settings → Secrets**:
```toml
postgres_url = "postgresql://postgres.xxxx:PASSWORD@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
whatsapp_number = "256XXXXXXXXX"
admin_password = "yourpassword"
