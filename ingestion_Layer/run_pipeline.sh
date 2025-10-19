#!/bin/bash

# Data Ingestion Pipeline
# This script runs the complete data ingestion from CSV -> MongoDB -> Elasticsearch

set -e  # Exit on error

echo "=========================================="
echo "  Data Ingestion Pipeline"
echo "=========================================="
echo ""

# Default values
CSV_PATH="${1:-../data/clean/enriched_posts.csv}"
MONGO_URI="${2:-mongodb://localhost:27017/}"
MONGO_DB="${3:-harcelement}"
MONGO_COLLECTION="${4:-enriched}"
ES_URI="${5:-http://localhost:9200}"
ES_INDEX="${6:-harcelement_posts}"
ES_USER="${7:-elastic}"
ES_PASSWORD="${8:-Q*aPCff9cD3Q6WDKjYpR}"

echo "Configuration:"
echo "  CSV Path: $CSV_PATH"
echo "  MongoDB: $MONGO_URI -> $MONGO_DB.$MONGO_COLLECTION"
echo "  Elasticsearch: $ES_URI -> $ES_INDEX"
echo ""

# Step 1: Load CSV into MongoDB
echo "Step 1/2: Loading CSV into MongoDB..."
python ingest_to_mongo.py \
  --csv-path "$CSV_PATH" \
  --mongo-uri "$MONGO_URI" \
  --db-name "$MONGO_DB" \
  --collection-name "$MONGO_COLLECTION"

if [ $? -ne 0 ]; then
  echo "❌ Error loading data into MongoDB"
  exit 1
fi

echo ""

# Step 2: Index MongoDB data into Elasticsearch
echo "Step 2/2: Indexing MongoDB data into Elasticsearch..."
python indexation.py \
  --mongo-uri "$MONGO_URI" \
  --db "$MONGO_DB" \
  --collection "$MONGO_COLLECTION" \
  --es-uri "$ES_URI" \
  --es-index "$ES_INDEX" \
  --es-user "$ES_USER" \
  --es-password "$ES_PASSWORD"

if [ $? -ne 0 ]; then
  echo "❌ Error indexing data into Elasticsearch"
  exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ Pipeline Complete!"
echo "=========================================="
echo ""

# Verify the data
echo "Verification:"
echo -n "  MongoDB documents: "
mongo_count=$(mongo "$MONGO_URI$MONGO_DB" --quiet --eval "db.$MONGO_COLLECTION.count()" 2>/dev/null || echo "Unable to count")
echo "$mongo_count"

echo -n "  Elasticsearch documents: "
es_count=$(curl -s -u "$ES_USER:$ES_PASSWORD" "$ES_URI/$ES_INDEX/_count" | grep -o '"count":[0-9]*' | cut -d: -f2)
echo "$es_count"

echo ""
echo "Access your data:"
echo "  - Kibana: http://localhost:5601"
echo "  - Elasticsearch: $ES_URI"
echo "  - MongoDB: $MONGO_URI"
