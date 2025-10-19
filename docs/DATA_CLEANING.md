# 🧼 Data Cleaning Pipeline Documentation

**Notebook**: `notebooks/Clean_Data.ipynb`  
**Last executed**: October 19, 2025  
**Dataset**: `data/raw/Approach to Social Media Cyberbullying and Harassment Detection Using Advanced Machine Learning.csv`

---

## 🎯 Objectives

The goal of the data cleaning stage is to transform the raw Kaggle dataset into a consistent, normalized dataset ready for NLP enrichment and indexing. This notebook handles:

- Duplicate removal to avoid double counting during aggregations.
- Label normalization to the canonical classes `Bullying` and `Not-Bullying`.
- Category (type) standardization to a controlled vocabulary (e.g., `Sexual`, `Threats`, `Religion`).
- Validation to drop invalid rows (e.g., missing or unrecognized labels).
- Exporting the cleaned dataset to `data/clean/posts.csv` for downstream pipelines.

---

## 🛠️ Implementation Overview

### 1. Environment Setup

```python
import re
import pandas as pd
import spacy
from difflib import get_close_matches
import logging
```

- **spaCy** (`en_core_web_sm`) is used for tokenization and lemmatization of label/type values. When the model is not available, a blank English pipeline is used as a fallback (see log below).
- Logging is configured at `INFO` level to provide progress updates during pipeline execution.

### 2. DataCleaner Class

Located directly in the notebook. Key methods:

| Method | Purpose |
|--------|---------|
| `normalize_with_spacy` | Tokenizes, lemmatizes, lowercases, strips punctuation from text. |
| `clean_label` | Maps raw label strings to `Bullying` or `Not-Bullying` using canonical mapping and fuzzy matching. |
| `clean_type` | Maps raw type/category strings to a controlled vocabulary using canonical mapping, plural stripping, and fuzzy matching. |
| `remove_duplicates` | Drops duplicate rows based on the `Text` column while preserving the first occurrence. |
| `clean_dataset` | Orchestrates the entire cleaning workflow; optional duplicate removal flag.

Canonical mappings embedded in the class guarantee consistent output:

```python
self.LABEL_CANONICAL = {
    "bullying": "Bullying",
    "not bullying": "Not-Bullying",
}

self.TYPE_CANONICAL = {
    "ethnicity": "Ethnicity",
    "sexual": "Sexual",
    "religion": "Religion",
    "threat": "Threats",
    "troll": "Troll",
    "vocational": "Vocational",
    "political": "Political",
    "racism": "Racism",
}
```

### 3. Cleaning Workflow

```python
raw_df = pd.read_csv(csv_path)
cleaner = DataCleaner()
cleaned_df = cleaner.clean_dataset(
    raw_df,
    text_column="Text",
    label_column="Label",
    type_column="Types"
)
```

Operations performed in order:

1. **Duplicate Removal** – duplicates based on identical `Text` are removed.
2. **Label Cleaning** – raw labels (e.g., "BULLYING", "NOT BULLYING", typos) are normalized.
3. **Type Cleaning** – raw types (variant spellings, plurals) are mapped to canonical values.
4. **Label-Type Consistency** – if the label is `Not-Bullying`, the type is set to `NaN`.
5. **Invalid Row Removal** – rows with missing labels after cleaning are dropped.

---

## 📊 Execution Logs (Notebook Run)

```
INFO:__main__:Loaded spaCy model: en_core_web_sm
INFO:__main__:Starting dataset cleaning pipeline...
INFO:__main__:Removing duplicate rows...
INFO:__main__: Removed 2472 duplicate rows (kept='first')
INFO:__main__:   Before: 8452 rows → After: 5980 rows
INFO:__main__:Cleaning label column...
INFO:__main__:Cleaning type column...
INFO:__main__:Cleaning complete. Removed 2 invalid rows.
INFO:__main__:Final dataset: 5978 rows
```

Key takeaways:
- **Duplicates removed**: 2,472
- **Invalid rows removed**: 2 (rows with empty/unrecognized labels)

---

## 📈 Dataset Summary

| Metric | Value |
|--------|-------|
| Original rows | 8,452 |
| Cleaned rows | 5,978 |
| Rows dropped | 2,474 |
| Final columns | `['Text', 'Label', 'Types']` |

### Label Distribution (after cleaning)

```text
Bullying        3,282
Not-Bullying    2,696
```

### Type Distribution (after cleaning)

Type values are only present for `Bullying` rows; `Not-Bullying` documents have `NaN` type.

```text
Troll         825
Sexual        682
Vocational    488
Political     484
Religion      428
Threats       216
Ethnicity     132
Racism          2
```

---

## 📄 Exported Artifact

```python
cleaned_df.to_csv("../data/clean/posts.csv", index=False)
```

- Output path: `data/clean/posts.csv`
- Column schema: `Text` (string), `Label` (categorical), `Types` (categorical / null)
- This file is the input to the preprocessing and NLP pipelines (`pipeline/preprocessor.py`, `pipeline/language_detector.py`, `pipeline/sentiment_analyzer.py`).

---

## ✅ Validation Checklist

- [x] Duplicates removed using `Text` column.
- [x] Labels normalized to two canonical classes.
- [x] Types/Topics mapped to controlled vocabulary.
- [x] Rows without valid labels dropped.
- [x] `Not-Bullying` rows have null types to avoid misleading aggregations.
- [x] Cleaned dataset persisted for downstream processing.

---

## 🔗 Downstream Dependencies

| Stage | File | Purpose |
|-------|------|---------|
| NLP Preprocessing | `pipeline/preprocessor.py` | Token cleanup, stopwords removal. |
| Language Detection | `pipeline/language_detector.py` | Adds `Language` and confidence scores. |
| Sentiment Analysis | `pipeline/sentiment_analyzer.py` | Generates sentiment scores & labels. |
| Elasticsearch Indexing | `ingestion_Layer/indexation.py` | Pushes enriched docs into `harcelement_posts`. |

The cleaning notebook ensures the data feeding these components is consistent and reliable.

---

## 📘 Reproducibility Notes

1. Ensure `en_core_web_sm` is installed (`python -m spacy download en_core_web_sm`). The notebook gracefully falls back to a blank model when unavailable, but the output may differ slightly.
2. The notebook expects the raw dataset at `data/raw/Approach to Social Media Cyberbullying and Harassment Detection Using Advanced Machine Learning.csv`.
3. Logging output provides a concise audit trail; keep logs intact for traceability.
4. Re-run the notebook whenever the raw dataset changes to refresh `posts.csv`.

---

**Author**: Project Data Engineering Team  
**Last update**: October 19, 2025
