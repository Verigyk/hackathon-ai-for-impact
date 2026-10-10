# API et stockage

Le navigateur appelle `/api/*` sur Next.js. Le BFF transmet à FastAPI en boucle locale et ajoute `X-Session` à partir du cookie `echappee-session` (UUID aléatoire, HttpOnly, SameSite=Lax). L’API Python écoute sur `127.0.0.1:8000`. Swagger : `/docs`.

| Méthode | Route | Réponse |
|---|---|---|
| GET | `/api/health` | État de service, mode démo |
| GET | `/api/status` | Sources et empreintes, volumes, providers, TTL |
| GET | `/api/stations?q=Foix` | Liste des gares du fichier |
| GET | `/api/places` | Lieux web découverts dans les dernières 24 h (catalogue démo uniquement si WEB_DISCOVERY=false) |
| POST | `/api/chat` | Champs extraits, informations manquantes, réponse, provider utilisé |
| POST | `/api/search` | Propositions, exclusions, avertissements, traces et projet |
| POST | `/api/options` | Option et allocations atomiques |
| POST | `/api/prereservations` | Dossier en attente de confirmation |
| GET | `/api/dossiers` | Dossiers de la session |
| POST | `/api/dossiers/{id}/release` | Option libérée |

Routes publiques : health, status, stations, places. Les autres exigent un UUID `X-Session`. Ce contexte local sépare les sessions mais n’est pas une authentification métier ; ne pas exposer directement FastAPI sur Internet.

## Projet de recherche

```json
{
  "mode": "guided",
  "origin": "Toulouse",
  "origin_station": null,
  "theme": "Moyen Âge",
  "level": "5e",
  "students": 28,
  "companions": 2,
  "date": "2026-11-06",
  "trip_type": "round_trip",
  "earliest": "08:00",
  "latest": "19:00",
  "visit_minutes": 120,
  "origin_access_minutes": 15,
  "scenario": "normal"
}
```

En mode `direct`, préciser `destination_id` (ID du catalogue) ou `destination_station` (code SNCF). Une gare manuellement sélectionnée évite les ambiguïtés de commune. La conversation `{ "message": "...", "fields": {} }` fusionne seulement les champs autorisés. La recherche finale passe toujours par les validations Pydantic.

Option : `{ "proposal_id": "UUID retourné", "idempotency_key": "UUID client stable" }`. Pré-réservation : `{ "dossier_id": "UUID", "teacher_name": "Enseignant Démo", "school": "Collège Démo", "email": "demo@example.com" }`.

Les erreurs sont structurées sous `detail`. Codes : 401 session, 404 ressource hors session/inconnue, 409 quota ou option expirée, 422 validation du projet, 503 backend/inventaire indisponible. Un 409 quota fournit `train`, `remaining`, `requested` et un message pour relancer la recherche. Les résultats de recherche expirent après 30 minutes.

## Bases

`sncf.sqlite` : `sources`, `stations`, `scheduled_stops`, `train_month_metrics`, `reference_services`. Les fichiers d’origine restent préservés ; chaque arrêt et métrique garde sa ligne source. L’application lit cette base en lecture seule après préparation des références au démarrage.

`app.sqlite` :

- `projects` : projet JSON et propriétaire de session.
- `proposals` : résultat Python immuable, projet et propriétaire.
- `dossiers` : statut, clé d’idempotence, expiration, instantané du voyage et contact de test.
- `school_allocations` : nombre de personnes par dossier/train/date.
- `cache` : recherches Wikimedia et lieux (24 h), coordonnées SNCF et itinéraires IGN (7 jours).

SQLite WAL et délai d’attente de 15 secondes. Le plafond est vérifié sous verrou d’écriture transactionnel, pas par un total calculé côté navigateur.

## Exploitation

Les sessions restent valables sept jours. Aucun traitement des coordonnées autre que leur stockage local. Aucun e-mail envoyé. Ne pas partager `app.sqlite`, qui contient les contacts saisis. Ne pas committer les données du hackathon ou `.env.local`. Faire une copie des bases avant un reset ou une réimportation. Pour repartir sur un inventaire neuf, utiliser une nouvelle base locale après sauvegarde et redémarrer ; aucun endpoint de purge publique n’est fourni.

Copilote : dates françaises (14 septembre 2026, 14/09/2026, 14/09/26, ISO), heures naturelles (9h du matin, 18 heures 30), aller/allez retour, effectif total via group_total. Les valeurs confirmées dans le formulaire sont conservées pendant la conversation. Niveau, durée d’activité (120 min) et accès gare (15 min) sont des options ajustables, sans question obligatoire. La jauge utilise group_total quand renseigné, sans inventer la répartition élèves/accompagnateurs.
