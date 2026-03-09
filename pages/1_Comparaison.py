"""
🔄 Page de Comparaison de Villes
Permet de comparer 2 villes françaises côte à côte sur différents critères
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.data_loader import (
    load_cities_data, 
    get_city_list, 
    get_city_info,
    get_employment_data,
    get_housing_data,
    get_weather_current
)

st.set_page_config(page_title="Comparaison de Villes", page_icon="🔄", layout="wide", initial_sidebar_state="collapsed")

from utils.navbar import inject_navbar_css, render_navbar
inject_navbar_css()
render_navbar("Comparaison")

st.markdown("""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-size:2.2rem; font-weight:700; color:#1e293b; margin:0; letter-spacing:-1px;">
        Comparaison de villes
    </h1>
    <p style="color:#64748b; font-size:1.05rem; margin-top:0.5rem;">
        Comparez deux villes françaises sur la démographie, l'emploi, le logement et la météo
    </p>
</div>
""", unsafe_allow_html=True)

# Chargement des données
df_cities = load_cities_data()
if df_cities.empty:
    st.error("❌ Impossible de charger les données")
    st.stop()

city_list = get_city_list(df_cities)

if not city_list:
    st.error("❌ Aucune ville disponible")
    st.stop()

default_city_index = city_list.index("Niort (79)") if "Niort (79)" in city_list else 0
default_city2_index = (default_city_index + 1) % len(city_list) if len(city_list) > 1 else default_city_index

# Sélection des villes
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏙️ Ville 1")
    city1 = st.selectbox(
        "Choisissez la première ville",
        options=city_list,
        index=default_city_index,
        key="city1"
    )

with col2:
    st.subheader("🏙️ Ville 2")
    city2 = st.selectbox(
        "Choisissez la deuxième ville",
        options=city_list,
        index=default_city2_index,
        key="city2"
    )

if city1 == city2:
    st.warning("⚠️ Veuillez sélectionner deux villes différentes")
    st.stop()

# Récupération des informations des villes
info1 = get_city_info(df_cities, city1)
info2 = get_city_info(df_cities, city2)

if info1 is None or info2 is None:
    st.error("❌ Impossible de récupérer les informations des villes")
    st.stop()

st.divider()

# Onglets de comparaison
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Vue d'ensemble",
    "👥 Démographie",
    "💼 Emploi",
    "🏠 Logement",
    "🌤️ Météo"
])

# ====== TAB 1: VUE D'ENSEMBLE ======
with tab1:
    st.header("📊 Vue d'Ensemble")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"🏙️ {city1}")
        
        if 'population' in info1:
            st.metric("Population", f"{int(info1['population']):,}")
        
        if 'altitude' in info1 and info1['altitude']:
            st.metric("Altitude", f"{int(info1['altitude'])} m")
        
        if 'lat' in info1 and 'lon' in info1:
            st.metric("Coordonnées", f"{info1['lat']:.4f}, {info1['lon']:.4f}")
        
        if 'departement_code' in info1:
            st.metric("Département", info1['departement_code'])
    
    with col2:
        st.subheader(f"🏙️ {city2}")
        
        if 'population' in info2:
            st.metric("Population", f"{int(info2['population']):,}")
        
        if 'altitude' in info2 and info2['altitude']:
            st.metric("Altitude", f"{int(info2['altitude'])} m")
        
        if 'lat' in info2 and 'lon' in info2:
            st.metric("Coordonnées", f"{info2['lat']:.4f}, {info2['lon']:.4f}")
        
        if 'departement_code' in info2:
            st.metric("Département", info2['departement_code'])
    
    st.divider()
    
    # Carte de localisation
    st.subheader("🗺️ Localisation")
    
    if 'lat' in info1 and 'lon' in info1 and 'lat' in info2 and 'lon' in info2:
        import pandas as pd
        map_data = pd.DataFrame({
            'ville': [city1, city2],
            'lat': [info1['lat'], info2['lat']],
            'lon': [info1['lon'], info2['lon']],
            'population': [info1.get('population', 0), info2.get('population', 0)]
        })
        
        fig_map = px.scatter_mapbox(
            map_data,
            lat='lat',
            lon='lon',
            hover_name='ville',
            hover_data={'population': ':,', 'lat': False, 'lon': False},
            size='population',
            color='ville',
            zoom=5,
            height=500
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

# ====== TAB 2: DÉMOGRAPHIE ======
with tab2:
    st.header("👥 Comparaison Démographique")
    
    if 'population' in info1 and 'population' in info2:
        pop1 = int(info1['population'])
        pop2 = int(info2['population'])
        
        # Graphique de comparaison
        fig_demo = go.Figure()
        
        fig_demo.add_trace(go.Bar(
            name=city1,
            x=['Population'],
            y=[pop1],
            text=[f"{pop1:,}"],
            textposition='auto',
            marker_color='#1f77b4'
        ))
        
        fig_demo.add_trace(go.Bar(
            name=city2,
            x=['Population'],
            y=[pop2],
            text=[f"{pop2:,}"],
            textposition='auto',
            marker_color='#ff7f0e'
        ))
        
        fig_demo.update_layout(
            title="Comparaison de la Population",
            yaxis_title="Habitants",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig_demo, use_container_width=True)
        
        # Statistiques
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"Population {city1}", f"{pop1:,}")
        
        with col2:
            st.metric(f"Population {city2}", f"{pop2:,}")
        
        with col3:
            diff = pop1 - pop2
            pct = (diff / pop2 * 100) if pop2 > 0 else 0
            st.metric(
                "Différence", 
                f"{abs(diff):,}",
                f"{pct:+.1f}%"
            )

# ====== TAB 3: EMPLOI ======
with tab3:
    st.header("💼 Comparaison de l'Emploi")
    
    if 'departement_code' in info1 and 'departement_code' in info2 and 'ville_nom' in info1 and 'ville_nom' in info2:
        # Récupération des données d'emploi réelles
        emp1 = get_employment_data(city1, info1['ville_nom'], info1['departement_code'])
        emp2 = get_employment_data(city2, info2['ville_nom'], info2['departement_code'])
        
        if emp1 and emp2:
            # Informations contextuelles
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"📍 {emp1.get('commune', 'N/A')} - Département {info1['departement_code']} ({emp1.get('annee', 'N/A')})")
            with col2:
                st.caption(f"📍 {emp2.get('commune', 'N/A')} - Département {info2['departement_code']} ({emp2.get('annee', 'N/A')})")
            
            st.divider()
            
            # Métriques côte à côte
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"💼 {city1}")
                taux_chomage1 = emp1.get('taux_chomage', 'N/A')
                st.metric("Taux de chômage", f"{taux_chomage1}%" if taux_chomage1 != 'N/A' else 'N/A')
                taux_activite1 = emp1.get('taux_activite', 'N/A')
                st.metric("Taux d'activité", f"{taux_activite1}%" if taux_activite1 != 'N/A' else 'N/A')
                taux_emploi1 = emp1.get('taux_emploi', 'N/A')
                st.metric("Taux d'emploi", f"{taux_emploi1}%" if taux_emploi1 != 'N/A' else 'N/A')
                pop1 = emp1.get('population_15_64', 'N/A')
                st.metric("Population 15-64 ans", f"{pop1:,}" if pop1 != 'N/A' else 'N/A')
            
            with col2:
                st.subheader(f"💼 {city2}")
                taux_chomage2 = emp2.get('taux_chomage', 'N/A')
                st.metric("Taux de chômage", f"{taux_chomage2}%" if taux_chomage2 != 'N/A' else 'N/A')
                taux_activite2 = emp2.get('taux_activite', 'N/A')
                st.metric("Taux d'activité", f"{taux_activite2}%" if taux_activite2 != 'N/A' else 'N/A')
                taux_emploi2 = emp2.get('taux_emploi', 'N/A')
                st.metric("Taux d'emploi", f"{taux_emploi2}%" if taux_emploi2 != 'N/A' else 'N/A')
                pop2 = emp2.get('population_15_64', 'N/A')
                st.metric("Population 15-64 ans", f"{pop2:,}" if pop2 != 'N/A' else 'N/A')
            
            st.divider()
            
            # Graphiques de comparaison
            col1, col2 = st.columns(2)
            
            with col1:
                if taux_chomage1 != 'N/A' and taux_chomage2 != 'N/A':
                    fig_chomage = go.Figure()
                    fig_chomage.add_trace(go.Bar(
                        name='Taux de chômage',
                        x=[city1, city2],
                        y=[taux_chomage1, taux_chomage2],
                        text=[f"{taux_chomage1}%", f"{taux_chomage2}%"],
                        textposition='auto',
                        marker_color=['#e74c3c', '#3498db']
                    ))
                    fig_chomage.update_layout(title="Taux de chômage", yaxis_title="Taux (%)")
                    st.plotly_chart(fig_chomage, use_container_width=True)
            
            with col2:
                if taux_activite1 != 'N/A' and taux_activite2 != 'N/A':
                    fig_activite = go.Figure()
                    fig_activite.add_trace(go.Bar(
                        name="Taux d'activité",
                        x=[city1, city2],
                        y=[taux_activite1, taux_activite2],
                        text=[f"{taux_activite1}%", f"{taux_activite2}%"],
                        textposition='auto',
                        marker_color=['#2ecc71', '#9b59b6']
                    ))
                    fig_activite.update_layout(title="Taux d'activité", yaxis_title="Taux (%)")
                    st.plotly_chart(fig_activite, use_container_width=True)
        else:
            st.warning("⚠️ Données d'emploi non disponibles pour l'une ou les deux villes")
    else:
        st.warning("⚠️ Informations manquantes pour l'une ou les deux villes")

# ====== TAB 4: LOGEMENT ======
with tab4:
    st.header("🏠 Comparaison du Logement")
    
    if 'departement_code' in info1 and 'departement_code' in info2 and 'ville_nom' in info1 and 'ville_nom' in info2:
        # Récupération des données de logement réelles
        log1 = get_housing_data(city1, info1['ville_nom'], info1['departement_code'])
        log2 = get_housing_data(city2, info2['ville_nom'], info2['departement_code'])
        
        if log1 and log2:
            # Informations contextuelles
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"📍 {log1.get('commune', 'N/A')} ({log1.get('annee', 'N/A')})")
            with col2:
                st.caption(f"📍 {log2.get('commune', 'N/A')} ({log2.get('annee', 'N/A')})")
            
            st.divider()
            
            # Métriques principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pieces1 = log1.get('pieces_moyennes', 'N/A')
                st.metric(f"Pièces moyennes {city1}", f"{pieces1}" if pieces1 != 'N/A' else 'N/A')
            
            with col2:
                pieces2 = log2.get('pieces_moyennes', 'N/A')
                st.metric(f"Pièces moyennes {city2}", f"{pieces2}" if pieces2 != 'N/A' else 'N/A')
            
            with col3:
                if pieces1 != 'N/A' and pieces2 != 'N/A':
                    diff = pieces1 - pieces2
                    st.metric("Différence", f"{diff:+.1f} pièces")
                else:
                    st.metric("Différence", "N/A")
            
            st.divider()
            
            # Détails par ville
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"🏠 {city1}")
                nb_log1 = log1.get('nombre_logements', 'N/A')
                st.metric("Nombre de logements", f"{nb_log1:,}" if nb_log1 != 'N/A' else 'N/A')
                
                taux_princ1 = 100 - log1.get('taux_residence_secondaire', 0) - log1.get('taux_logements_vacants', 0)
                st.metric("Résidences principales", f"{taux_princ1:.1f}%")
                st.metric("Résidences secondaires", f"{log1.get('taux_residence_secondaire', 0)}%")
                st.metric("Logements vacants", f"{log1.get('taux_logements_vacants', 0)}%")
            
            with col2:
                st.subheader(f"🏠 {city2}")
                nb_log2 = log2.get('nombre_logements', 'N/A')
                st.metric("Nombre de logements", f"{nb_log2:,}" if nb_log2 != 'N/A' else 'N/A')
                
                taux_princ2 = 100 - log2.get('taux_residence_secondaire', 0) - log2.get('taux_logements_vacants', 0)
                st.metric("Résidences principales", f"{taux_princ2:.1f}%")
                st.metric("Résidences secondaires", f"{log2.get('taux_residence_secondaire', 0)}%")
                st.metric("Logements vacants", f"{log2.get('taux_logements_vacants', 0)}%")
            
            st.divider()
            
            # Graphiques
            col_left, col_right = st.columns(2)
            
            with col_left:
                # Comparaison taux de vacance
                fig_vacance = go.Figure()
                fig_vacance.add_trace(go.Bar(
                    x=[city1, city2],
                    y=[log1.get('taux_logements_vacants', 0), log2.get('taux_logements_vacants', 0)],
                    text=[f"{log1.get('taux_logements_vacants', 0)}%", f"{log2.get('taux_logements_vacants', 0)}%"],
                    textposition='auto',
                    marker_color=['#e74c3c', '#3498db']
                ))
                fig_vacance.update_layout(
                    title="Taux de logements vacants (%)",
                    yaxis_title="Pourcentage (%)",
                    showlegend=False,
                    height=350
                )
                st.plotly_chart(fig_vacance, use_container_width=True)
            
            with col_right:
                # Type de logement
                housing_type = pd.DataFrame({
                    'Ville': [city1, city1, city2, city2],
                    'Type': ['Maisons', 'Appartements', 'Maisons', 'Appartements'],
                    'Pourcentage': [
                        log1.get('taux_maisons', 0),
                        log1.get('taux_appartements', 0),
                        log2.get('taux_maisons', 0),
                        log2.get('taux_appartements', 0)
                    ]
                })
                
                fig_type = px.bar(
                    housing_type,
                    x='Ville',
                    y='Pourcentage',
                    color='Type',
                    title="Répartition Maisons/Appartements (%)",
                    barmode='group',
                    color_discrete_sequence=['#f39c12', '#9b59b6'],
                    height=350
                )
                st.plotly_chart(fig_type, use_container_width=True)
        else:
            st.warning("⚠️ Données de logement non disponibles pour l'une ou les deux communes")
    else:
        st.warning("⚠️ Informations manquantes pour l'une ou les deux villes")

# ====== TAB 5: MÉTÉO ======
with tab5:
    st.header("🌤️ Comparaison Météo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"🌤️ {city1}")
        with st.spinner("Chargement météo..."):
            weather1 = get_weather_current(city1)
            if weather1 and 'current_condition' in weather1:
                current1 = weather1['current_condition'][0]
                st.metric("Température", f"{current1.get('temp_C', 'N/A')}°C")
                st.metric("Humidité", f"{current1.get('humidity', 'N/A')}%")
                st.metric("Vent", f"{current1.get('windspeedKmph', 'N/A')} km/h")
                
                if 'weatherDesc' in current1 and len(current1['weatherDesc']) > 0:
                    st.info(f"☁️ {current1['weatherDesc'][0].get('value', 'N/A')}")
    
    with col2:
        st.subheader(f"🌤️ {city2}")
        with st.spinner("Chargement météo..."):
            weather2 = get_weather_current(city2)
            if weather2 and 'current_condition' in weather2:
                current2 = weather2['current_condition'][0]
                st.metric("Température", f"{current2.get('temp_C', 'N/A')}°C")
                st.metric("Humidité", f"{current2.get('humidity', 'N/A')}%")
                st.metric("Vent", f"{current2.get('windspeedKmph', 'N/A')} km/h")
                
                if 'weatherDesc' in current2 and len(current2['weatherDesc']) > 0:
                    st.info(f"☁️ {current2['weatherDesc'][0].get('value', 'N/A')}")
    
    st.info("💡 Les coordonnées des villes proviennent d'OpenDataSoft, et la météo est fournie par Open-Meteo en temps réel")

st.markdown("""
<div class="site-footer">
    <p>Sources : OpenDataSoft · INSEE · Open Data France</p>
</div>
""", unsafe_allow_html=True)
