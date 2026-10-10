"""Contrôles indépendants du fournisseur LLM ; aucune dépendance à son SDK."""
from __future__ import annotations

import re
from datetime import date, timedelta

from .llm_schemas import ExtractionDemande, INTRODUCTIONS, Recommandation
from .services.texte import normaliser

MAX_MESSAGE = 10000
_INSTRUCTION = re.compile(r"\b(ignore[rz]?|oublie[rz]?)\b.{0,60}\b(instructions?|regles?|prompt)\b|"
                          r"\b(system prompt|api key|cle api|bypass)\b", re.IGNORECASE)


def message_interdit(message: str) -> bool:
    """Détection ciblée ; les schémas et les contrôles restent la vraie frontière."""
    n = normaliser(message)
    return len(message) > MAX_MESSAGE or bool(_INSTRUCTION.search(n) or re.search(
        r"\b(contourner|contourne|ignorer|ignore|desactiver|desactive)\b.{0,50}\b(quota|capacite|controle|limite)\b|"
        r"\b(invente|inventer)\b.{0,50}\b(places|horaires|confirmation|reservation)\b", n))


def valider_regles(extrait: dict) -> dict:
    """Le mode démo doit respecter les mêmes types que les sorties du modèle."""
    from pydantic import ValidationError
    resultat = {}
    for champ, valeur in extrait.items():
        a_valider = valeur.get("libelle") if champ == "lieu_depart" and isinstance(valeur, dict) else valeur
        try:
            ExtractionDemande.model_validate({champ: a_valider})
        except (ValidationError, TypeError):
            continue
        if isinstance(a_valider, str) and _INSTRUCTION.search(normaliser(a_valider)):
            continue
        resultat[champ] = valeur
    return resultat


def _dans_source(valeur: str, source: str) -> bool:
    return f" {normaliser(valeur)} " in f" {normaliser(source)} "


def valider_extraction(extraction: ExtractionDemande, message: str, aujourdhui: str,
                       regles: dict | None = None) -> dict:
    """Conserve seulement des champs étayés par le dernier message.

    Les valeurs déjà reconnues par le parseur ont priorité. Un rejet n'efface
    pas la demande existante ; le service chat garde son extraction par règles.
    """
    from .services import comprendre, themes

    regles = regles if regles is not None else comprendre.extraire(message, date.fromisoformat(aujourdhui))
    resultat = {}
    for champ, valeur in extraction.model_dump(exclude_none=True).items():
        if champ in regles:
            # Ne pas remplacer une donnée reconnue par une interprétation du LLM.
            continue
        if isinstance(valeur, str) and _INSTRUCTION.search(normaliser(valeur)):
            continue
        if champ in {"nb_eleves", "nb_accompagnateurs", "duree"}:
            # Affecter une quantité à la bonne catégorie nécessite une preuve
            # contextuelle du parseur, pas la présence d'un chiffre quelconque.
            continue
        if champ == "date":
            attendue = comprendre.extraire_date(message, date.fromisoformat(aujourdhui))
            if attendue is None and _dans_source("demain", message):
                attendue = (date.fromisoformat(aujourdhui) + timedelta(days=1)).isoformat()
            if valeur != attendue:
                continue
        elif champ in {"heure_depart_min", "heure_retour_max"}:
            # Ne pas attribuer une heure de retour au départ (ou inversement).
            continue
        elif champ == "theme":
            if not _dans_source(valeur, message) and themes.theme_dans_texte(message) != valeur:
                continue
        elif not _dans_source(valeur, message):
            continue
        resultat[champ] = valeur
    return resultat


def valider_recommandation(resultat: Recommandation, candidats: list[dict]) -> Recommandation | None:
    """Tout identifiant doit exister ; les justifications sont extractives.

    En cas de citation non étayée, on remplace le texte par l'intérêt pédagogique
    du catalogue. Une sélection inconnue ou incohérente fait rejeter la réponse.
    """
    catalogue = {s["site_id"]: s for s in candidats}
    notes = {s.site_id: s for s in resultat.sites}
    if len(notes) != len(resultat.sites) or len(set(resultat.choix)) != len(resultat.choix):
        return None
    if not set(notes).issubset(catalogue) or not set(resultat.choix).issubset(notes):
        return None
    for identifiant, evaluation in notes.items():
        site = catalogue[identifiant]
        sources = [site.get("interet_pedagogique", ""), *site.get("activites", [])]
        if _INSTRUCTION.search(normaliser(evaluation.justification)) or not any(
                evaluation.justification in source for source in sources if isinstance(source, str)):
            remplacement = site.get("interet_pedagogique", "")
            if not remplacement or _INSTRUCTION.search(normaliser(remplacement)):
                return None
            evaluation.justification = remplacement[:600]
    return resultat


def rendre_explication(introduction: str, faits: str) -> str | None:
    """Injecte les faits intacts : le modèle n'écrit aucun nombre opérationnel."""
    if introduction not in INTRODUCTIONS:
        return None
    marqueur = "texte de référence: "
    if marqueur not in faits:
        return None
    reference = faits.split(marqueur, 1)[1].strip()
    if not reference:
        return None
    if faits.startswith("niveau=rouge"):
        introduction = ""
    return " ".join(part for part in (introduction, reference) if part)


def explication_valide(texte: str, faits: str) -> bool:
    """Compatibilité du contrôle historique ; le chemin LLM utilise rendre_explication.

    Pour des faits avec texte de référence, seules les versions rendues par Python
    sont admises. Les anciens appels sans référence gardent le contrôle numérique.
    Ce dernier n'est PAS une preuve de vérité sémantique.
    """
    if "texte de référence: " in faits:
        return any(texte == rendre_explication(intro, faits) for intro in INTRODUCTIONS)
    if not texte or len(texte) > 600:
        return False
    heure = re.compile(r"(\d{1,2})\s*(?:h|:)\s*(\d{2})?")
    autorisees = {(int(h), int(m or 0)) for h, m in heure.findall(faits)}
    if any((int(h), int(m or 0)) not in autorisees for h, m in heure.findall(texte)):
        return False
    nombres = {int(n) for n in re.findall(r"\d+", faits)}
    if any(int(n) not in nombres for n in re.findall(r"\d+", heure.sub(" ", texte))):
        return False
    return re.search(r"confirm|(?<!pré-)\bréservée?s?\b", texte, re.IGNORECASE) is None
