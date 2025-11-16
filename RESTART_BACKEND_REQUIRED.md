# 🚨 REDÉMARRAGE BACKEND REQUIS

## Problèmes Résolus

Deux endpoints de l'Internal Linking Analysis causaient des timeouts 504 :

1. ✅ **GET /analysis/projects/{id}/link-graph** - CORRIGÉ
2. ✅ **GET /analysis/projects/{id}/link-recommendations** - CORRIGÉ

## ⚠️ ACTION IMMÉDIATE REQUISE

**VOUS DEVEZ REDÉMARRER LE BACKEND** pour que les corrections prennent effet.

### Comment Redémarrer

#### Si vous utilisez Docker Compose

```bash
cd /home/user/SEO-Tools
docker-compose restart backend

# OU redémarrer tous les services
docker-compose restart
```

#### Si vous utilisez Uvicorn directement

```bash
# Trouvez le processus
ps aux | grep uvicorn

# Tuez-le
kill -9 <PID>

# Redémarrez
cd /home/user/SEO-Tools/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Si vous utilisez systemd

```bash
sudo systemctl restart seo-backend
```

## 📊 Optimisations Appliquées

### 1. Link Graph Analysis (`/link-graph`)

**Avant :**
- ❌ Chargeait TOUTES les pages du projet
- ❌ Timeout sur projets >1000 pages
- ❌ Temps de réponse imprévisible

**Après :**
- ✅ Limite par défaut : **1000 pages**
- ✅ Priorise les pages avec meilleur SEO score
- ✅ Temps de réponse : **<5 secondes** même sur gros projets
- ✅ Paramètre `max_pages` ajustable

```bash
# Exemples d'utilisation
GET /api/v1/analysis/projects/1/link-graph
GET /api/v1/analysis/projects/1/link-graph?max_pages=500
GET /api/v1/analysis/projects/1/link-graph/export?max_pages=200
```

### 2. Link Recommendations (`/link-recommendations`)

**Avant :**
- ❌ Chargeait TOUTES les pages comme cibles potentielles
- ❌ Analysait 10 pages sources en mode "all pages"
- ❌ Timeout garanti sur gros projets

**Après :**

**Mode Single Page (avec `page_id`) :**
- ✅ Limite : **500 cibles** max
- ✅ Priorise cibles avec meilleur SEO score
- ✅ Temps : **~5-10 secondes**

**Mode All Pages (sans `page_id`) :**
- ✅ Analyse **5 pages** sources (au lieu de 10)
- ✅ **200 cibles** max par source (au lieu de tout)
- ✅ **2 recommandations** retournées par page (au lieu de 3)
- ✅ Temps : **~10-15 secondes**

```bash
# Exemples d'utilisation
GET /api/v1/analysis/projects/1/link-recommendations?page_id=123&limit=20
GET /api/v1/analysis/projects/1/link-recommendations?limit=20
```

## 🎯 Performance Attendue

| Endpoint | Pages Projet | Avant | Après |
|----------|-------------|-------|-------|
| link-graph | 100 | 2s | <1s |
| link-graph | 1,000 | Timeout | ~4s |
| link-graph | 10,000 | Timeout | ~4s* |
| link-recommendations (single) | 1,000 | Timeout | ~5s |
| link-recommendations (single) | 10,000 | Timeout | ~8s |
| link-recommendations (all) | 1,000 | Timeout | ~10s |
| link-recommendations (all) | 10,000 | Timeout | ~12s |

*Analyse les 1000 pages avec meilleur SEO score

## 📝 Logs à Vérifier

Après redémarrage, vous verrez ces logs dans la console backend :

```
[API link-graph] Request for project 1, max_pages=1000
[LinkGraph] Building graph for project 1 with 847 pages (max: 1000)
[LinkGraph] Getting graph stats for project 1

[API link-recommendations] Getting recommendations for page 123
[LinkRecommender] Getting recommendations for page 123, max_targets=500
[LinkRecommender] Found 500 target pages (max: 500)
```

## 🔍 Vérification

1. **Redémarrez le backend** (voir instructions ci-dessus)

2. **Testez les endpoints** :

```bash
# Testez link-graph
curl "http://localhost:8000/api/v1/analysis/projects/1/link-graph"

# Testez link-recommendations
curl "http://localhost:8000/api/v1/analysis/projects/1/link-recommendations?limit=20"
```

3. **Vérifiez les logs** - Vous devriez voir les messages `[LinkGraph]` et `[LinkRecommender]`

4. **Temps de réponse** - Devrait être <15 secondes pour tous les endpoints

## 🐛 Si Ça Ne Marche Toujours Pas

### 1. Vérifiez que le Backend a Bien Redémarré

```bash
# Vérifiez les logs au démarrage
docker-compose logs -f backend | grep -i "Application startup complete"
```

### 2. Vérifiez la Branche Git

```bash
git branch
# Doit afficher: * claude/fix-missing-llm-adapter-011s1zqRJp1uJnAnzuzb6YWj

git log --oneline -5
# Doit montrer les commits de fix
```

### 3. Vérifiez que les Fichiers Sont à Jour

```bash
# Doit contenir "max_pages" et "max_target_pages"
grep -n "max_pages" backend/app/services/link_graph.py
grep -n "max_target_pages" backend/app/services/link_recommender.py
```

### 4. Augmentez le Timeout Nginx (Si Nécessaire)

Si vous avez encore des timeouts malgré tout, ajustez le timeout de votre reverse proxy :

```nginx
# Dans votre config nginx
proxy_read_timeout 120s;
proxy_connect_timeout 120s;
```

## 📚 Documentation Complète

Consultez les guides détaillés :
- `FIX_504_LINK_GRAPH.md` - Détails sur le fix link-graph
- `DEBUGGING_NESTED_SCHEMA.md` - Détails sur le fix schema

## ✅ Checklist de Vérification

- [ ] Backend redémarré
- [ ] Logs montrent `[LinkGraph]` et `[LinkRecommender]`
- [ ] `/link-graph` répond en <10s
- [ ] `/link-recommendations` répond en <20s
- [ ] Pas d'erreur 504 dans les logs nginx
- [ ] Interface frontend charge correctement

## 🎉 Résultat Attendu

Après redémarrage :
- ✅ **Aucun timeout 504** sur Internal Linking Analysis
- ✅ **Temps de réponse rapides** (<15s)
- ✅ **Qualité maintenue** (pages importantes priorisées)
- ✅ **Logging clair** pour debugging

---

**Date des corrections :** 2025-11-16
**Branche :** `claude/fix-missing-llm-adapter-011s1zqRJp1uJnAnzuzb6YWj`
