# 🚀 Guide d'Installation Rapide

**Temps estimé**: 15 minutes

---

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir :

- ✅ **Docker** installé (version 20.10+)
- ✅ **Docker Compose** installé (version 3.8+)
- ✅ **Python** 3.8+ installé
- ✅ **Git** installé
- ✅ Au moins **8GB de RAM** disponible
- ✅ Au moins **20GB d'espace disque** libre

### Vérifier les installations

```bash
# Docker
docker --version
# Docker version 20.10.x

# Docker Compose
docker compose version
# Docker Compose version v2.x.x

# Python
python --version
# Python 3.8+

# Git
git --version
# git version 2.x.x
```

---

## 📥 Étape 1 : Cloner le Projet

```bash
# Cloner le repository
git clone <votre-repo-url>

# Naviguer dans le dossier
cd FinalFinal
```

---

## 🐳 Étape 2 : Démarrer les Services Docker

```bash
# Démarrer MongoDB, Elasticsearch et Kibana
docker compose up -d

# Vérifier que les services sont lancés
docker ps
```

Vous devriez voir 3 containers en cours d'exécution :
- `mongodb`
- `elasticsearch`
- `kibana`

---

## ⏳ Étape 3 : Attendre l'Initialisation

Les services prennent environ **30-60 secondes** pour démarrer complètement.

```bash
# Attendre 30 secondes
sleep 30

# Vérifier Elasticsearch
curl http://localhost:9200/_cluster/health

# Vérifier Kibana (devrait retourner 200 OK)
curl -I http://localhost:5601/api/status
```

---

## 🔑 Étape 4 : Initialiser les Credentials

```bash
# Exécuter le script d'initialisation Elasticsearch
docker exec elasticsearch bash /usr/local/bin/es-init.sh

# Attendre 10 secondes
sleep 10

# Vérifier que les credentials sont créés
ls credentials/
# elastic_password
# kibana_service_token
```

**Credentials créés** :
- **Username** : `elastic`
- **Password** : `Q*aPCff9cD3Q6WDKjYpR`

---

## 🐍 Étape 5 : Configurer l'Environnement Python

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Télécharger les modèles NLP
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"

# Télécharger les modèles spaCy
python -m spacy download en_core_web_sm
```

---

## 📊 Étape 6 : Exécuter le Pipeline

### Option A : Pipeline Automatique (Recommandé)

```bash
cd ingestion_Layer
./run_pipeline.sh
```

Cette commande exécute automatiquement :
1. Chargement CSV → MongoDB
2. Indexation MongoDB → Elasticsearch
3. Vérification des données

### Option B : Commandes Manuelles

```bash
# 1. Charger les données dans MongoDB
cd ingestion_Layer
python ingest_to_mongo.py --csv-path ../data/clean/enriched_posts.csv

# 2. Indexer dans Elasticsearch
python indexation.py

# 3. Créer le dashboard Kibana
cd ..
python create_kibana_dashboard_v2.py
```

---

## 🎨 Étape 7 : Accéder au Dashboard Kibana

### 1. Ouvrir votre navigateur

Aller à : **http://localhost:5601**

### 2. Se connecter

- **Username** : `elastic`
- **Password** : `Q*aPCff9cD3Q6WDKjYpR`

### 3. Accéder au Dashboard

1. Cliquer sur le menu hamburger (☰) en haut à gauche
2. Aller dans **Analytics** → **Dashboards**
3. Cliquer sur **"📊 Tableau de Bord - Analyse de Harcèlement"**

### 4. Configurer la plage de temps

- En haut à droite, cliquer sur le time picker
- Sélectionner **"Last 1 year"** ou **"Last 15 months"**
- Cliquer sur **"Update"**

---

## ✅ Étape 8 : Vérification

### Vérifier MongoDB

```bash
# Connexion MongoDB
mongo mongodb://localhost:27017/harcelement

# Dans le shell MongoDB
db.posts.count()        # Devrait retourner ~5978
db.enriched.count()     # Devrait retourner ~5978
```

### Vérifier Elasticsearch

```bash
# Compter les documents
curl -u "elastic:Q*aPCff9cD3Q6WDKjYpR" \
  "http://localhost:9200/harcelement_posts/_count"
# {"count":5978,...}

# Récupérer un document exemple
curl -u "elastic:Q*aPCff9cD3Q6WDKjYpR" \
  "http://localhost:9200/harcelement_posts/_search?size=1&pretty"
```

### Vérifier Kibana Dashboard

Dans Kibana, vous devriez voir :
- ✅ Pie chart "Répartition des langues"
- ✅ Pie chart "Répartition des sentiments"
- ✅ Timeline "Évolution temporelle"
- ✅ Table "Contenus les plus négatifs"
- ✅ Filtres interactifs fonctionnels

---

## 🎯 Résumé des URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Elasticsearch** | http://localhost:9200 | elastic / Q*aPCff9cD3Q6WDKjYpR |
| **Kibana** | http://localhost:5601 | elastic / Q*aPCff9cD3Q6WDKjYpR |
| **MongoDB** | mongodb://localhost:27017 | Pas de credentials |

---

## 🔧 Commandes Utiles

### Arrêter les services

```bash
docker compose down
```

### Redémarrer les services

```bash
docker compose restart
```

### Voir les logs

```bash
# Tous les services
docker compose logs -f

# Service spécifique
docker compose logs -f elasticsearch
docker compose logs -f kibana
docker compose logs -f mongodb
```

### Nettoyer complètement

```bash
# Arrêter et supprimer les volumes
docker compose down -v

# Supprimer les credentials
rm -rf credentials/*

# Redémarrer à zéro
docker compose up -d
```

---

## 🐛 Problèmes Courants

### Problème 1 : "Connection refused" Elasticsearch

**Solution** :
```bash
# Attendre plus longtemps
sleep 60

# Vérifier les logs
docker logs elasticsearch

# Redémarrer si nécessaire
docker compose restart elasticsearch
```

### Problème 2 : "No results found" dans Kibana

**Solution** :
1. Ajuster le time picker à "Last 1 year"
2. Rafraîchir l'index pattern
3. Exécuter : `python fix_kibana_dashboard.py`

### Problème 3 : Erreur d'authentification Kibana

**Solution** :
```bash
# Réinitialiser les credentials
docker exec elasticsearch bash /usr/local/bin/es-init.sh

# Redémarrer Kibana
docker compose restart kibana
```

### Problème 4 : Ports déjà utilisés

**Solution** :
```bash
# Vérifier les ports
netstat -tuln | grep -E '9200|5601|27017'

# Arrêter les processus conflictuels
# OU modifier docker-compose.yml pour utiliser d'autres ports
```

### Problème 5 : Mémoire insuffisante

**Solution** :
```bash
# Augmenter la mémoire Docker
# Docker Desktop → Settings → Resources → Memory : 8GB minimum

# Ou réduire la mémoire JVM d'Elasticsearch dans docker-compose.yml
# ES_JAVA_OPTS: -Xms1g -Xmx1g
```

---

## 📚 Documentation Complète

Pour plus de détails, consulter :

- **README.md** : Documentation complète du projet
- **docs/TECHNICAL_DOCUMENTATION.md** : Architecture détaillée
- **docs/LIVRABLES.md** : Liste complète des livrables
- **docs/GUIDE_KIBANA_DASHBOARD.md** : Guide détaillé Kibana
- **docs/SETUP_COMPLETE.md** : Configuration Elasticsearch/Kibana

---

## 🎉 Installation Terminée !

Vous êtes maintenant prêt à :

- ✅ Explorer le dashboard Kibana
- ✅ Analyser les 5,978 documents
- ✅ Créer des requêtes personnalisées
- ✅ Modifier et améliorer le pipeline
- ✅ Exécuter les tests unitaires

**Bon courage avec votre analyse ! 🚀**

---

## 📞 Besoin d'Aide ?

Si vous rencontrez des problèmes :

1. Consulter la section **Troubleshooting** dans README.md
2. Vérifier les logs Docker : `docker compose logs -f`
3. Vérifier le status des services : `docker ps`

---

*Guide d'Installation Rapide v1.0 - Octobre 2025*
