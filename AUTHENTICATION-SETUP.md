# 🔐 Configuration de l'authentification

## ⚠️ Problème actuel

**Si toutes les clés API permettent de se connecter**, c'est que la base de données n'est PAS initialisée.

---

## ✅ Solution: Initialiser la base de données

### Étape 1: Vérifier que les services tournent

```bash
docker compose ps
```

Vous devez voir:
- `backend` - Running
- `postgres` - Running
- `redis` - Running
- `frontend` - Running

---

### Étape 2: Exécuter le script d'initialisation

```bash
# Entrer dans le container backend
docker compose exec backend bash

# Exécuter le script bootstrap
python scripts/bootstrap.py

# Sortir du container
exit
```

**Ce script va:**
1. ✅ Créer l'extension pgvector dans PostgreSQL
2. ✅ Créer toutes les tables de la base de données
3. ✅ Créer un tenant par défaut "Default Organization" (plan Pro)
4. ✅ Générer UNE clé API valide
5. ✅ Afficher cette clé (à sauvegarder immédiatement!)

---

### Étape 3: Sauvegarder votre clé API

Le script va afficher quelque chose comme:

```
🎉 SETUP COMPLETE!
==================================================

📝 Your API Key (save this, it won't be shown again!):

    sk_test_a1b2c3d4e5f6789...

==================================================
```

**⚠️ IMPORTANT:**
- Cette clé ne sera JAMAIS ré-affichée
- Copiez-la dans un endroit sûr
- Vous en aurez besoin pour vous connecter au frontend

---

## 🔒 Comment fonctionne la sécurité

### Architecture de l'authentification

```
┌─────────────┐                    ┌──────────────┐
│   Frontend  │                    │   Backend    │
│             │                    │              │
│ 1. User     │  ─── X-API-Key ──▶│ 2. Hash key  │
│    enters   │      (header)      │    with      │
│    API key  │                    │    SHA256    │
│             │                    │              │
│             │                    │ 3. Lookup    │
│             │                    │    hash in   │
│             │                    │    database  │
│             │                    │              │
│             │  ◀── 200 OK ──────│ 4. Return    │
│             │     or 401 Unauthorized│ tenant   │
│             │                    │    info      │
└─────────────┘                    └──────────────┘
```

### Processus de validation

1. **Stockage** (backend/app/core/security.py:36)
   ```python
   def hash_api_key(api_key: str) -> str:
       return hashlib.sha256(api_key.encode()).hexdigest()
   ```
   - La clé brute n'est JAMAIS stockée en DB
   - Seul le hash SHA256 est sauvegardé
   - Comme les mots de passe hashés

2. **Vérification** (backend/app/core/security.py:129)
   ```python
   async def verify_api_key(api_key: str, db: AsyncSession):
       key_hash = hash_api_key(api_key)
       result = await db.execute(
           select(APIKey).where(APIKey.key_hash == key_hash)
       )
       api_key_obj = result.scalar_one_or_none()

       if not api_key_obj or not api_key_obj.is_valid:
           raise HTTPException(status_code=401, detail="Invalid API key")
   ```

3. **Frontend** (frontend/src/pages/Login.tsx)
   ```typescript
   api.setApiKey(apiKey);  // Stocke en localStorage
   await api.getQuota();   // Teste la validité
   ```

---

## 🎯 Quota du tenant par défaut

Le tenant créé par `bootstrap.py` a les quotas suivants:

- **Plan**: Pro
- **Projets max**: 50
- **Pages par crawl**: 10,000
- **Appels API par mois**: 100,000
- **Scopes**: `read,write,admin` (tous les droits)

---

## 🔧 Dépannage

### Erreur: "API key required"
➜ Vous n'avez pas fourni de clé ou elle est vide

### Erreur: "Invalid API key"
➜ La clé n'existe pas en base de données (pas de hash correspondant)

### Erreur: "API key is inactive or expired"
➜ La clé existe mais `is_active=false` ou expirée

### Toutes les clés fonctionnent
➜ Le script `bootstrap.py` n'a pas été exécuté
➜ Aucune clé valide n'existe en DB

---

## 🚀 Prochaines étapes

1. ✅ Exécuter `python scripts/bootstrap.py`
2. ✅ Copier la clé API générée
3. ✅ Rebuild le frontend: `./rebuild-frontend.sh`
4. ✅ Ouvrir `http://localhost`
5. ✅ Entrer votre clé API
6. ✅ Accéder au dashboard!

---

## 🔑 Gérer plusieurs clés API

Pour créer d'autres clés API:

```bash
# Via l'API (nécessite une clé admin existante)
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "X-API-Key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My New Key",
    "scopes": "read,write",
    "expires_at": null
  }'
```

Ou créez un script Python pour gérer les clés.

---

## 📊 Vérifier l'état de la DB

```bash
# Entrer dans le container postgres
docker compose exec postgres psql -U seouser -d seosaas

# Voir les tenants
SELECT id, name, slug, plan, is_active FROM tenants;

# Voir les clés API (hashes uniquement)
SELECT id, tenant_id, key_prefix, name, scopes, is_active
FROM api_keys;

# Sortir
\q
```
