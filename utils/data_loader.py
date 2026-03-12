"""
Module de chargement et de gestion des données pour l'application de comparaison de villes
"""
import re
import requests
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional

# URL de base pour l'API des villes (sans le filtre de pays)
CITIES_API_BASE_URL = "https://public.opendatasoft.com/api/records/1.0/search/?dataset=geonames-all-cities-with-a-population-1000&q=population>20000&rows=1000"
# Codes pays pour la France et les DOM-TOM
FRANCE_TERRITORIES = ['FR', 'GP', 'MQ', 'GF', 'RE', 'YT', 'NC', 'PF', 'PM', 'WF', 'BL', 'MF']
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Chemin vers les fichiers de données
LOGEMENT_FILE = Path(__file__).parent.parent / "data" / "logement.csv"
EMPLOI_FILE = Path(__file__).parent.parent / "data" / "emploi.csv"


def format_int_fr(value) -> str:
    """
    Formate un entier avec séparateur de milliers espace.
    Ex: 1234567 -> "1 234 567"
    """
    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return "N/A"


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


def _read_insee_csv(file_path: Path, required_columns: List[str]) -> pd.DataFrame:
    """
    Lit un CSV INSEE en gérant les variations de séparateur,
    d'encodage et de lignes d'en-tête.
    """
    read_attempts = [
        {"sep": ";", "encoding": "utf-8-sig"},
        {"sep": ";", "encoding": "latin-1"},
        {"sep": ",", "encoding": "utf-8-sig"},
        {"sep": ",", "encoding": "latin-1"},
        {"sep": None, "encoding": "utf-8-sig", "engine": "python"},
    ]

    for skiprows in (0, 4):
        for options in read_attempts:
            try:
                df = pd.read_csv(file_path, skiprows=skiprows, **options)
                if df.empty:
                    continue

                # Normaliser les noms de colonnes pour gérer les exports INSEE hétérogènes.
                rename_map = {
                    original: str(original).strip()
                    for original in df.columns
                    if str(original) != str(original).strip()
                }
                if rename_map:
                    df = df.rename(columns=rename_map)

                if all(col in df.columns for col in required_columns):
                    return df
            except Exception:
                continue

    return pd.DataFrame()


def _to_numeric_safe(series: pd.Series) -> pd.Series:
    """
    Convertit une série en numérique en gérant les espaces insécables,
    séparateurs de milliers et virgules décimales.
    """
    if pd.api.types.is_numeric_dtype(series):
        return series

    cleaned = (
        series.astype(str)
        .str.replace('\u202f', '', regex=False)
        .str.replace(' ', '', regex=False)
        .str.replace(',', '.', regex=False)
        .replace({'': None, 'nan': None, 'None': None})
    )
    return pd.to_numeric(cleaned, errors='coerce')


def _is_arrondissement(ville_name: str) -> bool:
    """
    Détecte si un nom de ville correspond à un arrondissement
    Ex: "Paris 10e Arrondissement", "Marseille 01", "Lyon 03"
    """
    if not ville_name:
        return False
    
    arrondissement_pattern = r'\s+\d+(er|e|ème)\s+(Arrondissement|arrondissement)'
    if re.search(arrondissement_pattern, ville_name):
        return True
    
    short_pattern = r'^(Paris|Marseille|Lyon)\s+\d{2}$'
    if re.search(short_pattern, ville_name):
        return True
    
    return False


def _extract_main_city_name(ville_name: str) -> Optional[str]:
    """
    Extrait le nom de la ville principale d'un arrondissement
    Ex: "Paris 10e Arrondissement" -> "Paris"
        "Marseille 01" -> "Marseille"
        "Lyon 3e Arrondissement" -> "Lyon"
    """
    if not ville_name:
        return None
    
    match = re.match(r'^(Paris|Marseille|Lyon)', ville_name)
    if match:
        return match.group(1)
    
    return None


@st.cache_data(ttl=3600)
def load_cities_data() -> pd.DataFrame:
    """
    Charge les données des villes françaises > 20 000 habitants depuis OpenDataSoft
    Inclut la France métropolitaine et les DOM-TOM
    Agrège les arrondissements de Paris, Marseille et Lyon dans leurs villes principales
    """
    all_rows = []
    
    try:
        # Interroger chaque territoire français pour couvrir métropole et outre-mer.
        for country_code in FRANCE_TERRITORIES:
            url = f"{CITIES_API_BASE_URL}&refine.country_code={country_code}"
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                records = data.get('records', [])

                for record in records:
                    fields = record.get('fields', {})
                    ville_name = fields.get('name')
                    departement_code = fields.get('admin2_code')
                    
                    # Regrouper les arrondissements sous la ville principale.
                    if ville_name and _is_arrondissement(ville_name):
                        main_city = _extract_main_city_name(ville_name)
                        if main_city:
                            ville_name = main_city
                    
                    # Éviter les doublons d'arrondissements pour Paris.
                    if departement_code == '75' and ville_name != 'Paris':
                        continue
                    
                    # Désambiguïser les villes homonymes dans les listes de sélection.
                    if ville_name and departement_code:
                        ville_display = f"{ville_name} ({departement_code})"
                    else:
                        ville_display = ville_name
                    
                    coordinates = fields.get('coordinates', [None, None])
                    lat = coordinates[0] if isinstance(coordinates, list) and len(coordinates) >= 2 else None
                    lon = coordinates[1] if isinstance(coordinates, list) and len(coordinates) >= 2 else None

                    all_rows.append({
                        'ville': ville_display,
                        'ville_nom': ville_name,
                        'population': fields.get('population'),
                        'region_code': fields.get('admin1_code'),
                        'departement_code': departement_code,
                        'pays': fields.get('country_code'),
                        'timezone': fields.get('timezone'),
                        'altitude': fields.get('dem'),
                        'lat': lat,
                        'lon': lon
                    })
            except Exception as e:
                st.warning(f"Impossible de charger les données pour {country_code}: {e}")
                continue

        df = pd.DataFrame(all_rows)
        
            # Fusionner les arrondissements pour obtenir une ligne par grande ville.
        if not df.empty:
            agg_dict = {
                'population': 'sum',
                'lat': 'mean',
                'lon': 'mean',
                'altitude': 'mean',
                'region_code': 'first',
                'departement_code': 'first',
                'pays': 'first',
                'timezone': 'first',
                'ville_nom': 'first'
            }
            df = df.groupby('ville', as_index=False).agg(agg_dict)
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des villes: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_communes_emploi_data() -> pd.DataFrame:
    """
    Charge les données d'emploi communales depuis le fichier CSV INSEE
    Agrège les données IRIS par commune
    """
    try:
        if not EMPLOI_FILE.exists():
            st.warning(f"Fichier de données d'emploi introuvable: {EMPLOI_FILE}")
            return pd.DataFrame()

        # Lire le fichier CSV (sans notion de feuilles)
        df = _read_insee_csv(EMPLOI_FILE, required_columns=['Code géographique'])
        if df.empty:
            st.warning(f"Impossible de lire le fichier d'emploi (format CSV invalide): {EMPLOI_FILE}")
            return pd.DataFrame()
        
        # Filtrer la première ligne qui contient les codes de colonnes
        df = df[df['Code géographique'].astype(str) != 'CODGEO']
        
        # Convertir les colonnes numériques
        numeric_cols = [
            'Pop 15-64 ans en 2022 (princ)',
            'Actifs 15-64 ans en 2022 (princ)',
            'Actifs occupés 15-64 ans en 2022 (princ)',
            'Chômeurs 15-64 ans en 2022 (princ)',
            'Inactifs 15-64 ans en 2022 (princ)',
            'Élèves, étudiants et stagiaires non rémunérés 15-64 ans en 2022 (princ)',
            'Retraités ou préretraités 15-64 ans en 2022 (princ)',
            'Autres inactifs 15-64 ans en 2022 (princ)',
            # Diplômes des actifs
            'Actifs Sans diplôme ou CEP en 2022 (princ)',
            'Actifs BEPC, brevet des collèges, DNB en 2022 (princ)',
            'Actifs CAP-BEP ou équiv. en 2022 (princ)',
            'Actifs Bac, brevet pro. ou équiv.  en 2022 (princ)',
            'Actifs Enseignement sup de niveau bac + 2  en 2022 (princ)',
            'Actifs Enseignement sup de niveau bac + 3 ou 4  en 2022 (princ)',
            'Actifs Enseignement sup de niveau bac + 5 ou plus  en 2022 (princ)',
            # Diplômes des chômeurs
            'Chômeurs Sans diplôme ou CEP en 2022 (princ)',
            'Chômeurs BEPC, brevet des collèges, DNB en 2022 (princ)',
            'Chômeurs CAP-BEP ou équiv. en 2022 (princ)',
            'Chômeurs Bac, brevet pro. ou équiv.  en 2022 (princ)',
            'Chômeurs Enseignement sup de niveau bac + 2  en 2022 (princ)',
            'Chômeurs Enseignement sup de niveau bac + 3 ou 4  en 2022 (princ)',
            'Chômeurs Enseignement sup de niveau bac + 5 ou plus  en 2022 (princ)',
            # PCS (Professions et Catégories Socioprofessionnelles)
            'Actifs 15-64 ans Agriculteurs exploitants en 2022 (compl)',
            'Actifs 15-64 ans Artisans, Comm., Chefs entr. en 2022 (compl)',
            'Actifs 15-64 ans Cadres, Prof. intel. sup. en 2022 (compl)',
            'Actifs 15-64 ans Prof. intermédiaires en 2022 (compl)',
            'Actifs 15-64 ans Employés en 2022 (compl)',
            'Actifs 15-64 ans Ouvriers en 2022 (compl)',
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = _to_numeric_safe(df[col])
        
        # Agréger par commune (code commune)
        agg_dict = {}
        for col in numeric_cols:
            if col in df.columns:
                agg_dict[col] = 'sum'
        
        # Ajouter les colonnes de libellés (prendre le premier)
        if 'Libellé géographique' in df.columns:
            agg_dict['Libellé géographique'] = 'first'
        if 'Département' in df.columns:
            agg_dict['Département'] = 'first'
        if 'Région' in df.columns:
            agg_dict['Région'] = 'first'
        
        df_communes = df.groupby('Code géographique').agg(agg_dict).reset_index()
        
        return df_communes
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données d'emploi: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_communes_logement_data() -> pd.DataFrame:
    """
    Charge les données de logement communales depuis le fichier CSV INSEE
    Agrège les données IRIS par commune
    """
    try:
        if not LOGEMENT_FILE.exists():
            st.warning(f"Fichier de données de logement introuvable: {LOGEMENT_FILE}")
            return pd.DataFrame()

        # Lire le fichier CSV (sans notion de feuilles)
        df = _read_insee_csv(LOGEMENT_FILE, required_columns=['Commune ou ARM'])
        if df.empty:
            st.warning(f"Impossible de lire le fichier logement (format CSV invalide): {LOGEMENT_FILE}")
            return pd.DataFrame()
        
        # Filtrer la première ligne qui contient les codes de colonnes
        if 'Iris' in df.columns:
            df = df[df['Iris'].astype(str) != 'IRIS']
        
        # Convertir les colonnes numériques
        numeric_cols = [
            'Logements en 2022 (princ)',
            'Résidences principales en 2022 (princ)',
            'Rés secondaires et logts occasionnels en 2022 (princ)',
            'Logements vacants en 2022 (princ)',
            'Maisons en 2022 (princ)',
            'Appartements en 2022 (princ)',
            'Rés princ 1 pièce en 2022 (princ)',
            'Rés princ 2 pièces en 2022 (princ)',
            'Rés princ 3 pièces en 2022 (princ)',
            'Rés princ 4 pièces en 2022 (princ)',
            'Rés princ 5 pièces ou plus en 2022 (princ)',
            'Pièces rés princ en 2022 (princ)',
            'Ménages en 2022 (princ)',
            'Rés princ occupées Propriétaires en 2022 (princ)',
            'Rés princ occupées Locataires en 2022 (princ)',
            'Rés princ HLM louée vide en 2022 (princ)',
            'Ménages au moins une voiture en 2022 (princ)',
            'Ménages deux voitures ou plus en 2022 (princ)'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = _to_numeric_safe(df[col])
        
        # Agréger par commune (code commune = Commune ou ARM)
        agg_dict = {}
        for col in numeric_cols:
            if col in df.columns:
                agg_dict[col] = 'sum'
        
        # Ajouter les colonnes de libellés (prendre le premier)
        agg_dict['Libellé commune ou ARM'] = 'first'
        if 'Département' in df.columns:
            agg_dict['Département'] = 'first'
        
        df_communes = df.groupby('Commune ou ARM').agg(agg_dict).reset_index()
        df_communes.rename(columns={'Commune ou ARM': 'code_commune'}, inplace=True)
        
        return df_communes
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données de logement: {e}")
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


@st.cache_data(ttl=3600)
def get_annual_temperature_average(city: str) -> Optional[float]:
    """
    Récupère la température moyenne annuelle depuis le début de l'année en cours
    Utilise l'API Open-Meteo Archive
    """
    try:
        from datetime import date
        
        df_cities = load_cities_data()
        if df_cities.empty or 'ville' not in df_cities.columns:
            return None

        city_match = df_cities[df_cities['ville'].str.lower() == city.lower()]
        if city_match.empty:
            return None

        city_info = city_match.iloc[0]
        lat = city_info.get('lat')
        lon = city_info.get('lon')

        if pd.isna(lat) or pd.isna(lon):
            return None

        # Récupérer les données du 01/01 de l'année courante à aujourd'hui
        today = date.today()
        current_year = today.year
        start_date = f"{current_year}-01-01"
        end_date = today.strftime("%Y-%m-%d")

        params = {
            "latitude": float(lat),
            "longitude": float(lon),
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto"
        }
        
        response = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=10)
        response.raise_for_status()

        daily = response.json().get('daily', {})
        max_temps = daily.get('temperature_2m_max', [])
        min_temps = daily.get('temperature_2m_min', [])

        if not max_temps or not min_temps:
            return None

        # Calculer la moyenne annuelle
        all_temps = [t for t in max_temps + min_temps if t is not None]
        if not all_temps:
            return None

        avg_temp = sum(all_temps) / len(all_temps)
        return round(avg_temp, 1)

    except Exception:
        return None


def get_employment_data(city: str, ville_nom: str, departement_code: str) -> Optional[Dict]:
    """
    Récupère les données d'emploi depuis le fichier Excel INSEE au niveau communal
    Agrège les données des arrondissements pour Paris, Marseille et Lyon
    """
    try:
        df_emploi = load_communes_emploi_data()
        if df_emploi.empty:
            return None
        
        df_cities = load_cities_data()
        if df_cities.empty:
            return None
        
        # Trouver le code commune depuis les données de villes
        city_info = df_cities[df_cities['ville'] == city]
        if city_info.empty:
            return None
        
        # Pour Paris, Marseille, Lyon : chercher tous les arrondissements
        if ville_nom in ['Paris', 'Marseille', 'Lyon']:
            # Chercher toutes les communes dont le code commence par le code du département
            # et dont le libellé contient le nom de la ville
            commune_data = df_emploi[
                (df_emploi['Département'] == departement_code) &
                (df_emploi['Libellé géographique'].str.contains(
                    f'^{ville_nom}', 
                    case=False, 
                    regex=True, 
                    na=False
                ))
            ]
        else:
            # Pour les autres villes, chercher par nom exact
            commune_data = df_emploi[
                df_emploi['Libellé géographique'].str.lower() == ville_nom.lower()
            ]
            
            # Si pas trouvé par nom, essayer avec le code département
            if commune_data.empty:
                communes_dept = df_emploi[df_emploi['Département'] == departement_code]
                if not communes_dept.empty:
                    for idx, row in communes_dept.iterrows():
                        if ville_nom.lower() in str(row['Libellé géographique']).lower():
                            commune_data = communes_dept[communes_dept.index == idx]
                            break
        
        if commune_data.empty:
            return None
        
        # Si plusieurs résultats (arrondissements), agréger
        if len(commune_data) > 1:
            # Sommer toutes les colonnes numériques
            numeric_cols = [
                'Pop 15-64 ans en 2022 (princ)',
                'Actifs 15-64 ans en 2022 (princ)',
                'Actifs occupés 15-64 ans en 2022 (princ)',
                'Chômeurs 15-64 ans en 2022 (princ)',
                'Inactifs 15-64 ans en 2022 (princ)',
                'Élèves, étudiants et stagiaires non rémunérés 15-64 ans en 2022 (princ)',
                'Retraités ou préretraités 15-64 ans en 2022 (princ)',
                'Autres inactifs 15-64 ans en 2022 (princ)'
            ]
            
            # Créer une ligne agrégée
            aggregated = {}
            for col in numeric_cols:
                if col in commune_data.columns:
                    aggregated[col] = commune_data[col].sum()
            
            # Ajouter les colonnes non-numériques
            aggregated['Libellé géographique'] = ville_nom
            aggregated['Département'] = departement_code
            aggregated['Code géographique'] = commune_data.iloc[0]['Code géographique']
            
            # Créer un Series pour traitement uniforme
            row = pd.Series(aggregated)
        else:
            row = commune_data.iloc[0]
        
        # Extraire les données
        pop_15_64 = row.get('Pop 15-64 ans en 2022 (princ)', 0)
        actifs = row.get('Actifs 15-64 ans en 2022 (princ)', 0)
        actifs_occupes = row.get('Actifs occupés 15-64 ans en 2022 (princ)', 0)
        chomeurs = row.get('Chômeurs 15-64 ans en 2022 (princ)', 0)
        inactifs = row.get('Inactifs 15-64 ans en 2022 (princ)', 0)
        etudiants = row.get('Élèves, étudiants et stagiaires non rémunérés 15-64 ans en 2022 (princ)', 0)
        retraites = row.get('Retraités ou préretraités 15-64 ans en 2022 (princ)', 0)
        autres_inactifs = row.get('Autres inactifs 15-64 ans en 2022 (princ)', 0)
        
        # Calculer les taux
        taux_activite = (actifs / pop_15_64 * 100) if pop_15_64 > 0 else 0
        taux_chomage = (chomeurs / actifs * 100) if actifs > 0 else 0
        taux_emploi = (actifs_occupes / pop_15_64 * 100) if pop_15_64 > 0 else 0
        part_inactifs = (inactifs / pop_15_64 * 100) if pop_15_64 > 0 else 0
        
        return {
            'commune': row.get('Libellé géographique', ville_nom),
            'code_commune': row.get('Code géographique', 'N/A'),
            'departement': departement_code,
            'annee': 2022,
            'population_15_64': int(pop_15_64) if pd.notna(pop_15_64) else 'N/A',
            'actifs': int(actifs) if pd.notna(actifs) else 'N/A',
            'actifs_occupes': int(actifs_occupes) if pd.notna(actifs_occupes) else 'N/A',
            'chomeurs': int(chomeurs) if pd.notna(chomeurs) else 'N/A',
            'inactifs': int(inactifs) if pd.notna(inactifs) else 'N/A',
            'etudiants': int(etudiants) if pd.notna(etudiants) else 'N/A',
            'retraites': int(retraites) if pd.notna(retraites) else 'N/A',
            'autres_inactifs': int(autres_inactifs) if pd.notna(autres_inactifs) else 'N/A',
            'taux_activite': round(taux_activite, 1) if taux_activite else 0,
            'taux_chomage': round(taux_chomage, 1) if taux_chomage else 0,
            'taux_emploi': round(taux_emploi, 1) if taux_emploi else 0,
            'part_inactifs': round(part_inactifs, 1) if part_inactifs else 0
        }
    except Exception as e:
        st.warning(f"Erreur lors de la récupération des données d'emploi pour {ville_nom}: {e}")
        return None


def get_housing_data(city: str, ville_nom: str, departement_code: str) -> Optional[Dict]:
    """
    Récupère les données de logement depuis le fichier Excel INSEE au niveau communal
    Agrège les données des arrondissements pour Paris, Marseille et Lyon
    """
    try:
        df_logements = load_communes_logement_data()
        if df_logements.empty:
            return None
        
        df_cities = load_cities_data()
        if df_cities.empty:
            return None
        
        # Trouver le code commune depuis les données de villes
        city_info = df_cities[df_cities['ville'] == city]
        if city_info.empty:
            return None
        
        # Pour Paris, Marseille, Lyon : chercher tous les arrondissements
        if ville_nom in ['Paris', 'Marseille', 'Lyon']:
            # Chercher toutes les communes dont le nom commence par la ville
            # Ex: "Paris 1er Arrondissement", "Paris", "Marseille 01", etc.
            commune_data = df_logements[
                df_logements['Libellé commune ou ARM'].str.contains(
                    f'^{ville_nom}', 
                    case=False, 
                    regex=True, 
                    na=False
                )
            ]
        else:
            # Pour les autres villes, chercher par nom exact
            commune_data = df_logements[
                df_logements['Libellé commune ou ARM'].str.lower() == ville_nom.lower()
            ]
            
            # Si pas trouvé par nom, essayer avec le code département
            if commune_data.empty:
                # Chercher toutes les communes du département et trouver la meilleure correspondance
                communes_dept = df_logements[df_logements['Département'] == departement_code]
                if not communes_dept.empty:
                    # Chercher la commune la plus proche par nom
                    for idx, row in communes_dept.iterrows():
                        if ville_nom.lower() in str(row['Libellé commune ou ARM']).lower():
                            commune_data = communes_dept[communes_dept.index == idx]
                            break
        
        if commune_data.empty:
            return None
        
        # Si plusieurs résultats (arrondissements), agréger
        if len(commune_data) > 1:
            # Sommer toutes les colonnes numériques
            numeric_cols = [
                'Logements en 2022 (princ)',
                'Résidences principales en 2022 (princ)',
                'Rés secondaires et logts occasionnels en 2022 (princ)',
                'Logements vacants en 2022 (princ)',
                'Maisons en 2022 (princ)',
                'Appartements en 2022 (princ)',
                'Pièces rés princ en 2022 (princ)',
                'Ménages en 2022 (princ)',
                'Rés princ occupées Propriétaires en 2022 (princ)',
                'Rés princ occupées Locataires en 2022 (princ)',
                'Rés princ HLM louée vide en 2022 (princ)'
            ]
            
            # Créer une ligne agrégée
            aggregated = {}
            for col in numeric_cols:
                if col in commune_data.columns:
                    aggregated[col] = commune_data[col].sum()
            
            # Ajouter les colonnes non-numériques
            aggregated['Libellé commune ou ARM'] = ville_nom
            aggregated['Département'] = departement_code
            aggregated['code_commune'] = commune_data.iloc[0]['code_commune']
            
            # Créer un Series pour traitement uniforme
            row = pd.Series(aggregated)
        else:
            row = commune_data.iloc[0]
        
        # Extraire les données
        nb_logements = row.get('Logements en 2022 (princ)', 0)
        nb_residences_principales = row.get('Résidences principales en 2022 (princ)', 0)
        nb_secondaires = row.get('Rés secondaires et logts occasionnels en 2022 (princ)', 0)
        nb_vacants = row.get('Logements vacants en 2022 (princ)', 0)
        nb_maisons = row.get('Maisons en 2022 (princ)', 0)
        nb_appartements = row.get('Appartements en 2022 (princ)', 0)
        nb_pieces_total = row.get('Pièces rés princ en 2022 (princ)', 0)
        nb_proprietaires = row.get('Rés princ occupées Propriétaires en 2022 (princ)', 0)
        nb_locataires = row.get('Rés princ occupées Locataires en 2022 (princ)', 0)
        nb_hlm = row.get('Rés princ HLM louée vide en 2022 (princ)', 0)
        nb_menages = row.get('Ménages en 2022 (princ)', 0)
        
        # Calculer les taux
        taux_vacants = (nb_vacants / nb_logements * 100) if nb_logements > 0 else 0
        taux_secondaires = (nb_secondaires / nb_logements * 100) if nb_logements > 0 else 0
        taux_maisons = (nb_maisons / nb_logements * 100) if nb_logements > 0 else 0
        taux_appartements = (nb_appartements / nb_logements * 100) if nb_logements > 0 else 0
        taux_proprietaires = (nb_proprietaires / nb_residences_principales * 100) if nb_residences_principales > 0 else 0
        taux_locataires = (nb_locataires / nb_residences_principales * 100) if nb_residences_principales > 0 else 0
        taux_hlm = (nb_hlm / nb_residences_principales * 100) if nb_residences_principales > 0 else 0
        pieces_moyennes = (nb_pieces_total / nb_residences_principales) if nb_residences_principales > 0 else 0
        
        return {
            'commune': row.get('Libellé commune ou ARM', ville_nom),
            'code_commune': row.get('code_commune', 'N/A'),
            'departement': departement_code,
            'annee': 2022,
            'nombre_logements': int(nb_logements) if pd.notna(nb_logements) else 'N/A',
            'nombre_residences_principales': int(nb_residences_principales) if pd.notna(nb_residences_principales) else 'N/A',
            'nombre_residences_secondaires': int(nb_secondaires) if pd.notna(nb_secondaires) else 'N/A',
            'nombre_logements_vacants': int(nb_vacants) if pd.notna(nb_vacants) else 'N/A',
            'nombre_maisons': int(nb_maisons) if pd.notna(nb_maisons) else 'N/A',
            'nombre_appartements': int(nb_appartements) if pd.notna(nb_appartements) else 'N/A',
            'nombre_menages': int(nb_menages) if pd.notna(nb_menages) else 'N/A',
            'taux_logements_vacants': round(taux_vacants, 1) if taux_vacants else 0,
            'taux_residence_secondaire': round(taux_secondaires, 1) if taux_secondaires else 0,
            'taux_maisons': round(taux_maisons, 1) if taux_maisons else 0,
            'taux_appartements': round(taux_appartements, 1) if taux_appartements else 0,
            'taux_proprietaires': round(taux_proprietaires, 1) if taux_proprietaires else 0,
            'taux_locataires': round(taux_locataires, 1) if taux_locataires else 0,
            'taux_hlm': round(taux_hlm, 1) if taux_hlm else 0,
            'pieces_moyennes': round(pieces_moyennes, 1) if pieces_moyennes else 0,
            'nb_proprietaires': int(nb_proprietaires) if pd.notna(nb_proprietaires) else 'N/A',
            'nb_locataires': int(nb_locataires) if pd.notna(nb_locataires) else 'N/A',
            'nb_hlm': int(nb_hlm) if pd.notna(nb_hlm) else 'N/A'
        }
    except Exception as e:
        st.warning(f"Erreur lors de la récupération des données de logement pour {ville_nom}: {e}")
        return None




def get_formation_data(city: str, ville_nom: str, departement_code: str) -> Optional[Dict]:
    """
    Récupère les données de formations/diplômes depuis le fichier CSV INSEE.
    Utilise les colonnes diplômes et PCS de la base Activité-Emploi-Chômage RP2022.
    Couvre la population active 15-64 ans par niveau de diplôme et catégorie socio-pro.
    """
    try:
        df_emploi = load_communes_emploi_data()
        if df_emploi.empty:
            return None

        df_cities = load_cities_data()
        if df_cities.empty:
            return None

        city_info = df_cities[df_cities['ville'] == city]
        if city_info.empty:
            return None

        # Recherche des données de la commune (même logique que get_employment_data)
        if ville_nom in ['Paris', 'Marseille', 'Lyon']:
            commune_data = df_emploi[
                (df_emploi['Département'] == departement_code) &
                (df_emploi['Libellé géographique'].str.contains(
                    f'^{ville_nom}', case=False, regex=True, na=False
                ))
            ]
        else:
            commune_data = df_emploi[
                df_emploi['Libellé géographique'].str.lower() == ville_nom.lower()
            ]
            if commune_data.empty:
                communes_dept = df_emploi[df_emploi['Département'] == departement_code]
                if not communes_dept.empty:
                    for idx, row in communes_dept.iterrows():
                        if ville_nom.lower() in str(row['Libellé géographique']).lower():
                            commune_data = communes_dept[communes_dept.index == idx]
                            break

        if commune_data.empty:
            return None

        # Agréger si plusieurs lignes (arrondissements)
        if len(commune_data) > 1:
            dipl_pcs_cols = [
                'Actifs Sans diplôme ou CEP en 2022 (princ)',
                'Actifs BEPC, brevet des collèges, DNB en 2022 (princ)',
                'Actifs CAP-BEP ou équiv. en 2022 (princ)',
                'Actifs Bac, brevet pro. ou équiv.  en 2022 (princ)',
                'Actifs Enseignement sup de niveau bac + 2  en 2022 (princ)',
                'Actifs Enseignement sup de niveau bac + 3 ou 4  en 2022 (princ)',
                'Actifs Enseignement sup de niveau bac + 5 ou plus  en 2022 (princ)',
                'Chômeurs Sans diplôme ou CEP en 2022 (princ)',
                'Chômeurs BEPC, brevet des collèges, DNB en 2022 (princ)',
                'Chômeurs CAP-BEP ou équiv. en 2022 (princ)',
                'Chômeurs Bac, brevet pro. ou équiv.  en 2022 (princ)',
                'Chômeurs Enseignement sup de niveau bac + 2  en 2022 (princ)',
                'Chômeurs Enseignement sup de niveau bac + 3 ou 4  en 2022 (princ)',
                'Chômeurs Enseignement sup de niveau bac + 5 ou plus  en 2022 (princ)',
                'Actifs 15-64 ans Agriculteurs exploitants en 2022 (compl)',
                'Actifs 15-64 ans Artisans, Comm., Chefs entr. en 2022 (compl)',
                'Actifs 15-64 ans Cadres, Prof. intel. sup. en 2022 (compl)',
                'Actifs 15-64 ans Prof. intermédiaires en 2022 (compl)',
                'Actifs 15-64 ans Employés en 2022 (compl)',
                'Actifs 15-64 ans Ouvriers en 2022 (compl)',
                'Actifs 15-64 ans en 2022 (princ)',
                'Chômeurs 15-64 ans en 2022 (princ)',
            ]
            aggregated = {}
            for col in dipl_pcs_cols:
                if col in commune_data.columns:
                    aggregated[col] = commune_data[col].sum()
            aggregated['Libellé géographique'] = ville_nom
            aggregated['Département'] = departement_code
            row = pd.Series(aggregated)
        else:
            row = commune_data.iloc[0]

        def _safe_int(val):
            return int(val) if pd.notna(val) and val != 0 else 0

        # Diplômes des actifs (7 niveaux)
        dipl_labels = [
            'Sans diplôme / CEP',
            'BEPC / Brevet',
            'CAP-BEP',
            'Bac / Brevet pro.',
            'Bac+2',
            'Bac+3/4',
            'Bac+5 et plus',
        ]
        actifs_dipl_cols = [
            'Actifs Sans diplôme ou CEP en 2022 (princ)',
            'Actifs BEPC, brevet des collèges, DNB en 2022 (princ)',
            'Actifs CAP-BEP ou équiv. en 2022 (princ)',
            'Actifs Bac, brevet pro. ou équiv.  en 2022 (princ)',
            'Actifs Enseignement sup de niveau bac + 2  en 2022 (princ)',
            'Actifs Enseignement sup de niveau bac + 3 ou 4  en 2022 (princ)',
            'Actifs Enseignement sup de niveau bac + 5 ou plus  en 2022 (princ)',
        ]
        chomeurs_dipl_cols = [
            'Chômeurs Sans diplôme ou CEP en 2022 (princ)',
            'Chômeurs BEPC, brevet des collèges, DNB en 2022 (princ)',
            'Chômeurs CAP-BEP ou équiv. en 2022 (princ)',
            'Chômeurs Bac, brevet pro. ou équiv.  en 2022 (princ)',
            'Chômeurs Enseignement sup de niveau bac + 2  en 2022 (princ)',
            'Chômeurs Enseignement sup de niveau bac + 3 ou 4  en 2022 (princ)',
            'Chômeurs Enseignement sup de niveau bac + 5 ou plus  en 2022 (princ)',
        ]

        actifs_by_dipl = [_safe_int(row.get(c, 0)) for c in actifs_dipl_cols]
        chomeurs_by_dipl = [_safe_int(row.get(c, 0)) for c in chomeurs_dipl_cols]

        # Taux de chômage par niveau de diplôme
        taux_chomage_by_dipl = []
        for a, ch in zip(actifs_by_dipl, chomeurs_by_dipl):
            taux_chomage_by_dipl.append(round(ch / a * 100, 1) if a > 0 else 0)

        # PCS
        pcs_labels = [
            'Agriculteurs',
            'Artisans / Comm.',
            'Cadres',
            'Prof. intermédiaires',
            'Employés',
            'Ouvriers',
        ]
        pcs_cols = [
            'Actifs 15-64 ans Agriculteurs exploitants en 2022 (compl)',
            'Actifs 15-64 ans Artisans, Comm., Chefs entr. en 2022 (compl)',
            'Actifs 15-64 ans Cadres, Prof. intel. sup. en 2022 (compl)',
            'Actifs 15-64 ans Prof. intermédiaires en 2022 (compl)',
            'Actifs 15-64 ans Employés en 2022 (compl)',
            'Actifs 15-64 ans Ouvriers en 2022 (compl)',
        ]
        pcs_values = [_safe_int(row.get(c, 0)) for c in pcs_cols]
        total_pcs = sum(pcs_values)
        pcs_pct = [round(v / total_pcs * 100, 1) if total_pcs > 0 else 0 for v in pcs_values]

        total_actifs = _safe_int(row.get('Actifs 15-64 ans en 2022 (princ)', 0))
        total_actifs_dipl = sum(actifs_by_dipl)

        return {
            'commune': row.get('Libellé géographique', ville_nom),
            'departement': departement_code,
            'annee': 2022,
            'total_actifs': total_actifs,
            'dipl_labels': dipl_labels,
            'actifs_by_dipl': actifs_by_dipl,
            'chomeurs_by_dipl': chomeurs_by_dipl,
            'taux_chomage_by_dipl': taux_chomage_by_dipl,
            'pcs_labels': pcs_labels,
            'pcs_values': pcs_values,
            'pcs_pct': pcs_pct,
            # Taux de diplômés du supérieur (bac+2 et plus) parmi les actifs
            'part_superieur': round(
                sum(actifs_by_dipl[4:]) / total_actifs_dipl * 100, 1
            ) if total_actifs_dipl > 0 else 0,
            # Part des actifs sans diplôme
            'part_sans_diplome': round(
                actifs_by_dipl[0] / total_actifs_dipl * 100, 1
            ) if total_actifs_dipl > 0 else 0,
        }
    except Exception as e:
        st.warning(f"Erreur lors de la récupération des données de formation pour {ville_nom}: {e}")
        return None


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
