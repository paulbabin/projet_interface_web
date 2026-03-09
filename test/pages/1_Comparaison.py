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
    generate_mock_employment_data,
    generate_mock_housing_data,
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
    
    if 'population' in info1 and 'population' in info2:
        # Génération de données d'emploi fictives
        emp1 = generate_mock_employment_data(city1, int(info1['population']))
        emp2 = generate_mock_employment_data(city2, int(info2['population']))
        
        # Métriques côte à côte
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"💼 {city1}")
            st.metric("Taux de chômage", f"{emp1['taux_chomage']}%")
            st.metric("Taux d'activité", f"{emp1['taux_activite']}%")
            st.metric("Emplois salariés", f"{emp1['emploi_salarie']:,}")
            st.metric("Emplois non salariés", f"{emp1['emploi_non_salarie']:,}")
        
        with col2:
            st.subheader(f"💼 {city2}")
            st.metric("Taux de chômage", f"{emp2['taux_chomage']}%")
            st.metric("Taux d'activité", f"{emp2['taux_activite']}%")
            st.metric("Emplois salariés", f"{emp2['emploi_salarie']:,}")
            st.metric("Emplois non salariés", f"{emp2['emploi_non_salarie']:,}")
        
        st.divider()
        
        # Graphiques de comparaison
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Taux de chômage
            fig_chomage = go.Figure()
            fig_chomage.add_trace(go.Bar(
                x=[city1, city2],
                y=[emp1['taux_chomage'], emp2['taux_chomage']],
                text=[f"{emp1['taux_chomage']}%", f"{emp2['taux_chomage']}%"],
                textposition='auto',
                marker_color=['#1f77b4', '#ff7f0e']
            ))
            fig_chomage.update_layout(
                title="Taux de Chômage (%)",
                yaxis_title="Taux (%)",
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig_chomage, use_container_width=True)
        
        with col_right:
            # Répartition public/privé
            import pandas as pd
            
            sectors_data = pd.DataFrame({
                'Ville': [city1, city1, city2, city2],
                'Secteur': ['Public', 'Privé', 'Public', 'Privé'],
                'Emplois': [
                    emp1['secteur_public'],
                    emp1['secteur_prive'],
                    emp2['secteur_public'],
                    emp2['secteur_prive']
                ]
            })
            
            fig_sectors = px.bar(
                sectors_data,
                x='Ville',
                y='Emplois',
                color='Secteur',
                title="Répartition Public/Privé",
                barmode='group',
                height=350
            )
            st.plotly_chart(fig_sectors, use_container_width=True)

# ====== TAB 4: LOGEMENT ======
with tab4:
    st.header("🏠 Comparaison du Logement")
    
    if 'population' in info1 and 'population' in info2:
        # Génération de données de logement fictives
        log1 = generate_mock_housing_data(city1, int(info1['population']))
        log2 = generate_mock_housing_data(city2, int(info2['population']))
        
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"Prix/m² {city1}", f"{log1['prix_moyen_m2']:,} €")
        
        with col2:
            st.metric(f"Prix/m² {city2}", f"{log2['prix_moyen_m2']:,} €")
        
        with col3:
            diff = log1['prix_moyen_m2'] - log2['prix_moyen_m2']
            pct = (diff / log2['prix_moyen_m2'] * 100) if log2['prix_moyen_m2'] > 0 else 0
            st.metric("Différence", f"{abs(diff):,} €", f"{pct:+.1f}%")
        
        st.divider()
        
        # Détails par ville
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"🏠 {city1}")
            st.metric("Nombre de logements", f"{log1['nombre_logements']:,}")
            st.metric("Résidences principales", f"{log1['taux_residence_principale']}%")
            st.metric("Résidences secondaires", f"{log1['taux_residence_secondaire']}%")
            st.metric("Logements vacants", f"{log1['taux_logements_vacants']}%")
        
        with col2:
            st.subheader(f"🏠 {city2}")
            st.metric("Nombre de logements", f"{log2['nombre_logements']:,}")
            st.metric("Résidences principales", f"{log2['taux_residence_principale']}%")
            st.metric("Résidences secondaires", f"{log2['taux_residence_secondaire']}%")
            st.metric("Logements vacants", f"{log2['taux_logements_vacants']}%")
        
        st.divider()
        
        # Graphiques
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Prix au m²
            fig_prix = go.Figure()
            fig_prix.add_trace(go.Bar(
                x=[city1, city2],
                y=[log1['prix_moyen_m2'], log2['prix_moyen_m2']],
                text=[f"{log1['prix_moyen_m2']:,} €", f"{log2['prix_moyen_m2']:,} €"],
                textposition='auto',
                marker_color=['#1f77b4', '#ff7f0e']
            ))
            fig_prix.update_layout(
                title="Prix Moyen au m² (€)",
                yaxis_title="Prix (€)",
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig_prix, use_container_width=True)
        
        with col_right:
            # Type de logement
            import pandas as pd
            
            housing_type = pd.DataFrame({
                'Ville': [city1, city1, city2, city2],
                'Type': ['Maisons', 'Appartements', 'Maisons', 'Appartements'],
                'Pourcentage': [
                    log1['maisons'],
                    log1['appartements'],
                    log2['maisons'],
                    log2['appartements']
                ]
            })
            
            fig_type = px.bar(
                housing_type,
                x='Ville',
                y='Pourcentage',
                color='Type',
                title="Répartition Maisons/Appartements (%)",
                barmode='group',
                height=350
            )
            st.plotly_chart(fig_type, use_container_width=True)

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
