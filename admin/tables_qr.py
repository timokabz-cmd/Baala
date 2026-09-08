"""Manage tables and generate their QR codes, pointing at the correct main.py-based URL."""
import streamlit as st
import re
from lib.db import query, execute

st.title("🔗 Tables & QR Codes")

app_url = st.text_input(
    "Your live app URL — paste the ROOT url only, no page name at the end",
    value=st.session_state.get("app_url", ""),
    placeholder="https://your-app.streamlit.app",
)
if app_url:
    st.session_state.app_url = app_url

st.divider()
st.subheader("Tables")
tables = query("select * from tables order by label")
for t in tables:
    with st.container(border=True):
        st.write(f"**{t['label']}** ({t.get('zone') or 'no zone'})")
        if app_url:
            link = f"{app_url.rstrip('/')}/?table={t['qr_slug']}"
            st.code(link, language=None)
            try:
                import qrcode
                import io
                img = qrcode.make(link)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.image(buf.getvalue(), width=180, caption=f"QR for {t['label']}")
                st.download_button(
                    "Download QR", buf.getvalue(), file_name=f"{t['qr_slug']}_qr.png", key=f"dl_{t['id']}"
                )
            except ImportError:
                st.caption("Install `qrcode` package to generate QR images.")

st.divider()
st.subheader("➕ Add a table")
label = st.text_input("Table label", placeholder="e.g. Table 4, VIP 1, Patio 2")
zone = st.text_input("Zone (optional)", placeholder="e.g. Indoor, Patio, VIP")
if st.button("Add table", type="primary"):
    if label:
        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        execute("insert into tables (label, zone, qr_slug) values (%s, %s, %s)", (label, zone, slug))
        st.success(f"Added {label}")
        st.rerun()
