"""
Module de chargement et de gestion des données pour l'application de comparaison de villes
"""
import requests
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional

CITIES_API_URL = "https://public.opendatasoft.com/api/records/1.0/search/?dataset=geonames-all-cities-with-a-population-1000&q=population>20000&rows=1000&refine.country_code=FR"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _weather_code_to_label(code: Optional[int]) -> str:
    labels = {
        0: "Ciel dégagé",
        1: "Principalement dégagé",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brouillard",
        48: "Brouillard givrant",
        51: "Bruine légère",
        53: "Bruine modérée",
        55: "Bruine dense",
        61: "Pluie faible",
        63: "Pluie modérée",
        65: "Pluie forte",
        71: "Neige faible",
        73: "Neige modérée",
        75: "Neige forte",
        80: "Averses faibles",
        81: "Averses modérées",
        82: "Averses fortes",
        95: "Orage",
        96: "Orage avec grêle",
        99: "Orage violent"
    }
    return labels.get(code, "Conditions non disponibles")


def _fallback_weather_current() -> Dict:
    return {
        'current_condition': [{
            'temp_C': 'N/A',
            'weatherDesc': [{'value': 'Données non disponibles'}],
            'humidity': 'N/A',
            'windspeedKmph': 'N/A',
            'FeelsLikeC': 'N/A',
            'pressure': 'N/A',
            'visibility': 'N/A',
            'precipMM': 'N/A'
        }]
    }

@st.cache_data(ttl=3600)
def load_cities_data() -> pd.DataFrame:
    """
    Charge les données des villes françaises > 20 000 habitants depuis OpenDataSoft
    """
    try:
        response = requests.get(CITIES_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        records = data.get('records', [])
        rows = []

        for record in records:
            fields = record.get('fields', {})
            coordinates = fields.get('coordinates', [None, None])
            lat = coordinates[0] if isinstance(coordinates, list) and len(coordinates) >= 2 else None
            lon = coordinates[1] if isinstance(coordinates, list) and len(coordinates) >= 2 else None

            rows.append({
                'ville': fields.get('name'),
                'population': fields.get('population'),
                'region_code': fields.get('admin1_code'),
                'departement_code': fields.get('admin2_code'),
                'pays': fields.get('country_code'),
                'timezone': fields.get('timezone'),
                'altitude': fields.get('dem'),
                'lat': lat,
                'lon': lon
            })

        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Erreur lors du chargement des villes: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_insee_employment_data() -> pd.DataFrame:
    """
    Charge les données d'emploi depuis l'API INSEE (simulé avec des données fictives)
    En production, utiliser l'API officielle de l'INSEE avec authentification
    """
    # TODO: Remplacer par l'API INSEE réelle avec authentification
    # Pour l'instant, retourne un DataFrame vide qui sera complété avec des données simulées
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_housing_data() -> pd.DataFrame:
    """
    Charge les données de logement (DVF - Demandes de Valeurs Foncières)
    """
    # Utilise l'API data.gouv.fr pour les données DVF
    url = "https://public.opendatasoft.com/api/records/1.0/search/"
    params = {
        "dataset": "dvf-communes",
        "rows": 1000
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        records = data.get('records', [])
        return pd.json_normalize(records)
    except Exception as e:
        st.warning(f"Impossible de charger les données de logement: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=1800)
def get_weather_current(city: str) -> Dict:
    """
    Récupère la météo actuelle pour une ville
    Coordonnées via OpenDataSoft, météo via Open-Meteo
    """
    try:
        df_cities = load_cities_data()
        if df_cities.empty or 'ville' not in df_cities.columns:
            return _fallback_weather_current()

        city_match = df_cities[df_cities['ville'].str.lower() == city.lower()]
        if city_match.empty:
            return _fallback_weather_current()

        city_info = city_match.iloc[0]
        lat = city_info.get('lat')
        lon = city_info.get('lon')

        if pd.isna(lat) or pd.isna(lon):
            return _fallback_weather_current()

        params = {
            "latitude": float(lat),
            "longitude": float(lon),
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,pressure_msl,cloud_cover,wind_speed_10m,visibility,weather_code",
            "timezone": "auto"
        }
        response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()

        current = response.json().get('current', {})
        weather_code = current.get('weather_code')

        return {
            'current_condition': [{
                'temp_C': str(round(current.get('temperature_2m'))) if current.get('temperature_2m') is not None else 'N/A',
                'weatherDesc': [{'value': _weather_code_to_label(weather_code)}],
                'humidity': str(round(current.get('relative_humidity_2m'))) if current.get('relative_humidity_2m') is not None else 'N/A',
                'windspeedKmph': str(round(current.get('wind_speed_10m'))) if current.get('wind_speed_10m') is not None else 'N/A',
                'FeelsLikeC': str(round(current.get('apparent_temperature'))) if current.get('apparent_temperature') is not None else 'N/A',
                'pressure': str(round(current.get('pressure_msl'))) if current.get('pressure_msl') is not None else 'N/A',
                'visibility': str(round((current.get('visibility') or 0) / 1000)) if current.get('visibility') is not None else 'N/A',
                'precipMM': str(current.get('precipitation', 'N/A'))
            }]
        }
    except Exception:
        return _fallback_weather_current()


@st.cache_data(ttl=1800)
def get_weather_forecast(city: str) -> List[Dict]:
    """
    Récupère les prévisions météo pour une ville
    """
    try:
        df_cities = load_cities_data()
        if df_cities.empty or 'ville' not in df_cities.columns:
            return []

        city_match = df_cities[df_cities['ville'].str.lower() == city.lower()]
        if city_match.empty:
            return []

        city_info = city_match.iloc[0]
        lat = city_info.get('lat')
        lon = city_info.get('lon')

        if pd.isna(lat) or pd.isna(lon):
            return []

        params = {
            "latitude": float(lat),
            "longitude": float(lon),
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "forecast_days": 3,
            "timezone": "auto"
        }
        response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()

        daily = response.json().get('daily', {})
        dates = daily.get('time', [])
        max_temps = daily.get('temperature_2m_max', [])
        min_temps = daily.get('temperature_2m_min', [])
        weather_codes = daily.get('weather_code', [])

        forecast = []
        for date, max_temp, min_temp, code in zip(dates, max_temps, min_temps, weather_codes):
            forecast.append({
                'date': date,
                'maxtempC': str(round(max_temp)) if max_temp is not None else 'N/A',
                'mintempC': str(round(min_temp)) if min_temp is not None else 'N/A',
                'hourly': [{
                    'weatherDesc': [{'value': _weather_code_to_label(code)}]
                }]
            })

        return forecast
    except Exception:
        return []


def get_city_wikipedia_summary(city_name: str) -> str:
    """
    Récupère le résumé Wikipedia d'une ville
    """
    try:
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{city_name}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('extract', 'Aucune description disponible')
    except:
        pass
    
    return "Aucune description disponible"


def generate_mock_employment_data(city: str, population: int) -> Dict:
    """
    Génère des données d'emploi fictives basées sur la population
    À remplacer par de vraies données de l'API Pôle Emploi / INSEE
    """
    import random
    random.seed(hash(city) % 1000)
    
    taux_chomage = round(random.uniform(5, 12), 1)
    taux_activite = round(random.uniform(65, 75), 1)
    
    return {
        'taux_chomage': taux_chomage,
        'taux_activite': taux_activite,
        'emploi_salarie': int(population * 0.35),
        'emploi_non_salarie': int(population * 0.08),
        'secteur_public': int(population * 0.15),
        'secteur_prive': int(population * 0.28),
    }


def generate_mock_housing_data(city: str, population: int) -> Dict:
    """
    Génère des données de logement fictives
    À remplacer par de vraies données INSEE / DVF
    """
    import random
    random.seed(hash(city) % 1000)
    
    prix_m2 = int(random.uniform(1500, 4500))
    
    return {
        'prix_moyen_m2': prix_m2,
        'nombre_logements': int(population * 0.48),
        'taux_residence_principale': round(random.uniform(75, 92), 1),
        'taux_residence_secondaire': round(random.uniform(3, 12), 1),
        'taux_logements_vacants': round(random.uniform(5, 15), 1),
        'maisons': round(random.uniform(30, 70), 1),
        'appartements': round(random.uniform(30, 70), 1),
    }


def get_climate_data(city: str) -> Dict:
    """
    Récupère les données climatiques annuelles
    """
    try:
        current = get_weather_current(city)
        return {
            'available': bool(current and current.get('current_condition')),
            'data': current
        }
    except Exception:
        pass

    return {'available': False}


def get_city_list(df: pd.DataFrame) -> List[str]:
    """
    Retourne la liste des noms de villes triée
    """
    if 'ville' in df.columns:
        return sorted(df['ville'].dropna().unique().tolist())
    return []


def get_city_info(df: pd.DataFrame, city_name: str) -> Optional[pd.Series]:
    """
    Retourne les informations d'une ville spécifique
    """
    if 'ville' in df.columns:
        city_data = df[df['ville'] == city_name]
        if not city_data.empty:
            return city_data.iloc[0]
    return None
