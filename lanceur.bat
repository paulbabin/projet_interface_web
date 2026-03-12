@echo off
echo ==============
echo Installation des librairies en cours...
echo ==============
pip install -r requirements.txt

echo .
echo ==============
echo Lancement de l'appli Streamlit
echo ==============
streamlit run app.py
pause