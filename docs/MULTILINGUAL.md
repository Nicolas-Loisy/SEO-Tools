# Support Multilingue / Multilingual Support

## 🌍 Langues Supportées / Supported Languages

Le SEO SaaS Tool supporte nativement le **français** et l'**anglais**, ainsi que **50+ autres langues**.

The SEO SaaS Tool natively supports **French** and **English**, as well as **50+ other languages**.

### Langues principales / Main languages:
- 🇫🇷 Français (French)
- 🇬🇧 English
- 🇪🇸 Español (Spanish)
- 🇩🇪 Deutsch (German)
- 🇮🇹 Italiano (Italian)
- 🇵🇹 Português (Portuguese)
- 🇳🇱 Nederlands (Dutch)
- 🇵🇱 Polski (Polish)
- 🇷🇺 Русский (Russian)
- 🇨🇳 中文 (Chinese)
- 🇯🇵 日本語 (Japanese)
- Et plus encore / And many more...

## 🔧 Fonctionnalités Multilingues / Multilingual Features

### 1. Détection Automatique de Langue / Automatic Language Detection

Le crawler détecte automatiquement la langue du contenu :

The crawler automatically detects content language:

```python
# Automatique depuis l'attribut HTML
# Automatic from HTML attribute
<html lang="fr">  # → Détecté comme "fr"

# Ou détection automatique du contenu
# Or automatic content detection
"Bonjour le monde"  # → Détecté comme "fr"
"Hello world"       # → Détecté comme "en"
```

### 2. Embeddings Sémantiques Multilingues / Multilingual Semantic Embeddings

Modèle par défaut : **paraphrase-multilingual-MiniLM-L12-v2**

Default model: **paraphrase-multilingual-MiniLM-L12-v2**

```python
from app.services.nlp import get_embedding_service

# Modèle multilingue (par défaut)
# Multilingual model (default)
service = get_embedding_service("multilingual")

# Générer des embeddings pour n'importe quelle langue
# Generate embeddings for any language
embedding_fr = service.generate_embedding("Ceci est un texte en français")
embedding_en = service.generate_embedding("This is an English text")

# Les embeddings sont dans le même espace vectoriel !
# Embeddings are in the same vector space!
similarity = service.compute_similarity(embedding_fr, embedding_en)
```

### 3. Analyse de Texte Multilingue / Multilingual Text Analysis

#### Extraction de mots-clés / Keyword Extraction

```python
from app.services.nlp import extract_keywords

# Français
mots_cles_fr = extract_keywords(
    "Le référencement naturel améliore la visibilité",
    language="fr",
    top_n=5
)
# → ["référencement", "naturel", "améliore", "visibilité"]

# English
keywords_en = extract_keywords(
    "Search engine optimization improves visibility",
    language="en",
    top_n=5
)
# → ["search", "engine", "optimization", "improves", "visibility"]
```

#### Score de Lisibilité / Readability Score

```python
from app.services.nlp import calculate_readability_score

# Français (Flesch-Vacca)
score_fr = calculate_readability_score(
    "Le texte est facile à lire.",
    language="fr"
)

# English (Flesch Reading Ease)
score_en = calculate_readability_score(
    "The text is easy to read.",
    language="en"
)
```

## 🚀 Utilisation / Usage

### Via API

#### Créer un projet multilingue / Create a multilingual project

```bash
# Site en français
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mon Site Web FR",
    "domain": "https://mon-site.fr"
  }'

# English site
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My EN Website",
    "domain": "https://my-site.com"
  }'
```

#### Générer des embeddings multilingues / Generate multilingual embeddings

```bash
# Le système détecte automatiquement la langue
# The system automatically detects the language
curl -X POST \
  -H "X-API-Key: YOUR_KEY" \
  http://localhost:8000/api/v1/analysis/projects/1/embeddings
```

#### Trouver des pages similaires (cross-language) / Find similar pages

Les embeddings multilingues permettent de trouver des pages similaires **même dans différentes langues** !

Multilingual embeddings allow finding similar pages **even across languages**!

```bash
# Trouve des pages similaires en français OU en anglais
# Finds similar pages in French OR English
curl -H "X-API-Key: YOUR_KEY" \
  "http://localhost:8000/api/v1/analysis/projects/1/similar-pages/1"
```

### Via Python

```python
import requests

API_KEY = "sk_test_..."
BASE_URL = "http://localhost:8000/api/v1"

headers = {"X-API-Key": API_KEY}

# Créer un projet français
response = requests.post(
    f"{BASE_URL}/projects/",
    headers=headers,
    json={
        "name": "Site Multilingue",
        "domain": "https://example.fr",
    }
)

project_id = response.json()["id"]

# Lancer un crawl
requests.post(
    f"{BASE_URL}/crawl/",
    headers=headers,
    json={"project_id": project_id, "mode": "fast"}
)

# Générer les embeddings (multilingues automatiquement)
requests.post(
    f"{BASE_URL}/analysis/projects/{project_id}/embeddings",
    headers=headers
)
```

## 🔍 Stop Words

Les stop words (mots vides) sont gérés pour chaque langue :

Stop words are handled for each language:

### Français / French
```
le, la, les, un, une, des, de, du, et, ou, mais, dans, avec,
pour, par, sur, à, en, ce, qui, que, dont, où, ...
```

### English
```
the, is, at, which, on, a, an, and, or, but, in, with, to,
for, of, as, by, that, this, it, from, ...
```

## ⚙️ Configuration

### Choisir le Modèle d'Embeddings / Choose Embedding Model

```python
from app.services.nlp import get_embedding_service

# Option 1 : Multilingue rapide (384 dims) - RECOMMANDÉ
# Option 1: Fast multilingual (384 dims) - RECOMMENDED
service = get_embedding_service("multilingual")

# Option 2 : Anglais uniquement (384 dims, plus rapide)
# Option 2: English only (384 dims, faster)
service = get_embedding_service("english")

# Option 3 : Multilingue haute qualité (768 dims, plus lent)
# Option 3: High-quality multilingual (768 dims, slower)
service = get_embedding_service("multilingual-large")
```

### Variables d'Environnement / Environment Variables

```env
# Modèle d'embeddings par défaut
# Default embedding model
EMBEDDING_MODEL=multilingual  # multilingual | english | multilingual-large

# Langues supportées (pour validation)
# Supported languages (for validation)
SUPPORTED_LANGUAGES=en,fr,es,de,it,pt,nl,pl,ru,zh,ja
```

## 📊 Performance

### Modèles Disponibles / Available Models

| Modèle / Model | Langues | Dimensions | Vitesse / Speed | Qualité / Quality |
|----------------|---------|------------|-----------------|-------------------|
| `multilingual` | 50+ | 384 | ⚡ Rapide / Fast | ⭐⭐⭐⭐ Excellente |
| `english` | 1 (EN) | 384 | ⚡⚡ Très rapide | ⭐⭐⭐⭐ Excellente |
| `multilingual-large` | 50+ | 768 | 🐢 Lent / Slow | ⭐⭐⭐⭐⭐ Meilleure |

### Recommandations / Recommendations

- **Sites français/anglais mixtes**: Utilisez `multilingual` (défaut)
- **Mixed French/English sites**: Use `multilingual` (default)

- **Sites anglais uniquement**: Utilisez `english` pour un gain de performance
- **English-only sites**: Use `english` for performance gain

- **Meilleure qualité**: Utilisez `multilingual-large` (2x plus lent)
- **Best quality**: Use `multilingual-large` (2x slower)

## 🧪 Tests

### Tester la Détection de Langue / Test Language Detection

```python
from app.services.nlp import detect_language

# Français
assert detect_language("Bonjour le monde") == "fr"

# English
assert detect_language("Hello world") == "en"

# Espagnol
assert detect_language("Hola mundo") == "es"
```

### Tester les Embeddings Cross-Langue / Test Cross-Language Embeddings

```python
from app.services.nlp import get_embedding_service

service = get_embedding_service("multilingual")

# Textes similaires dans différentes langues
# Similar texts in different languages
emb_fr = service.generate_embedding("référencement naturel")
emb_en = service.generate_embedding("search engine optimization")

# Devrait avoir une similarité élevée (> 0.5)
# Should have high similarity (> 0.5)
similarity = service.compute_similarity(emb_fr, emb_en)
print(f"Similarité cross-langue : {similarity}")
```

## 🐛 Troubleshooting

### La langue n'est pas détectée correctement

**Problème**: Le système détecte mal la langue du contenu.

**Solution**:
1. Vérifier que le contenu a au moins 20 caractères
2. Ajouter l'attribut `lang` dans le HTML : `<html lang="fr">`
3. Vérifier que le texte contient suffisamment de mots

### Language is not detected correctly

**Issue**: The system incorrectly detects content language.

**Solution**:
1. Ensure content has at least 20 characters
2. Add `lang` attribute in HTML: `<html lang="en">`
3. Check that text contains enough words

### Les embeddings ne fonctionnent pas bien

**Problème**: Les similarités entre pages sont incohérentes.

**Solution**:
1. Vérifier que vous utilisez le modèle `multilingual`
2. Régénérer tous les embeddings : `POST /analysis/projects/{id}/embeddings`
3. Attendre la fin du traitement batch

### Embeddings don't work well

**Issue**: Similarities between pages are inconsistent.

**Solution**:
1. Verify you're using the `multilingual` model
2. Regenerate all embeddings: `POST /analysis/projects/{id}/embeddings`
3. Wait for batch processing to complete

## 📚 Ressources / Resources

- [sentence-transformers Documentation](https://www.sbert.net/)
- [Modèle Multilingual-MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
- [langdetect Library](https://pypi.org/project/langdetect/)

## ✨ Exemples Complets / Complete Examples

Voir `/docs/examples/` pour des exemples complets en français et anglais.

See `/docs/examples/` for complete examples in French and English.
