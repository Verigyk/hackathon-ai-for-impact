"""Formats internes du LLM. Le contrat HTTP existant reste inchangé."""
from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

TexteCourt = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
Identifiant = Annotated[str, StringConstraints(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")]
Heure = Annotated[str, StringConstraints(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")]
NiveauClasse = Literal["CP", "CE1", "CE2", "CM1", "CM2", "6e", "5e", "4e", "3e", "2de", "1re", "Tle"]
INTRODUCTIONS = ("", "Voici le détail de cette proposition.", "Voici les éléments pour préparer votre sortie.")


class SortieLLM(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ExtractionDemande(SortieLLM):
    niveau: NiveauClasse | None = None
    theme: TexteCourt | None = None
    # Ne pas couper à 50 : le professeur peut déclarer un groupe trop grand.
    # La règle métier doit alors le signaler, sans tronquer son effectif.
    nb_eleves: Annotated[int, Field(ge=1, le=10000)] | None = None
    nb_accompagnateurs: Annotated[int, Field(ge=0, le=10000)] | None = None
    date: Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$")] | None = None
    duree: Literal["journee", "demi-journee"] | None = None
    heure_depart_min: Heure | None = None
    heure_retour_max: Heure | None = None
    lieu_depart: TexteCourt | None = None
    destination_souhaitee: TexteCourt | None = None

    @field_validator("date")
    @classmethod
    def date_reelle(cls, valeur: str | None) -> str | None:
        if valeur is not None:
            date.fromisoformat(valeur)
        return valeur


class SiteNote(SortieLLM):
    site_id: Identifiant
    note: Annotated[int, Field(ge=0, le=3)]
    justification: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]


class Recommandation(SortieLLM):
    sites: Annotated[list[SiteNote], Field(max_length=20)]
    choix: Annotated[list[Identifiant], Field(min_length=1, max_length=3)]


class Explication(SortieLLM):
    proposition_id: Identifiant
    introduction: Literal["", "Voici le détail de cette proposition.", "Voici les éléments pour préparer votre sortie."]


class Explications(SortieLLM):
    explications: Annotated[list[Explication], Field(max_length=30)]
