# Copilote local avec Ollama

Le projet utilise l’installation Ollama présente sur cet ordinateur et le modèle `mistral:latest` déjà téléchargé. Les échanges restent sur le serveur local `127.0.0.1:11434`. Aucune clé API n’est nécessaire.

La configuration se trouve dans `.env.local`, exclu de Git :

```ini
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=mistral:latest
```

Ouvrir Ollama avant de lancer le projet avec `node scripts/dev.mjs`. `ollama list` affiche les modèles disponibles. Pour changer de modèle, modifier `OLLAMA_MODEL` puis redémarrer le backend. La première réponse peut être plus lente pendant le chargement en mémoire.

Le copilote reçoit les douze derniers messages et les informations connues. Il renvoie un JSON contenant les corrections et une réponse conversationnelle. Les corrections sont validées par Pydantic. Une demande ambiguë comme « je veux changer ça » conserve le projet et demande quel élément modifier. Le LLM ne calcule aucun horaire ferroviaire, disponibilité ou score : ces résultats restent calculés par le moteur Python.

Si Ollama échoue ou renvoie des champs invalides, le serveur conserve l’extraction locale et signale le repli dans la réponse. Le timeout Ollama est de 180 secondes ; le proxy attend au maximum 195 secondes pour une conversation.

API utilisée : https://docs.ollama.com/api/chat
