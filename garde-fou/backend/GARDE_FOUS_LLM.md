# Garde-fous du copilote liO

Ces changements sont locaux, dans la copie de `Mohamed-Front`. Aucun commit,
push, changement de branche ou déploiement n'est nécessaire pour les utiliser.

## Fichiers et responsabilités

| Fichier | Responsabilité |
| --- | --- |
| `app/prompts.py` | Instructions communes, trois rôles et version des prompts |
| `app/llm_schemas.py` | Formats internes Pydantic stricts, types, bornes, heures et dates |
| `app/garde_fous.py` | Preuves dans le message, contrôle du catalogue et rendu des explications |
| `app/llm.py` | Appels Claude, validation avant utilisation et repli déterministe |
| `app/services/chat.py` | Extraction par règles prioritaire lors de la fusion avec le LLM |
| `app/services/dialogue.py` | Corrections prioritaires, variantes de formulation et fautes courantes |
| `app/services/recommander.py` | Contrôles de transport avant le classement par le LLM |
| `app/services/dossiers.py` | Cohérence projet/proposition et transaction du quota à la pré-réservation |
| `app/services/expliquer.py` | Faits et texte de référence produits par le moteur Python |
| `tests/test_garde_fous_llm.py` | Tests avec réponses LLM adverses, sans clé ni réseau |

Les endpoints, les schémas HTTP de `app/schemas.py` et le frontend sont inchangés.
Les prompts et classes restent importables depuis `app.llm` pour compatibilité.
Le schéma **interne** de génération des explications change : le LLM renvoie
`proposition_id` et `introduction`, jamais un résumé opérationnel libre.

## Flux de protection

1. Le message du professeur et les données sont transmis comme données JSON.
   Le prompt interdit de traiter leur contenu comme de nouvelles instructions.
2. La sortie repasse par un schéma strict : clés inconnues, types incorrects,
   dates inexistantes, heures impossibles et notes hors 0–3 sont rejetés.
3. Les champs déjà compris par le parseur ne peuvent pas être remplacés par le LLM.
   Les quantités et les rôles des heures restent ceux reconnus par le parseur,
   y compris pour les réponses courtes interprétées par le chat.
4. Les autres champs sont conservés seulement s'ils sont étayés par le dernier
   message (texte exprimé, thème reconnu, date française/ISO ou « demain »).
   Une donnée rejetée n'efface pas les informations déjà connues.
5. La recommandation utilise uniquement des identifiants évalués du catalogue.
   Avant tout appel au modèle, Python écarte les sites sans proposition acceptable
   ou dont l'accès gare-site est rouge. Le LLM ne peut pas réintroduire ces sites.
   Les identifiants inconnus ou dupliqués font rejeter la sélection. Une
   justification non citée depuis le catalogue est remplacée par son texte local.
6. Pour expliquer le voyage, le LLM sélectionne une introduction parmi trois
   phrases autorisées. Python ajoute le résumé original **intact**. Les horaires,
   places, contraintes, alternatives et avertissements ne peuvent pas être
   permutés ou supprimés par le modèle. Une proposition rouge garde son refus.
7. En cas d'échec, de refus ou de sortie invalide, le code utilise les règles et
   gabarits existants. Les journaux indiquent le motif technique sans afficher
   le contenu brut des messages ou des erreurs du fournisseur.
   Les réponses tronquées (`max_tokens`), suspendues ou non terminées sont également rejetées.

Le SDK stable `messages.parse` est utilisé lorsqu'il existe ; sinon son équivalent
`beta.messages.parse` est utilisé. Les paramètres beta de repli non nécessaires
ont été retirés. Le modèle configuré est conservé sans substitution silencieuse.
Seuls les champs nécessaires à l'extraction sont transmis au modèle, sans e-mail,
référence de dossier ou donnée supplémentaire reçue dans la demande.

Les deux modes partagent les validations des valeurs reconnues. Une demande comme
« ej veux changer le nombre des eleves » interrompt les questions restantes et
demande le nouvel effectif. La réponse « 28 » ne modifie pas les accompagnateurs.
Une année, une date invalide ou un total de personnes non réparti ne deviennent
pas automatiquement un nombre d'élèves. Les fautes courantes dans les mois et
les dates sans espace sont normalisées, mais aucune date inexistante n'est inventée.

Exemple : avec 30 voyageurs et 50 places, le modèle ne peut pas produire
« 50 voyageurs et 30 places ». Il ne reçoit aucune possibilité de modifier
ces valeurs dans le résumé présenté au professeur.

## Modifier les instructions

Modifiez les constantes de `app/prompts.py` puis mettez à jour `VERSION_PROMPTS`.
Chaque rôle reçoit ses propres instructions. Ne placez pas de données professeur,
de secret ou de clé API dans ce fichier.

Si vous ajoutez un champ extrait, ajoutez également son type dans
`ExtractionDemande`, son contrôle de provenance dans `valider_extraction` et
un test de valeur valide et inventée. Ajouter uniquement une consigne au prompt
ne suffit pas. Un nouveau ton d'explication doit être ajouté aux valeurs
autorisées du schéma et à `INTRODUCTIONS` avant d'être utilisé.

## Activation et tests

Installez les dépendances existantes de `backend/requirements.txt` puis, depuis
`backend`, définissez `ANTHROPIC_API_KEY` et éventuellement `LIO_LLM_MODEL` dans
l'environnement. Aucun nouveau fournisseur ni dépendance n'est ajouté.
Le nom de modèle par défaut existant est conservé ; sa disponibilité et
l'accès réel à l'API dépendent de votre compte Anthropic.

Sans clé, les parcours utilisent les règles locales. `/api/sante.mode` indique
la configuration, pas le succès du dernier appel : un échec peut déclencher
le repli même si `mode` vaut `llm`.

```bash
python -m pytest tests/test_garde_fous_llm.py
python -m pytest
uvicorn app.main:app --reload --port 8000
```

Ne lancez pas une deuxième API sur le même port si une autre copie tourne déjà.
Les tests emploient des bases temporaires et n'affectent pas les dossiers réels.

Validation locale : 95 tests passent, dont 50 cas nouveaux. Les appels Claude
sont simulés dans ces tests ; aucun appel payant réel n'a été exécuté.

## Limites et règles métier

Les garde-fous réduisent les possibilités d'hallucination ; ils ne certifient
ni l'exactitude du catalogue ni la réalité d'une disponibilité externe.
La note pédagogique 0–3 reste un jugement du LLM et sert uniquement au classement.
Le critère pédagogique du score de confiance est désormais calculé à partir des
thèmes et niveaux du catalogue : changer la note du LLM ne change pas ce score.
Les données historiques et leurs hypothèses restent celles du moteur.

Déclarer plus de 50 élèves n'est pas tronqué silencieusement : le code doit
indiquer le dépassement. Le quota scolaire est élèves + accompagnateurs, cumulé
avec les groupes positionnés, et doit être revérifié côté backend au moment de
pré-réserver. Un prompt ne remplace pas cette règle métier.

Lorsqu'un projet change, le frontend efface ses anciennes recommandations,
comparaisons et propositions sélectionnées. Le backend refuse une pré-réservation
dont la demande diffère de celle de la proposition. La date effectivement stockée
est celle du trajet choisi, y compris pour une alternative. La transaction SQLite
de réservation verrouille la lecture de la jauge et l'insertion des places ; un
test de deux demandes simultanées vérifie qu'une seule est acceptée lorsqu'il
n'y a pas assez de places pour les deux. Les propositions rouges sont refusées.

L'authentification, l'exactitude des sources et l'intégration d'une confirmation
réelle SNCF restent hors du périmètre des garde-fous LLM. Les états de confirmation
existants dans cette démo sont des simulations, pas une connexion au système SNCF.

## Tester depuis l'interface locale

L'instance locale est accessible sur `http://127.0.0.1:5174` avec le backend
sur `http://127.0.0.1:8011`. Le proxy Vite accepte `LIO_API_URL` pour choisir
le backend ; sans variable il utilise le port 8000 comme auparavant.

Depuis une nouvelle sortie, saisir successivement : « Je connais déjà ma
destination », « Arènes de Nîmes », « CM2 », « 55 élèves », « 2 accompagnateurs »,
« ej veux changer le nombre des eleves », « 28 », « 30fervrier 2027 », puis
« 14/11/2026 ». Le dépassement doit être signalé immédiatement, la correction
doit conserver les accompagnateurs et la date impossible doit être refusée.

Les corrections sont déjà appliquées à l'API locale. Sans clé Anthropic, elle
reste en mode `demo` : les tests automatisés couvrent aussi les réponses LLM
simulées, mais ne certifient pas l'accès au fournisseur réel.
