# 🔑 Comment Reset/Regénérer une clé API

## 🚀 **Méthode rapide (RECOMMANDÉE)**

### Linux/Mac:
```bash
chmod +x generate-new-key.sh
./generate-new-key.sh
```

### Windows:
```cmd
generate-new-key.bat
```

Le script va:
1. ✅ Vérifier que le backend tourne
2. ✅ Demander un nom pour la clé
3. ✅ Demander les scopes (read, write, admin)
4. ✅ Générer une nouvelle clé
5. ✅ Afficher la clé **UNE SEULE FOIS**

**⚠️ IMPORTANT:** Copiez la clé immédiatement, elle ne sera plus affichée!

---

## 🔧 **Méthode manuelle**

### Étape 1: Entrer dans le container backend
```bash
docker compose exec backend bash
```

### Étape 2: Lancer le script de génération
```bash
python scripts/generate_key.py
```

### Étape 3: Suivre les instructions
```
Enter a name for this key: Mon nouveau projet
Enter scopes: read,write,admin
```

### Étape 4: Copier la clé affichée
```
📝 Your NEW API Key (save this now!):

    sk_test_a1b2c3d4e5f6789...
```

### Étape 5: Sortir du container
```bash
exit
```

---

## 🗑️ **Désactiver une ancienne clé**

Si vous voulez désactiver une clé (au lieu de la supprimer):

```bash
docker compose exec postgres psql -U seouser -d seosaas
```

```sql
-- Voir toutes les clés
SELECT id, key_prefix, name, scopes, is_active, created_at
FROM api_keys
ORDER BY created_at DESC;

-- Désactiver une clé par son ID
UPDATE api_keys SET is_active = false WHERE id = 1;

-- Vérifier
SELECT id, key_prefix, name, is_active FROM api_keys;

-- Sortir
\q
```

---

## 🔍 **Voir toutes vos clés**

```bash
docker compose exec postgres psql -U seouser -d seosaas -c "
SELECT
    id,
    key_prefix,
    name,
    scopes,
    is_active,
    created_at,
    last_used_at
FROM api_keys
ORDER BY created_at DESC;
"
```

Exemple de sortie:
```
 id | key_prefix  |     name      |    scopes     | is_active |       created_at        |      last_used_at
----+-------------+---------------+---------------+-----------+-------------------------+-------------------------
  2 | sk_test_ | New Key       | read,write    | t         | 2025-11-10 22:00:00    | 2025-11-10 22:05:00
  1 | sk_test_ | Bootstrap Key | read,write,.. | t         | 2025-11-10 20:00:00    | 2025-11-10 21:30:00
```

---

## ❌ **Supprimer une clé définitivement**

**⚠️ ATTENTION:** Cette action est irréversible!

```bash
docker compose exec postgres psql -U seouser -d seosaas
```

```sql
-- Supprimer une clé par son ID
DELETE FROM api_keys WHERE id = 1;

-- Ou supprimer toutes les clés d'un tenant
DELETE FROM api_keys WHERE tenant_id = 1;
```

---

## 🔐 **Comprendre les scopes**

### Scopes disponibles:

- **`read`** - Lecture seule (GET requests)
  - Voir les projets, pages, stats
  - Ne peut PAS modifier

- **`write`** - Lecture + écriture
  - Tout ce que `read` peut faire
  - Créer/modifier projets
  - Lancer des crawls
  - Générer du contenu

- **`admin`** - Accès complet
  - Tout ce que `write` peut faire
  - Gérer les webhooks
  - Modifier les quotas
  - Supprimer des projets

### Exemples de combinaisons:

```bash
# Clé lecture seule (analytics, monitoring)
Scopes: read

# Clé standard (la plupart des cas)
Scopes: read,write

# Clé admin (full access)
Scopes: read,write,admin
```

---

## 🛡️ **Sécurité des clés API**

### Comment c'est stocké:

1. **Clé brute** (ce que vous voyez): `sk_test_a1b2c3d4e5f6...`
2. **Hash en DB**: `9f86d081884c7d659a2feaa0c55ad015a3bf4f1b...`
3. **Impossible** de récupérer la clé brute depuis le hash

C'est comme un mot de passe hashé!

### Vérification:

```python
# Quand vous envoyez votre clé
raw_key = "sk_test_a1b2c3d4..."

# Backend hash la clé
key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

# Compare avec la DB
if api_key_obj.key_hash == key_hash:
    # ✅ Valide!
```

---

## 🔄 **Rotation des clés (Bonnes pratiques)**

### Quand regénérer une clé:

- ✅ La clé a été exposée (commit git, logs, etc.)
- ✅ Un développeur quitte l'équipe
- ✅ Tous les 90 jours (rotation automatique)
- ✅ Après un incident de sécurité

### Comment faire:

1. **Générer** une nouvelle clé
2. **Tester** avec la nouvelle clé
3. **Mettre à jour** tous les services
4. **Désactiver** l'ancienne clé
5. **Attendre 7 jours** (au cas où)
6. **Supprimer** l'ancienne clé

---

## 🆘 **Dépannage**

### Erreur: "No active tenant found"
```bash
# Le tenant n'existe pas, créez-en un
docker compose exec backend python scripts/bootstrap.py
```

### Erreur: "Database session not available"
```bash
# Le backend ne tourne pas
docker compose up -d backend

# Attendre 5 secondes puis réessayer
```

### Ma clé ne marche pas
```bash
# Vérifier que la clé existe et est active
docker compose exec postgres psql -U seouser -d seosaas -c "
SELECT key_prefix, name, is_active
FROM api_keys
WHERE key_prefix LIKE '$(echo YOUR_KEY | cut -c1-8)%';
"

# Si is_active = f (false), la réactiver:
docker compose exec postgres psql -U seouser -d seosaas -c "
UPDATE api_keys
SET is_active = true
WHERE key_prefix = 'sk_test_';
"
```

### Tester une clé directement
```bash
# Remplacer YOUR_KEY par votre clé
curl -H "X-API-Key: YOUR_KEY" http://localhost:3000/api/v1/usage/quota

# Devrait retourner un JSON avec vos quotas
# Si 401 → Clé invalide
# Si 403 → Clé inactive ou expirée
```

---

## 📝 **Résumé rapide**

### Générer une nouvelle clé:
```bash
./generate-new-key.sh
```

### Voir toutes les clés:
```bash
docker compose exec postgres psql -U seouser -d seosaas -c "SELECT * FROM api_keys;"
```

### Désactiver une clé:
```sql
UPDATE api_keys SET is_active = false WHERE id = 1;
```

### Tester une clé:
```bash
curl -H "X-API-Key: YOUR_KEY" http://localhost:3000/api/v1/usage/quota
```

---

**C'est tout!** 🎉

Votre nouvelle clé est prête à être utilisée dans le frontend.
