# Project Overview

## What This Pipeline Does
- Cleans social-media posts for cyberbullying detection.
- Enriches each post with normalized labels, languages, and sentiment scores.
- Loads enriched data into MongoDB and Elasticsearch for dashboarding in Kibana.

## Project Structure (key folders)
- `data/` – raw, clean, processed datasets.
- `docs/` – stage-specific documentation and guides.
- `pipeline/` – preprocessing, language detection, sentiment analysis, combined runner.
- `ingestion_Layer/` – scripts for MongoDB ingestion and Elasticsearch indexing.
- `notebooks/` – exploratory and cleaning notebooks.
- `tests/` – pytest suites for preprocessing, NLP pipeline, and ingestion.
- `docker-compose.yml` & helper scripts – bring up MongoDB, Elasticsearch, Kibana.

## End-to-End Flow
1. **Data Cleaning** (`notebooks/Clean_Data.ipynb`)
   - Removes duplicates, fixes labels/types, exports `data/clean/posts.csv`.
2. **Text Preprocessing** (`pipeline/preprocessor.py`)
   - Normalizes text (HTML strip, stopwords, lemmatization) → `data/processed/preprocessed_posts.csv`.
3. **Language Detection** (`pipeline/language_detector.py`)
   - Adds `Language` and `Language_Confidence` → `data/processed/posts_with_language.csv`.
4. **Sentiment Analysis** (`pipeline/sentiment_analyzer.py`)
   - Adds VADER/TextBlob/ensemble fields → `data/processed/posts_with_sentiment.csv`.
5. **Combined Runner** (`pipeline/nlp_pipeline.py`)
   - Executes language + sentiment stages in one command.
6. **Ingestion Layer**
   - `ingestion_Layer/ingest_to_mongo.py`: loads CSV into MongoDB.
   - `ingestion_Layer/indexation.py`: indexes MongoDB docs into Elasticsearch.
7. **Analytics**
   - Kibana (via Docker) visualizes language and sentiment trends.

## Running the NLP Pipeline
```bash
# preprocess text first (not shown here)
python3 pipeline/nlp_pipeline.py \
  --input data/processed/preprocessed_posts.csv \
  --text-column Text_processed \
  --language-output data/processed/posts_with_language.csv \
  --sentiment-output data/processed/posts_with_sentiment.csv
```

## Container Stack
- `mongo` (port 27017): stores enriched posts.
- `elasticsearch` (port 9200): search + analytics index.
- `kibana` (port 5601): dashboards and reporting.

Start locally:
```bash
docker compose up -d
```
Credentials and service tokens live under `credentials/` after first boot.

## Tests
`pytest` covers preprocessing, NLP pipeline integration, and ingestion-layer interactions with live MongoDB/Elasticsearch instances.

## Key Outputs
- `data/clean/posts.csv`: canonical cleaned dataset.
- `data/processed/posts_with_sentiment.csv`: final enriched dataset for indexing.
- Elasticsearch index (`harcelement_posts*`): powers Kibana dashboards.

## Maintenance Tips
- Re-run cleaning + preprocessing whenever raw data changes.
- Refresh Elasticsearch/Kibana after schema or scoring tweaks.
- Update `docker-compose.yml` credentials only through `es-init.sh` to keep tokens in sync.
