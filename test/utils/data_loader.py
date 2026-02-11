"""
Module de chargement et de gestion des données pour l'application de comparaison de villes
"""
import requests
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional

@st.cache_data(ttl=3600)
def load_cities_data() -> pd.DataFrame:
    """
    Charge les données des villes françaises > 20 000 habitants depuis OpenDataSoft
    """
    url = "https://public.opendatasoft.com/api/records/1.0/search/"
    params = {
        "dataset": "geonames-all-cities-with-a-population-1000",
        "q": "population>20000",
        "rows": 1000,
        "refine.country_code": "FR"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        records = data.get('records', [])
        df = pd.json_normalize(records)
        
        # Extraire les coordonnées correctement
        if 'fields.coordinates' in df.columns:
            df['lat'] = df['fields.coordinates'].apply(lambda x: x[1] if isinstance(x, list) and len(x) >= 2 else None)
            df['lon'] = df['fields.coordinates'].apply(lambda x: x[0] if isinstance(x, list) and len(x) >= 2 else None)
        
        # Renommer les colonnes importantes
        column_mapping = {
            'fields.name': 'ville',
            'fields.population': 'population',
            'fields.admin1_code': 'region_code',
            'fields.admin2_code': 'departement_code',
            'fields.country_code': 'pays',
            'fields.timezone': 'timezone',
            'fields.dem': 'altitude'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        return df
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
    Utilise OpenWeatherMap (nécessite une clé API gratuite)
    """
    # Pour démo, utilise wttr.in qui ne nécessite pas de clé
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    return {
        'current_condition': [{
            'temp_C': 'N/A',
            'weatherDesc': [{'value': 'Données non disponibles'}],
            'humidity': 'N/A',
            'windspeedKmph': 'N/A'
        }]
    }


@st.cache_data(ttl=1800)
def get_weather_forecast(city: str) -> List[Dict]:
    """
    Récupère les prévisions météo pour une ville
    """
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('weather', [])
    except:
        pass
    
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
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'available': True,
                'data': data
            }
    except:
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
