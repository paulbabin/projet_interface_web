"""
🔄 Page de Comparaison de Villes
Permet de comparer 2 villes françaises côte à côte sur différents critères
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path
from groq import Groq
from gtts import gTTS


sys.path.append(str(Path(__file__).parent.parent))
from utils.data_loader import (
    load_cities_data, 
    get_city_list, 
    get_city_info,
    get_employment_data,
    get_housing_data,
    get_weather_current,
    get_weather_forecast,
    get_formation_data,
    get_annual_temperature_average,
    format_int_fr
)

st.set_page_config(page_title="Comparaison de Villes", page_icon="🔄", layout="wide", initial_sidebar_state="collapsed")

from utils.navbar import inject_navbar_css, render_navbar
from utils.style import COLOR_LOW, COLOR_MEDIUM, COLOR_HIGH, COLOR_SEQUENCE, SOFT, PALETTE
inject_navbar_css()
render_navbar("Comparaison")

st.markdown("""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-size:2.2rem; font-weight:700; color:#1e293b; margin:0; letter-spacing:-1px;">
        Comparaison de villes
    </h1>
    <p style="color:#64748b; font-size:1.05rem; margin-top:0.5rem;">
        Comparez deux villes françaises sur la démographie, l'emploi, le logement et la météo
    </p>
</div>
""", unsafe_allow_html=True)

# Charger les villes disponibles pour alimenter tous les onglets.
df_cities = load_cities_data()
if df_cities.empty:
    st.error("❌ Impossible de charger les données")
    st.stop()

city_list = get_city_list(df_cities)

if not city_list:
    st.error("❌ Aucune ville disponible")
    st.stop()

default_city_index = city_list.index("Niort (79)") if "Niort (79)" in city_list else 0
default_city2_index = city_list.index("Poitiers (86)") if "Poitiers (86)" in city_list else 0
# Sélection des deux villes à comparer.
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏙️ Ville 1")
    city1 = st.selectbox(
        "Choisissez la première ville",
        options=city_list,
        index=default_city_index,
        key="city1"
    )

with col2:
    st.subheader("🏙️ Ville 2")
    city2 = st.selectbox(
        "Choisissez la deuxième ville",
        options=city_list,
        index=default_city2_index,
        key="city2"
    )

if city1 == city2:
    st.warning("⚠️ Veuillez sélectionner deux villes différentes")
    st.stop()

# Charger les métadonnées communes utilisées dans les comparaisons.
info1 = get_city_info(df_cities, city1)
info2 = get_city_info(df_cities, city2)

if info1 is None or info2 is None:
    st.error("❌ Impossible de récupérer les informations des villes")
    st.stop()


# Précharger le contexte logement pour afficher la commune et l'année en tête d'onglet.
log1 = None
log2 = None
if 'departement_code' in info1 and 'departement_code' in info2 and 'ville_nom' in info1 and 'ville_nom' in info2:
    log1 = get_housing_data(city1, info1['ville_nom'], info1['departement_code'])
    log2 = get_housing_data(city2, info2['ville_nom'], info2['departement_code'])


def _render_tab_context(log_data_1, log_data_2):
    if log_data_1 and log_data_2:
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"📍 {log_data_1.get('commune', 'N/A')} ({log_data_1.get('annee', 'N/A')})")
        with col2:
            st.caption(f"📍 {log_data_2.get('commune', 'N/A')} ({log_data_2.get('annee', 'N/A')})")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"📍 {city1}")
        with col2:
            st.caption(f"📍 {city2}")

st.divider()

# Répartir la comparaison par thème métier.
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔍 Comparaison intelligente",
    "📊 Vue d'ensemble",
    "👥 Démographie",
    "💼 Emploi",
    "🎓 Formations",
    "🏠 Logement",
    "🌤️ Météo"
])


with tab1:
    st.header("🔍 Comparaison intelligente")

    # Générer un verdict court via Groq, puis le lire en audio.
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)

    if st.button("Lancer la comparaison", disabled=client is None):
        with st.spinner("L'IA prépare sa meilleure punchline pour M.Garnier..."):
            prompt = f"""
            Ton rôle est de convaincre François Garnier, le professeur qui nous évalue, de choisir entre {city1} et {city2}. 
            Adresse-toi directement à lui par son prénom (ex: "François, écoute-moi bien...", "Franchement François...").
            Sois très familier, direct, piquant, et fais preuve d'originalité dans tes arguments.
            RÈGLE ABSOLUE : Si l'une des deux villes est Niort, tu dois jurer à Garnier que Niort est la meilleure ville et le forcer à la choisir. Rappelle lui que c'est la ou il est né et que la ville a besoin de lui. Si aucune des villes est Niort, n'en parle pas.
            CONTRAINTE DE FORMAT : Fais très court, DEUX phrases maximums. Pas de bonjour, pas d'introduction.
            """
            
            reponse = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            texte_ia = reponse.choices[0].message.content

            st.success("Verdict pour M. Garnier :")
            st.write(f"**{texte_ia}**")
                    
            try:
                tts = gTTS(text=texte_ia, lang='fr', tld='fr')
                
                fichier_audio = "clash_ia.mp3"
                tts.save(fichier_audio)
                
                with open(fichier_audio, "rb") as f:
                    st.audio(f.read(), format='audio/mpeg', autoplay=True)
                    
            except Exception as e:
                st.error(f"Oups, le lecteur audio a planté : {e}")

with tab2:
    st.header("📊 Vue d'Ensemble")
    _render_tab_context(log1, log2)

    col1, col2 = st.columns(2)
    
    with col1:        
        if 'population' in info1:
            st.metric("Population", format_int_fr(info1['population']))
        
        if 'altitude' in info1 and info1['altitude']:
            st.metric("Altitude", f"{int(info1['altitude'])} m")
        
        if 'departement_code' in info1:
            st.metric("Département", info1['departement_code'])
    
    with col2:        
        if 'population' in info2:
            st.metric("Population", format_int_fr(info2['population']))
        
        if 'altitude' in info2 and info2['altitude']:
            st.metric("Altitude", f"{int(info2['altitude'])} m")
        
        if 'departement_code' in info2:
            st.metric("Département", info2['departement_code'])
    
    st.divider()
    
    # Carte de localisation
    st.subheader("🗺️ Localisation")
    
    if 'lat' in info1 and 'lon' in info1 and 'lat' in info2 and 'lon' in info2:
        import pandas as pd
        map_data = pd.DataFrame({
            'ville': [city1, city2],
            'lat': [info1['lat'], info2['lat']],
            'lon': [info1['lon'], info2['lon']],
            'population': [info1.get('population', 0), info2.get('population', 0)]
        })
        map_data['population_fr'] = map_data['population'].apply(format_int_fr)
        
        fig_map = px.scatter_mapbox(
            map_data,
            lat='lat',
            lon='lon',
            hover_name='ville',
            hover_data={'population': False, 'population_fr': True, 'lat': False, 'lon': False},
            size='population',
            color='ville',
            zoom=5,
            height=500
        )
        fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

# ====== TAB 3: DÉMOGRAPHIE ======
with tab3:
    st.header("👥 Comparaison Démographique")
    _render_tab_context(log1, log2)
    
    if 'population' in info1 and 'population' in info2:
        pop1 = int(info1['population'])
        pop2 = int(info2['population'])
        
        # Statistiques
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"Population {city1}", format_int_fr(pop1))
        
        with col2:
            st.metric(f"Population {city2}", format_int_fr(pop2))
        
        with col3:
            diff = pop1 - pop2
            st.metric("Différence", format_int_fr(abs(diff)))

        st.divider()

        # Graphique de comparaison
        fig_demo = go.Figure()
        
        fig_demo.add_trace(go.Bar(
            name=city1,
            x=['Population'],
            y=[pop1],
            text=[format_int_fr(pop1)],
            textposition='auto',
            marker_color=COLOR_LOW if pop1 <= pop2 else COLOR_HIGH
        ))
        
        fig_demo.add_trace(go.Bar(
            name=city2,
            x=['Population'],
            y=[pop2],
            text=[format_int_fr(pop2)],
            textposition='auto',
            marker_color=COLOR_LOW if pop2 <= pop1 else COLOR_HIGH
        ))
        
        fig_demo.update_layout(
            title="Comparaison de la Population",
            yaxis_title="Habitants",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig_demo, use_container_width=True)
        
        st.divider()       

        # Normaliser les codes département pour éviter les écarts de format (ex: 01 vs 1)
        def _normalize_dept_code(value):
            if pd.isna(value):
                return ''
            txt = str(value).strip().upper()
            if txt.isdigit():
                return str(int(txt))
            return txt

        dept1 = _normalize_dept_code(info1.get('departement_code', ''))
        dept2 = _normalize_dept_code(info2.get('departement_code', ''))
        dept_series = df_cities['departement_code'].apply(_normalize_dept_code)

        total_pop = df_cities['population'].sum()
        rank_nat_1 = int((df_cities['population'] > pop1).sum() + 1)
        rank_nat_2 = int((df_cities['population'] > pop2).sum() + 1)

        dept_df1 = df_cities[dept_series == dept1]
        dept_df2 = df_cities[dept_series == dept2]

        nb_villes_dept_1 = len(dept_df1)
        nb_villes_dept_2 = len(dept_df2)
        rang_dept_1 = int((dept_df1['population'] > pop1).sum() + 1) if not dept_df1.empty else 0
        rang_dept_2 = int((dept_df2['population'] > pop2).sum() + 1) if not dept_df2.empty else 0

        part_pop_1 = (pop1 / total_pop * 100) if total_pop > 0 else 0
        part_pop_2 = (pop2 / total_pop * 100) if total_pop > 0 else 0

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"**{city1}**")
            st.metric("Villes dans le département", format_int_fr(nb_villes_dept_1))
            st.metric("Rang dans le département", f"#{rang_dept_1}" if rang_dept_1 > 0 else "N/A")
            st.metric("Rang national", f"#{rank_nat_1}")
            st.metric("Part de population", f"{part_pop_1:.2f}%")

        with c2:
            st.markdown(f"**{city2}**")
            st.metric("Villes dans le département", format_int_fr(nb_villes_dept_2))
            st.metric("Rang dans le département", f"#{rang_dept_2}" if rang_dept_2 > 0 else "N/A")
            st.metric("Rang national", f"#{rank_nat_2}")
            st.metric("Part de population", f"{part_pop_2:.2f}%")

# ====== TAB 4: EMPLOI ======
with tab4:
    st.header("💼 Comparaison de l'Emploi")
    _render_tab_context(log1, log2)

    if 'departement_code' in info1 and 'departement_code' in info2 and 'ville_nom' in info1 and 'ville_nom' in info2:
        # Récupération des données d'emploi réelles
        emp1 = get_employment_data(city1, info1['ville_nom'], info1['departement_code'])
        emp2 = get_employment_data(city2, info2['ville_nom'], info2['departement_code'])
        
        if emp1 and emp2:            
            # Métriques côte à côte
            col1, col2 = st.columns(2)
            
            with col1:
                taux_chomage1 = emp1.get('taux_chomage', 'N/A')
                st.metric("Taux de chômage", f"{taux_chomage1}%" if taux_chomage1 != 'N/A' else 'N/A')
                taux_activite1 = emp1.get('taux_activite', 'N/A')
                st.metric("Taux d'activité", f"{taux_activite1}%" if taux_activite1 != 'N/A' else 'N/A')
                taux_emploi1 = emp1.get('taux_emploi', 'N/A')
                st.metric("Taux d'emploi", f"{taux_emploi1}%" if taux_emploi1 != 'N/A' else 'N/A')
                pop1 = emp1.get('population_15_64', 'N/A')
                st.metric("Population 15-64 ans", format_int_fr(pop1) if pop1 != 'N/A' else 'N/A')
            
            with col2:
                taux_chomage2 = emp2.get('taux_chomage', 'N/A')
                st.metric("Taux de chômage", f"{taux_chomage2}%" if taux_chomage2 != 'N/A' else 'N/A')
                taux_activite2 = emp2.get('taux_activite', 'N/A')
                st.metric("Taux d'activité", f"{taux_activite2}%" if taux_activite2 != 'N/A' else 'N/A')
                taux_emploi2 = emp2.get('taux_emploi', 'N/A')
                st.metric("Taux d'emploi", f"{taux_emploi2}%" if taux_emploi2 != 'N/A' else 'N/A')
                pop2 = emp2.get('population_15_64', 'N/A')
                st.metric("Population 15-64 ans", format_int_fr(pop2) if pop2 != 'N/A' else 'N/A')
            
            st.divider()

            # 1) Comparaison groupée des principaux taux
            if all(v != 'N/A' for v in [taux_chomage1, taux_chomage2, taux_activite1, taux_activite2, taux_emploi1, taux_emploi2]):
                rates_df = pd.DataFrame({
                    'Indicateur': ["Taux de chômage", "Taux d'activité", "Taux d'emploi"] * 2,
                    'Ville': [city1, city1, city1, city2, city2, city2],
                    'Valeur': [
                        taux_chomage1, taux_activite1, taux_emploi1,
                        taux_chomage2, taux_activite2, taux_emploi2
                    ]
                })

                fig_rates = px.bar(
                    rates_df,
                    x='Indicateur',
                    y='Valeur',
                    color='Ville',
                    barmode='group',
                    text='Valeur',
                    title="Comparaison des taux clés de l'emploi",
                    color_discrete_sequence=[COLOR_MEDIUM, COLOR_HIGH]
                )
                fig_rates.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig_rates.update_layout(yaxis_title="Pourcentage (%)")
                st.plotly_chart(fig_rates, use_container_width=True)

            st.divider()
            
            # 2) Structure de la population 15-64 ans (en %)
            pop_emp1 = emp1.get('population_15_64', 'N/A')
            pop_emp2 = emp2.get('population_15_64', 'N/A')
            actifs_occupes1 = emp1.get('actifs_occupes', 'N/A')
            actifs_occupes2 = emp2.get('actifs_occupes', 'N/A')
            chomeurs1 = emp1.get('chomeurs', 'N/A')
            chomeurs2 = emp2.get('chomeurs', 'N/A')
            inactifs1 = emp1.get('inactifs', 'N/A')
            inactifs2 = emp2.get('inactifs', 'N/A')

            if all(v != 'N/A' for v in [pop_emp1, pop_emp2, actifs_occupes1, actifs_occupes2, chomeurs1, chomeurs2, inactifs1, inactifs2]) and pop_emp1 > 0 and pop_emp2 > 0:
                structure_df = pd.DataFrame({
                    'Ville': [city1, city1, city1, city2, city2, city2],
                    'Catégorie': ['Actifs occupés', 'Chômeurs', 'Inactifs'] * 2,
                    'Pourcentage': [
                        actifs_occupes1 / pop_emp1 * 100,
                        chomeurs1 / pop_emp1 * 100,
                        inactifs1 / pop_emp1 * 100,
                        actifs_occupes2 / pop_emp2 * 100,
                        chomeurs2 / pop_emp2 * 100,
                        inactifs2 / pop_emp2 * 100,
                    ]
                })

                fig_structure = px.bar(
                    structure_df,
                    x='Ville',
                    y='Pourcentage',
                    color='Catégorie',
                    barmode='stack',
                    title="Structure de la population 15-64 ans (%)",
                    color_discrete_sequence=COLOR_SEQUENCE
                )
                fig_structure.update_layout(yaxis_title="Pourcentage (%)")
                st.plotly_chart(fig_structure, use_container_width=True)

            st.divider()
            
            # Comparaison des effectifs absolus
            if all(v != 'N/A' for v in [actifs_occupes1, actifs_occupes2, chomeurs1, chomeurs2, inactifs1, inactifs2]):
                volumes_df = pd.DataFrame({
                    'Statut': ["Actifs occupés", "Chômeurs", "Inactifs"] * 2,
                    'Ville': [city1, city1, city1, city2, city2, city2],
                    'Effectif': [
                        actifs_occupes1, chomeurs1, inactifs1,
                        actifs_occupes2, chomeurs2, inactifs2
                    ]
                })
                volumes_df['Effectif_fr'] = volumes_df['Effectif'].apply(format_int_fr)

                fig_volumes = px.bar(
                    volumes_df,
                    x='Statut',
                    y='Effectif',
                    color='Ville',
                    barmode='group',
                    text='Effectif_fr',
                    title="Comparaison des effectifs (15-64 ans)",
                    color_discrete_sequence=[COLOR_MEDIUM, COLOR_HIGH]
                )
                fig_volumes.update_traces(texttemplate='%{text}', textposition='outside')
                fig_volumes.update_layout(yaxis_title="Nombre de personnes")

                
                st.plotly_chart(fig_volumes, use_container_width=True)

            st.divider()
            # ── PCS : structure socio-professionnelle ──
            form1 = get_formation_data(city1, info1['ville_nom'], info1['departement_code'])
            form2 = get_formation_data(city2, info2['ville_nom'], info2['departement_code'])

            if form1 and form2 and sum(form1.get('pcs_values', [])) > 0 and sum(form2.get('pcs_values', [])) > 0:
                pcs_left, pcs_right = st.columns(2)

                with pcs_left:
                    fig_pcs1 = px.pie(
                        names=form1['pcs_labels'],
                        values=form1['pcs_values'],
                        title=f"CSP — {city1}",
                        color_discrete_sequence=PALETTE,
                        hole=0.35,
                        height=380
                    )
                    fig_pcs1.update_traces(textposition='outside', textinfo='label+percent')
                    st.plotly_chart(fig_pcs1, use_container_width=True)

                with pcs_right:
                    fig_pcs2 = px.pie(
                        names=form2['pcs_labels'],
                        values=form2['pcs_values'],
                        title=f"CSP — {city2}",
                        color_discrete_sequence=PALETTE,
                        hole=0.35,
                        height=380
                    )
                    fig_pcs2.update_traces(textposition='outside', textinfo='label+percent')
                    st.plotly_chart(fig_pcs2, use_container_width=True)
            else:
                st.info("ℹ️ Données CSP non disponibles pour ce comparatif")
                
        else:
            st.warning("⚠️ Données d'emploi non disponibles pour l'une ou les deux villes")
    else:
        st.warning("⚠️ Informations manquantes pour l'une ou les deux villes")

# ====== TAB 5: LOGEMENT ======
with tab6:
    st.header("🏠 Comparaison du Logement")
    _render_tab_context(log1, log2)
    
    if 'departement_code' in info1 and 'departement_code' in info2 and 'ville_nom' in info1 and 'ville_nom' in info2:
        # Récupération des données de logement réelles
        log1 = get_housing_data(city1, info1['ville_nom'], info1['departement_code'])
        log2 = get_housing_data(city2, info2['ville_nom'], info2['departement_code'])
        
        if log1 and log2:            
            # Métriques principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pieces1 = log1.get('pieces_moyennes', 'N/A')
                st.metric(f"Pièces moyennes {city1}", f"{pieces1}" if pieces1 != 'N/A' else 'N/A')
            
            with col2:
                pieces2 = log2.get('pieces_moyennes', 'N/A')
                st.metric(f"Pièces moyennes {city2}", f"{pieces2}" if pieces2 != 'N/A' else 'N/A')
            
            with col3:
                if pieces1 != 'N/A' and pieces2 != 'N/A':
                    diff = pieces1 - pieces2
                    st.metric("Différence", f"{diff:+.1f} pièces")
                else:
                    st.metric("Différence", "N/A")
            
            st.divider()
            
            # Détails par ville
            col1, col2 = st.columns(2)
            with col1:
                nb_log1 = log1.get('nombre_logements', 'N/A')
                st.metric("Nombre de logements", format_int_fr(nb_log1) if nb_log1 != 'N/A' else 'N/A')
                
                taux_princ1 = 100 - log1.get('taux_residence_secondaire', 0) - log1.get('taux_logements_vacants', 0)
                st.metric("Résidences principales", f"{taux_princ1:.1f}%")
                st.metric("Résidences secondaires", f"{log1.get('taux_residence_secondaire', 0)}%")
                st.metric("Logements vacants", f"{log1.get('taux_logements_vacants', 0)}%")
            
            with col2:
                nb_log2 = log2.get('nombre_logements', 'N/A')
                st.metric("Nombre de logements", format_int_fr(nb_log2) if nb_log2 != 'N/A' else 'N/A')
                
                taux_princ2 = 100 - log2.get('taux_residence_secondaire', 0) - log2.get('taux_logements_vacants', 0)
                st.metric("Résidences principales", f"{taux_princ2:.1f}%")
                st.metric("Résidences secondaires", f"{log2.get('taux_residence_secondaire', 0)}%")
                st.metric("Logements vacants", f"{log2.get('taux_logements_vacants', 0)}%")
            
            st.divider()
            
            # Graphiques
            col_left, col_right = st.columns(2)
            
            with col_left:
                # Comparaison taux de vacance
                fig_vacance = go.Figure()
                fig_vacance.add_trace(go.Bar(
                    x=[city1, city2],
                    y=[log1.get('taux_logements_vacants', 0), log2.get('taux_logements_vacants', 0)],
                    text=[f"{log1.get('taux_logements_vacants', 0)}%", f"{log2.get('taux_logements_vacants', 0)}%"],
                    textposition='auto',
                    marker_color=[COLOR_MEDIUM, COLOR_HIGH]
                ))
                fig_vacance.update_layout(
                    title="Taux de logements vacants (%)",
                    yaxis_title="Pourcentage (%)",
                    showlegend=False,
                    height=350
                )
                st.plotly_chart(fig_vacance, use_container_width=True)
            
            with col_right:
                # Type de logement
                housing_type = pd.DataFrame({
                    'Ville': [city1, city1, city2, city2],
                    'Type': ['Maisons', 'Appartements', 'Maisons', 'Appartements'],
                    'Pourcentage': [
                        log1.get('taux_maisons', 0),
                        log1.get('taux_appartements', 0),
                        log2.get('taux_maisons', 0),
                        log2.get('taux_appartements', 0)
                    ]
                })
                
                fig_type = px.bar(
                    housing_type,
                    x='Ville',
                    y='Pourcentage',
                    color='Type',
                    title="Répartition Maisons/Appartements (%)",
                    barmode='group',
                    color_discrete_sequence=[COLOR_LOW, COLOR_HIGH],
                    height=350
                )
                st.plotly_chart(fig_type, use_container_width=True)

            st.divider()

            adv_left, adv_right = st.columns(2)

            with adv_left:
                # Statut d'occupation (propriétaires / locataires / autres)
                taux_prop1 = log1.get('taux_proprietaires', 0)
                taux_prop2 = log2.get('taux_proprietaires', 0)
                taux_loc1 = log1.get('taux_locataires', 0)
                taux_loc2 = log2.get('taux_locataires', 0)

                occ_df = pd.DataFrame({
                    'Ville': [city1, city1, city1, city2, city2, city2],
                    'Statut': ['Propriétaires', 'Locataires', 'Autres'] * 2,
                    'Pourcentage': [
                        taux_prop1,
                        taux_loc1,
                        max(0, 100 - taux_prop1 - taux_loc1),
                        taux_prop2,
                        taux_loc2,
                        max(0, 100 - taux_prop2 - taux_loc2)
                    ]
                })

                fig_occ = px.bar(
                    occ_df,
                    x='Ville',
                    y='Pourcentage',
                    color='Statut',
                    barmode='stack',
                    title="Statut d'occupation des résidences principales (%)",
                    color_discrete_sequence=COLOR_SEQUENCE,
                    height=360
                )
                fig_occ.update_layout(yaxis_title="Pourcentage (%)")
                st.plotly_chart(fig_occ, use_container_width=True)

            with adv_right:
                # Radar des taux clés logement
                radar_categories = [
                    "Vacance",
                    "Rés. secondaires",
                    "Maisons",
                    "Appartements",
                    "HLM"
                ]

                fig_radar_log = go.Figure()
                fig_radar_log.add_trace(go.Scatterpolar(
                    r=[
                        log1.get('taux_logements_vacants', 0),
                        log1.get('taux_residence_secondaire', 0),
                        log1.get('taux_maisons', 0),
                        log1.get('taux_appartements', 0),
                        log1.get('taux_hlm', 0)
                    ],
                    theta=radar_categories,
                    fill='toself',
                    name=city1,
                    line=dict(color=COLOR_LOW)
                ))
                fig_radar_log.add_trace(go.Scatterpolar(
                    r=[
                        log2.get('taux_logements_vacants', 0),
                        log2.get('taux_residence_secondaire', 0),
                        log2.get('taux_maisons', 0),
                        log2.get('taux_appartements', 0),
                        log2.get('taux_hlm', 0)
                    ],
                    theta=radar_categories,
                    fill='toself',
                    name=city2,
                    line=dict(color=COLOR_HIGH)
                ))
                fig_radar_log.update_layout(
                    title="Profil logement (radar des taux)",
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    height=360
                )
                st.plotly_chart(fig_radar_log, use_container_width=True)

            # Intensité logements par ménage
            menages1 = log1.get('nombre_menages', 'N/A')
            menages2 = log2.get('nombre_menages', 'N/A')
            nb_log1 = log1.get('nombre_logements', 'N/A')
            nb_log2 = log2.get('nombre_logements', 'N/A')

            if all(v != 'N/A' for v in [menages1, menages2, nb_log1, nb_log2]) and menages1 > 0 and menages2 > 0:
                intensity_df = pd.DataFrame({
                    'Ville': [city1, city2],
                    'Logements par ménage': [nb_log1 / menages1, nb_log2 / menages2]
                })

                fig_intensity = px.bar(
                    intensity_df,
                    x='Ville',
                    y='Logements par ménage',
                    text='Logements par ménage',
                    title="Intensité du parc : logements par ménage",
                    color='Ville',
                    color_discrete_sequence=[COLOR_MEDIUM, COLOR_HIGH],
                    height=340
                )
                fig_intensity.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig_intensity.update_layout(showlegend=False, yaxis_title="Ratio")
                st.plotly_chart(fig_intensity, use_container_width=True)
        else:
            st.warning("⚠️ Données de logement non disponibles pour l'une ou les deux communes")
    else:
        st.warning("⚠️ Informations manquantes pour l'une ou les deux villes")

# ====== TAB 6: FORMATIONS ======
with tab5:
    st.header("🎓 Comparaison des Formations & Diplômes")
    _render_tab_context(log1, log2)

    if 'departement_code' in info1 and 'departement_code' in info2 and 'ville_nom' in info1 and 'ville_nom' in info2:
        form1 = get_formation_data(city1, info1['ville_nom'], info1['departement_code'])
        form2 = get_formation_data(city2, info2['ville_nom'], info2['departement_code'])

        if form1 and form2:
        # ── Métriques résumées ──
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric(f"🎓 Bac+2 et + ({city1})", f"{form1['part_superieur']}%")
            with c2:
                st.metric(f"🎓 Bac+2 et + ({city2})", f"{form2['part_superieur']}%")
            with c3:
                st.metric(f"Sans diplôme ({city1})", f"{form1['part_sans_diplome']}%")
            with c4:
                st.metric(f"Sans diplôme ({city2})", f"{form2['part_sans_diplome']}%")

            st.divider()

            # ── Répartition des diplômes (barres groupées) ──
            dipl_total1 = sum(form1['actifs_by_dipl']) or 1
            dipl_total2 = sum(form2['actifs_by_dipl']) or 1
            dipl_pct1 = [round(v / dipl_total1 * 100, 1) for v in form1['actifs_by_dipl']]
            dipl_pct2 = [round(v / dipl_total2 * 100, 1) for v in form2['actifs_by_dipl']]

            dipl_df = pd.DataFrame({
                'Niveau': form1['dipl_labels'] * 2,
                'Ville': [city1] * 7 + [city2] * 7,
                'Pourcentage': dipl_pct1 + dipl_pct2,
            })

            fig_dipl = px.bar(
                dipl_df,
                x='Niveau',
                y='Pourcentage',
                color='Ville',
                barmode='group',
                text='Pourcentage',
                title="Distribution des diplômes parmi les actifs (%)",
                color_discrete_sequence=[COLOR_MEDIUM, COLOR_HIGH],
                height=420
            )
            fig_dipl.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_dipl.update_layout(yaxis_title="% des actifs", xaxis_title="")
            st.plotly_chart(fig_dipl, use_container_width=True)

            st.divider()

            # ── Taux de chômage par niveau de diplôme ──
            taux_df = pd.DataFrame({
                'Niveau': form1['dipl_labels'] * 2,
                'Ville': [city1] * 7 + [city2] * 7,
                'Taux de chômage (%)': form1['taux_chomage_by_dipl'] + form2['taux_chomage_by_dipl'],
            })

            fig_taux = px.bar(
                taux_df,
                x='Niveau',
                y='Taux de chômage (%)',
                color='Ville',
                barmode='group',
                text='Taux de chômage (%)',
                title="Risque de chômage par niveau de diplôme (%)",
                color_discrete_sequence=[COLOR_MEDIUM, COLOR_HIGH],
                height=420
            )
            fig_taux.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_taux.update_layout(yaxis_title="Taux de chômage (%)", xaxis_title="")
            st.plotly_chart(fig_taux, use_container_width=True)

            st.divider()

            radar_labels = ['Sans diplôme', 'CAP-BEP', 'Bac', 'Bac+2', 'Bac+3/4', 'Bac+5+']
            radar_idx = [0, 2, 3, 4, 5, 6]  # indices dans dipl_pct
            r1 = [dipl_pct1[i] for i in radar_idx]
            r2 = [dipl_pct2[i] for i in radar_idx]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=r1 + [r1[0]],
                theta=radar_labels + [radar_labels[0]],
                fill='toself', name=city1,
                line=dict(color=COLOR_LOW)
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=r2 + [r2[0]],
                theta=radar_labels + [radar_labels[0]],
                fill='toself', name=city2,
                line=dict(color=COLOR_HIGH)
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title="Profil comparatif des niveaux de diplôme (%)",
                height=420
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        else:
            st.warning("⚠️ Données de formations non disponibles pour l'une ou les deux villes")
    else:
        st.warning("⚠️ Informations manquantes pour l'une ou les deux villes")

# ====== TAB 7: MÉTÉO ======
with tab7:
    st.header("🌤️ Comparaison Météo")
    _render_tab_context(log1, log2)
    current_year = pd.Timestamp.today().year
    
    col_temp1, col_temp2 = st.columns(2)
    
    with col_temp1:
        with st.spinner("Calcul température moyenne..."):
            avg_temp1 = get_annual_temperature_average(city1)
        if avg_temp1 is not None:
            st.metric(f"Température moyenne annuelle ({current_year})", f"{avg_temp1}°C")
            
    with col_temp2:
        with st.spinner("Calcul température moyenne..."):
            avg_temp2 = get_annual_temperature_average(city2)
        if avg_temp2 is not None:
            st.metric(f"Température moyenne annuelle ({current_year})", f"{avg_temp2}°C")
    
    st.divider()

    col1, col2 = st.columns(2)
    
    with col1:
        with st.spinner("Chargement météo..."):
            weather1 = get_weather_current(city1)
            if weather1 and 'current_condition' in weather1:
                current1 = weather1['current_condition'][0]
                st.metric("Température", f"{current1.get('temp_C', 'N/A')}°C")
                st.metric("Humidité", f"{current1.get('humidity', 'N/A')}%")
                st.metric("Vent", f"{current1.get('windspeedKmph', 'N/A')} km/h")
                st.metric("Précipitations", f"{current1.get('precipMM', 'N/A')} mm")
                
                if 'weatherDesc' in current1 and len(current1['weatherDesc']) > 0:
                    st.info(f"☁️ {current1['weatherDesc'][0].get('value', 'N/A')}")
    
    with col2:
        with st.spinner("Chargement météo..."):
            weather2 = get_weather_current(city2)
            if weather2 and 'current_condition' in weather2:
                current2 = weather2['current_condition'][0]
                st.metric("Température", f"{current2.get('temp_C', 'N/A')}°C")
                st.metric("Humidité", f"{current2.get('humidity', 'N/A')}%")
                st.metric("Vent", f"{current2.get('windspeedKmph', 'N/A')} km/h")
                st.metric("Précipitations", f"{current2.get('precipMM', 'N/A')} mm")
                
                if 'weatherDesc' in current2 and len(current2['weatherDesc']) > 0:
                    st.info(f"☁️ {current2['weatherDesc'][0].get('value', 'N/A')}")

    st.divider()
    st.subheader("📊 Prévisions météo (3 jours)")

    forecast1 = get_weather_forecast(city1)
    forecast2 = get_weather_forecast(city2)

    if forecast1 or forecast2:
        fig_forecast = go.Figure()

        def _add_forecast_traces(forecast_data, city_name, color_max, color_min):
            if not forecast_data:
                return

            forecast_df = pd.DataFrame(forecast_data[:3])
            forecast_df['maxtempC'] = pd.to_numeric(forecast_df['maxtempC'], errors='coerce')
            forecast_df['mintempC'] = pd.to_numeric(forecast_df['mintempC'], errors='coerce')
            forecast_df['date_label'] = pd.to_datetime(forecast_df['date'], errors='coerce').dt.strftime('%d/%m/%Y')
            forecast_df['date_label'] = forecast_df['date_label'].fillna(forecast_df['date'])

            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['date_label'],
                y=forecast_df['maxtempC'],
                mode='lines+markers',
                name=f"{city_name} - Max",
                line=dict(color=color_max, width=3)
            ))

            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['date_label'],
                y=forecast_df['mintempC'],
                mode='lines+markers',
                name=f"{city_name} - Min",
                line=dict(color=color_min, width=3, dash='dot')
            ))

        _add_forecast_traces(forecast1, city1, COLOR_MEDIUM, COLOR_MEDIUM)
        _add_forecast_traces(forecast2, city2, COLOR_LOW, COLOR_LOW)

        fig_forecast.update_layout(
            title="Comparaison des températures prévues",
            xaxis_title="Date",
            yaxis_title="Température (°C)",
            hovermode='x unified',
            height=420
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.warning("⚠️ Prévisions météo non disponibles")   
st.markdown("""
<div class="site-footer">
    <p>Sources : OpenDataSoft · INSEE · Open Data France · Open-Meteo</p>
</div>
""", unsafe_allow_html=True)
