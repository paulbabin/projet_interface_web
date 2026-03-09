#%%
import requests
import pandas as pd
import streamlit as st

url_base = "https://public.opendatasoft.com/api/records/1.0/search/?dataset=geonames-all-cities-with-a-population-1000&q=population>20000&rows=1000&refine.country_code=FR"

# Récupérer les données de l'API
response = requests.get(url_base)
data = response.json()

# Extraire les enregistrements et créer le DataFrame
records = data.get('records', [])
df = pd.json_normalize(records)

print(f"Nombre de villes: {len(df)}")
print(df.head())

# Streamlit - Affichage de la carte
st.title("🗺️ Carte des villes françaises > 20 000 habitants")

# Préparer les données pour la carte
if 'fields.coordinates' in df.columns:
    # Extraire latitude et longitude
    df['latitude'] = df['fields.coordinates'].apply(lambda x: x[0] if isinstance(x, list) and len(x) >= 2 else None)
    df['longitude'] = df['fields.coordinates'].apply(lambda x: x[1] if isinstance(x, list) and len(x) >= 2 else None)
elif 'fields.latitude' in df.columns and 'fields.longitude' in df.columns:
    df['latitude'] = df['fields.latitude']
    df['longitude'] = df['fields.longitude']

# Supprimer les lignes sans coordonnées
map_data = df[['latitude', 'longitude']].dropna()

st.write(f"**{len(map_data)} villes affichées sur la carte**")
st.map(map_data)

#%%

