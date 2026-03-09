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
    generate_mock_employment_data
)

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
    
    if city_info is not None and 'population' in city_info:
        st.header(f"📊 Données d'emploi - {selected_city}")
        
        # Générer les données d'emploi
        emp_data = generate_mock_employment_data(selected_city, int(city_info['population']))
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💼 Taux de chômage",
                f"{emp_data['taux_chomage']}%",
                delta=None,
                help="Pourcentage de la population active au chômage"
            )
        
        with col2:
            st.metric(
                "📈 Taux d'activité",
                f"{emp_data['taux_activite']}%",
                help="Pourcentage de la population en âge de travailler qui est active"
            )
        
        with col3:
            st.metric(
                "👔 Emplois salariés",
                f"{emp_data['emploi_salarie']:,}",
                help="Nombre d'emplois salariés"
            )
        
        with col4:
            st.metric(
                "🏢 Emplois non salariés",
                f"{emp_data['emploi_non_salarie']:,}",
                help="Indépendants, professions libérales, etc."
            )
        
        st.divider()
        
        # Graphiques
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Répartition Public/Privé
            st.subheader("🏛️ Répartition des emplois")
            
            sectors_df = pd.DataFrame({
                'Secteur': ['Secteur Public', 'Secteur Privé'],
                'Emplois': [emp_data['secteur_public'], emp_data['secteur_prive']]
            })
            
            fig_sectors = px.pie(
                sectors_df,
                values='Emplois',
                names='Secteur',
                title=f"Répartition Public/Privé à {selected_city}",
                color_discrete_sequence=['#1f77b4', '#ff7f0e']
            )
            st.plotly_chart(fig_sectors, use_container_width=True)
        
        with col_right:
            # Répartition Salariés/Non salariés
            st.subheader("💼 Type d'emploi")
            
            employment_df = pd.DataFrame({
                'Type': ['Salariés', 'Non salariés'],
                'Nombre': [emp_data['emploi_salarie'], emp_data['emploi_non_salarie']]
            })
            
            fig_employment = px.bar(
                employment_df,
                x='Type',
                y='Nombre',
                title=f"Salariés vs Non salariés",
                text='Nombre',
                color='Type',
                color_discrete_sequence=['#2ecc71', '#e74c3c']
            )
            fig_employment.update_traces(texttemplate='%{text:,}', textposition='outside')
            st.plotly_chart(fig_employment, use_container_width=True)
        
        st.divider()
        
        # Comparaison avec d'autres villes
        st.subheader("📊 Comparaison avec d'autres villes")
        
        # Sélection de villes pour comparaison
        comparison_cities = st.multiselect(
            "Sélectionnez des villes à comparer",
            [c for c in city_list if c != selected_city],
            default=[c for c in city_list if c != selected_city][:3]
        )
        
        if comparison_cities:
            comparison_data = []
            
            # Ville sélectionnée
            comparison_data.append({
                'Ville': selected_city,
                'Taux de chômage': emp_data['taux_chomage'],
                'Taux d\'activité': emp_data['taux_activite']
            })
            
            # Autres villes
            for city in comparison_cities:
                info = get_city_info(df_cities, city)
                if info is not None and 'population' in info:
                    emp = generate_mock_employment_data(city, int(info['population']))
                    comparison_data.append({
                        'Ville': city,
                        'Taux de chômage': emp['taux_chomage'],
                        'Taux d\'activité': emp['taux_activite']
                    })
            
            comp_df = pd.DataFrame(comparison_data)
            
            # Graphique de comparaison
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Bar(
                name='Taux de chômage',
                x=comp_df['Ville'],
                y=comp_df['Taux de chômage'],
                text=comp_df['Taux de chômage'].apply(lambda x: f"{x}%"),
                textposition='auto',
                marker_color='#e74c3c'
            ))
            
            fig_comparison.add_trace(go.Bar(
                name='Taux d\'activité',
                x=comp_df['Ville'],
                y=comp_df['Taux d\'activité'],
                text=comp_df['Taux d\'activité'].apply(lambda x: f"{x}%"),
                textposition='auto',
                marker_color='#2ecc71'
            ))
            
            fig_comparison.update_layout(
                title="Comparaison des indicateurs d'emploi",
                yaxis_title="Taux (%)",
                barmode='group',
                height=500
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Tableau de données
            st.dataframe(comp_df.set_index('Ville'), use_container_width=True)

st.markdown("""
<div class="site-footer">
    <p>Sources : OpenDataSoft · INSEE · Open Data France</p>
</div>
""", unsafe_allow_html=True)
