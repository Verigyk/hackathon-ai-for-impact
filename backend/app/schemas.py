"""Contrat d'API en Pydantic : miroir champ pour champ de API_CONTRACT.md (snake_case)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Niveau = Literal["vert", "orange", "rouge"]
Statut = Literal["OPTION", "PRE_RESERVATION", "CONFIRMATION", "CONTRE_PROPOSITION", "ANNULE"]


class Modele(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Gare(Modele):
    code_uic: str
    nom: str
    lat: float
    lon: float
    distance_m: Optional[float] = None


class LieuDepart(Modele):
    libelle: str
    lat: Optional[float] = None
    lon: Optional[float] = None


class Demande(Modele):
    niveau: Optional[str] = None
    theme: Optional[str] = None
    nb_eleves: Optional[int] = None
    nb_accompagnateurs: Optional[int] = None
    date: Optional[str] = None
    duree: Optional[Literal["journee", "demi-journee"]] = None
    heure_depart_min: Optional[str] = None
    heure_retour_max: Optional[str] = None
    lieu_depart: Optional[LieuDepart] = None
    gare_depart: Optional[Gare] = None
    destination_souhaitee: Optional[str] = None
    champs_manquants: list[str] = Field(default_factory=list)

    @field_validator("niveau", "theme", "date", "duree", "heure_depart_min", "heure_retour_max",
                     "destination_souhaitee", "nb_eleves", "nb_accompagnateurs",
                     "lieu_depart", "gare_depart", mode="before")
    @classmethod
    def _vide_en_null(cls, v):
        # Un champ de formulaire vide arrive souvent sous la forme "" : on le traite comme absent.
        if isinstance(v, str) and not v.strip():
            return None
        return v


class AccesGareSite(Modele):
    mode: Literal["pied", "urbain"]
    minutes_groupe: int
    niveau: Niveau
    message: str


class Destination(Modele):
    site_id: str
    nom: str
    commune: str
    gare: Gare
    interet_pedagogique: str
    activites: list[str]
    themes: list[str]
    niveaux: list[str]
    temps_trajet_min: Optional[int] = None
    correspondances: int
    acces_gare_site: AccesGareSite
    indice_confiance: int
    niveau: Niveau


class Segment(Modele):
    train: str
    gare_depart: str
    gare_arrivee: str
    depart: str
    arrivee: str


class Trajet(Modele):
    segments: list[Segment]
    depart: str
    arrivee: str
    duree_min: int
    correspondances: int


class Jauge(Modele):
    capacite: int
    sous_option: int
    disponibles: int
    groupes_positionnes: int
    besoin: int
    niveau: Niveau


class Controle(Modele):
    regle: str
    libelle: str
    niveau: Niveau
    message: str


class CritereIndice(Modele):
    critere: str
    points: int
    max: int
    explication: str


class Indice(Modele):
    score: int
    niveau: Niveau
    details: list[CritereIndice]


class Proposition(Modele):
    proposition_id: str
    site_id: str
    date: str
    aller: Trajet
    retour: Trajet
    jauge_aller: Jauge
    jauge_retour: Jauge
    marge_avant_visite_min: int
    controles: list[Controle]
    indice: Indice
    explication_ia: str
    est_alternative: bool
    remplace: Optional[str] = None


class EtapeDossier(Modele):
    statut: Statut
    date: str
    message: str


class Dossier(Modele):
    reference: str
    statut: Statut
    message: str
    email: str
    demande: Demande
    site: Destination
    proposition: Proposition
    historique: list[EtapeDossier]
    cree_le: str


class MessageChat(Modele):
    role: Literal["user", "assistant"]
    content: str


# --- Corps et réponses des routes -----------------------------------------------------------

class Sante(Modele):
    ok: bool
    mode: Literal["llm", "demo"]
    donnees: Literal["demo", "sncf"]


class RequeteChat(Modele):
    messages: list[MessageChat] = Field(default_factory=list)
    demande: Optional[Demande] = None


class ReponseChat(Modele):
    reponse: str
    demande: Demande
    complete: bool
    suggestions: list[str]
    mode: Literal["llm", "demo"]


class RequeteDemande(Modele):
    demande: Demande


class ReponseDestinations(Modele):
    destinations: list[Destination]
    message: str


class RequeteTrajets(Modele):
    demande: Demande
    site_id: str


class ReponseTrajets(Modele):
    site: Destination
    propositions: list[Proposition]
    message: str


class RequetePreReservation(Modele):
    proposition_id: str
    email: str
    demande: Optional[Demande] = None


class RequeteSimulation(Modele):
    decision: Literal["confirmer", "contre-proposition"]


class RequeteRetour(Modele):
    reference: str
    satisfaction: int = Field(ge=1, le=5)
    adaptation_train: int = Field(ge=1, le=5)
    acces_gare_site: int = Field(ge=1, le=5)
    confiance: int = Field(ge=1, le=5)
    recommande: bool
    commentaire: Optional[str] = ""


class ReponseRetour(Modele):
    ok: bool
    indice_avant: int
    indice_apres: int
    message: str


# --- Vote en classe (v2) --------------------------------------------------------------------

class OptionSondage(Modele):
    site_id: str
    nom: str
    commune: str
    interet_pedagogique: str
    indice_confiance: int
    niveau: Niveau
    votes: int


class Sondage(Modele):
    code: str
    titre: str
    statut: Literal["ouvert", "ferme"]
    options: list[OptionSondage]
    total_votes: int
    gagnant: Optional[str] = None
    cree_le: str


class RequeteSondage(Modele):
    demande: Demande
    destinations: list[Destination]


class RequeteVote(Modele):
    site_id: str
    votant_id: str


class Reseau(Modele):
    ip_locale: Optional[str] = None
