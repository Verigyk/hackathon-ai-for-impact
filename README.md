# SNCF · Sorties scolaires en Occitanie

Application locale de hackathon : un enseignant décrit un projet ou choisit une gare d’arrivée ; l’application recherche des lieux sur le web et vérifie des trajets liO avec les deux fichiers SNCF fournis. Interface inspirée de SNCF, copilote Ollama, itinéraires piétons IGN et inventaire scolaire local.

## Lancer

Prérequis : Node.js, Python 3.12 et Ollama avec `mistral:latest` (déjà installé sur l’ordinateur de développement).

```powershell
node scripts/dev.mjs
```

Interface : http://127.0.0.1:3000/
Documentation API : http://127.0.0.1:8000/docs

La configuration locale `.env.local` contient `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=mistral:latest` et `DEMO_MODE=true`. `WEB_DISCOVERY=true` est la valeur par défaut : aucune clé payante n’est nécessaire pour la recherche Wikimedia, les gares SNCF et les accès piétons IGN. Il faut un accès Internet pour les premières recherches ; les résultats sont ensuite mis en cache.

Les dépendances sont déjà installées dans cet espace. Pour une nouvelle installation, consulter les scripts `scripts/setup.mjs` et `scripts/import_data.py`. Les bases SNCF sont créées à partir de `data/raw/Data_Hackathon.csv` et `data/raw/Detail_desserte.xlsx` ; garder les noms et les règles d’importation du script. Les données du hackathon sont privées à cet usage et exclues de Git.

## Vérifier

```powershell
python scripts/run_tests.py
node node_modules/typescript/bin/tsc --noEmit
node node_modules/next/dist/bin/next build
```

Les tests réseau sont simulés pour être reproductibles ; les API publiques sont aussi vérifiées séparément dans les tests manuels. La validation couvre le dialogue, les dates, les sources web, les limites d’accès, la concurrence sur les jauges, l’expiration et l’isolation des sessions.

## Ce que l’application fait réellement

- Recherche de nouveaux lieux géolocalisés en Occitanie à partir du thème, avec sources visibles.
- Rapprochement avec les gares officielles SNCF et calcul de marche IGN, majoré pour le groupe.
- Vérification déterministe de trajets directs, des horaires, du retour, des marges et du quota scolaire.
- Conversation locale avec Mistral, champs structurés validés et historique des douze derniers messages.
- Comparaison des sorties, détail de journée et options locales atomiques avec dossiers téléchargeables.

Les horaires d’ouverture, tarifs et accueils de groupes restent à confirmer auprès des lieux. Les données ferroviaires sont historiques avec l’hypothèse de stabilité du hackathon. Les autorisations et places groupes sont simulées ; aucun dossier n’est envoyé à la SNCF. Ce projet indépendant ne constitue pas le service officiel SNCF Connect. Le déploiement est reporté à la demande de l’utilisateur.

## Documentation

- [Architecture](docs/architecture.md)
- [Recherche web et provenance](docs/recherche-web.md)
- [Ollama](docs/ollama.md)
- [API](docs/api.md)
- [Validation](docs/validation.md)
