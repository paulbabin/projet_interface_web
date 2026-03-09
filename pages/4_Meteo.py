"""
🌤️ Page Météo et Climat
Données météorologiques actuelles et prévisionnelles
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
    get_weather_current,
    get_weather_forecast
)

st.set_page_config(page_title="Météo", page_icon="🌤️", layout="wide", initial_sidebar_state="collapsed")

from utils.navbar import inject_navbar_css, render_navbar
inject_navbar_css()
render_navbar("Météo")

st.markdown("""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-size:2.2rem; font-weight:700; color:#1e293b; margin:0; letter-spacing:-1px;">
        Météo et climat
    </h1>
    <p style="color:#64748b; font-size:1.05rem; margin-top:0.5rem;">
        Conditions météo actuelles et prévisions des villes françaises
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
    st.header(f"🌤️ Météo - {selected_city}")
    
    # Météo actuelle
    with st.spinner("☁️ Chargement des données météo..."):
        weather_data = get_weather_current(selected_city)
    
    if weather_data and 'current_condition' in weather_data:
        current = weather_data['current_condition'][0]
        
        st.subheader("📍 Conditions Actuelles")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = current.get('temp_C', 'N/A')
            st.metric(
                "🌡️ Température",
                f"{temp}°C" if temp != 'N/A' else 'N/A',
                help="Température actuelle"
            )
        
        with col2:
            humidity = current.get('humidity', 'N/A')
            st.metric(
                "💧 Humidité",
                f"{humidity}%" if humidity != 'N/A' else 'N/A',
                help="Taux d'humidité"
            )
        
        with col3:
            wind = current.get('windspeedKmph', 'N/A')
            st.metric(
                "💨 Vent",
                f"{wind} km/h" if wind != 'N/A' else 'N/A',
                help="Vitesse du vent"
            )
        
        with col4:
            feels_like = current.get('FeelsLikeC', 'N/A')
            st.metric(
                "🌡️ Ressenti",
                f"{feels_like}°C" if feels_like != 'N/A' else 'N/A',
                help="Température ressentie"
            )
        
        # Description météo
        if 'weatherDesc' in current and len(current['weatherDesc']) > 0:
            weather_desc = current['weatherDesc'][0].get('value', 'N/A')
            st.info(f"☁️ **{weather_desc}**")
        
        # Informations supplémentaires
        col1, col2, col3 = st.columns(3)
        
        with col1:
            pressure = current.get('pressure', 'N/A')
            st.metric("🔽 Pression", f"{pressure} mb" if pressure != 'N/A' else 'N/A')
        
        with col2:
            visibility = current.get('visibility', 'N/A')
            st.metric("👁️ Visibilité", f"{visibility} km" if visibility != 'N/A' else 'N/A')
        
        with col3:
            precip = current.get('precipMM', 'N/A')
            st.metric("🌧️ Précipitations", f"{precip} mm" if precip != 'N/A' else 'N/A')
        
        st.divider()
        
        # Prévisions
        st.subheader("📅 Prévisions à 3 jours")
        
        forecast_data = get_weather_forecast(selected_city)
        
        if forecast_data:
            # Préparer les données de prévisions
            forecast_list = []
            
            for day in forecast_data[:3]:  # 3 jours
                date = day.get('date', 'N/A')
                max_temp = day.get('maxtempC', 'N/A')
                min_temp = day.get('mintempC', 'N/A')
                
                hourly = day.get('hourly', [])
                if hourly and len(hourly) > 0:
                    weather_desc = hourly[0].get('weatherDesc', [{}])[0].get('value', 'N/A')
                else:
                    weather_desc = 'N/A'
                
                forecast_list.append({
                    'Date': date,
                    'Température Max': max_temp,
                    'Température Min': min_temp,
                    'Conditions': weather_desc
                })
            
            # Affichage des prévisions en colonnes
            cols = st.columns(len(forecast_list))
            
            for idx, (col, forecast) in enumerate(zip(cols, forecast_list)):
                with col:
                    st.markdown(f"### 📅 {forecast['Date']}")
                    st.metric("🔺 Max", f"{forecast['Température Max']}°C")
                    st.metric("🔻 Min", f"{forecast['Température Min']}°C")
                    st.caption(f"☁️ {forecast['Conditions']}")
            
            st.divider()
            
            # Graphique de température
            st.subheader("📊 Évolution des températures")
            
            if forecast_list:
                forecast_df = pd.DataFrame(forecast_list)
                
                # Convertir en numérique
                forecast_df['Température Max'] = pd.to_numeric(forecast_df['Température Max'], errors='coerce')
                forecast_df['Température Min'] = pd.to_numeric(forecast_df['Température Min'], errors='coerce')
                
                fig_temp = go.Figure()
                
                fig_temp.add_trace(go.Scatter(
                    x=forecast_df['Date'],
                    y=forecast_df['Température Max'],
                    mode='lines+markers',
                    name='Température Max',
                    line=dict(color='#e74c3c', width=3),
                    marker=dict(size=10)
                ))
                
                fig_temp.add_trace(go.Scatter(
                    x=forecast_df['Date'],
                    y=forecast_df['Température Min'],
                    mode='lines+markers',
                    name='Température Min',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=10)
                ))
                
                fig_temp.update_layout(
                    title=f"Prévisions de température - {selected_city}",
                    xaxis_title="Date",
                    yaxis_title="Température (°C)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.warning("⚠️ Prévisions non disponibles pour cette ville")
    
    else:
        st.error("❌ Impossible de récupérer les données météo pour cette ville")
    

st.markdown("""
<div class="site-footer">
    <p>Sources : OpenDataSoft · INSEE · Open Data France</p>
</div>
""", unsafe_allow_html=True)
