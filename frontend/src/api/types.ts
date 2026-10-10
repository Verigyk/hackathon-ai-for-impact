// Miroir TypeScript de API_CONTRACT.md (racine du repo). Modifier le contrat d'abord.

export type Niveau = 'vert' | 'orange' | 'rouge'

export interface Gare {
  code_uic: string
  nom: string
  lat: number
  lon: number
  distance_m?: number | null
}

export interface LieuDepart {
  libelle: string
  lat: number | null
  lon: number | null
}

export interface Demande {
  niveau: string | null
  theme: string | null
  nb_eleves: number | null
  nb_accompagnateurs: number | null
  date: string | null
  duree: 'journee' | 'demi-journee' | null
  heure_depart_min: string | null
  heure_retour_max: string | null
  lieu_depart: LieuDepart | null
  gare_depart: Gare | null
  destination_souhaitee: string | null
  champs_manquants: string[]
}

export interface AccesGareSite {
  mode: 'pied' | 'urbain'
  minutes_groupe: number
  niveau: Niveau
  message: string
}

export interface Destination {
  site_id: string
  nom: string
  commune: string
  gare: Gare
  interet_pedagogique: string
  activites: string[]
  themes: string[]
  niveaux: string[]
  temps_trajet_min: number | null
  correspondances: number
  acces_gare_site: AccesGareSite
  indice_confiance: number
  niveau: Niveau
}

export interface Segment {
  train: string
  gare_depart: string
  gare_arrivee: string
  depart: string
  arrivee: string
}

export interface Trajet {
  segments: Segment[]
  depart: string
  arrivee: string
  duree_min: number
  correspondances: number
}

export interface Jauge {
  capacite: number
  sous_option: number
  disponibles: number
  groupes_positionnes: number
  besoin: number
  niveau: Niveau
}

export interface Controle {
  regle: string
  libelle: string
  niveau: Niveau
  message: string
}

export interface CritereIndice {
  critere: string
  points: number
  max: number
  explication: string
}

export interface Indice {
  score: number
  niveau: Niveau
  details: CritereIndice[]
}

export interface Proposition {
  proposition_id: string
  site_id: string
  date: string
  aller: Trajet
  retour: Trajet
  jauge_aller: Jauge
  jauge_retour: Jauge
  marge_avant_visite_min: number
  controles: Controle[]
  indice: Indice
  explication_ia: string
  est_alternative: boolean
  remplace: string | null
}

export type Statut = 'OPTION' | 'PRE_RESERVATION' | 'CONFIRMATION' | 'CONTRE_PROPOSITION' | 'ANNULE'

export interface EtapeDossier {
  statut: Statut
  date: string
  message: string
}

export interface Dossier {
  reference: string
  statut: Statut
  message: string
  email: string
  demande: Demande
  site: Destination
  proposition: Proposition
  historique: EtapeDossier[]
  cree_le: string
}

export interface MessageChat {
  role: 'user' | 'assistant'
  content: string
}

export interface Sante {
  ok: boolean
  mode: 'llm' | 'demo'
  donnees: 'demo' | 'sncf'
}

export interface ReponseChat {
  reponse: string
  demande: Demande
  complete: boolean
  suggestions: string[]
  mode: 'llm' | 'demo'
}

export interface ReponseDestinations {
  destinations: Destination[]
  message: string
}

export interface ReponseTrajets {
  site: Destination
  propositions: Proposition[]
  message: string
}

export interface RetourExperience {
  reference: string
  satisfaction: number
  adaptation_train: number
  acces_gare_site: number
  confiance: number
  recommande: boolean
  commentaire: string
}

export interface ReponseRetour {
  ok: boolean
  indice_avant: number
  indice_apres: number
  message: string
}

export const DEMANDE_VIDE: Demande = {
  niveau: null,
  theme: null,
  nb_eleves: null,
  nb_accompagnateurs: null,
  date: null,
  duree: null,
  heure_depart_min: null,
  heure_retour_max: null,
  lieu_depart: null,
  gare_depart: null,
  destination_souhaitee: null,
  champs_manquants: ['niveau', 'theme', 'nb_eleves', 'nb_accompagnateurs', 'date', 'lieu_depart'],
}

// ---------- Vote en classe (v2) ----------

export interface OptionSondage {
  site_id: string
  nom: string
  commune: string
  interet_pedagogique: string
  indice_confiance: number
  niveau: Niveau
  votes: number
}

export interface Sondage {
  code: string
  titre: string
  statut: 'ouvert' | 'ferme'
  options: OptionSondage[]
  total_votes: number
  gagnant: string | null
  cree_le: string
}

export interface Reseau {
  ip_locale: string | null
}
