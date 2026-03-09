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
from utils.data_loader import load_cities_data, get_city_list
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

# ===== Filtre de population (inline) =====
if 'population' in df_cities.columns:
    min_pop = int(df_cities['population'].min())
    max_pop = int(df_cities['population'].max())

    col_filter1, col_filter2 = st.columns([3, 1])
    with col_filter1:
        pop_range = st.slider(
            "Filtrer par population",
            min_value=min_pop,
            max_value=max_pop,
            value=(min_pop, max_pop),
            step=10000,
            format="%d"
        )
    with col_filter2:
        st.markdown("")
        nb_filtered = len(df_cities[(df_cities['population'] >= pop_range[0]) & (df_cities['population'] <= pop_range[1])])
        st.info(f"**{nb_filtered}** villes affichées")

    df_filtered = df_cities[
        (df_cities['population'] >= pop_range[0]) &
        (df_cities['population'] <= pop_range[1])
    ]
else:
    df_filtered = df_cities

# ===== Contenu principal =====
tab1, tab2, tab3 = st.tabs(["🗺️ Carte Interactive", "📊 Statistiques", "📋 Liste des Villes"])

with tab1:
    st.header("Carte des Villes Françaises")

    if 'lat' in df_filtered.columns and 'lon' in df_filtered.columns:
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
            color_continuous_scale='Blues',
            size_max=30,
            zoom=5,
            height=600,
        )

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

    if 'lat' in df_filtered.columns and 'lon' in df_filtered.columns:
        with st.expander("Vue alternative (carte simple)"):
            st.map(df_filtered[['lat', 'lon']].dropna())

with tab2:
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

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Distribution de la population")
            fig_hist = px.histogram(
                df_filtered,
                x='population',
                nbins=30,
                title="Répartition des villes par population",
                labels={'population': 'Population', 'count': 'Nombre de villes'},
                color_discrete_sequence=['#2563eb']
            )
            fig_hist.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#1e293b'),
                title_font=dict(size=14),
                xaxis=dict(gridcolor='#f1f5f9'),
                yaxis=dict(gridcolor='#f1f5f9')
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with col_right:
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

with tab3:
    st.header("Liste des Villes")

    search = st.text_input("Rechercher une ville", placeholder="Entrez le nom d'une ville...")

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
            height=500
        )
    else:
        st.dataframe(df_display, use_container_width=True, height=500)

    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger les données (CSV)",
        data=csv,
        file_name="villes_francaises.csv",
        mime="text/csv"
    )

# Footer
st.markdown("""
<div class="site-footer">
    <p>Projet réalisé dans le cadre du cours de Programmation Web</p>
    <p>Sources : OpenDataSoft · INSEE · Open Data France</p>
</div>
""", unsafe_allow_html=True)
