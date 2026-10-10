# Démonstration au jury

1. Ouvrir http://127.0.0.1:3000 et choisir « Avec le copilote ».
2. Saisir : « Nous partons de Toulouse le 6 novembre 2026, avec 28 élèves de 5e et 2 accompagnateurs. Thème Moyen Âge, aller-retour dès 8h et retour avant 19h. » Les détails secondaires restent ajustables dans le formulaire replié.
3. Cliquer sur « Découvrir les sorties possibles ». Le guide recherche des lieux sur Wikimedia ; les coordonnées officielles des gares et le routage piéton IGN servent à filtrer les accès. Le moteur vérifie les trains avant d’afficher les propositions.
4. Lors de la recette du 10 octobre, l’abbaye Saint-Pierre de Moissac était compatible : aller 09:52–10:50, retour 14:41–15:40, accès de groupe 14 minutes et indice 91/100. Les résultats peuvent changer avec les sources web et les options locales enregistrées.
5. Ouvrir « Voir la journée » : montrer les sources, le fil horaire et les facteurs du score. L’ouverture et l’accueil scolaire du lieu ne sont pas vérifiés ; cette réserve reste visible.
6. Poser une option locale de test avec des coordonnées fictives. Elle bloque la jauge scolaire partagée, puis devient un dossier en attente. Rien n’est transmis à SNCF.
7. Dans « Sources & fiabilité », expliquer les fichiers historiques, les APIs publiques, le modèle Ollama et les hypothèses du hackathon.

## Destination connue

Choisir « Rechercher un trajet », indiquer les gares de départ et d’arrivée, la date, l’effectif et les heures. Un aller simple mobilise seulement la jauge de l’aller. Une recherche vers une gare connue ne vérifie pas une visite culturelle.

## Jauge scolaire

Le plafond de 50 concerne les élèves et accompagnateurs de tous les groupes scolaires sur un même train et une même date. Deux demandes de 30 personnes ne passent pas ensemble : la deuxième option est refusée et une nouvelle recherche permet de trouver les alternatives. Le contrôle est transactionnel et porte sur tous les trains du dossier, sans allocation partielle.

Les tests concurrentiels utilisent un inventaire temporaire : ne pas effacer les dossiers saisis pour préparer la présentation. Les options locales expirent au bout de 30 minutes et peuvent être libérées dans « Mes dossiers ».

## Pitch

Un enseignant décrit son projet. Notre outil recherche des lieux sourcés, vérifie le trajet et explique les propositions. L’IA comprend le besoin ; Python contrôle les horaires, les marges, les accès et le quota scolaire. La réservation reste locale pour le hackathon, les horaires historiques sont supposés stables et les annulations sont exclues.

## Avant la présentation

Lancer Ollama, puis les deux services via `node scripts/dev.mjs`. Tester le réseau public et le parcours ci-dessus avant le passage. La recherche web ne nécessite pas de clé mais dépend de Wikimedia, SNCF Open Data et IGN. En cas d’indisponibilité, le système signale le problème sans inventer de destination.
