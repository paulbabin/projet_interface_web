"""
🏠 Page Logement
Analyse du marché immobilier et du logement par ville
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
    get_housing_data
)

st.set_page_config(page_title="Logement", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

from utils.navbar import inject_navbar_css, render_navbar
inject_navbar_css()
render_navbar("Logement")

st.markdown("""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-size:2.2rem; font-weight:700; color:#1e293b; margin:0; letter-spacing:-1px;">
        Logement et immobilier
    </h1>
    <p style="color:#64748b; font-size:1.05rem; margin-top:0.5rem;">
        Analyse du marché du logement dans les villes françaises
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
        
        st.header(f"🏠 Marché du logement - {selected_city}")
        
        # Récupérer les données de logement réelles
        housing_data = get_housing_data(selected_city, ville_nom, departement_code)
        
        if housing_data:
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                pieces_moy = housing_data.get('pieces_moyennes', 'N/A')
                st.metric(
                    "🏠 Pièces moyennes",
                    f"{pieces_moy}" if pieces_moy != 'N/A' else 'N/A',
                    help="Nombre moyen de pièces par résidence principale"
                )
            
            with col2:
                nb_logements = housing_data.get('nombre_logements', 'N/A')
                st.metric(
                    "🏘️ Nombre de logements",
                    f"{nb_logements:,}" if nb_logements != 'N/A' else 'N/A',
                    help="Nombre total de logements dans la commune"
                )
            
            with col3:
                taux_hlm = housing_data.get('taux_hlm', 'N/A')
                st.metric(
                    "🏡 HLM",
                    f"{taux_hlm}%" if taux_hlm != 'N/A' else 'N/A',
                    help="Taux de logements HLM parmi les résidences principales"
                )
            
            with col4:
                taux_vacants = housing_data.get('taux_logements_vacants', 'N/A')
                st.metric(
                    "🔑 Logements vacants",
                    f"{taux_vacants}%" if taux_vacants != 'N/A' else 'N/A',
                    help="Taux de logements inoccupés"
                )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                taux_prop = housing_data.get('taux_proprietaires', 'N/A')
                st.metric(
                    "🏠 Propriétaires",
                    f"{taux_prop}%" if taux_prop != 'N/A' else 'N/A',
                    help="Taux de propriétaires parmi les résidences principales"
                )
            
            with col2:
                taux_loc = housing_data.get('taux_locataires', 'N/A')
                st.metric(
                    "🔑 Locataires",
                    f"{taux_loc}%" if taux_loc != 'N/A' else 'N/A',
                    help="Taux de locataires parmi les résidences principales"
                )
            
            with col3:
                nb_menages = housing_data.get('nombre_menages', 'N/A')
                st.metric(
                    "👨‍👩‍👧‍👦 Ménages",
                    f"{nb_menages:,}" if nb_menages != 'N/A' else 'N/A',
                    help="Nombre total de ménages"
                )
            
            st.divider()
            
            # Graphiques
            col_left, col_right = st.columns(2)
            
            with col_left:
                # Répartition des types de résidences
                st.subheader("🏘️ Visualisation")
                
                nb_logements = housing_data.get('nombre_logements', 0)
                nb_principales = housing_data.get('nombre_residences_principales', 0)
                nb_secondaires = housing_data.get('nombre_residences_secondaires', 0)
                nb_vacants = housing_data.get('nombre_logements_vacants', 0)
                
                if nb_logements and nb_logements != 'N/A':
                    taux_principales = (nb_principales / nb_logements * 100) if nb_logements > 0 else 0
                    taux_secondaires = (nb_secondaires / nb_logements * 100) if nb_logements > 0 else 0
                    taux_vacants_calc = (nb_vacants / nb_logements * 100) if nb_logements > 0 else 0
                    
                    residence_df = pd.DataFrame({
                        'Type': ['Résidences principales', 'Résidences secondaires', 'Logements vacants'],
                        'Pourcentage': [
                            round(taux_principales, 1),
                            round(taux_secondaires, 1),
                            round(taux_vacants_calc, 1)
                        ]
                    })
                    
                    fig_residence = px.pie(
                        residence_df,
                        values='Pourcentage',
                        names='Type',
                        title=f"Répartition des logements",
                        color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c']
                    )
                    st.plotly_chart(fig_residence, use_container_width=True)
                else:
                    st.warning("⚠️ Données de répartition non disponibles")
            
            with col_right:
                # Maisons vs Appartements
                st.subheader("")
                
                taux_maisons = housing_data.get('taux_maisons', 'N/A')
                taux_appartements = housing_data.get('taux_appartements', 'N/A')
                
                if taux_maisons != 'N/A' and taux_appartements != 'N/A':
                    type_df = pd.DataFrame({
                        'Type': ['Maisons', 'Appartements'],
                        'Pourcentage': [taux_maisons, taux_appartements]
                    })
                    
                    fig_type = px.bar(
                        type_df,
                        x='Type',
                        y='Pourcentage',
                        title=f"Répartition par type",
                        text='Pourcentage',
                        color='Type',
                        color_discrete_sequence=['#f39c12', '#9b59b6']
                    )
                    fig_type.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig_type.update_layout(yaxis_title="Pourcentage (%)")
                    st.plotly_chart(fig_type, use_container_width=True)
                else:
                    st.warning("⚠️ Données de répartition non disponibles")
            
            # Graphique statut d'occupation
            taux_prop_val = housing_data.get('taux_proprietaires', 0)
            taux_loc_val = housing_data.get('taux_locataires', 0)
            
            if taux_prop_val != 'N/A' and taux_loc_val != 'N/A':
                statut_df = pd.DataFrame({
                    'Statut': ['Propriétaires', 'Locataires', 'Autres'],
                    'Pourcentage': [
                        taux_prop_val,
                        taux_loc_val,
                        100 - taux_prop_val - taux_loc_val
                    ]
                })
                
                fig_statut = px.pie(
                    statut_df,
                    values='Pourcentage',
                    names='Statut',
                    title="Répartition par statut d'occupation",
                    color_discrete_sequence=['#27ae60', '#e67e22', '#95a5a6']
                )
                st.plotly_chart(fig_statut, use_container_width=True)
                
            else:
                st.warning("⚠️ Données de logement non disponibles pour cette commune")

st.markdown("""
<div class="site-footer">
    <p>Sources : OpenDataSoft · Caisse des Dépôts · Open Data France</p>
</div>
""", unsafe_allow_html=True)
