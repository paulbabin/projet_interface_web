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

# Configuration de la page
st.set_page_config(
    page_title="CompaVille - Comparateur de Villes",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# En-tête
st.markdown('<div class="main-header">🏙️ CompaVille</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Explorez et comparez les villes françaises de plus de 20 000 habitants</div>', unsafe_allow_html=True)

# Chargement des données
with st.spinner("🔄 Chargement des données des villes..."):
    df_cities = load_cities_data()

if df_cities.empty:
    st.error("❌ Impossible de charger les données des villes")
    st.stop()

# Sidebar - Informations et filtres
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/320px-Flag_of_France.svg.png", width=100)
    st.title("📊 Informations")
    
    st.metric("Nombre de villes", f"{len(df_cities):,}")
    
    if 'population' in df_cities.columns:
        total_pop = df_cities['population'].sum()
        st.metric("Population totale", f"{int(total_pop):,}")
        st.metric("Population moyenne", f"{int(df_cities['population'].mean()):,}")
    
    st.divider()
    
    st.markdown("### 🔍 Filtres")
    
    # Filtre par population
    if 'population' in df_cities.columns:
        min_pop = int(df_cities['population'].min())
        max_pop = int(df_cities['population'].max())
        
        pop_range = st.slider(
            "Population",
            min_value=min_pop,
            max_value=max_pop,
            value=(min_pop, max_pop),
            step=10000,
            format="%d"
        )
        
        df_filtered = df_cities[
            (df_cities['population'] >= pop_range[0]) & 
            (df_cities['population'] <= pop_range[1])
        ]
    else:
        df_filtered = df_cities
    
    st.info(f"📍 **{len(df_filtered)}** villes affichées")
    
    st.divider()
    
    st.markdown("### 📖 Navigation")
    st.markdown("""
    - 🗺️ **Accueil**: Carte des villes
    - 🔄 **Comparaison**: Comparez 2 villes
    - 📊 **Données Générales**: Infos détaillées
    - 💼 **Emploi**: Taux de chômage, secteurs
    - 🏠 **Logement**: Prix, types de logement
    - 🌤️ **Météo**: Climat et prévisions
    """)

# Contenu principal
tab1, tab2, tab3 = st.tabs(["🗺️ Carte Interactive", "📊 Statistiques", "📋 Liste des Villes"])

with tab1:
    st.header("🗺️ Carte des Villes Françaises > 20 000 habitants")
    
    if 'lat' in df_filtered.columns and 'lon' in df_filtered.columns:
        # Carte interactive avec Plotly
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
            color_continuous_scale='Viridis',
            size_max=30,
            zoom=5,
            height=600,
            title=f"Carte de {len(df_filtered)} villes françaises"
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":40,"l":0,"b":0}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Coordonnées géographiques non disponibles pour la carte")
    
    # Carte simple Streamlit en fallback
    if 'lat' in df_filtered.columns and 'lon' in df_filtered.columns:
        with st.expander("🗺️ Vue alternative (Carte Streamlit simple)"):
            st.map(df_filtered[['lat', 'lon']].dropna())

with tab2:
    st.header("📊 Statistiques des Villes")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏙️ Villes affichées",
            f"{len(df_filtered):,}",
            delta=f"{len(df_filtered) - len(df_cities)}" if len(df_filtered) != len(df_cities) else None
        )
    
    if 'population' in df_filtered.columns:
        with col2:
            st.metric(
                "👥 Population totale",
                f"{int(df_filtered['population'].sum()):,}"
            )
        
        with col3:
            st.metric(
                "📈 Plus grande ville",
                df_filtered.loc[df_filtered['population'].idxmax(), 'ville'] if 'ville' in df_filtered.columns else "N/A",
                f"{int(df_filtered['population'].max()):,} hab."
            )
        
        with col4:
            st.metric(
                "📉 Plus petite ville",
                df_filtered.loc[df_filtered['population'].idxmin(), 'ville'] if 'ville' in df_filtered.columns else "N/A",
                f"{int(df_filtered['population'].min()):,} hab."
            )
        
        st.divider()
        
        # Graphiques
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 Distribution de la population")
            fig_hist = px.histogram(
                df_filtered,
                x='population',
                nbins=30,
                title="Répartition des villes par population",
                labels={'population': 'Population', 'count': 'Nombre de villes'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col_right:
            st.subheader("🏆 Top 10 des villes les plus peuplées")
            if 'ville' in df_filtered.columns:
                top10 = df_filtered.nlargest(10, 'population')[['ville', 'population']]
                fig_bar = px.bar(
                    top10,
                    x='population',
                    y='ville',
                    orientation='h',
                    title="Top 10 des villes",
                    labels={'population': 'Population', 'ville': 'Ville'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.header("📋 Liste Complète des Villes")
    
    # Barre de recherche
    search = st.text_input("🔍 Rechercher une ville", placeholder="Entrez le nom d'une ville...")
    
    if search:
        df_display = df_filtered[df_filtered['ville'].str.contains(search, case=False, na=False)] if 'ville' in df_filtered.columns else df_filtered
    else:
        df_display = df_filtered
    
    # Colonnes à afficher
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
    
    # Téléchargement des données
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger les données (CSV)",
        data=csv,
        file_name="villes_francaises.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>🎓 Projet réalisé dans le cadre du cours de Programmation Web</p>
    <p>📊 Sources: OpenDataSoft, INSEE, Open Data France</p>
</div>
""", unsafe_allow_html=True)
