"""
📊 Page Données Générales
Vue détaillée des informations générales d'une ville
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.data_loader import (
    load_cities_data,
    get_city_list,
    get_city_info,
    get_city_wikipedia_summary
)

st.set_page_config(page_title="Données Générales", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

from utils.navbar import inject_navbar_css, render_navbar
inject_navbar_css()
render_navbar("Données")

st.title("Données Générales")
st.markdown("Informations détaillées sur les villes françaises")

# Chargement des données
df_cities = load_cities_data()
city_list = get_city_list(df_cities)

# Sélection de ville
selected_city = st.selectbox("🏙️ Sélectionnez une ville", city_list)

if selected_city:
    city_info = get_city_info(df_cities, selected_city)
    
    if city_info is not None:
        st.header(f"🏙️ {selected_city}")
        
        # Récupérer le résumé Wikipedia
        with st.spinner("📖 Chargement des informations..."):
            wiki_summary = get_city_wikipedia_summary(selected_city)
        
        # Afficher le résumé
        if wiki_summary and wiki_summary != "Aucune description disponible":
            with st.expander("📖 Description de la ville (Wikipedia)", expanded=True):
                st.write(wiki_summary)
        
        st.divider()
        
        # Informations principales
        st.subheader("📍 Informations Principales")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'population' in city_info:
                st.metric(
                    "👥 Population",
                    f"{int(city_info['population']):,}",
                    help="Nombre d'habitants"
                )
            
            if 'altitude' in city_info and city_info['altitude']:
                st.metric(
                    "⛰️ Altitude",
                    f"{int(city_info['altitude'])} m",
                    help="Altitude moyenne"
                )
        
        with col2:
            if 'departement_code' in city_info:
                st.metric(
                    "📮 Département",
                    city_info['departement_code'],
                    help="Code département"
                )
            
            if 'region_code' in city_info and city_info['region_code']:
                st.metric(
                    "🗺️ Région",
                    city_info['region_code'],
                    help="Code région"
                )
        
        with col3:
            if 'lat' in city_info and 'lon' in city_info:
                st.metric(
                    "📍 Latitude",
                    f"{city_info['lat']:.4f}",
                    help="Coordonnée latitude"
                )
                st.metric(
                    "📍 Longitude",
                    f"{city_info['lon']:.4f}",
                    help="Coordonnée longitude"
                )
        
        st.divider()
        
        # Carte de localisation
        st.subheader("🗺️ Localisation")
        
        if 'lat' in city_info and 'lon' in city_info:
            map_df = pd.DataFrame({
                'ville': [selected_city],
                'lat': [city_info['lat']],
                'lon': [city_info['lon']]
            })
            
            fig_map = px.scatter_mapbox(
                map_df,
                lat='lat',
                lon='lon',
                hover_name='ville',
                zoom=10,
                height=400
            )
            fig_map.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":0,"l":0,"b":0}
            )
            st.plotly_chart(fig_map, use_container_width=True)
        
        st.divider()
        
        # Comparaison avec les villes voisines
        st.subheader("🏘️ Comparaison Régionale")
        
        # Filtrer les villes du même département
        if 'departement_code' in city_info and 'departement_code' in df_cities.columns:
            same_dept = df_cities[
                (df_cities['departement_code'] == city_info['departement_code']) &
                (df_cities['ville'] != selected_city)
            ]
            
            if not same_dept.empty and 'population' in same_dept.columns:
                st.write(f"📊 Villes du département {city_info['departement_code']}")
                
                # Top 5 des villes du département
                top_dept = same_dept.nlargest(5, 'population')[['ville', 'population']]
                
                # Ajouter la ville sélectionnée
                current_city_data = pd.DataFrame({
                    'ville': [selected_city],
                    'population': [city_info.get('population', 0)]
                })
                
                combined = pd.concat([current_city_data, top_dept]).drop_duplicates()
                combined = combined.sort_values('population', ascending=False)
                
                # Graphique
                fig_dept = px.bar(
                    combined,
                    x='population',
                    y='ville',
                    orientation='h',
                    title=f"Populations dans le département {city_info['departement_code']}",
                    labels={'population': 'Population', 'ville': 'Ville'},
                    color='population',
                    color_continuous_scale='Viridis'
                )
                fig_dept.update_traces(texttemplate='%{x:,}', textposition='outside')
                fig_dept.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_dept, use_container_width=True)
                
                # Statistiques du département
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Villes dans le département",
                        len(same_dept) + 1
                    )
                
                with col2:
                    rank = (same_dept['population'] > city_info.get('population', 0)).sum() + 1
                    st.metric(
                        f"Rang de {selected_city}",
                        f"#{rank}"
                    )
                
                with col3:
                    avg_pop = same_dept['population'].mean()
                    st.metric(
                        "Population moyenne",
                        f"{int(avg_pop):,}"
                    )
        
        st.divider()
        
        # Statistiques nationales
        st.subheader("🇫🇷 Contexte National")
        
        if 'population' in city_info and 'population' in df_cities.columns:
            total_cities = len(df_cities)
            rank = (df_cities['population'] > city_info['population']).sum() + 1
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Rang national",
                    f"#{rank}",
                    f"sur {total_cities}"
                )
            
            with col2:
                percentile = (1 - rank / total_cities) * 100
                st.metric(
                    "Percentile",
                    f"{percentile:.1f}%",
                    help="Pourcentage de villes plus petites"
                )
            
            with col3:
                avg_pop_national = df_cities['population'].mean()
                diff_pct = ((city_info['population'] - avg_pop_national) / avg_pop_national * 100)
                st.metric(
                    "vs Moyenne nationale",
                    f"{diff_pct:+.1f}%",
                    help="Écart avec la population moyenne"
                )
            
            with col4:
                total_pop = df_cities['population'].sum()
                share = (city_info['population'] / total_pop * 100)
                st.metric(
                    "Part de la population",
                    f"{share:.2f}%",
                    help="Part de la population totale des grandes villes"
                )
        
        # Toutes les données brutes
        with st.expander("🔍 Voir toutes les données brutes"):
            st.json(city_info.to_dict())

st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem 0;'>
    <p>📊 Sources: OpenDataSoft, Wikipedia, Open Data France</p>
    <p>🔄 Données mises à jour régulièrement</p>
</div>
""", unsafe_allow_html=True)
