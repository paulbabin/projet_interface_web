"""
💼 Page Emploi
Analyse détaillée de l'emploi et du chômage par ville
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
    get_employment_data
)
from utils.number_format import format_int_fr

st.set_page_config(page_title="Emploi", page_icon="💼", layout="wide", initial_sidebar_state="collapsed")

from utils.navbar import inject_navbar_css, render_navbar
inject_navbar_css()
render_navbar("Emploi")

st.markdown("""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-size:2.2rem; font-weight:700; color:#1e293b; margin:0; letter-spacing:-1px;">
        Emploi et chômage
    </h1>
    <p style="color:#64748b; font-size:1.05rem; margin-top:0.5rem;">
        Analyse des indicateurs d'emploi des villes françaises
    </p>
</div>
""", unsafe_allow_html=True)

# Chargement des données
df_cities = load_cities_data()
city_list = get_city_list(df_cities)
default_city_index = city_list.index("Niort (79)") if "Niort (79)" in city_list else 0

# Sélection de ville
selected_city = st.selectbox("🏙️ Sélectionnez une ville", city_list, index=default_city_index)

if selected_city:
    city_info = get_city_info(df_cities, selected_city)
    
    if city_info is not None and 'departement_code' in city_info:
        departement_code = city_info['departement_code']
        ville_nom = city_info.get('ville_nom', selected_city)
        
        st.header(f"📊 Données d'emploi - {selected_city}")
        
        # Récupérer les données d'emploi réelles
        emp_data = get_employment_data(selected_city, ville_nom, departement_code)
        
        if emp_data:
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                taux_chomage = emp_data.get('taux_chomage', 'N/A')
                st.metric(
                    "💼 Taux de chômage",
                    f"{taux_chomage}%" if taux_chomage != 'N/A' else 'N/A',
                    delta=None,
                    help="Pourcentage de chômeurs parmi les actifs (15-64 ans)"
                )
            
            with col2:
                taux_activite = emp_data.get('taux_activite', 'N/A')
                st.metric(
                    "📈 Taux d'activité",
                    f"{taux_activite}%" if taux_activite != 'N/A' else 'N/A',
                    help="Pourcentage d'actifs parmi la population 15-64 ans"
                )
            
            with col3:
                taux_emploi = emp_data.get('taux_emploi', 'N/A')
                st.metric(
                    "👥 Taux d'emploi",
                    f"{taux_emploi}%" if taux_emploi != 'N/A' else 'N/A',
                    help="Pourcentage d'actifs occupés parmi la population 15-64 ans"
                )
            
            with col4:
                part_inactifs = emp_data.get('part_inactifs', 'N/A')
                st.metric(
                    "📏 Part d'inactifs",
                    f"{part_inactifs}%" if part_inactifs != 'N/A' else 'N/A',
                    help="Pourcentage d'inactifs parmi la population 15-64 ans"
                )
            
            st.divider()
            
            pop_15_64 = emp_data.get('population_15_64', 'N/A')
            actifs = emp_data.get('actifs', 'N/A')
            actifs_occupes = emp_data.get('actifs_occupes', 'N/A')
            chomeurs = emp_data.get('chomeurs', 'N/A')
            inactifs = emp_data.get('inactifs', 'N/A')
            autres_inactifs = emp_data.get('autres_inactifs', 'N/A')

            # Grille 2 x 3
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                st.metric("👥 Population 15-64 ans", format_int_fr(pop_15_64) if pop_15_64 != 'N/A' else 'N/A')
            with row1_col2:
                st.metric("💼 Actifs", format_int_fr(actifs) if actifs != 'N/A' else 'N/A')

            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                st.metric("✅ Actifs occupés", format_int_fr(actifs_occupes) if actifs_occupes != 'N/A' else 'N/A')
            with row2_col2:
                st.metric("❌ Chômeurs", format_int_fr(chomeurs) if chomeurs != 'N/A' else 'N/A')

            row3_col1, row3_col2 = st.columns(2)
            with row3_col1:
                st.metric("🚫 Total inactifs", format_int_fr(inactifs) if inactifs != 'N/A' else 'N/A')
            with row3_col2:
                st.metric("📄 Autres inactifs", format_int_fr(autres_inactifs) if autres_inactifs != 'N/A' else 'N/A')
            
        else:
            st.warning("⚠️ Données d'emploi non disponibles pour cette commune")

st.markdown("""
<div class="site-footer">
    <p>Sources : OpenDataSoft · INSEE · Open Data France</p>
</div>
""", unsafe_allow_html=True)
