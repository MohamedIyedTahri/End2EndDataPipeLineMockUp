# Data Ingestion Layer

This directory contains scripts to load data from CSV files into MongoDB and then index it into Elasticsearch.

## 📋 Prerequisites

- MongoDB running on `localhost:27017` (or specify different URI)
- Elasticsearch running on `localhost:9200` (or specify different URI)
- Python packages: `pymongo`, `elasticsearch`, `pandas`

## 🔐 Credentials

**Elasticsearch:**
- Username: `elastic`
- Password: `Q*aPCff9cD3Q6WDKjYpR`
- URL: `http://localhost:9200` (HTTP, not HTTPS)

**MongoDB:**
- No authentication required (default setup)
- URL: `mongodb://localhost:27017/`

## 🚀 Quick Start

### Option 1: Use the Pipeline Script (Recommended)

Run the complete pipeline with default settings:

```bash
./run_pipeline.sh
```

Or specify custom paths:

```bash
./run_pipeline.sh \
  /path/to/data.csv \
  mongodb://localhost:27017/ \
  harcelement \
  enriched \
  http://localhost:9200 \
  harcelement_posts \
  elastic \
  Q*aPCff9cD3Q6WDKjYpR
```

### Option 2: Run Scripts Individually

**Step 1: Load CSV into MongoDB**

```bash
python ingest_to_mongo.py \
  --csv-path ../data/clean/enriched_posts.csv \
  --mongo-uri mongodb://localhost:27017/ \
  --db-name harcelement \
  --collection-name enriched
```

**Step 2: Index MongoDB data into Elasticsearch**

```bash
python indexation.py \
  --mongo-uri mongodb://localhost:27017/ \
  --db harcelement \
  --collection enriched \
  --es-uri http://localhost:9200 \
  --es-index harcelement_posts \
  --es-user elastic \
  --es-password Q*aPCff9cD3Q6WDKjYpR
```

### Option 3: Use Default Values

Both scripts now have sensible defaults, so you can run them without arguments:

```bash
python ingest_to_mongo.py
python indexation.py
```

## 📁 Scripts Overview

### `ingest_to_mongo.py`

Loads CSV data into MongoDB and adds an `Id_Post` field.

**Default values:**
- CSV Path: Prompts user if not provided
- MongoDB URI: `mongodb://localhost:27017/`
- Database: `harcelement`
- Collection: `posts`

**Arguments:**
```bash
--csv-path         Path to CSV file
--mongo-uri        MongoDB connection URI
--db-name          Database name
--collection-name  Collection name
```

### `indexation.py`

Reads data from MongoDB and indexes it into Elasticsearch with transformed schema.

**Default values:**
- MongoDB URI: `mongodb://localhost:27017/`
- Database: `harcelement`
- Collection: `enriched`
- Elasticsearch URI: `http://localhost:9200`
- Index: `harcelement_posts`
- Username: `elastic`
- Password: `Q*aPCff9cD3Q6WDKjYpR`

**Arguments:**
```bash
--mongo-uri       MongoDB connection URI
--db              Database name
--collection      Collection name
--es-uri          Elasticsearch URI (use http:// not https://)
--es-index        Target index name
--es-user         Elasticsearch username
--es-password     Elasticsearch password
--no-verify-ssl   Disable SSL verification (not needed for HTTP)
```

### `run_pipeline.sh`

Automated pipeline that runs both scripts in sequence.

**Usage:**
```bash
./run_pipeline.sh [csv_path] [mongo_uri] [db] [collection] [es_uri] [es_index] [es_user] [es_password]
```

All arguments are optional and will use defaults if not provided.

## 🔍 Verification

**Check MongoDB:**
```bash
mongo mongodb://localhost:27017/harcelement --eval "db.enriched.count()"
```

**Check Elasticsearch:**
```bash
curl -u "elastic:Q*aPCff9cD3Q6WDKjYpR" "http://localhost:9200/harcelement_posts/_count"
```

**Check specific document:**
```bash
curl -u "elastic:Q*aPCff9cD3Q6WDKjYpR" "http://localhost:9200/harcelement_posts/_search?size=1&pretty"
```

## 📊 Data Schema

### MongoDB Schema (Input)
- `Text`: Post content
- `Language`: Detected language
- `Sentiment_Ensemble_Label`: Sentiment classification
- `Sentiment_Ensemble_Score`: Confidence score
- Other fields from CSV...

### Elasticsearch Schema (Output)
```json
{
  "titre": "text",           // Generic title (placeholder)
  "contenu": "text",         // Post content (from Text field)
  "auteur": "keyword",       // Author (placeholder: "anonyme")
  "date": "date",           // Random date within past year
  "URL": "keyword",         // URL (placeholder)
  "langue": "keyword",      // Language code
  "sentiment": "keyword",   // Sentiment label
  "score": "float"          // Sentiment confidence score
}
```

## 🐛 Troubleshooting

### Error: Connection refused (Elasticsearch)

Make sure Elasticsearch is running and you're using HTTP (not HTTPS):
```bash
docker ps | grep elasticsearch
curl http://localhost:9200
```

### Error: Connection refused (MongoDB)

Make sure MongoDB is running:
```bash
docker ps | grep mongo
mongo mongodb://localhost:27017/ --eval "db.version()"
```

### Error: Authentication failed

Verify credentials:
```bash
curl -u "elastic:Q*aPCff9cD3Q6WDKjYpR" http://localhost:9200
```

### Error: Index already exists

Delete and recreate:
```bash
curl -X DELETE -u "elastic:Q*aPCff9cD3Q6WDKjYpR" "http://localhost:9200/harcelement_posts"
python indexation.py
```

## 📈 Performance Tips

1. **Bulk Size**: The scripts use Elasticsearch's bulk API for efficient indexing
2. **Batch Processing**: For very large datasets, consider processing in batches
3. **MongoDB Indexes**: Create indexes on frequently queried fields
4. **Connection Pooling**: Both scripts reuse connections efficiently

## ✅ Success!

After running the pipeline, you should see:
- ✅ CSV data loaded into MongoDB
- ✅ Data indexed in Elasticsearch
- ✅ Data visible in Kibana at http://localhost:5601

Now you can create visualizations and dashboards in Kibana!
