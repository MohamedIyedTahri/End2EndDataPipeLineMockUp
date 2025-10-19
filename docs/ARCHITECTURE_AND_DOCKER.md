# System Architecture & Docker Stack

**Scope**: End-to-end NLP pipeline, persistence layer, and containerized deployment for analytics.

---

## 🧠 High-Level Architecture

```
          ┌─────────────────────┐
          │ Raw Social Dataset │
          │   (CSV format)     │
          └────────┬───────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│                    Data Cleaning Stage                 │
│  - notebooks/Clean_Data.ipynb                          │
│  - Deduplication, label/type normalization             │
└───────────┬────────────────────────────────────────────┘
            │  data/clean/posts.csv
            ▼
┌────────────────────────────────────────────────────────┐
│                    Preprocessing Stage                 │
│  - pipeline/preprocessor.py                            │
│  - Strip HTML, remove noise, lemmatize tokens          │
└───────────┬────────────────────────────────────────────┘
            │  data/processed/preprocessed_posts.csv
            ▼
┌────────────────────────────────────────────────────────┐
│                 Language Detection Stage               │
│  - pipeline/language_detector.py                       │
│  - ISO 639-1 language tags + confidence                │
└───────────┬────────────────────────────────────────────┘
            │  data/processed/posts_with_language.csv
            ▼
┌────────────────────────────────────────────────────────┐
│                Sentiment Analysis Stage                │
│  - pipeline/sentiment_analyzer.py                      │
│  - VADER, TextBlob, ensemble sentiment & confidence    │
└───────────┬────────────────────────────────────────────┘
            │  data/processed/posts_with_sentiment.csv
            ▼
┌────────────────────────────────────────────────────────┐
│                 Persistence & Analytics                │
│  - ingestion_Layer/ingest_to_mongo.py → MongoDB        │
│  - ingestion_Layer/indexation.py → Elasticsearch       │
│  - Kibana dashboards / API consumers                   │
└────────────────────────────────────────────────────────┘
```

### Component Summary
- **Data Cleaning**: Notebook-driven workflow that removes duplicates, normalizes labels/types, and exports `data/clean/posts.csv` as the canonical dataset for all downstream stages.
- **Preprocessor**: Cleans and normalizes text using NLTK stopwords, BeautifulSoup, regex rules, and lemmatization for downstream model accuracy.
- **Language Detector**: Leverages `langdetect` with deterministic seeding and validation, producing language codes plus confidence metrics for routing and analytics.
- **Sentiment Analyzer**: Combines VADER (social-media tuned) with TextBlob (polarity/subjectivity) into a weighted ensemble score and label.
- **Ingestion Layer**:
  - `ingest_to_mongo.py` loads the enriched CSV into MongoDB and mirrors `_id` to `Id_Post`.
  - `indexation.py` pulls MongoDB docs, injects metadata (language, sentiment, score), and bulk indexes into Elasticsearch for search-ready access.
- **Visualization**: Kibana dashboards operate on the Elasticsearch index to monitor abuse trends, sentiment distribution, and language splits.

---

## 🐳 Docker Compose Stack

| Service | Image | Purpose | Ports | Volumes |
|--------|--------|---------|-------|---------|
| `mongo` | `mongo:6.0` | Stores enriched posts used by indexation and APIs | `27017:27017` | `mongodata:/data/db` |
| `elasticsearch` | `docker.elastic.co/elasticsearch/elasticsearch:8.12.0` | Search + analytics data store | `9200:9200` | `esdata:/usr/share/elasticsearch/data`, `./es-init.sh`, `./credentials` |
| `kibana` | `docker.elastic.co/kibana/kibana:8.12.0` | Dashboard UI and saved visualizations | `5601:5601` | `./kibana-init.sh`, `./kibana.yml`, `./credentials` |

### Service Details
- **MongoDB**
  - Default credentials disabled; rely on network isolation for local development.
  - Persistent storage through `mongodata` named volume; remove with `docker volume rm mongodata` to reset.

- **Elasticsearch**
  - Configured as a secured single node (`xpack.security.enabled=true`).
  - `es-init.sh` changes the default `elastic` password and writes it (plus a Kibana service token) into `credentials/`.
  - Health check ensures the container is responsive before Kibana attempts to connect.

- **Kibana**
  - `kibana-init.sh` blocks until Elasticsearch and the service token are ready, then injects credentials into `kibana.yml` inside the container.
  - Uses service-account authentication; no direct password secrets inside the container image.

### Running the Stack
```bash
# Start everything
docker compose up -d

# Or start individual services
docker compose up -d mongo
```

Check status:
```bash
docker compose ps
curl -u elastic:<password> http://localhost:9200/_cluster/health
curl http://localhost:5601/status
```

> Password and service token are written to `credentials/elastic_password` and `credentials/kibana_service_token` respectively.

---

## 🔄 Data Flow & Deploy Integration
1. Generate processed datasets locally with the pipeline scripts (`preprocessor.py`, `language_detector.py`, `sentiment_analyzer.py`).
2. Run `ingest_to_mongo.py` pointing to MongoDB (`mongodb://localhost:27017/` outside containers or `mongodb://mongo:27017/` inside Docker).
3. Execute `indexation.py` with Elasticsearch credentials (`elastic` + password from `credentials/elastic_password`).
4. Kibana dashboards (http://localhost:5601) visualize the indexed data. Custom setup scripts (`setup_kibana_dashboard.py`) can automate dashboard creation.

Environment variables for local runs:
```bash
export MONGO_URI="mongodb://localhost:27017/"
export ES_URI="http://localhost:9200"
export ES_USER="elastic"
export ES_PASSWORD="Q*aPCff9cD3Q6WDKjYpR"
```

When executing inside another container or remote environment, swap `localhost` for service names (`mongo`, `elasticsearch`).

---

## ✅ Operational Checklist
- [ ] Refresh processed CSV (`posts_with_sentiment.csv`).
- [ ] `docker compose up -d mongo elasticsearch kibana`.
- [ ] Load data into MongoDB via `ingest_to_mongo.py`.
- [ ] Index Elastic with `indexation.py`.
- [ ] Open Kibana dashboards and validate connectivity.

---

**Maintainers**: Data Engineering & DevOps Teams  
**Last Updated**: October 19, 2025
