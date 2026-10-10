"""Vocabulaire des thèmes pédagogiques : synonymes -> thème canonique du catalogue."""
from __future__ import annotations

from .texte import normaliser

SYNONYMES: dict[str, list[str]] = {
    "Moyen Âge": ["moyen age", "moyen ages", "moyenage", "medieval", "medievale", "medievaux",
                  "medievales", "epoque medievale", "chateau fort", "chateaux forts", "chevaliers",
                  "chevalerie", "cathares", "catharisme", "feodalite", "feodal", "seigneurs",
                  "art roman", "art gothique", "croisades", "croisade", "cathedrales"],
    "Antiquité": ["antiquite", "antique", "romains", "romaine", "rome antique", "gallo romain",
                  "gallo romaine", "gallo romains", "gaule romaine", "grece antique", "grecs",
                  "gladiateurs", "empire romain", "monde romain"],
    "Préhistoire": ["prehistoire", "prehistorique", "prehistoriques", "paleolithique",
                    "neolithique", "cro magnon", "art parietal", "grottes ornees"],
    "Espace et astronomie": ["espace", "astronomie", "systeme solaire", "planetes", "etoiles",
                             "astronautes", "conquete spatiale", "fusees", "univers"],
    "Sciences et nature": ["sciences", "science", "svt", "sciences de la vie", "nature",
                           "biodiversite", "evolution", "dinosaures", "animaux", "environnement",
                           "ecologie", "ocean", "oceans", "mer", "vivant"],
    "Arts": ["art", "arts", "arts plastiques", "histoire des arts", "peinture", "peintres",
             "musee d art", "beaux arts", "sculpture", "art contemporain"],
    "Temps modernes": ["temps modernes", "louis xiv", "xviie siecle", "17e siecle", "renaissance",
                       "canal du midi", "riquet", "grands travaux", "monarchie absolue"],
    "Première Guerre mondiale": ["premiere guerre mondiale", "grande guerre", "guerre de 14 18",
                                 "14 18", "1914 1918", "poilus"],
}

_INDEX = sorted(((s, canon) for canon, syns in SYNONYMES.items() for s in syns),
                key=lambda x: -len(x[0]))


def theme_dans_texte(texte: str) -> str | None:
    """Thème canonique mentionné dans le texte (le synonyme le plus long l'emporte)."""
    n = f" {normaliser(texte)} "
    meilleur = None
    for syn, canon in _INDEX:
        i = n.find(f" {syn} ")
        if i >= 0 and (meilleur is None or len(syn) > meilleur[0]):
            meilleur = (len(syn), canon)
    return meilleur[1] if meilleur else None


def canonique(theme: str | None) -> str | None:
    if not theme:
        return None
    n = normaliser(theme)
    for canon in SYNONYMES:
        if normaliser(canon) == n:
            return canon
    return theme_dans_texte(theme)
