"""Shared helpers: WhatsApp message building, currency formatting, order codes."""
import random
import string
import urllib.parse


def format_ugx(amount):
    """UGX 45,000 style formatting."""
    return f"UGX {amount:,.0f}"


def generate_order_number():
    """Short human-friendly order code, e.g. ORD-4471."""
    return f"ORD-{random.randint(1000, 9999)}"


def build_whatsapp_order_link(whatsapp_number, order_number, table_label, items, subtotal, notes=""):
    """
    Build a wa.me link pre-filled with the order details, matching the
    same QR -> WhatsApp pattern as the rooms app.
    items: list of dicts with keys name, quantity, unit_price, line_total
    """
    lines = [
        f"New order: {order_number}",
        f"Table: {table_label}",
        "",
        "Items:",
    ]
    for it in items:
        lines.append(f"- {it['quantity']}x {it['name']} ({format_ugx(it['line_total'])})")
    lines.append("")
    lines.append(f"Subtotal: {format_ugx(subtotal)}")
    if notes:
        lines.append(f"Notes: {notes}")
    lines.append("")
    lines.append("Please confirm my order.")

    message = "\n".join(lines)
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{whatsapp_number}?text={encoded}"


def build_whatsapp_receipt_link(whatsapp_number, order_number, items, subtotal, tip, total):
    """Confirmation/receipt-style message once an order is marked paid."""
    lines = [
        f"Receipt for {order_number}",
        "",
    ]
    for it in items:
        lines.append(f"- {it['quantity']}x {it['name']}: {format_ugx(it['line_total'])}")
    lines.append("")
    lines.append(f"Subtotal: {format_ugx(subtotal)}")
    if tip:
        lines.append(f"Tip: {format_ugx(tip)}")
    lines.append(f"Total: {format_ugx(total)}")
    lines.append("")
    lines.append("Thank you for visiting!")

    message = "\n".join(lines)
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{whatsapp_number}?text={encoded}"


STATUS_COLORS = {
    "pending": "#94a3b8",
    "confirmed": "#3b82f6",
    "preparing": "#f59e0b",
    "ready": "#10b981",
    "served": "#8b5cf6",
    "paid": "#22c55e",
    "cancelled": "#ef4444",
}

STATUS_LABELS = {
    "pending": "🕐 Pending",
    "confirmed": "✅ Confirmed",
    "preparing": "👨‍🍳 Preparing",
    "ready": "🔔
