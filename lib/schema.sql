-- ============================================================
-- Bar & Restaurant Management System — Schema
-- Run this once in Supabase SQL Editor (or via psql) to set up.
-- ============================================================

-- ---------- MENU ----------
create table if not exists menu_items (
    id            bigserial primary key,
    name          text not null,
    description   text,
    category      text not null check (category in ('bar', 'restaurant')),
    subcategory   text,
    price         numeric(12,2) not null,
    cost_price    numeric(12,2),
    photo_url     text,
    is_available  boolean default true,
    track_stock   boolean default false,
    inventory_id  bigint,
    created_at    timestamptz default now(),
    updated_at    timestamptz default now()
);

-- ---------- TABLES ----------
create table if not exists tables (
    id            bigserial primary key,
    label         text not null,
    zone          text,
    qr_slug       text unique not null,
    is_active     boolean default true,
    created_at    timestamptz default now()
);

-- ---------- STAFF ----------
create table if not exists staff (
    id            bigserial primary key,
    name          text not null,
    role          text not null check (role in ('owner', 'manager', 'waiter', 'bartender', 'chef', 'cashier')),
    phone         text,
    pin_hash      text,
    is_active     boolean default true,
    created_at    timestamptz default now()
);

-- ---------- SHIFTS ----------
create table if not exists shifts (
    id            bigserial primary key,
    staff_id      bigint references staff(id) on delete cascade,
    shift_date    date not null,
    start_time    time not null,
    end_time      time not null,
    role_on_shift text,
    notes         text,
    created_at    timestamptz default now()
);

-- ---------- INVENTORY ----------
create table if not exists inventory (
    id             bigserial primary key,
    item_name      text not null,
    unit           text not null,
    quantity_on_hand numeric(12,2) not null default 0,
    reorder_level  numeric(12,2) not null default 0,
    cost_per_unit  numeric(12,2),
    supplier       text,
    last_restocked timestamptz,
    created_at     timestamptz default now(),
    updated_at     timestamptz default now()
);

alter table menu_items
    add constraint fk_menu_inventory foreign key (inventory_id) references inventory(id) on delete set null;

create table if not exists inventory_movements (
    id            bigserial primary key,
    inventory_id  bigint references inventory(id) on delete cascade,
    change_qty    numeric(12,2) not null,
    reason        text,
    staff_id      bigint references staff(id),
    created_at    timestamptz default now()
);

-- ---------- ORDERS ----------
create table if not exists orders (
    id             bigserial primary key,
    order_number   text unique not null,
    table_id       bigint references tables(id),
    service_type   text not null check (service_type in ('dine_in', 'takeaway', 'delivery')),
    status         text not null default 'pending'
                   check (status in ('pending','confirmed','preparing','ready','served','paid','cancelled')),
    subtotal       numeric(12,2) not null default 0,
    tip_amount     numeric(12,2) not null default 0,
    total          numeric(12,2) not null default 0,
    payment_method text check (payment_method in ('cash','mobile_money','card','not_paid')),
    waiter_id      bigint references staff(id),
    guest_phone    text,
    notes          text,
    created_at     timestamptz default now(),
    updated_at     timestamptz default now()
);

create table if not exists order_items (
    id            bigserial primary key,
    order_id      bigint references orders(id) on delete cascade,
    menu_item_id  bigint references menu_items(id),
    item_name     text not null,
    unit_price    numeric(12,2) not null,
    quantity      integer not null default 1,
    line_total    numeric(12,2) not null
);

-- ---------- TIPS ----------
create table if not exists tips (
    id            bigserial primary key,
    order_id      bigint references orders(id) on delete cascade,
    staff_id      bigint references staff(id),
    amount        numeric(12,2) not null,
    method        text check (method in ('cash','mobile_money','added_to_bill')),
    created_at    timestamptz default now()
);

-- ---------- INDEXES ----------
create index if not exists idx_orders_status on orders(status);
create index if not exists idx_orders_created on orders(created_at);
create index if not exists idx_order_items_order on order_items(order_id);
create index if not exists idx_tips_staff on tips(staff_id);
create index if not exists idx_shifts_date on shifts(shift_date);
create index if not exists idx_menu_category on menu_items(category);
