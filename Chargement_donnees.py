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

#%%
