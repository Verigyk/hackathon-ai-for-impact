# Recherche web et accès aux lieux

La recherche est active par défaut (`WEB_DISCOVERY=true`) et ne nécessite aucune clé payante.

1. Le thème produit des requêtes vers l’API publique de Wikipédia en français. Les résultats doivent être des lieux avec des coordonnées, pas des listes, des régions ou des pages d’homonymie.
2. L’application charge les coordonnées officielles des gares de voyageurs SNCF. Elle rapproche les codes UIC des gares du fichier Détail desserte et conserve les départements d’Occitanie.
3. Les lieux sont rapprochés des gares directement desservies depuis le départ pour le jour de semaine demandé. Un rayon géographique de 3 km préfiltre les candidats ; il ne représente pas un temps de marche.
4. L’API IGN calcule un véritable itinéraire piéton. Le moteur majore ce temps de 25 % pour le groupe et exige au plus 20 minutes. Aucun bus urbain n’est inventé quand la marche est trop longue.
5. Le moteur ferroviaire vérifie ensuite les horaires historiques transposés, le retour, la durée de l’activité, les marges et la jauge scolaire locale avant de montrer la destination.

Les résultats sont bornés : quatre recherches au plus pour le Moyen Âge, quinze articles par requête, douze lieux à traiter et deux requêtes réseau simultanées. La couverture n’est donc pas exhaustive. Le cache conserve la recherche et les lieux 24 heures, la géographie et les accès 7 jours. Les sources et la date de calcul sont conservées dans les propositions.

## Ce qui est vérifié et ce qui reste inconnu

- Le lieu et sa position proviennent d’une page Wikipédia sourcée ; le texte affiché est attribué à Wikipédia sous CC BY-SA. L’intérêt pédagogique est une proposition à valider par l’enseignant, pas une activité réservée.
- Les coordonnées de gares sont officielles ; un itinéraire IGN reste une estimation de marche, pas une garantie d’accessibilité ou de sécurité pour une classe.
- Les horaires d’ouverture, tarifs, créneaux d’accueil de groupes et accessibilité PMR ne sont pas disponibles dans ces API. Ils sont affichés comme non vérifiés. La durée d’activité est déclarée par l’enseignant et la plage 0–24 h sert uniquement au calcul d’un itinéraire provisoire, sans prétendre que le site est ouvert.
- Les horaires ferroviaires restent issus des deux fichiers du hackathon, avec l’hypothèse de stabilité demandée par l’utilisateur. Les autorisations et places groupes restent simulées dans un inventaire local. Aucune demande n’est envoyée à la SNCF.

En cas d’échec des API, l’application signale l’indisponibilité et ne remplace pas les résultats par des destinations inventées. `WEB_DISCOVERY=false` restaure explicitement l’ancien catalogue de démonstration, notamment pour les tests isolés.

## Sources

- Recherche : https://www.mediawiki.org/wiki/API:Search
- Lieux : https://fr.wikipedia.org/
- Gares : https://ressources.data.sncf.com/explore/dataset/gares-de-voyageurs/
- Marche : https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/calcul-itineraire/

DATAtourisme et les sites des lieux pourront apporter une information touristique plus riche, notamment l’ouverture et l’accueil pédagogique, avec leurs accès et licences respectifs. Ils ne sont pas annoncés comme connectés dans cette version.
