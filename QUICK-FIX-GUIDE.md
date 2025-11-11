# 🚨 Guide de réparation rapide

## Problèmes actuels
- ❌ Le site n'a pas de style (Tailwind CSS ne charge pas)
- ❌ Toutes les clés API fonctionnent (base de données non initialisée)

---

## ✅ Solution complète (1 commande!)

### Sur Linux/Mac:
```bash
chmod +x fix-everything.sh
./fix-everything.sh
```

### Sur Windows:
```cmd
fix-everything.bat
```

**Ce script va:**
1. ✅ Arrêter tous les containers
2. ✅ Démarrer PostgreSQL et Redis
3. ✅ Exécuter les migrations Alembic
4. ✅ Créer un tenant + générer une vraie clé API
5. ✅ Rebuild le frontend sans cache (avec Tailwind)
6. ✅ Redémarrer tous les services

**Durée:** ~3-5 minutes

---

## 🎯 Après l'exécution

1. **Copiez la clé API affichée** (format: `sk_test_...`)
2. **Ouvrez** http://localhost
3. **Videz le cache du navigateur:**
   - Chrome/Edge: `Ctrl+Shift+Delete` → Cocher "Cached images and files" → Clear
   - Ou simplement: `Ctrl+Shift+R` (hard refresh)
4. **Entrez votre clé API**
5. **Profitez du nouveau design!** 🎨

---

## 🎨 Ce que vous devriez voir

### Page de Login:
- ✅ Fond dégradé bleu avec animations
- ✅ Panneau gauche avec logos et features
- ✅ Formulaire blanc élégant avec ombres
- ✅ Icônes et transitions fluides

### Dashboard:
- ✅ Cartes avec statistiques
- ✅ Barres de progression colorées
- ✅ Liste des projets récents
- ✅ Alertes de quotas

---

## 🐛 Dépannage

### Le style ne s'affiche toujours pas

**1. Vérifiez que le frontend est bien rebuilt:**
```bash
docker images | grep frontend
```
La date de création doit être récente (quelques minutes).

**2. Vérifiez les logs du frontend:**
```bash
docker compose logs frontend
```

Vous devriez voir:
```
frontend-1  | VITE v5.x.x  ready in XXX ms
frontend-1  | ➜  Local:   http://localhost:5173/
```

**3. Videz COMPLÈTEMENT le cache:**
- Ouvrir DevTools (F12)
- Onglet "Network"
- Cocher "Disable cache"
- Rafraîchir avec `Ctrl+Shift+R`

**4. Rebuild manuel si nécessaire:**
```bash
docker compose down
docker rmi seo-tools-frontend:latest  # Supprimer l'image
docker compose build --no-cache frontend
docker compose up -d
```

---

### La clé API ne fonctionne toujours pas

**1. Vérifiez que bootstrap.py a bien créé la clé:**
```bash
docker compose exec postgres psql -U seouser -d seosaas -c "SELECT id, key_prefix, name, is_active FROM api_keys;"
```

Vous devriez voir:
```
 id | key_prefix |     name      | is_active
----+------------+---------------+-----------
  1 | sk_test_ | Bootstrap Key |     t
```

**2. Si vide, relancez bootstrap:**
```bash
docker compose exec backend python scripts/bootstrap.py
```

**3. Testez la clé directement:**
```bash
curl -H "X-API-Key: VOTRE_CLE" http://localhost:8000/api/v1/usage/quota
```

Devrait retourner un JSON avec vos quotas.

---

## 📋 Commandes utiles

### Voir les logs en temps réel:
```bash
docker compose logs -f frontend backend
```

### Redémarrer juste le frontend:
```bash
docker compose restart frontend
```

### Vérifier l'état des services:
```bash
docker compose ps
```

### Entrer dans le container backend:
```bash
docker compose exec backend bash
```

### Vérifier la base de données:
```bash
docker compose exec postgres psql -U seouser -d seosaas
```

---

## 🎯 Checklist de vérification

Après avoir exécuté `fix-everything.sh`, vérifiez:

- [ ] Le script a affiché une clé API (format: `sk_test_...`)
- [ ] Vous avez copié cette clé
- [ ] `docker compose ps` montre tous les services "Up"
- [ ] `http://localhost` affiche la page de login stylée
- [ ] Le cache du navigateur est vidé
- [ ] Vous pouvez vous connecter avec la clé
- [ ] Le dashboard affiche des cartes colorées

Si tous les points sont cochés, c'est bon! ✅

---

## 🆘 Toujours des problèmes?

### Option nucléaire (reset complet):

```bash
# ATTENTION: Efface TOUTES les données!
docker compose down -v  # Supprime aussi les volumes
docker system prune -a  # Nettoie tout Docker
./fix-everything.sh     # Recommence à zéro
```

Cela va:
- ⚠️ Supprimer TOUTES les données (projets, crawls, etc.)
- ⚠️ Supprimer toutes les images Docker
- ✅ Garantir un environnement propre

---

## 📞 Aide supplémentaire

Si rien ne fonctionne, partagez les logs:
```bash
docker compose logs frontend > frontend-logs.txt
docker compose logs backend > backend-logs.txt
```

Et vérifiez:
- Version de Docker: `docker --version`
- Version de Docker Compose: `docker compose version`
- Espace disque: `df -h`
