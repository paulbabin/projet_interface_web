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
    generate_mock_housing_data
)

st.set_page_config(page_title="Logement", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

from utils.navbar import inject_navbar_css, render_navbar
inject_navbar_css()
render_navbar("Logement")

st.title("Logement et Immobilier")
st.markdown("Analyse du marché du logement dans les villes françaises")

# Chargement des données
df_cities = load_cities_data()
city_list = get_city_list(df_cities)

# Sélection de ville
selected_city = st.selectbox("🏙️ Sélectionnez une ville", city_list)

if selected_city:
    city_info = get_city_info(df_cities, selected_city)
    
    if city_info is not None and 'population' in city_info:
        st.header(f"🏠 Marché du logement - {selected_city}")
        
        # Générer les données de logement
        housing_data = generate_mock_housing_data(selected_city, int(city_info['population']))
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Prix moyen/m²",
                f"{housing_data['prix_moyen_m2']:,} €",
                help="Prix moyen au mètre carré"
            )
        
        with col2:
            st.metric(
                "🏘️ Nombre de logements",
                f"{housing_data['nombre_logements']:,}",
                help="Nombre total de logements"
            )
        
        with col3:
            st.metric(
                "🏡 Résidences principales",
                f"{housing_data['taux_residence_principale']}%",
                help="Logements occupés par leurs propriétaires ou locataires"
            )
        
        with col4:
            st.metric(
                "🔑 Logements vacants",
                f"{housing_data['taux_logements_vacants']}%",
                help="Logements inoccupés"
            )
        
        st.divider()
        
        # Graphiques
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Répartition des types de résidences
            st.subheader("🏘️ Types de résidences")
            
            residence_df = pd.DataFrame({
                'Type': ['Résidences principales', 'Résidences secondaires', 'Logements vacants'],
                'Pourcentage': [
                    housing_data['taux_residence_principale'],
                    housing_data['taux_residence_secondaire'],
                    housing_data['taux_logements_vacants']
                ]
            })
            
            fig_residence = px.pie(
                residence_df,
                values='Pourcentage',
                names='Type',
                title=f"Répartition des logements à {selected_city}",
                color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c']
            )
            st.plotly_chart(fig_residence, use_container_width=True)
        
        with col_right:
            # Maisons vs Appartements
            st.subheader("🏡 Types de logements")
            
            type_df = pd.DataFrame({
                'Type': ['Maisons', 'Appartements'],
                'Pourcentage': [housing_data['maisons'], housing_data['appartements']]
            })
            
            fig_type = px.bar(
                type_df,
                x='Type',
                y='Pourcentage',
                title=f"Maisons vs Appartements",
                text='Pourcentage',
                color='Type',
                color_discrete_sequence=['#f39c12', '#9b59b6']
            )
            fig_type.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_type.update_layout(yaxis_title="Pourcentage (%)")
            st.plotly_chart(fig_type, use_container_width=True)
        
        st.divider()
        
        # Comparaison des prix avec d'autres villes
        st.subheader("💰 Comparaison des prix immobiliers")
        
        # Sélection de villes pour comparaison
        comparison_cities = st.multiselect(
            "Sélectionnez des villes à comparer",
            [c for c in city_list if c != selected_city],
            default=[c for c in city_list if c != selected_city][:4]
        )
        
        if comparison_cities:
            comparison_data = []
            
            # Ville sélectionnée
            comparison_data.append({
                'Ville': selected_city,
                'Prix/m²': housing_data['prix_moyen_m2'],
                'Nombre de logements': housing_data['nombre_logements']
            })
            
            # Autres villes
            for city in comparison_cities:
                info = get_city_info(df_cities, city)
                if info is not None and 'population' in info:
                    housing = generate_mock_housing_data(city, int(info['population']))
                    comparison_data.append({
                        'Ville': city,
                        'Prix/m²': housing['prix_moyen_m2'],
                        'Nombre de logements': housing['nombre_logements']
                    })
            
            comp_df = pd.DataFrame(comparison_data)
            
            # Graphique de comparaison des prix
            fig_price = px.bar(
                comp_df,
                x='Ville',
                y='Prix/m²',
                title="Comparaison des prix au m²",
                text='Prix/m²',
                color='Prix/m²',
                color_continuous_scale='RdYlGn_r'
            )
            fig_price.update_traces(texttemplate='%{text:,} €', textposition='outside')
            fig_price.update_layout(yaxis_title="Prix au m² (€)", height=500)
            st.plotly_chart(fig_price, use_container_width=True)
            
            # Graphique nombre de logements
            fig_count = px.bar(
                comp_df,
                x='Ville',
                y='Nombre de logements',
                title="Nombre de logements par ville",
                text='Nombre de logements',
                color='Ville'
            )
            fig_count.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig_count.update_layout(yaxis_title="Nombre de logements", showlegend=False)
            st.plotly_chart(fig_count, use_container_width=True)
            
            # Tableau de données
            st.dataframe(
                comp_df.set_index('Ville').style.format({
                    'Prix/m²': '{:,.0f} €',
                    'Nombre de logements': '{:,.0f}'
                }),
                use_container_width=True
            )
        
        st.divider()
        
        # Estimation de budget
        st.subheader("🧮 Estimateur de budget")
        
        col1, col2 = st.columns(2)
        
        with col1:
            surface = st.number_input(
                "Surface souhaitée (m²)",
                min_value=10,
                max_value=500,
                value=70,
                step=5
            )
        
        with col2:
            type_bien = st.selectbox("Type de bien", ["Appartement", "Maison"])
        
        # Calcul du prix estimé
        prix_estime = housing_data['prix_moyen_m2'] * surface
        
        # Ajustement selon le type
        if type_bien == "Maison":
            prix_estime = prix_estime * 0.9  # Légèrement moins cher au m²
        
        st.success(f"💰 **Prix estimé**: {prix_estime:,.0f} €")
        st.info(f"📊 Soit {housing_data['prix_moyen_m2']:,.0f} €/m² pour {surface} m²")

st.divider()
st.info("💡 Note: Les données immobilières sont simulées. En production, utiliser les données DVF (Demandes de Valeurs Foncières) et l'API data.gouv.fr.")
