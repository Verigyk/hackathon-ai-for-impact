# Garde-fous LLM — fichiers à intégrer

Ce dossier contient uniquement les 18 fichiers ajoutés ou modifiés pour renforcer les trois appels LLM et les validations du projet. Il ne constitue pas une application autonome.

## Intégration

- Base de travail : branche `Mohamed-Front`, commit `8b6094b06335a62ad0c778df32f1d7ee8be51254`.
- Les chemins sous ce dossier correspondent aux chemins dans l'application : `garde-fou/backend/app/prompts.py` doit être intégré dans `backend/app/prompts.py`, etc.
- Comparer les fichiers avec la version courante du projet avant de les fusionner afin de conserver les éventuelles modifications des autres contributeurs.
- Intégrer les fichiers Python, les tests et les deux fichiers frontend ensemble. Les fichiers modifiés importent les nouveaux modules.
- La configuration Vite accepte `LIO_API_URL` pour cibler le backend ; sa valeur par défaut reste `http://localhost:8000`.

## Documentation et vérification

Voir `backend/GARDE_FOUS_LLM.md` pour les règles, les limites et les scénarios de test, ainsi que `backend/README.md` pour le lancement.

La version complète de l'application utilisée pour vérifier ces fichiers a passé 95 tests backend, la compilation TypeScript, le build Vite et le lint frontend. Les appels LLM ont été testés avec des réponses simulées ; aucun appel réel à Claude n'a été vérifié.

Les fichiers de données, secrets, dépendances installées et bases SQLite locales ne sont pas inclus. L'activation du fournisseur LLM reste liée à la configuration du projet.
