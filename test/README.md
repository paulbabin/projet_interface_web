# 🏙️ CompaVille - Comparateur de Villes Françaises

Application web interactive pour explorer et comparer les villes françaises de plus de 20 000 habitants.

## 📋 Description

**CompaVille** est une application Streamlit permettant de visualiser, explorer et comparer les villes françaises sur différents critères :
- 📊 Données démographiques
- 💼 Emploi et chômage
- 🏠 Logement et immobilier
- 🌤️ Météo et climat
- 🗺️ Cartographie interactive

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip

### Installation des dépendances

```powershell
pip install -r requirements.txt
```

Ou installez les packages individuellement :

```powershell
pip install streamlit pandas requests plotly numpy
```

## ▶️ Lancement de l'application

Pour lancer l'application Streamlit :

```powershell
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 📁 Structure du Projet

```
projet_interface_web/
│
├── app.py                      # Page principale avec carte interactive
├── requirements.txt            # Dépendances Python
├── README.md                   # Ce fichier
│
├── pages/                      # Pages Streamlit multi-pages
│   ├── 1_Comparaison.py       # Comparaison de 2 villes
│   ├── 2_Emploi.py            # Analyse de l'emploi
│   ├── 3_Logement.py          # Marché immobilier
│   ├── 4_Meteo.py             # Météo et climat
│   └── 5_Donnees_Generales.py # Informations détaillées
│
└── utils/                      # Utilitaires
    └── data_loader.py         # Fonctions de chargement des données
```

## 🎯 Fonctionnalités

### Page Principale (Accueil)
- 🗺️ Carte interactive des villes françaises (Plotly)
- 📊 Statistiques générales
- 🔍 Filtres par population
- 📋 Liste complète des villes

### Page Comparaison
- 🔄 Comparaison côte à côte de 2 villes
- 📊 Graphiques comparatifs
- 💼 Emploi
- 🏠 Logement
- 🌤️ Météo

### Pages Thématiques
- **💼 Emploi** : Taux de chômage, secteurs d'activité
- **🏠 Logement** : Prix immobilier, types de logement
- **🌤️ Météo** : Conditions actuelles et prévisions
- **📊 Données Générales** : Démographie, localisation, statistiques

## 📊 Sources de Données

- **OpenDataSoft** : Données géographiques des villes
- **Wikipedia API** : Descriptions des villes
- **wttr.in** : Données météorologiques en temps réel
- **Données simulées** : Emploi et logement (pour démonstration)

> ⚠️ **Note** : Les données d'emploi et de logement sont actuellement simulées pour démonstration. En production, il faudrait intégrer les APIs officielles de l'INSEE et de Pôle Emploi.

## 🛠️ Technologies Utilisées

- **Streamlit** : Framework d'application web
- **Plotly** : Visualisations interactives
- **Pandas** : Manipulation de données
- **Requests** : Appels API

## 📝 Projet Universitaire

Ce projet a été réalisé dans le cadre du cours de **Programmation Web (VCOD)** à l'Université de Poitiers.

### Objectifs du Projet
- ✅ Interface web multi-pages avec Streamlit
- ✅ Comparaison de 2 villes françaises
- ✅ Villes de plus de 20 000 habitants
- ✅ Données obligatoires : Général, Emploi, Logement, Météo
- ✅ Cartographie interactive
- ✅ Multiples sources de données (API, Open Data)

## 🔮 Améliorations Futures

- 🔐 Intégration de l'API INSEE avec authentification
- 🏢 API Pôle Emploi pour données d'emploi réelles
- 🏠 API DVF (Demandes de Valeurs Foncières) pour prix immobiliers réels
- 🎭 Ajout de données culturelles et touristiques
- 📱 Responsive design optimisé mobile
- 💾 Base de données locale pour cache persistant
- 📈 Graphiques supplémentaires et analyses avancées

## 👥 Auteur

Projet réalisé par Nicolas BENOIT
Semestre 4 - Programmation Web (VCOD)
Université de Poitiers

## 📄 Licence

Ce projet est à usage éducatif uniquement.

---

**💡 Astuce** : Pour une meilleure expérience, utilisez un écran large et un navigateur récent (Chrome, Firefox, Edge).
