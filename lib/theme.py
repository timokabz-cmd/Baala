"""
Premium visual theme for El Nivel Bar & Lounge.
Import and call inject_theme() once at the top of every page file,
immediately after the imports (main.py already calls st.set_page_config,
so no page should call it again).
"""
import streamlit as st

PREMIUM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500&family=Jost:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

html, body, [class*="css"] { font-family: 'Jost', sans-serif; }

.stApp {
    background: radial-gradient(1200px 620px at 50% -10%, #251a10 0%, #0f0c0a 55%) fixed;
    color: #f2ead9;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }

.main .block-container { max-width: 640px; padding-top: 2.2rem; padding-bottom: 6rem; }
@media (max-width: 640px) {
    .main .block-container { padding-left: 1rem; padding-right: 1rem; }
}

h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #e6c87a !important;
    font-weight: 600;
    letter-spacing: 0.02em;
}
p, span, label, .stMarkdown, .stCaption, div[data-testid="stCaptionContainer"], small {
    color: #cbbb9d;
}

.hero-eyebrow {
    letter-spacing: 0.42em; text-transform: uppercase; color: #8a7a5e;
    font-size: 0.68rem; font-weight: 500;
}
.hero-title {
    font-family: 'Playfair Display', serif; font-size: 2.5rem; color: #e6c87a;
    margin: 0.25rem 0 0; line-height: 1.08; font-weight: 600;
}
.hero-sub {
    color: #a89880; font-weight: 300; letter-spacing: 0.18em;
    font-size: 0.78rem; text-transform: uppercase; margin-top: 0.4rem;
}
.gold-rule {
    height: 1px; border: none; margin: 1.2rem 0;
    background: linear-gradient(90deg, transparent, rgba(201,162,39,0.55), transparent);
}
.table-badge {
    display: inline-block; border: 1px solid rgba(201,162,39,0.45); color: #e6c87a;
    border-radius: 999px; padding: 0.32rem 1rem; font-size: 0.75rem;
    letter-spacing: 0.16em; text-transform: uppercase; margin-top: 0.9rem;
}

.premium-label {
    font-size: 0.7rem; letter-spacing: 0.3em; text-transform: uppercase;
    color: #a89880; margin: 1.7rem 0 0.7rem; font-weight: 500;
}
.menu-card {
    background: linear-gradient(160deg, #1d1610 0%, #130e0a 100%);
    border: 1px solid rgba(201,162,39,0.16);
    border-radius: 14px; padding: 0.85rem 1.1rem; min-height: 88px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.35);
}
.item-name { font-family: 'Playfair Display', serif; color: #e6c87a; font-size: 1.06rem; font-weight: 600; }
.item-desc { color: #9d8d72; font-size: 0.84rem; font-weight: 300; margin-top: 0.15rem; }
.item-price { color: #c9a227; letter-spacing: 0.06em; font-size: 0.92rem; font-weight: 500; margin-top: 0.3rem; }

div[role="radiogroup"] {
    gap: 0.4rem; background: rgba(0,0,0,0.3); padding: 0.3rem;
    border-radius: 999px; border: 1px solid rgba(201,162,39,0.14);
}
div[role="radiogroup"] label { border-radius: 999px !important; padding: 0.3rem 1rem !important; border: 1px solid transparent; }
div[role="radiogroup"] label p { color: #d8cbaa !important; font-weight: 400; }
div[role="radiogroup"] label:has(input:checked) { background: linear-gradient(135deg, #e6c87a, #c9a227) !important; }
div[role="radiogroup"] label:has(input:checked) p { color: #171106 !important; font-weight: 600; }

.stButton > button {
    background: linear-gradient(135deg, #e6c87a 0%, #c9a227 100%) !important;
    color: #171106 !important; border: none !important; border-radius: 10px !important;
    font-family: 'Jost', sans-serif !important; letter-spacing: 0.08em;
    font-weight: 600 !important; box-shadow: 0 4px 18px rgba(201,162,39,0.28);
    transition: filter 0.15s ease;
}
.stButton > button:hover { filter: brightness(1.08); color: #171106 !important; }
.stButton > button:active { filter: brightness(0.96); }

section[data-testid="stSidebar"] {
    background: #0b0806;
    border-right: 1px solid rgba(201,162,39,0.12);
}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #e6c87a !important; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stCaption {
    color: #cbbb9d !important;
}
.stSidebar .gold-rule { margin: 0.8rem 0; }

div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] > div, div[data-baseweb="select"] > div {
    color: #f2ead9 !important; background-color: #1c150f !important;
    border: 1px solid rgba(201,162,39,0.28) !important; border-radius: 8px !important;
}
div[data-testid="stNumberInput"] { width: 92px; }
div[data-testid="stNumberInput"] button { color: #c9a227 !important; }
div[data-baseweb="checkbox"] span { color: #cbbb9d !important; }
div[data-baseweb="checkbox"] > div:first-child { border-color: #c9a227 !important; }
hr { border-color: rgba(201,162,39,0.14) !important; }

div[data-testid="stInfo"] {
    background: rgba(201,162,39,0.08); border: 1px solid rgba(201,162,39,0.25);
}
div[data-testid="stSuccess"] {
    background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.3);
}
div[data-testid="stSuccess"] p, div[data-testid="stInfo"] p { color: #e6dcc4 !important; }
"""


def inject_theme():
    st.markdown(f"<style>{PREMIUM_CSS}</style>", unsafe_allow_html=True)
