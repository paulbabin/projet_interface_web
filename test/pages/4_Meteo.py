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

st.set_page_config(page_title="Météo", page_icon="🌤️", layout="wide")

st.title("🌤️ Météo et Climat")
st.markdown("Conditions météorologiques actuelles et prévisions")

# Chargement des données
df_cities = load_cities_data()
city_list = get_city_list(df_cities)

# Sélection de ville
selected_city = st.selectbox("🏙️ Sélectionnez une ville", city_list)

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
    
    st.divider()
    
    # Comparaison météo entre villes
    st.subheader("🌍 Comparaison Météo")
    
    comparison_cities = st.multiselect(
        "Comparez la météo avec d'autres villes",
        [c for c in city_list if c != selected_city],
        default=[]
    )
    
    if comparison_cities:
        all_cities = [selected_city] + comparison_cities
        temp_comparison = []
        
        with st.spinner("Chargement des données..."):
            for city in all_cities:
                weather = get_weather_current(city)
                if weather and 'current_condition' in weather:
                    current_cond = weather['current_condition'][0]
                    temp_comparison.append({
                        'Ville': city,
                        'Température': current_cond.get('temp_C', 'N/A'),
                        'Humidité': current_cond.get('humidity', 'N/A'),
                        'Vent': current_cond.get('windspeedKmph', 'N/A')
                    })
        
        if temp_comparison:
            comp_df = pd.DataFrame(temp_comparison)
            
            # Convertir en numérique
            comp_df['Température'] = pd.to_numeric(comp_df['Température'], errors='coerce')
            comp_df['Humidité'] = pd.to_numeric(comp_df['Humidité'], errors='coerce')
            comp_df['Vent'] = pd.to_numeric(comp_df['Vent'], errors='coerce')
            
            # Graphique de comparaison
            fig_comp = go.Figure()
            
            fig_comp.add_trace(go.Bar(
                name='Température (°C)',
                x=comp_df['Ville'],
                y=comp_df['Température'],
                text=comp_df['Température'].apply(lambda x: f"{x:.0f}°C" if pd.notna(x) else 'N/A'),
                textposition='auto',
                marker_color='#e74c3c'
            ))
            
            fig_comp.update_layout(
                title="Comparaison des températures",
                yaxis_title="Température (°C)",
                height=400
            )
            
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # Tableau de comparaison
            st.dataframe(comp_df.set_index('Ville'), use_container_width=True)

st.divider()
st.info("💡 Les données météo sont fournies en temps réel par wttr.in. Pour des données climatiques annuelles, consultez Météo France.")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem 0;'>
    <p>📊 Source: wttr.in | Mise à jour en temps réel</p>
</div>
""", unsafe_allow_html=True)
