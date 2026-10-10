# Validation du prototype

Recette du 10 octobre 2026 : **39 tests automatisés réussis**, vérification TypeScript et compilation Next.js.

## Contrôles automatisés

`python scripts/run_tests.py` utilise des bases temporaires pour vérifier notamment :

- Quota scolaire partagé de 50, concurrence (12 demandes de 6 personnes, occupation finale 48), dates séparées et aucune survente.
- Contrôle atomique aller/retour, idempotence, expiration et libération des options, isolation des dossiers par session.
- Horaires historiques transposés au même jour de semaine, cohérence des marges, aller simple et refus des effectifs excessifs.
- Conversation française : dates et heures naturelles, variantes et fautes courantes, conservation des données, rejet des champs invalides ou inventés, historique transmis au modèle.
- Recherche web : exclusion des listes et des lieux sans coordonnées, distance géographique, refus d’une marche de groupe supérieure à 20 minutes, conservation des sources et des ouvertures inconnues.

Les tests API neutralisent le réseau externe avec WEB_DISCOVERY=false. Les tests du module web utilisent des réponses simulées : ils ne prouvent pas la disponibilité permanente des services publics.

## Vérifications réelles

Ollama / mistral:latest testé sur le poste. Wikimedia, coordonnées SNCF et routage piéton IGN appelés réellement. Recherche guidée dans le navigateur : Toulouse, 6 novembre 2026, 30 personnes, Moyen Âge, 08:00–19:00. Résultat : abbaye Saint-Pierre de Moissac, trains 871856 (09:52–10:50) et 871863 (14:41–15:40), marche de groupe 14 minutes, indice 91/100. Détail de journée, sources et avertissement sur l’accueil du lieu vérifiés.

Interface inspirée de SNCF, formulaire secondaire replié, bouton d’action visible dès que le projet est complet. Vérification de la largeur mobile à 390 pixels : aucun dépassement horizontal sur les résultats. Captures dans outputs/.

Les parcours option, pré-réservation et libération avaient été vérifiés dans le navigateur avant la refonte et restent couverts par les tests API. La dictée dépend du navigateur et de ses permissions ; elle n’est pas validée sur tous les postes.

## Limites assumées

Pas de réservation SNCF réelle, de billets, de compte enseignant, de transmission de dossier ou de déploiement. Horaires historiques réputés stables selon le périmètre du hackathon ; annulations exclues. Autorisations et inventaire scolaire simulés localement. Trajets ferroviaires directs uniquement. Les ouvertures, tarifs, accueils scolaires et besoins PMR des lieux web restent à vérifier auprès du site. Les accès calculés incluent une marge de groupe de 25 %, sans garantie sur les conditions réelles de terrain.

Le score est un barème explicite, pas une probabilité. Wikimedia peut produire des résultats incomplets : l’application filtre les propositions, mais ne promet pas un inventaire exhaustif du patrimoine régional. Le mode WEB_DISCOVERY=false conserve cinq lieux de démonstration pour les tests isolés.
