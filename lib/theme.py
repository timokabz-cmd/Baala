Good, useful to know it's not just your logged-in view — let's fix both properly.

**1. Fork/GitHub bar** — I was wrong to assume this only shows to you. This is Streamlit Cloud's **"Hosted by Streamlit" toolbar**, which appears to *everyone* by default, not just the owner. It's controllable via a setting, not something guests can dismiss. Let's hide it properly with the correct CSS target (my earlier `[data-testid="stHeader"]` fix handled the header but missed this specific toolbar element, which Streamlit renders in a different container).

**2. Cart delay + no delete option** — let's dig into why caching alone didn't fix the delay, and add a proper remove button per cart item.

Let's fix the toolbar first:

That confirms it — I never targeted the actual toolbar element (`stToolbar` / `stDeployButton` / viewer badge), only the header bar. Let's add the correct selectors:

Now let's tackle the cart delay properly. The caching I added should have helped the *menu query*, but the real bottleneck may be something else — every widget interaction in Streamlit re-runs the **entire script**, including all the `st.markdown` HTML rendering for every single menu card (30+ items), not just the DB query. Let's check how many items are actually rendering per category, since that itself could be the lag if there's no pagination:

The bar menu alone has ~100+ drink items across all those insert blocks. That's a lot of `st.markdown` + `st.number_input` widget pairs rendering on every single rerun — likely the real cause of the lag, more than the DB query itself. Let's fix this properly with Streamlit's `st.form`, which batches all the quantity inputs and only reruns once, on submit, rather than on every single `+` tap:

Actually, wrapping the whole menu in a form changes behavior significantly (no live item-by-item feedback), which may not be what you want. A better, more surgical fix: since Bar has ~100 items but a guest only views one category at a time (Restaurant *or* Bar), the real fix is to **not render number inputs for items with 0 quantity as separate always-live widgets** — but actually, the simplest true fix for perceived speed is different: **the delay you're describing (~20 sec) is far larger than normal Streamlit rerun overhead** even for 100 widgets. This smells like it's still a network call happening somewhere per-tap. Let me check the full render loop for anything still querying live:

Found the real bug — this is a critical one: **`value=0` is hardcoded** on every `number_input`. That means every rerun resets the widget back to displaying `0`, ignoring `st.session_state[f"qty_{it['id']}"]` which Streamlit already tracks automatically via the `key`. There's no explicit network delay bug — the actual problem is a **state/rerender conflict**: Streamlit is fighting itself between the hardcoded `value=0` and the widget's own session-state-backed value, which can cause exactly this kind of sluggish, delayed-looking behavior as it reconciles on each rerun.

Let's fix this properly and add per-item delete/remove capability at the same time:

Now let's add per-item remove buttons in the checkout panel itself, since that's the natural place a guest expects to edit their cart:

Let's rebuild this section to include a remove (✕) button per line item, and make sure removing also resets the corresponding `qty_` widget key so the menu list reflects it correctly:

There's a subtlety here: since `render_checkout_panel()` returns early if cart becomes empty, and we `del` mid-loop then `st.rerun()` immediately, that's safe — the rerun restarts the whole script fresh rather than continuing the now-stale loop. Let's verify:

Clean. Let me do one more check — confirm the qty widget reset logic is safe (Streamlit disallows setting a widget's session-state key directly if the widget hasn't been instantiated yet in that run, but since we `st.rerun()` right after, the next full run will read the reset value before the widget re-renders, which is the correct pattern):

All verified. Here are both complete files.

**File A — replace `lib/theme.py`**

```python
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

#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] {
    background: transparent;
}
/* Keep the sidebar toggle control visible and tappable -- the previous
   rule hid the entire header, which also hid this button, locking users
   out of the sidebar (cart, order status, staff/admin login) entirely. */
[data-testid="stHeader"] button {
    visibility: visible !important;
    color: #e6c87a !important;
}
/* Hide Streamlit Cloud's own chrome: the Fork/GitHub/menu toolbar and
   the "Hosted with Streamlit" viewer badge. These are separate elements
   from stHeader, which is why they survived the earlier fix. */
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stAppDeployButton,
[data-testid="stAppViewerBadge"],
a[href*="streamlit.io"] {
    visibility: hidden !important;
    display: none !important;
}

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
/* Force dark text on ALL inner elements of the button -- Streamlit wraps
   the label in nested <p>/<div> tags that otherwise inherit the lighter
   body text color and wash out against the gold background. */
.stButton > button, .stButton > button * {
    color: #171106 !important;
}
.stButton > button:hover { filter: brightness(1.08); }
.stButton > button:hover, .stButton > button:hover * { color: #171106 !important; }
.stButton > button:active { filter: brightness(0.96); }

/* Inline checkout panel (opened from the on-page cart banner) */
.checkout-panel {
    background: linear-gradient(160deg, #1d1610 0%, #130e0a 100%);
    border: 1px solid rgba(201,162,39,0.28);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin: 0.6rem 0 1.2rem;
    box-shadow: 0 6px 24px rgba(0,0,0,0.4);
}

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
```

**File B — replace `guest/home.py`**
