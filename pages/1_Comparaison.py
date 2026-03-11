"""
🔄 Page de Comparaison de Villes
Permet de comparer 2 villes françaises côte à côte sur différents critères
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.data_loader import (
    load_cities_data, 
    get_city_list, 
    get_city_info,
    get_employment_data,
    get_housing_data,
    get_weather_current,
    get_weather_forecast
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
        
        if 'departement_code' in info1:
            st.metric("Département", info1['departement_code'])
    
    with col2:
        st.subheader(f"🏙️ {city2}")
        
        if 'population' in info2:
            st.metric("Population", f"{int(info2['population']):,}")
        
        if 'altitude' in info2 and info2['altitude']:
            st.metric("Altitude", f"{int(info2['altitude'])} m")
        
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
        fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
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

        st.divider()

        # Normaliser les codes département pour éviter les écarts de format (ex: 01 vs 1)
        def _normalize_dept_code(value):
            if pd.isna(value):
                return ''
            txt = str(value).strip().upper()
            if txt.isdigit():
                return str(int(txt))
            return txt

        dept1 = _normalize_dept_code(info1.get('departement_code', ''))
        dept2 = _normalize_dept_code(info2.get('departement_code', ''))
        dept_series = df_cities['departement_code'].apply(_normalize_dept_code)

        total_pop = df_cities['population'].sum()
        rank_nat_1 = int((df_cities['population'] > pop1).sum() + 1)
        rank_nat_2 = int((df_cities['population'] > pop2).sum() + 1)

        dept_df1 = df_cities[dept_series == dept1]
        dept_df2 = df_cities[dept_series == dept2]

        nb_villes_dept_1 = len(dept_df1)
        nb_villes_dept_2 = len(dept_df2)
        rang_dept_1 = int((dept_df1['population'] > pop1).sum() + 1) if not dept_df1.empty else 0
        rang_dept_2 = int((dept_df2['population'] > pop2).sum() + 1) if not dept_df2.empty else 0

        part_pop_1 = (pop1 / total_pop * 100) if total_pop > 0 else 0
        part_pop_2 = (pop2 / total_pop * 100) if total_pop > 0 else 0

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"**{city1}**")
            st.metric("Villes dans le département", f"{nb_villes_dept_1:,}")
            st.metric("Rang dans le département", f"#{rang_dept_1}" if rang_dept_1 > 0 else "N/A")
            st.metric("Rang national", f"#{rank_nat_1}")
            st.metric("Part de population", f"{part_pop_1:.2f}%")

        with c2:
            st.markdown(f"**{city2}**")
            st.metric("Villes dans le département", f"{nb_villes_dept_2:,}")
            st.metric("Rang dans le département", f"#{rang_dept_2}" if rang_dept_2 > 0 else "N/A")
            st.metric("Rang national", f"#{rank_nat_2}")
            st.metric("Part de population", f"{part_pop_2:.2f}%")

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

            # 1) Comparaison groupée des principaux taux
            if all(v != 'N/A' for v in [taux_chomage1, taux_chomage2, taux_activite1, taux_activite2, taux_emploi1, taux_emploi2]):
                rates_df = pd.DataFrame({
                    'Indicateur': ["Taux de chômage", "Taux d'activité", "Taux d'emploi"] * 2,
                    'Ville': [city1, city1, city1, city2, city2, city2],
                    'Valeur': [
                        taux_chomage1, taux_activite1, taux_emploi1,
                        taux_chomage2, taux_activite2, taux_emploi2
                    ]
                })

                fig_rates = px.bar(
                    rates_df,
                    x='Indicateur',
                    y='Valeur',
                    color='Ville',
                    barmode='group',
                    text='Valeur',
                    title="Comparaison des taux clés de l'emploi",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e']
                )
                fig_rates.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig_rates.update_layout(yaxis_title="Pourcentage (%)")
                st.plotly_chart(fig_rates, use_container_width=True)

            st.divider()
            # 3) Écarts entre villes
            if all(v != 'N/A' for v in [taux_chomage1, taux_chomage2, taux_activite1, taux_activite2, taux_emploi1, taux_emploi2]):
                gaps_df = pd.DataFrame({
                    'Indicateur': ["Chômage", "Activité", "Emploi"],
                    'Écart (ville 1 - ville 2)': [
                        taux_chomage1 - taux_chomage2,
                        taux_activite1 - taux_activite2,
                        taux_emploi1 - taux_emploi2
                    ]
                })
                gaps_df['Couleur'] = gaps_df['Écart (ville 1 - ville 2)'].apply(lambda x: 'Supérieur' if x >= 0 else 'Inférieur')

                fig_gaps = px.bar(
                    gaps_df,
                    x='Indicateur',
                    y='Écart (ville 1 - ville 2)',
                    color='Couleur',
                    text='Écart (ville 1 - ville 2)',
                    title=f"Écarts de {city1} par rapport à {city2} (points)",
                    color_discrete_map={'Supérieur': '#16a34a', 'Inférieur': '#dc2626'}
                )
                fig_gaps.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                fig_gaps.update_layout(yaxis_title="Points de pourcentage")
                st.plotly_chart(fig_gaps, use_container_width=True)
            st.divider()
            
            # 2) Structure de la population 15-64 ans (en %)
            pop_emp1 = emp1.get('population_15_64', 'N/A')
            pop_emp2 = emp2.get('population_15_64', 'N/A')
            actifs_occupes1 = emp1.get('actifs_occupes', 'N/A')
            actifs_occupes2 = emp2.get('actifs_occupes', 'N/A')
            chomeurs1 = emp1.get('chomeurs', 'N/A')
            chomeurs2 = emp2.get('chomeurs', 'N/A')
            inactifs1 = emp1.get('inactifs', 'N/A')
            inactifs2 = emp2.get('inactifs', 'N/A')

            if all(v != 'N/A' for v in [pop_emp1, pop_emp2, actifs_occupes1, actifs_occupes2, chomeurs1, chomeurs2, inactifs1, inactifs2]) and pop_emp1 > 0 and pop_emp2 > 0:
                structure_df = pd.DataFrame({
                    'Ville': [city1, city1, city1, city2, city2, city2],
                    'Catégorie': ['Actifs occupés', 'Chômeurs', 'Inactifs'] * 2,
                    'Pourcentage': [
                        actifs_occupes1 / pop_emp1 * 100,
                        chomeurs1 / pop_emp1 * 100,
                        inactifs1 / pop_emp1 * 100,
                        actifs_occupes2 / pop_emp2 * 100,
                        chomeurs2 / pop_emp2 * 100,
                        inactifs2 / pop_emp2 * 100,
                    ]
                })

                fig_structure = px.bar(
                    structure_df,
                    x='Ville',
                    y='Pourcentage',
                    color='Catégorie',
                    barmode='stack',
                    title="Structure de la population 15-64 ans (%)",
                    color_discrete_sequence=['#2ecc71', '#e74c3c', '#f39c12']
                )
                fig_structure.update_layout(yaxis_title="Pourcentage (%)")
                st.plotly_chart(fig_structure, use_container_width=True)

            st.divider()
            
            # Comparaison des effectifs absolus
            if all(v != 'N/A' for v in [actifs_occupes1, actifs_occupes2, chomeurs1, chomeurs2, inactifs1, inactifs2]):
                volumes_df = pd.DataFrame({
                    'Statut': ["Actifs occupés", "Chômeurs", "Inactifs"] * 2,
                    'Ville': [city1, city1, city1, city2, city2, city2],
                    'Effectif': [
                        actifs_occupes1, chomeurs1, inactifs1,
                        actifs_occupes2, chomeurs2, inactifs2
                    ]
                })

                fig_volumes = px.bar(
                    volumes_df,
                    x='Statut',
                    y='Effectif',
                    color='Ville',
                    barmode='group',
                    text='Effectif',
                    title="Comparaison des effectifs (15-64 ans)",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e']
                )
                fig_volumes.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                fig_volumes.update_layout(yaxis_title="Nombre de personnes")
                st.plotly_chart(fig_volumes, use_container_width=True)
                
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

            st.divider()

            adv_left, adv_right = st.columns(2)

            with adv_left:
                # Statut d'occupation (propriétaires / locataires / autres)
                taux_prop1 = log1.get('taux_proprietaires', 0)
                taux_prop2 = log2.get('taux_proprietaires', 0)
                taux_loc1 = log1.get('taux_locataires', 0)
                taux_loc2 = log2.get('taux_locataires', 0)

                occ_df = pd.DataFrame({
                    'Ville': [city1, city1, city1, city2, city2, city2],
                    'Statut': ['Propriétaires', 'Locataires', 'Autres'] * 2,
                    'Pourcentage': [
                        taux_prop1,
                        taux_loc1,
                        max(0, 100 - taux_prop1 - taux_loc1),
                        taux_prop2,
                        taux_loc2,
                        max(0, 100 - taux_prop2 - taux_loc2)
                    ]
                })

                fig_occ = px.bar(
                    occ_df,
                    x='Ville',
                    y='Pourcentage',
                    color='Statut',
                    barmode='stack',
                    title="Statut d'occupation des résidences principales (%)",
                    color_discrete_sequence=['#16a34a', '#f59e0b', '#94a3b8'],
                    height=360
                )
                fig_occ.update_layout(yaxis_title="Pourcentage (%)")
                st.plotly_chart(fig_occ, use_container_width=True)

            with adv_right:
                # Radar des taux clés logement
                radar_categories = [
                    "Vacance",
                    "Rés. secondaires",
                    "Maisons",
                    "Appartements",
                    "HLM"
                ]

                fig_radar_log = go.Figure()
                fig_radar_log.add_trace(go.Scatterpolar(
                    r=[
                        log1.get('taux_logements_vacants', 0),
                        log1.get('taux_residence_secondaire', 0),
                        log1.get('taux_maisons', 0),
                        log1.get('taux_appartements', 0),
                        log1.get('taux_hlm', 0)
                    ],
                    theta=radar_categories,
                    fill='toself',
                    name=city1,
                    line=dict(color='#1f77b4')
                ))
                fig_radar_log.add_trace(go.Scatterpolar(
                    r=[
                        log2.get('taux_logements_vacants', 0),
                        log2.get('taux_residence_secondaire', 0),
                        log2.get('taux_maisons', 0),
                        log2.get('taux_appartements', 0),
                        log2.get('taux_hlm', 0)
                    ],
                    theta=radar_categories,
                    fill='toself',
                    name=city2,
                    line=dict(color='#ff7f0e')
                ))
                fig_radar_log.update_layout(
                    title="Profil logement (radar des taux)",
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    height=360
                )
                st.plotly_chart(fig_radar_log, use_container_width=True)

            # Intensité logements par ménage
            menages1 = log1.get('nombre_menages', 'N/A')
            menages2 = log2.get('nombre_menages', 'N/A')
            nb_log1 = log1.get('nombre_logements', 'N/A')
            nb_log2 = log2.get('nombre_logements', 'N/A')

            if all(v != 'N/A' for v in [menages1, menages2, nb_log1, nb_log2]) and menages1 > 0 and menages2 > 0:
                intensity_df = pd.DataFrame({
                    'Ville': [city1, city2],
                    'Logements par ménage': [nb_log1 / menages1, nb_log2 / menages2]
                })

                fig_intensity = px.bar(
                    intensity_df,
                    x='Ville',
                    y='Logements par ménage',
                    text='Logements par ménage',
                    title="Intensité du parc : logements par ménage",
                    color='Ville',
                    color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                    height=340
                )
                fig_intensity.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig_intensity.update_layout(showlegend=False, yaxis_title="Ratio")
                st.plotly_chart(fig_intensity, use_container_width=True)
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
                st.metric("Précipitations", f"{current1.get('precipMM', 'N/A')} mm")
                
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
                st.metric("Précipitations", f"{current2.get('precipMM', 'N/A')} mm")
                
                if 'weatherDesc' in current2 and len(current2['weatherDesc']) > 0:
                    st.info(f"☁️ {current2['weatherDesc'][0].get('value', 'N/A')}")

    st.divider()
    st.subheader("📊 Prévisions météo (3 jours)")

    forecast1 = get_weather_forecast(city1)
    forecast2 = get_weather_forecast(city2)

    if forecast1 or forecast2:
        fig_forecast = go.Figure()

        def _add_forecast_traces(forecast_data, city_name, color_max, color_min):
            if not forecast_data:
                return

            forecast_df = pd.DataFrame(forecast_data[:3])
            forecast_df['maxtempC'] = pd.to_numeric(forecast_df['maxtempC'], errors='coerce')
            forecast_df['mintempC'] = pd.to_numeric(forecast_df['mintempC'], errors='coerce')
            forecast_df['date_label'] = pd.to_datetime(forecast_df['date'], errors='coerce').dt.strftime('%d/%m/%Y')
            forecast_df['date_label'] = forecast_df['date_label'].fillna(forecast_df['date'])

            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['date_label'],
                y=forecast_df['maxtempC'],
                mode='lines+markers',
                name=f"{city_name} - Max",
                line=dict(color=color_max, width=3)
            ))

            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['date_label'],
                y=forecast_df['mintempC'],
                mode='lines+markers',
                name=f"{city_name} - Min",
                line=dict(color=color_min, width=3, dash='dot')
            ))

        _add_forecast_traces(forecast1, city1, '#e74c3c', '#ff9f7f')
        _add_forecast_traces(forecast2, city2, '#3498db', '#8ec9ff')

        fig_forecast.update_layout(
            title="Comparaison des températures prévues",
            xaxis_title="Date",
            yaxis_title="Température (°C)",
            hovermode='x unified',
            height=420
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.warning("⚠️ Prévisions météo non disponibles")   
st.markdown("""
<div class="site-footer">
    <p>Sources : OpenDataSoft · INSEE · Open Data France</p>
</div>
""", unsafe_allow_html=True)
