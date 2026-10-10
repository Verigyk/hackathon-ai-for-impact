# Contrat d'API du copilote liO

Source de vérité partagée entre `backend/` (FastAPI, modèles Pydantic) et `frontend/src/api/types.ts`. Toute modification se fait ici d'abord, puis des deux côtés.

- Base : `http://localhost:8000/api` (le front passe par le proxy Vite sur `/api`).
- Format : JSON, noms de champs en `snake_case`, dates `AAAA-MM-JJ`, heures `HH:MM`, horodatages ISO 8601.
- Erreurs : statut HTTP 4xx/5xx avec `{ "detail": "message lisible en français" }`.
- Niveaux de statut partout : `"vert" | "orange" | "rouge"`.
- Données de démonstration : tant que les vrais fichiers SNCF ne sont pas chargés, l'API sert un jeu de démonstration et le dit (`GET /api/sante` → `donnees: "demo"`).

## Objets

```ts
type Niveau = "vert" | "orange" | "rouge";

interface Gare { code_uic: string; nom: string; lat: number; lon: number; distance_m?: number | null }

interface LieuDepart { libelle: string; lat: number | null; lon: number | null }

interface Demande {
  niveau: string | null;              // "5e"
  theme: string | null;               // "Moyen Âge"
  nb_eleves: number | null;
  nb_accompagnateurs: number | null;
  date: string | null;                // "2026-11-12"
  duree: "journee" | "demi-journee" | null;
  heure_depart_min: string | null;    // "08:00"
  heure_retour_max: string | null;    // "19:00"
  lieu_depart: LieuDepart | null;
  gare_depart: Gare | null;           // déduite du lieu si absente
  destination_souhaitee: string | null; // quand l'enseignant sait déjà où aller
  champs_manquants: string[];         // noms des champs obligatoires encore vides
}

interface AccesGareSite { mode: "pied" | "urbain"; minutes_groupe: number; niveau: Niveau; message: string }

interface Destination {
  site_id: string; nom: string; commune: string;
  gare: Gare;
  interet_pedagogique: string;
  activites: string[];
  themes: string[]; niveaux: string[];
  temps_trajet_min: number | null;    // trajet train depuis la gare de départ, meilleur cas
  correspondances: number;
  acces_gare_site: AccesGareSite;
  indice_confiance: number;           // 0-100, meilleur trajet trouvé
  niveau: Niveau;
}

interface Segment { train: string; gare_depart: string; gare_arrivee: string; depart: string; arrivee: string }

interface Trajet { segments: Segment[]; depart: string; arrivee: string; duree_min: number; correspondances: number }

interface Jauge { capacite: number; sous_option: number; disponibles: number; groupes_positionnes: number; besoin: number; niveau: Niveau }

interface Controle { regle: string; libelle: string; niveau: Niveau; message: string }

interface CritereIndice { critere: string; points: number; max: number; explication: string }

interface Indice { score: number; niveau: Niveau; details: CritereIndice[] }

interface Proposition {
  proposition_id: string;
  site_id: string;
  date: string;
  aller: Trajet;
  retour: Trajet;
  jauge_aller: Jauge;
  jauge_retour: Jauge;
  marge_avant_visite_min: number;
  controles: Controle[];
  indice: Indice;
  explication_ia: string;             // phrase claire, jamais d'horaire ou de place inventés
  est_alternative: boolean;
  remplace: string | null;            // proposition_id de la proposition rouge qu'elle remplace
}

type Statut = "OPTION" | "PRE_RESERVATION" | "CONFIRMATION" | "CONTRE_PROPOSITION" | "ANNULE";

interface EtapeDossier { statut: Statut; date: string; message: string }

interface Dossier {
  reference: string;                  // "LIO-2026-000123"
  statut: Statut;
  message: string;                    // ex. "Demande de pré-réservation transmise — confirmation en attente"
  email: string;
  demande: Demande;
  site: Destination;
  proposition: Proposition;
  historique: EtapeDossier[];
  cree_le: string;
}

interface MessageChat { role: "user" | "assistant"; content: string }
```

## Routes

| Méthode et route | Corps envoyé | Réponse | Rôle |
|---|---|---|---|
| `GET /api/sante` | — | `{ ok: true, mode: "llm" \| "demo", donnees: "demo" \| "sncf" }` | État de l'API, affiché discrètement dans le front |
| `POST /api/chat` | `{ messages: MessageChat[], demande: Demande \| null }` | `{ reponse: string, demande: Demande, complete: boolean, suggestions: string[], mode: "llm" \| "demo" }` | Conversation avec Tchouette. Remplit la `Demande` au fil des messages. `complete` passe à `true` quand les champs obligatoires sont remplis. `suggestions` = 2 à 4 réponses rapides cliquables |
| `POST /api/demande/valider` | `{ demande: Demande }` (champs saisis dans le formulaire) | `Demande` | Chemin formulaire : géocode le lieu, trouve la gare, recalcule `champs_manquants` |
| `POST /api/destinations` | `{ demande: Demande }` | `{ destinations: Destination[], message: string }` | 3 destinations au plus, tirées du catalogue uniquement. Si `destination_souhaitee` est remplie, elle passe en premier |
| `POST /api/trajets` | `{ demande: Demande, site_id: string }` | `{ site: Destination, propositions: Proposition[], message: string }` | Propositions triées par indice décroissant. Une proposition rouge est suivie de son alternative (`est_alternative: true`) |
| `POST /api/pre-reservations` | `{ proposition_id: string, email: string, demande: Demande }` | `Dossier` | Pose une OPTION puis transmet la demande : statut `PRE_RESERVATION`. Jamais `CONFIRMATION` à ce stade |
| `GET /api/pre-reservations/{reference}` | — | `Dossier` | Suivi du dossier |
| `POST /api/pre-reservations/{reference}/simuler-reponse` | `{ decision: "confirmer" \| "contre-proposition" }` | `Dossier` | Démo : simule la réponse du chargé de clientèle SNCF |
| `POST /api/retours` | `{ reference, satisfaction, adaptation_train, acces_gare_site, confiance, recommande, commentaire }` (notes de 1 à 5, `recommande` booléen) | `{ ok: true, indice_avant: number, indice_apres: number, message: string }` | Retour d'expérience, qui fait évoluer le critère satisfaction de l'indice du site |

## Champs obligatoires de la `Demande`

`niveau`, `theme` (sauf si `destination_souhaitee` est remplie), `nb_eleves`, `nb_accompagnateurs`, `date`, `lieu_depart`. Les autres ont une valeur par défaut : `duree = "journee"`, `heure_depart_min = "08:00"`, `heure_retour_max = "18:00"`.

## Vote en classe (v2)

L'enseignant fait voter sa classe entre les destinations proposées. Il projette un QR code ; les élèves le scannent avec leur téléphone (même réseau Wi-Fi) et votent. Les votes sont anonymes : aucun prénom, seulement un identifiant aléatoire stocké dans le navigateur de l'élève pour éviter les doubles votes (un élève peut changer d'avis tant que le vote est ouvert).

```ts
interface OptionSondage {
  site_id: string;
  nom: string;
  commune: string;
  interet_pedagogique: string;
  indice_confiance: number;
  niveau: Niveau;
  votes: number;
}

interface Sondage {
  code: string;                       // 6 caractères sans ambiguïté, ex. "TCH4K7"
  titre: string;                      // ex. "Où part la 5e pour le Moyen Âge ?"
  statut: "ouvert" | "ferme";
  options: OptionSondage[];           // dans l'ordre des destinations proposées
  total_votes: number;
  gagnant: string | null;             // site_id, renseigné à la fermeture (égalité : meilleur indice)
  cree_le: string;
}
```

| Méthode et route | Corps envoyé | Réponse | Rôle |
|---|---|---|---|
| `POST /api/sondages` | `{ demande: Demande, destinations: Destination[] }` | `Sondage` | Crée le vote : au moins 2 destinations (sinon 422), seules les 4 premières sont gardées |
| `GET /api/sondages/{code}` | — | `Sondage` | Lecture (le front de l'enseignant interroge toutes les 2 s) ; 404 si code inconnu |
| `POST /api/sondages/{code}/votes` | `{ site_id: string, votant_id: string }` | `Sondage` | Vote ou change de vote ; 409 `{detail}` si le vote est fermé, 422 si `site_id` n'est pas dans le vote |
| `POST /api/sondages/{code}/fermer` | — | `Sondage` | Ferme le vote et désigne le gagnant |
| `GET /api/reseau` | — | `{ ip_locale: string \| null }` | Adresse IP de la machine sur le réseau local, pour fabriquer l'URL du QR code quand le site est ouvert sur `localhost` |
