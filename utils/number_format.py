"""
Utilitaires de formatage numérique (fr-FR).
"""


def format_int_fr(value) -> str:
    """
    Formate un entier avec séparateur de milliers espace.
    Ex: 1234567 -> "1 234 567"
    """
    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return "N/A"
