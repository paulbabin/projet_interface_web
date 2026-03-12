"""Styles partagés pour l'application (couleurs, palettes, séquences Plotly)
Ce fichier centralise la nuance de bleu et les palettes utilisées par les pages.
"""
# Palette principale
PRIMARY = "#08306b"
SECONDARY = "#2b6cb0"
LIGHT = "#7fb8f7"
ACCENT = "#08519c"
SOFT = "#5aa3e6"
PALE = "#dbe9fb"

# Séquences utiles pour Plotly
PRIMARY_PAIR = [PRIMARY, SECONDARY]
STACK_SEQ = [LIGHT, SOFT, SECONDARY]
TYPE_SEQ = [LIGHT, SECONDARY]
PIE_SEQ = [PALE, LIGHT, ACCENT]

PALETTE = [PRIMARY, SECONDARY, LIGHT, SOFT, ACCENT, PALE]

def get_primary():
    return PRIMARY
