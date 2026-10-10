"""Les 3 appels au LLM (Claude) : comprendre, recommander, expliquer. Rien d'autre.

Le LLM ne calcule jamais d'horaire, de place disponible ni de score global : il extrait la demande,
classe et justifie des sites DU CATALOGUE, et choisit une introduction pour un résumé intégralement rendu par Python. Toute réponse est validée ; en cas d'erreur réseau, de refus ou de sortie invalide, le
code retombe sur le mode démo (règles déterministes).

Mode « llm » si ANTHROPIC_API_KEY est définie, sinon mode « demo ».
"""
from __future__ import annotations

import json
import logging
import os
from typing import TypeVar

from pydantic import BaseModel

from . import garde_fous
from .garde_fous import explication_valide  # compatibilité des anciens imports
from .llm_schemas import ExtractionDemande, Recommandation, Explication, Explications, SiteNote
from .prompts import SYSTEME_COMPRENDRE, SYSTEME_RECOMMANDER, SYSTEME_EXPLIQUER

log = logging.getLogger("lio.llm")

MODELE = os.environ.get("LIO_LLM_MODEL", "claude-opus-5-5")
T = TypeVar("T", bound=BaseModel)

_client = None


def mode() -> str:
    return "llm" if os.environ.get("ANTHROPIC_API_KEY") else "demo"


def _get_client():
    global _client
    if _client is None:
        import anthropic

        # Délais courts : l'interface attend, et on a toujours un repli déterministe.
        _client = anthropic.Anthropic(timeout=25.0, max_retries=1)
    return _client


def _appeler(systeme: str, contenu: str, format_sortie: type[T], max_tokens: int = 4000) -> T | None:
    """Un appel structuré (sortie JSON validée par Pydantic). None en cas d'échec ou de refus."""
    if len(contenu) > 60000 or mode() != "llm":
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = _get_client()
        # Privilégier l'API stable lorsqu'elle est exposée par le SDK.
        parser = getattr(getattr(client, "messages", None), "parse", None)
        if parser is None:
            parser = client.beta.messages.parse
        reponse = parser(
            model=MODELE,
            max_tokens=max_tokens,
            system=systeme,
            messages=[{"role": "user", "content": contenu}],
            output_format=format_sortie,
        )
    except anthropic.APIConnectionError as e:  # inclut les dépassements de délai
        log.warning("LLM injoignable (%s), repli démo.", type(e).__name__)
        return None
    except anthropic.RateLimitError as e:
        log.warning("LLM limité en débit (%s), repli démo.", type(e).__name__)
        return None
    except anthropic.APIStatusError as e:
        log.warning("Erreur de l'API LLM (%s), repli démo.", e.status_code)
        return None
    except Exception as e:  # sortie non conforme au schéma, etc.
        log.warning("Réponse LLM inutilisable (%s), repli démo.", type(e).__name__)
        return None
    if getattr(reponse, "stop_reason", None) != "end_turn":
        log.warning("Réponse LLM refusée, tronquée ou incomplète ; repli déterministe.")
        return None
    try:
        # Même un objet déjà construit doit repasser les validations locales.
        sortie = reponse.parsed_output
        if sortie is None:
            return None
        return format_sortie.model_validate(sortie.model_dump() if isinstance(sortie, BaseModel) else sortie)
    except Exception:
        log.warning("Sortie LLM rejetée par le schéma ; repli déterministe.")
        return None


# Les schémas et prompts restent accessibles depuis app.llm pour compatibilité.


def extraire_demande(dernier_message: str, message_assistant: str | None, demande_actuelle: dict,
                     aujourdhui: str, extraction_regles: dict | None = None) -> dict | None:
    if not dernier_message.strip() or len(dernier_message) > garde_fous.MAX_MESSAGE:
        return None
    contenu = json.dumps({
        "date_du_jour": aujourdhui,
        "demande_connue": {k: v for k, v in demande_actuelle.items()
                           if k in ExtractionDemande.model_fields},
        "question_precedente": message_assistant or "",
        "dernier_message": dernier_message,
    }, ensure_ascii=False)
    r = _appeler(SYSTEME_COMPRENDRE, contenu, ExtractionDemande, max_tokens=3000)
    if r is None:
        return None
    try:
        r = ExtractionDemande.model_validate(r.model_dump())
        return garde_fous.valider_extraction(r, dernier_message, aujourdhui, extraction_regles)
    except (ValueError, TypeError, AttributeError):
        log.warning("Extraction LLM rejetée ; conservation du parseur local.")
        return None


def recommander(demande: dict, candidats: list[dict]) -> Recommandation | None:
    if not candidats or len(candidats) > 20:
        return None
    contenu = json.dumps({"demande": demande, "catalogue": candidats}, ensure_ascii=False)
    r = _appeler(SYSTEME_RECOMMANDER, contenu, Recommandation, max_tokens=6000)
    if r is None:
        return None
    try:
        r = Recommandation.model_validate(r.model_dump())
        validee = garde_fous.valider_recommandation(r, candidats)
        if validee is None:
            log.warning("Sélection LLM hors catalogue ou incohérente ; repli déterministe.")
        return validee
    except (ValueError, TypeError, AttributeError):
        log.warning("Recommandation LLM rejetée ; repli déterministe.")
        return None


def expliquer(faits_par_proposition: dict[str, str]) -> dict[str, str]:
    """Le LLM choisit le ton ; Python conserve tous les faits et avertissements."""
    if not faits_par_proposition or len(faits_par_proposition) > 30:
        return {}
    contenu = json.dumps({"propositions": faits_par_proposition}, ensure_ascii=False)
    r = _appeler(SYSTEME_EXPLIQUER, contenu, Explications, max_tokens=3000)
    if r is None:
        return {}
    try:
        r = Explications.model_validate(r.model_dump())
    except (ValueError, TypeError, AttributeError):
        log.warning("Explication LLM rejetée ; gabarits conservés.")
        return {}
    ids = [e.proposition_id for e in r.explications]
    if len(set(ids)) != len(ids) or not set(ids).issubset(faits_par_proposition):
        log.warning("Identifiant de proposition LLM inconnu ou dupliqué ; gabarits conservés.")
        return {}
    out = {}
    for e in r.explications:
        texte = garde_fous.rendre_explication(e.introduction, faits_par_proposition[e.proposition_id])
        if texte is not None:
            out[e.proposition_id] = texte
    return out
