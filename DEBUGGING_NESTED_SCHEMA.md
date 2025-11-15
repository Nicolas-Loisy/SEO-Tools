# Debugging Nested Schema Levels

## Le Problème

Quand vous cliquez sur "Enhance with AI" dans l'interface de génération de JSON-LD, des niveaux `"schema"` imbriqués apparaissent :

```json
{
  "schema": {
    "schema": {
      "@context": "https://schema.org",
      "@type": "WebSite",
      ...
    }
  }
}
```

Au lieu du format correct :

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  ...
}
```

## Les Solutions Mises en Place

### 1. Fonction de Nettoyage Récursive
`_unwrap_nested_schema()` dans `/backend/app/services/schema_enhancer.py:135-147`

Cette fonction nettoie récursivement TOUS les niveaux `"schema"` incorrects, même s'il y en a 3, 4, 5...

### 2. Nettoyage en Entrée
Ligne 241 de `schema_enhancer.py` : Le schema est nettoyé AVANT d'être envoyé au LLM

### 3. Nettoyage en Sortie
Ligne 202 de `schema_enhancer.py` : Le schema reçu du LLM est nettoyé AVANT d'être retourné

### 4. Double Vérification dans l'API
Ligne 780 de `/backend/app/api/v1/endpoints/analysis.py` : Un second nettoyage est appliqué avant de retourner au frontend

### 5. Prompt LLM Ultra-Explicite
Ligne 272-320 de `schema_enhancer.py` : Le prompt contient maintenant :
- ✅ Un exemple CORRECT du format attendu
- ⚠️ Deux exemples WRONG montrant ce qu'il NE FAUT PAS faire
- 5 règles obligatoires claires

### 6. Logging Complet
Des logs détaillés permettent de tracer exactement où le problème se produit :

```
[API enhance] Input schema keys: [...]
[API enhance] Input has nested schema: True/False
[SchemaEnhancer] Raw LLM response length: 1234
[Parser] Parsed JSON successfully, top-level keys: [...]
[Parser] WARNING: Found nested 'schema' key, unwrapping...
[API enhance] Output has nested schema: True/False
```

## Comment Vérifier si le Fix Fonctionne

### 1. Redémarrez le Backend

```bash
cd /home/user/SEO-Tools/backend
# Arrêtez l'application si elle tourne
# Redémarrez-la (docker-compose, uvicorn, etc.)
```

### 2. Testez l'Enhancement

1. Générez un schema initial pour une page
2. Cliquez sur "Enhance with AI"
3. Regardez les logs du backend dans la console

### 3. Analysez les Logs

Vous devriez voir :

```
[API enhance] Input schema keys: ['@context', '@type', 'name', ...]
[API enhance] Input has nested schema: False  <-- Doit être False !
[SchemaEnhancer] Raw LLM response length: 1523
[Parser] Parsed JSON successfully, top-level keys: ['enhanced_schema', 'improvements', 'recommendations']
[Parser] Extracted enhanced_schema, keys: ['@context', '@type', ...]
```

**Si vous voyez :**
```
[Parser] WARNING: Found nested 'schema' key, unwrapping...
```

Cela signifie que le LLM retourne ENCORE une mauvaise structure malgré nos instructions. Dans ce cas :

### 4. Solutions si le Bug Persiste

#### Option A: Vérifier la Clé API
Le modèle OpenAI utilisé peut ne pas bien suivre les instructions. Vérifiez :
- Que `OPENAI_API_KEY` est bien configurée
- Quel modèle est utilisé (GPT-3.5-turbo vs GPT-4)

#### Option B: Forcer un Modèle Plus Performant
Dans `/backend/app/services/llm_adapter.py`, ligne 118, changez le modèle par défaut :

```python
if model is None:
    # Forcer GPT-4 qui suit mieux les instructions
    model = "gpt-4"  # Au lieu de models[0]
```

#### Option C: Vérifier les Modèles Disponibles
```python
from app.services.llm import LLMFactory
print(LLMFactory.get_provider_models("openai"))
```

## Structure du Flux de Données

1. **Frontend génère un schema** → `POST /schema/generate`
   - Retour : `{"schema": {...JSON-LD...}, "html": "..."}`

2. **Frontend clique "Enhance"** → `POST /schema/enhance` avec body `{"schema": {...JSON-LD...}}`
   - FastAPI extrait le paramètre `schema` du body
   - `schema` = le JSON-LD direct (ex: `{"@context": "...", "@type": "WebSite"}`)

3. **Backend nettoie l'entrée**
   - `_unwrap_nested_schema(schema)` au cas où

4. **Backend appelle le LLM**
   - Prompt ultra-explicite avec exemples WRONG/CORRECT

5. **Backend parse la réponse**
   - Extrait `enhanced_schema` du JSON retourné
   - `_unwrap_nested_schema(enhanced_schema)`

6. **Backend double-check avant retour**
   - Encore un `_unwrap_nested_schema()` dans l'API endpoint

7. **Frontend reçoit**
   - `{"enhanced_schema": {...JSON-LD propre...}, "improvements": [...], ...}`

## Tests Automatiques

Exécutez le test pour vérifier que l'unwrap fonctionne :

```bash
cd /home/user/SEO-Tools
python test_schema_unwrap.py
```

Tous les tests doivent passer ✅

## En Cas d'Échec

Si après toutes ces modifications le bug persiste :

1. **Capturez les logs complets** lors d'un appel à enhance
2. **Vérifiez la réponse brute du LLM** dans `[SchemaEnhancer] Response preview`
3. **Partagez ces logs** pour analyse approfondie

Le problème viendrait alors probablement de :
- La configuration du provider LLM
- Le modèle utilisé qui ne suit pas les instructions
- Un problème réseau/API qui corrompt la réponse

## Résumé des Fichiers Modifiés

- ✅ `/backend/app/services/llm_adapter.py` - Wrapper LLM créé
- ✅ `/backend/app/services/schema_enhancer.py` - Prompt amélioré + unwrap + logs
- ✅ `/backend/app/api/v1/endpoints/analysis.py` - Double unwrap + logs
- ✅ `/test_schema_unwrap.py` - Suite de tests

Tous les changements sont sur la branche `claude/fix-missing-llm-adapter-011s1zqRJp1uJnAnzuzb6YWj`.
