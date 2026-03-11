"""
🏙️ CompaVille - Comparateur de Villes Françaises
Page principale avec carte interactive des villes > 20 000 habitants
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer utils
sys.path.append(str(Path(__file__).parent))
from utils.data_loader import load_cities_data
from utils.navbar import inject_navbar_css, render_navbar

# Configuration de la page
st.set_page_config(
    page_title="CompaVille - Comparateur de Villes",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== Navbar =====
inject_navbar_css()
render_navbar("Accueil")

# ===== Page Header =====
st.markdown("""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-size:2.2rem; font-weight:700; color:#1e293b; margin:0; letter-spacing:-1px;">
        Explorez les villes françaises
    </h1>
    <p style="color:#64748b; font-size:1.05rem; margin-top:0.5rem;">
        Carte interactive et données des villes de plus de 20 000 habitants
    </p>
</div>
""", unsafe_allow_html=True)

# Chargement des données
with st.spinner("Chargement des données..."):
    df_cities = load_cities_data()

if df_cities.empty:
    st.error("❌ Impossible de charger les données des villes")
    st.stop()

# ===== Données complètes (sans filtre) =====
df_filtered = df_cities

# ===== Contenu principal (sans onglets) =====
st.header("Statistiques")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Villes affichées",
        f"{len(df_filtered):,}",
        delta=f"{len(df_filtered) - len(df_cities)}" if len(df_filtered) != len(df_cities) else None
    )

if 'population' in df_filtered.columns:
    with col2:
        st.metric("Population totale", f"{int(df_filtered['population'].sum()):,}")

    with col3:
        st.metric(
            "Plus grande ville",
            df_filtered.loc[df_filtered['population'].idxmax(), 'ville'] if 'ville' in df_filtered.columns else "N/A",
            f"{int(df_filtered['population'].max()):,} hab."
        )

    with col4:
        st.metric(
            "Plus petite ville",
            df_filtered.loc[df_filtered['population'].idxmin(), 'ville'] if 'ville' in df_filtered.columns else "N/A",
            f"{int(df_filtered['population'].min()):,} hab."
        )

st.divider()
st.header("Carte des Villes Françaises")

if 'lat' in df_filtered.columns and 'lon' in df_filtered.columns:
    # Define base map properties
    fig = px.scatter_mapbox(
        df_filtered,
        lat='lat',
        lon='lon',
        hover_name='ville' if 'ville' in df_filtered.columns else None,
        hover_data={
            'population': ':,',
            'lat': ':.4f',
            'lon': ':.4f'
        } if 'population' in df_filtered.columns else None,
        size='population' if 'population' in df_filtered.columns else None,
        color='population' if 'population' in df_filtered.columns else None,
        # Echelle de couleur du bleu clair au bleu foncé/violet
        color_continuous_scale=["#bbd1e7","#1e3a8a", "#5e0580"],
        # Caper l'échelle de couleur à 500 000 pour mieux voir les nuances des villes moyennes
        range_color=[0, 500000],
        size_max=35,
        zoom=4.8,
        center={'lat': 46.603354, 'lon': 1.888334}, # Centre de la France
        height=600,
    )

    # Style 'carto-positron' public
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter'),
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Coordonnées géographiques non disponibles pour la carte")

if 'population' in df_filtered.columns:
    st.divider()

    st.subheader("Top 10 des villes")
    if 'ville' in df_filtered.columns:
        top10 = df_filtered.nlargest(10, 'population')[['ville', 'population']]
        fig_bar = px.bar(
            top10,
            x='population',
            y='ville',
            orientation='h',
            title="Top 10 des villes les plus peuplées",
            labels={'population': 'Population', 'ville': 'Ville'},
            color_discrete_sequence=['#3b82f6']
        )
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color='#1e293b'),
            title_font=dict(size=14),
            xaxis=dict(gridcolor='#f1f5f9'),
            yaxis=dict(gridcolor='#f1f5f9')
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    st.subheader("Tableau des villes")

    search = st.text_input("Rechercher une ville", placeholder="Entrez le nom d'une ville...", key="search_stats")

    if search:
        df_display = df_filtered[df_filtered['ville'].str.contains(search, case=False, na=False)] if 'ville' in df_filtered.columns else df_filtered
    else:
        df_display = df_filtered

    display_columns = []
    if 'ville' in df_display.columns:
        display_columns.append('ville')
    if 'population' in df_display.columns:
        display_columns.append('population')
    if 'departement_code' in df_display.columns:
        display_columns.append('departement_code')
    if 'altitude' in df_display.columns:
        display_columns.append('altitude')
    if 'lat' in df_display.columns and 'lon' in df_display.columns:
        display_columns.extend(['lat', 'lon'])

    if display_columns:
        st.dataframe(
            df_display[display_columns].sort_values('population', ascending=False) if 'population' in display_columns else df_display[display_columns],
            use_container_width=True,
            height=400
        )
    else:
        st.dataframe(df_display, use_container_width=True, height=400)

    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger les données (CSV)",
        data=csv,
        file_name="villes_francaises.csv",
        mime="text/csv",
        key="download_stats"
    )

# Footer
st.markdown("""
<div class="site-footer">
    <p>Sources : OpenDataSoft · Caisse des Dépôts · Open-Meteo · Open Data France</p>
</div>
""", unsafe_allow_html=True)
