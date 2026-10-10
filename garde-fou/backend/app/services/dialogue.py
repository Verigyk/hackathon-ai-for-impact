"""Intentions de correction déterministes, indépendantes du modèle et des champs manquants."""
import re
from difflib import get_close_matches

from .texte import normaliser

VERBES = {"changer", "change", "modifier", "modifie", "corriger", "corrige", "remplacer", "remplace"}
CIBLES = [
    ("nb_accompagnateurs", {"accompagnateurs", "accompagnateur", "adultes", "profs", "professeurs"}),
    ("nb_eleves", {"eleves", "eleve", "enfants", "effectif"}),
    ("destination_souhaitee", {"destination", "visite"}),
    ("heure_retour_max", {"retour"}),
    ("heure_depart_min", {"heure", "horaire", "horaires"}),
    ("date", {"date", "jour"}), ("theme", {"theme", "sujet"}),
    ("niveau", {"classe", "niveau"}),
    ("lieu_depart", {"depart", "lieu", "etablissement"}),
]


def champ_modification(message: str) -> str | None:
    mots = normaliser(message).split()
    if not any(m in VERBES or (len(m) >= 5 and get_close_matches(m, VERBES, n=1, cutoff=0.85)) for m in mots):
        return None
    for champ, noms in CIBLES:
        if any(m in noms or (len(m) >= 5 and get_close_matches(m, noms, n=1, cutoff=0.85)) for m in mots):
            return champ
    return None


def demande_precision(message: str, champ: str) -> bool:
    """Une intention sans nouvelle valeur doit ouvrir une question, pas remplir un thème."""
    if champ in {"nb_eleves", "nb_accompagnateurs", "date", "heure_depart_min", "heure_retour_max"}:
        return not re.search(r"\d", message) and not re.search(
            r"\b(demain|aujourd hui|deux|trois|quatre|cinq|six|vingt|trente|quarante)\b", normaliser(message))
    return not re.search(r"\b(pour|par|plutot|finalement)\b|:", normaliser(message))
