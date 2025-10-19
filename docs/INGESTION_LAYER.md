# 🗄️ Ingestion Layer Documentation

**Modules**: `ingestion_Layer/ingest_to_mongo.py`, `ingestion_Layer/indexation.py`  
**Latest dataset**: `data/processed/posts_with_sentiment.csv` (source for ingestion)  
**Targets**: MongoDB collection → Elasticsearch index

---

## 🚦 Overview

This layer bridges the analytics-ready CSV outputs (language + sentiment enriched) into operational data stores:
- **Stage 1 – MongoDB load**: Persist the enriched CSV with stable identifiers (`ingest_to_mongo.py`).
- **Stage 2 – Elasticsearch indexation**: Transform MongoDB documents and publish them to an Elasticsearch index (`indexation.py`).

Together, they enable the Kibana dashboards, search features, and downstream services to consume the processed dataset in near-real-time.

---

## 📥 `ingest_to_mongo.py`

### Objective

Load a CSV file into MongoDB, append the `Id_Post` field (copy of `_id`), and keep the collection ready for Elasticsearch indexing.

### CLI Usage

```bash
python3 ingestion_Layer/ingest_to_mongo.py \
  --csv-path data/processed/posts_with_sentiment.csv \
  --mongo-uri mongodb://localhost:27017/ \
  --db-name harcelement \
  --collection-name enriched
```

If any argument is omitted, the script prompts interactively with sensible defaults:
- `--mongo-uri`: `mongodb://localhost:27017/`
- `--db-name`: `harcelement`
- `--collection-name`: `posts`

### Processing Steps

1. **CSV ingest**: Reads the specified file using pandas; all columns are preserved.
2. **Bulk insert**: `insert_many` writes every record into the target collection.
3. **Identifier sync**: A subsequent `update_many` copies each `_id` into a new `Id_Post` field for downstream compatibility.

### Expectations

- Input CSV must exist and match the pipeline schema (language + sentiment columns included).
- MongoDB must be reachable with credentials baked into the URI.
- After execution, the target collection contains all CSV rows with both `_id` and `Id_Post` fields.

---

## 🔁 `indexation.py`

### Objective

Pull enriched documents from MongoDB, apply light transformations, and bulk index them into Elasticsearch for search and dashboarding.

### CLI Usage

```bash
python3 ingestion_Layer/indexation.py \
  --mongo-uri mongodb://localhost:27017/ \
  --db harcelement \
  --collection enriched \
  --es-uri http://localhost:9200 \
  --es-index harcelement_posts \
  --es-user elastic \
  --es-password <password>
```

Add `--no-verify-ssl` when targeting a cluster without valid certificates.

### Processing Steps

1. **Connections**
   - Reuses MongoDB URI, DB, and collection parameters from the ingest stage.
   - Builds an Elasticsearch client with optional basic authentication.
2. **Index bootstrap**
   - `create_index_if_not_exists` creates a mapping with fields: `titre`, `contenu`, `auteur`, `date`, `URL`, `langue`, `sentiment`, and `score`.
3. **Document transform**
   - `transform_document` maps MongoDB records into Elasticsearch `_source`, injecting placeholders for missing metadata and a random `date` within the last year (`generate_random_date`).
4. **Bulk indexing**
   - Uses `helpers.bulk` for efficient ingestion; `_id` is coerced to string for Elasticsearch compatibility.

### Output Schema (Elasticsearch)

| Field | Source | Notes |
|-------|--------|-------|
| `titre` | Placeholder | Customize when headline data becomes available. |
| `contenu` | `Text` column | Primary text body. |
| `auteur` | Placeholder | Update with real author metadata if available. |
| `date` | Generated | Randomized within past 365 days; adjust for real timestamps. |
| `URL` | Placeholder | Replace with real permalink if known. |
| `langue` | `Language` column | Depends on prior language detection stage. |
| `sentiment` | `Sentiment_Ensemble_Label` | Ensemble sentiment label. |
| `score` | `Sentiment_Ensemble_Score` | Cast to float for numeric aggregations. |

---

## 🔗 Data Flow & Dependencies

1. `data/processed/posts_with_sentiment.csv` (language/sentiment pipeline output).
2. `ingest_to_mongo.py` loads CSV → MongoDB `enriched` collection with `Id_Post`.
3. `indexation.py` reads from MongoDB, creates/updates Elasticsearch index `harcelement_posts`.
4. Kibana dashboards and API consumers query Elasticsearch for interactive analytics.

Ensure Stage 1 completes successfully before launching Stage 2 to avoid indexing empty or stale collections.

---

## 🧪 Validation Tips

- **MongoDB sanity check**: `db.enriched.countDocuments()` and spot-check documents via `findOne()` to confirm `Id_Post` presence.
- **Elasticsearch health**: `GET /harcelement_posts/_count` (via Kibana Dev Tools or curl) to verify indexed document totals.
- **Field verification**: Inspect a sample doc (`GET /harcelement_posts/_doc/<id>`) to ensure `langue`, `sentiment`, and `score` were propagated.
- **Date audit**: The randomized date assists time-series visualizations; replace with actual timestamps if available to avoid misleading trends.

---

## ⚠️ Caveats & Recommendations

- The MongoDB insert does **not** de-duplicate rows. Clear or archive the collection before re-running to prevent duplicates.
- Random dates are placeholders; swap `generate_random_date` with real ingestion timestamps when accessible.
- Elasticsearch mapping currently treats text fields generically. Add analyzers, keyword subfields, or custom scoring strategies as dashboards evolve.
- Credentials (`--es-password`) are provided as CLI args; prefer environment variables or secrets management in production.
- Network operations are synchronous; for large datasets consider batching or streaming to manage memory footprint.

---

## ✅ Checklist

- [ ] Confirm `posts_with_sentiment.csv` is up-to-date.
- [ ] MongoDB instance running and accessible.
- [ ] Elasticsearch cluster reachable and has sufficient disk space.
- [ ] Run `ingest_to_mongo.py` with desired collection name.
- [ ] Run `indexation.py` and verify indexed document count matches MongoDB source.

---

**Maintainer**: Data Platform / DevOps Team  
**Next review**: Align with infrastructure changes (Mongo/Elastic upgrades) or when evolving document schema.
