"""Premium landing page for El Nivel Bar & Lounge - the first screen a
guest sees after scanning a table QR code: business logo, address, and
two large links into the Restaurant and Bar menus.

PURELY ADDITIVE: no existing file is modified. Requires:
1. This file added as guest/landing.py
2. It registered in main.py (see the accompanying main.py - additive only)
3. The logo image committed to the repo as assets/logo.png
   (a styled text fallback is shown if the file is missing)
"""
import base64
import os

import streamlit as st
from lib.db import query

ADDRESS_LINE_1 = "Kiwatule · Kampala"
ADDRESS_LINE_2 = "After Oryx Petrol Station - road on the right before the bridge"
TAGLINE = "Bar & Restaurant — one tap away."
LOGO_PATH = "assets/logo.png"

LANDING_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500&family=Jost:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

.stApp { background: #f4eee3 !important; }
[data-testid="stHeader"] { background: transparent !important; }

/* keep the nav sidebar consistent with the dark app theme */
section[data-testid="stSidebar"] { background: #14100c; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label { color: #e8dcc2 !important; }

.landing-logo-card {
    background: #ffffff; border-radius: 26px; padding: 1.7rem 2rem;
    box-shadow: 0 14px 40px rgba(28,19,12,0.14); text-align: center;
    margin-top: 0.4rem;
}
.landing-logo-card img { width: 100%; max-width: 330px; display: block; margin: 0 auto; }
.landing-fallback {
    font-family: 'Playfair Display', Georgia, serif; font-size: 2.1rem;
    color: #1c130c; letter-spacing: 0.01em;
}
.landing-eyebrow {
    letter-spacing: 0.34em; text-transform: uppercase; color: #8a7a63;
    font-size: 0.74rem; font-weight: 500; text-align: center; margin-top: 1.1rem;
}
.landing-address {
    color: #6f6152; font-size: 0.8rem; font-weight: 400; text-align: center;
    margin-top: 0.5rem; letter-spacing: 0.03em;
}
.landing-table {
    display: inline-block; border: 1px solid rgba(28,19,12,0.28); color: #1c130c;
    border-radius: 999px; padding: 0.3rem 1rem; font-size: 0.72rem;
    letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 0.9rem;
}
.landing-rule {
    height: 1px; border: none; margin: 1.5rem auto 1.1rem; width: 64px;
    background: linear-gradient(90deg, transparent, #e87722, transparent);
}
.landing-tagline {
    font-family: 'Playfair Display', Georgia, serif; font-style: italic;
    color: #4a3e30; font-size: 1.05rem; text-align: center; margin-bottom: 1.8rem;
}
.landing-footer {
    text-align: center; color: #a3967f; font-size: 0.7rem;
    letter-spacing: 0.24em; text-transform: uppercase; margin-top: 2.8rem;
}

/* the only buttons on this page are the two menu links */
.stButton > button {
    background: #1c130c !important; color: #f7f2e7 !important;
    border: none !important; border-radius: 16px !important;
    padding: 0.9rem 1rem !important; font-family: 'Jost', sans-serif !important;
    font-size: 1.0rem !important; letter-spacing: 0.1em !important;
    font-weight: 500 !important; box-shadow: 0 8px 24px rgba(28,19,12,0.22) !important;
    height: auto !important; min-height: 3.4rem !important;
    transition: transform 0.15s ease, background 0.15s ease !important;
}
.stButton > button:hover {
    background: #e87722 !important; color: #fffdf8 !important;
    transform: translateY(-1px);
}
"""

st.markdown(f"<style>{LANDING_CSS}</style>", unsafe_allow_html=True)

# ---- table context (same read-only lookup as guest/home.py; a DB hiccup
# must never take the landing page down) ----
table_label = None
table_slug = st.query_params.get("table", None)
if table_slug:
    try:
        rows = query("select label from tables where qr_slug = %s and is_active = true", (table_slug,))
        if rows:
            table_label = rows[0]["label"]
    except Exception:
        pass

# ---- hero: logo, address, tagline ----
if table_label:
    st.markdown(
        f"<div style='text-align:center'><span class='landing-table'>Table {table_label}</span></div>",
        unsafe_allow_html=True,
    )

if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        "<div class='landing-logo-card'>"
        f"<img src='data:image/png;base64,{logo_b64}' alt='el Nivel'/>"
        "</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<div class='landing-logo-card'>"
        "<span class='landing-fallback'>el N<span style='color:#e87722'>iv</span>el</span>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown(f"<p class='landing-eyebrow'>{ADDRESS_LINE_1}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='landing-address'>{ADDRESS_LINE_2}</p>", unsafe_allow_html=True)
st.markdown("<hr class='landing-rule'>", unsafe_allow_html=True)
st.markdown(f"<p class='landing-tagline'>{TAGLINE}</p>", unsafe_allow_html=True)

# ---- the two menu links ----
if st.button("🍽️   Restaurant", use_container_width=True):
    st.switch_page("guest/home.py")
if st.button("🍸   Bar", use_container_width=True):
    st.switch_page("guest/home.py")

st.markdown("<p class='landing-footer'>Kampala · Uganda</p>", unsafe_allow_html=True)
