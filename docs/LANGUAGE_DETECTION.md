# 🌍 Language Detection Pipeline Documentation

**Module**: `pipeline/language_detector.py`  
**Input**: `data/processed/preprocessed_posts.csv`  
**Output**: `data/processed/posts_with_language.csv`  
**Last run**: October 19, 2025

---

## 🎯 Objective

Enrich each post with an ISO 639-1 language code and a confidence score to support:

- Language-specific analytics in Elasticsearch/Kibana
- Routing to appropriate NLP models (e.g., sentiment per language)
- Filtering/segmentation in downstream reporting

The detector wraps the `langdetect` library with consistent seeding, guard rails for short texts, and optional fallback heuristics.

---

## 🛠️ Core Components

### `LanguageDetector`

| Method | Description |
|--------|-------------|
| `detect_language(text)` | Returns best ISO 639-1 code or `unknown` for invalid/unsupported input. |
| `detect_language_with_confidence(text)` | Returns `(language, probability)` pair. |
| `process_dataframe(df, text_column, language_column, confidence_column)` | Vectorized enrichment of pandas DataFrames. |
| `get_detection_statistics(df, ...)` | Computes summary metrics (language distribution, avg confidence, unknown rate). |
| `filter_by_language(df, target_languages)` | Convenience helper for segmentation. |

Safeguards:
- Minimum text length (default **10 characters**). Shorter strings → `unknown`.
- Supported language set restricted to `langdetect`’s ISO codes.
- Exceptions (`LangDetectException`) downgraded to debug logs to avoid pipeline failures.

### `AdvancedLanguageDetector`

Extends the base detector with:
- **Fallback heuristics** (`_character_based_detection`, `_simple_pattern_detection`) for texts that fail the primary model.
- **Language family grouping** (`get_language_family`) for aggregated analytics.
- Toggle via `enable_fallback` (default `True` when using the advanced class).

> The current pipeline uses the base `LanguageDetector`; enable the advanced class for domains where fallback heuristics add value.

---

## ▶️ Execution (Latest Run)

```bash
python3 pipeline/language_detector.py \
  --csv-input data/processed/preprocessed_posts.csv \
  --csv-output data/processed/posts_with_language.csv \
  --text-column Text_processed
```

Result:
```
Enriched CSV saved to: data/processed/posts_with_language.csv
```

Notes:
- We feed the **preprocessed** text column (`Text_processed`) for higher accuracy.
- The script always appends `Language` and `Language_Confidence` columns to the output CSV.
- To use fallback heuristics, add `--advanced`.
- Adjust sensitivity for short texts with `--min-length` (default 10).

---

## 📦 Output Schema

`data/processed/posts_with_language.csv` retains all preprocessing columns and appends:

| Column | Type | Description |
|--------|------|-------------|
| `Language` | string | Detected ISO 639-1 code (`en`, `fr`, …) or `unknown`. |
| `Language_Confidence` | float | `langdetect` probability in 
[0, 1]; `0.0` when detection fails. |

Sample rows:

| Text (truncated) | Text_processed | Language | Confidence |
|------------------|----------------|----------|------------|
| Ten outside soon doctor… | ten outside soon doctor… | `en` | 0.999998 |
| my life has come to a… | life come standstill… | `en` | 0.999995 |
| girl this nigga make… | girl nigga make sick… | `en` | 0.857141 |
| I wanna fuck you | want to fuck | `en` | 0.857140 |
| Oh hey, you should be… | oh hey ashamed disgusting self | `en` | 0.999996 |

---

## 📈 Detection Statistics (Oct 19, 2025)

| Metric | Value |
|--------|-------|
| Total documents | 5,978 |
| Unique languages detected | 32 |
| Unknown labels | 373 (6.24%) |
| Average confidence | 0.8473 |

### Top Languages

| Rank | Code | Count | Share | Avg Confidence |
|------|------|-------|-------|----------------|
| 1 | `en` | 3,962 | 66.28% | 0.9415 |
| 2 | `unknown` | 373 | 6.24% | 0.0000 |
| 3 | `fr` | 249 | 4.17% | 0.8168 |
| 4 | `it` | 206 | 3.45% | 0.8068 |
| 5 | `af` | 181 | 3.03% | 0.8463 |
| 6 | `no` | 144 | 2.41% | 0.8246 |
| 7 | `da` | 131 | 2.19% | 0.8027 |
| 8 | `ro` | 79 | 1.32% | 0.8399 |
| 9 | `nl` | 72 | 1.20% | 0.8419 |
| 10 | `et` | 62 | 1.04% | 0.8368 |

Interpretation:
- Dataset is largely English, but 9+ other languages appear with meaningful volume.
- ~6% of posts fall below the detection threshold (very short content). Consider lowering `--min-length` or using advanced fallback if this proportion must shrink.
- Confidence scores are generally high (>0.80); dashboards can filter by `Language_Confidence >= 0.6` for reliable segmentation.

---

## 🔄 Integration Points

| Consumer | Expectation |
|----------|-------------|
| NLP sentiment pipeline | Optional per-language routing (e.g., skip English-only models for `fr`). |
| Elasticsearch indexing (`ingestion_Layer/indexation.py`) | Stores `langue` field (currently taken from MongoDB; switch to the detector output for stronger accuracy). |
| Kibana dashboard filters | `Language` drives pie chart segmentation and filter pills. |
| Reporting notebooks | Confidence scores can be used to weight statistics or exclude low-certainty entries. |

To keep Elasticsearch in sync, ensure `indexation.py` uses the enriched CSV/collection that contains `Language` and `Language_Confidence`.

---

## 🧪 Validation Tips

- **Short-text audit**: Inspect posts flagged as `unknown` to confirm they are too short or non-linguistic (e.g., emojis only).
- **Confidence thresholding**: When building analytics, discard rows with `Language_Confidence < 0.5` to reduce noise.
- **Manual spot checks**: Sample non-English posts and verify language correctness (especially for closely related languages like `da` vs `no`).
- **Fallback evaluation**: If excessive `unknown` values persist, run with `--advanced` and compare results.

---

## ⚠️ Caveats & Recommendations

- `langdetect` can misclassify slang or code-switched text. Confidence scores capture uncertainty; treat low values carefully.
- Language codes `zh-cn` and `zh-tw` map to simplified/traditional Chinese; unify if analytics require a single `zh` bucket.
- Seed (`DetectorFactory.seed = 42`) ensures deterministic results; do not remove unless reproducibility is unimportant.
- Ensure the processed text column is populated (empty strings from preprocessing will become `unknown`).

---

## ✅ Checklist

- [x] Preprocessed dataset available (`data/processed/preprocessed_posts.csv`).
- [x] Language detector executed with real data.
- [x] Enriched dataset saved (`data/processed/posts_with_language.csv`).
- [x] Statistics captured for documentation and dashboard validation.

---

**Maintainer**: NLP/Data Engineering Team  
**Next review**: Pair with updates to preprocessing or when expanding language support.
