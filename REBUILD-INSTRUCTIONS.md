# Comment voir les modifications du frontend

## Méthode rapide (Script automatique)

### Sur Linux/Mac:
```bash
./rebuild-frontend.sh
```

### Sur Windows:
```cmd
rebuild-frontend.bat
```

---

## Méthode manuelle (étape par étape)

### 1. Arrêter tous les containers
```bash
docker compose down
```

### 2. Supprimer les images du frontend (force un rebuild complet)
```bash
docker rmi seosaas-frontend:latest
# ou
docker rmi seo-tools-frontend:latest
```

### 3. Rebuild sans cache
```bash
docker compose build --no-cache frontend
```

### 4. Redémarrer tous les services
```bash
docker compose up -d
```

### 5. Vérifier les logs
```bash
# Logs du frontend
docker compose logs -f frontend

# Logs du backend
docker compose logs -f backend
```

---

## Vider le cache du navigateur

**Chrome/Edge:**
- `Ctrl+Shift+R` (Windows/Linux)
- `Cmd+Shift+R` (Mac)

**Firefox:**
- `Ctrl+F5` (Windows/Linux)
- `Cmd+Shift+R` (Mac)

**Ou manuellement:**
1. Ouvrir les DevTools (F12)
2. Clic droit sur le bouton Refresh
3. Sélectionner "Empty Cache and Hard Reload"

---

## Vérifier que ça marche

1. Ouvrir `http://localhost` dans votre navigateur
2. Vérifier la console du navigateur (F12) - il ne devrait pas y avoir d'erreurs rouges
3. Essayer de naviguer:
   - Login avec votre API key
   - Dashboard devrait se charger sans erreur
   - Aller sur la page Projects
   - Aller sur la page Usage

---

## Debugging

### Si vous voyez toujours des erreurs:

**1. Vérifier que le frontend est bien rebuild:**
```bash
docker images | grep frontend
```
La date de création devrait être récente.

**2. Vérifier les logs du frontend:**
```bash
docker compose logs frontend
```

**3. Vérifier les logs du backend:**
```bash
docker compose logs backend
```

**4. Tester l'API directement:**
```bash
curl http://localhost:8000/api/v1/health
```

**5. Rebuild TOUT sans cache (nucléaire):**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Modifications apportées

Les fichiers suivants ont été modifiés avec une meilleure gestion des erreurs:

- ✅ `frontend/src/pages/Dashboard.tsx` - Safe fallback pour quota.current_usage
- ✅ `frontend/src/pages/Projects.tsx` - Ajout barre de recherche + gestion erreurs
- ✅ `frontend/src/pages/Usage.tsx` - Safe fallback pour quota.remaining
- ✅ `frontend/src/pages/ProjectDetail.tsx` - Meilleure gestion des erreurs

**Problème résolu:**
```
TypeError: Cannot read properties of undefined (reading 'total_api_calls')
```

Toutes les pages utilisent maintenant des valeurs par défaut si les données sont undefined.
