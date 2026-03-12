# MétaPolis — Tableau de bord de comparaison de villes françaises

## 1) Contexte du projet

Ce projet répond au sujet suivant : concevoir en équipe une interface web (ici en **Streamlit**, avec visualisations **Plotly**) permettant de **sélectionner et comparer 2 villes françaises** sur plusieurs thématiques, au travers d’un tableau de bord multi-pages/onglets.

L’application développée s’appelle **MétaPolis**.

---

## 2) Objectifs pédagogiques couverts

- Construire une application data interactive orientée utilisateur.
- Intégrer des données hétérogènes : API + fichiers locaux.
- Produire des indicateurs comparatifs clairs et actionnables.
- Structurer un projet Python/Streamlit maintenable (pages, utilitaires, cache, séparation des responsabilités).

---

## 3) Respect des consignes du sujet

### Contraintes imposées

1. **Villes françaises de plus de 20 000 habitants**  
	✅ Respecté via filtrage OpenDataSoft (`population>20000`) et pays FR/territoires français.

2. **Sources de données variées (fichiers + API)**  
	✅ Respecté (INSEE en local + OpenDataSoft + Open-Meteo + API IA).

3. **Données obligatoires : générales, emploi, logement, météo**  
	✅ Respecté sur les pages dédiées + page de comparaison.

4. **Météo : climat à l’année + prochains jours**  
	✅ Respecté :
	- moyenne de température depuis le début de l’année courante,
	- prévisions météo à 3 jours.

5. **Indicateur obligatoire : cartographie des villes > 20 000 habitants**  
	✅ Respecté avec carte interactive Plotly Mapbox.

6. **Données complémentaires**  
	✅ Implémenté : **Formation / Diplômes** (+ comparaison IA textuelle).

---

## 4) Fonctionnalités principales

### Accueil
- Vue synthétique nationale.
- Carte interactive de toutes les villes éligibles.
- Top des villes par population.

### Focus ville
- Informations générales : population, département, altitude, localisation.
- Positionnement départemental et national.

### Emploi
- Taux de chômage, d’activité, d’emploi, part d’inactifs.
- Volumes 15–64 ans : actifs, actifs occupés, chômeurs, inactifs.

### Logement
- Parc de logements, vacance, HLM, structure propriétaires/locataires.
- Répartition résidences principales/secondaires/vacantes.

### Météo
- Conditions actuelles (température, humidité, vent, pression, etc.).
- Prévisions à 3 jours.
- Indicateur de température moyenne annuelle (année courante).

### Comparaison (2 villes)
- Comparaison multi-onglets : vue d’ensemble, démographie, emploi, logement, formations, météo.
- Indicateurs côte à côte + graphiques comparatifs.

---

## 5) Sources de données

### APIs
- **OpenDataSoft (villes + population + géolocalisation)**  
  https://public.opendatasoft.com/api/records/1.0/search/?dataset=geonames-all-cities-with-a-population-1000&q=population>20000&rows=1000&refine.country_code=FR

- **Open-Meteo (météo actuelle, prévisions, historique)**  
  https://api.open-meteo.com/

- **API IA (Groq)** pour la comparaison textuelle.

### Fichiers locaux
- **INSEE emploi** : `data/emploi.csv`
- **INSEE logement** : `data/logement.csv`

### Référence open data utilisée
- https://opendata.caissedesdepots.fr/api/explore/v2.1/catalog/datasets/logements-et-logements-sociaux-dans-les-departements/exports/csv?use_labels=true


---

## 6) Structure du projet

- `app.py` : page d’accueil (synthèse + cartographie)
- `pages/1_Comparaison.py` : comparaison de 2 villes
- `pages/2_Emploi.py` : analyse emploi
- `pages/3_Logement.py` : analyse logement
- `pages/4_Meteo.py` : météo & prévisions
- `pages/5_Donnees_Generales.py` : focus ville
- `utils/data_loader.py` : chargement/normalisation/calcul des données
- `utils/navbar.py` : barre de navigation
- `data/` : fichiers CSV locaux

---

## 7) Exécution du projet

### Option A — Exécution locale 

**Lancer le projet via `lanceur.bat`**.

Avant l’exécution, **ajouter manuellement les clés API nécessaires** (notamment la clé IA) dans la configuration prévue par votre groupe (`lanceur.bat`, variables d’environnement, ou fichier de config local selon votre version).

### Option B — Version déployée (recommandée)

Le projet est aussi accessible via :  
**metapolis.streamlit.app**

---

## 8) Remarques d’exploitation

- Le projet est conçu pour des villes françaises > 20 000 habitants.
- Certaines données dépendent de la disponibilité des APIs externes au moment de l’exécution.
- Les données météo sont mises en cache pour améliorer les performances.

---

## 9) Auteurs

Projet réalisé en groupe par B.Paul A.Constant B.Rafael et B.Nathael dans le cadre du challenge de réalisation d’un tableau de bord data interactif.

