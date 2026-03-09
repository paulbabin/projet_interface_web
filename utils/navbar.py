"""
Module partagé pour les styles et la navbar commune à toutes les pages.
Utilise st.page_link() pour naviguer sans ouvrir de nouveaux onglets.
"""
import streamlit as st


def inject_navbar_css():
    """Injecte le CSS minimaliste partagé pour toutes les pages."""
    st.markdown("""
    <style>
    /* ===== Google Font ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ===== Global ===== */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ===== Hide Sidebar ===== */
    section[data-testid="stSidebar"] { display: none !important; }
    button[data-testid="stSidebarCollapsedControl"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* ===== Navbar container ===== */
    .navbar-container {
        border-bottom: 1px solid #e2e8f0;
        margin: -1rem -1rem 1.5rem -1rem;
        padding: 0.6rem 2rem;
        background: #ffffff;
    }
    .navbar-brand-text {
        font-size: 1.35rem;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.5px;
        line-height: 2.4rem;
    }
    .navbar-brand-text span { color: #2563eb; }

    /* ===== Page Links (st.page_link) — style as navbar items ===== */
    [data-testid="stPageLink"] a {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        color: #64748b !important;
        padding: 0.45rem 0.9rem !important;
        border-radius: 6px !important;
        text-decoration: none !important;
        transition: all 0.2s ease !important;
        border: none !important;
        background: transparent !important;
    }
    [data-testid="stPageLink"] a:hover {
        color: #2563eb !important;
        background: #f1f5f9 !important;
    }
    /* Active page link */
    [data-testid="stPageLink"] a[aria-current="page"],
    .nav-active [data-testid="stPageLink"] a {
        color: #2563eb !important;
        background: #eff6ff !important;
        font-weight: 600 !important;
    }

    /* ===== Headers ===== */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: #1e293b !important;
        letter-spacing: -0.5px;
    }

    /* ===== Metrics ===== */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #2563eb;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
        transform: translateY(-2px);
    }
    [data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1e293b !important;
        font-weight: 700;
    }

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: transparent;
        border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748b;
        font-weight: 500;
        padding: 0.8rem 1.2rem;
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
        border-bottom: 2px solid #2563eb !important;
        font-weight: 600;
    }

    /* ===== Buttons ===== */
    .stButton > button {
        background: #2563eb !important;
        color: #ffffff !important;
        font-weight: 600;
        border: none !important;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #1d4ed8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }

    /* ===== Download Button ===== */
    .stDownloadButton > button {
        background: transparent !important;
        color: #2563eb !important;
        border: 1px solid #2563eb !important;
        font-weight: 500;
        border-radius: 8px;
    }
    .stDownloadButton > button:hover {
        background: #eff6ff !important;
    }

    /* ===== Inputs ===== */
    .stTextInput input {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px;
    }
    .stTextInput input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }

    /* ===== DataFrame ===== */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
    }

    /* ===== Dividers ===== */
    hr { border: none; height: 1px; background: #e2e8f0; }

    /* ===== Footer ===== */
    .site-footer {
        text-align: center;
        padding: 2rem 0;
        color: #94a3b8;
        font-size: 0.85rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
    }

    @media (max-width: 768px) {
        .navbar-container { padding: 0.6rem 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_navbar(active_page="Accueil"):
    """Affiche la navbar avec st.page_link() pour la navigation interne (même onglet)."""

    # Brand + links in columns
    brand_col, *link_cols = st.columns([2, 1, 1, 1, 1, 1, 1])

    with brand_col:
        st.markdown(
            '<div class="navbar-brand-text">🏙️ <span>Compa</span>Ville</div>',
            unsafe_allow_html=True
        )

    pages = [
        ("Accueil", "app.py"),
        ("Focus ville", "pages/5_Donnees_Generales.py"),
        ("Emploi", "pages/2_Emploi.py"),
        ("Logement", "pages/3_Logement.py"),
        ("Météo", "pages/4_Meteo.py"),
        ("Comparaison", "pages/1_Comparaison.py"),
    ]

    for col, (label, page_path) in zip(link_cols, pages):
        with col:
            st.page_link(page_path, label=label)

    # Séparateur sous la navbar
    st.markdown('<div style="border-bottom:1px solid #e2e8f0; margin: -0.5rem -1rem 1.5rem -1rem;"></div>', unsafe_allow_html=True)
