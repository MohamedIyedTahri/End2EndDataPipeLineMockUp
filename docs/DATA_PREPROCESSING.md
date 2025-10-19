# 🧹 Data Preprocessing Pipeline Documentation

**Module**: `pipeline/preprocessor.py`  
**Input**: `data/clean/posts.csv` (cleaned dataset)  
**Output**: `data/processed/preprocessed_posts.csv`  
**Last run**: October 19, 2025  

---

## 🎯 Purpose

Prepare text content for downstream NLP tasks by applying deterministic, reproducible transformations:

- Normalize case and strip HTML/URLs
- Remove punctuation, digits, and excess whitespace
- Drop stopwords and lemmatize tokens
- Optionally expand contractions and translate emojis to text descriptions
- Provide dataset-level metrics to monitor the impact of preprocessing

This step ensures consistent textual features for language detection, sentiment analysis, and Elasticsearch indexing.

---

## 🛠️ Key Components

### `TextPreprocessor`
A reusable class that exposes:

| Method | Description |
|--------|-------------|
| `preprocess_text(text)` | Applies the ordered cleanup pipeline to a single string. |
| `preprocess_dataframe(df, text_column, output_column, keep_original)` | Vectorized preprocessing over a DataFrame column. |
| `batch_preprocess(texts)` | Convenience wrapper for list inputs. |
| `get_preprocessing_stats(original_texts, processed_texts)` | Computes summary statistics (requires non-null strings). |

### `AdvancedTextPreprocessor`
Extends the base class with:

- **Contraction handling** via `contractions.fix`
- **Emoji decoding** via `emoji.demojize`
- Optional sentiment scoring with TextBlob (`analyze_sentiment` helper)

High-level ordering inside `preprocess_text`:

```text
lowercase → strip HTML → remove URLs → strip control chars → drop punctuation → drop digits → trim whitespace → remove stopwords → lemmatize → (optional) expand contractions → (optional) demojize
```

NLTK resources (`stopwords`, `wordnet`) are lazily downloaded on first use; the loader logs success and reuses cached copies under `~/nltk_data`.

---

## ▶️ How to Run the Pipeline

1. Ensure the processed data directory exists:
   ```bash
   mkdir -p data/processed
   ```
2. Execute the CLI (keeps original column to simplify analysis/logging):
   ```bash
   python3 pipeline/preprocessor.py \
     --input data/clean/posts.csv \
     --output data/processed/preprocessed_posts.csv \
     --text_column Text \
     --keep_original
   ```

**Actual run log (Oct 19, 2025):**
```
[nltk_data] Package wordnet is already up-to-date
[✔] Preprocessing complete. Output saved to data/processed/preprocessed_posts.csv
```

> ℹ️ Without `--keep_original`, the script drops the raw text column and renames `Text_processed` back to `Text`. At present, downstream statistics expect `Text_processed`, so `--keep_original` is recommended.

---

## 📦 Output Schema

`data/processed/preprocessed_posts.csv` contains 5,978 rows with these columns:

| Column | Type | Description |
|--------|------|-------------|
| `Text` | string | Original post text (unchanged when `--keep_original` is set). |
| `Label` | category | Canonical labels from cleaning stage (`Bullying`, `Not-Bullying`). |
| `Types` | category/NaN | Harassment category for bullying posts (e.g., `Sexual`, `Troll`). |
| `Text_processed` | string | Preprocessed text suitable for NLP models. |

Sample rows (head):

| # | Text | Text_processed |
|---|------|----------------|
| 0 | `Ten outside soon doctor shake everyone treatment leaving me again.` | `ten outside soon doctor shake everyone treatment leaving again` |
| 1 | `my life has come to a standstill and at this point i have no idea what to do any more` | `life come standstill point idea any more` |
| 2 | `girl this nigga make me sick to my stomach` | `girl nigga make sick stomach` |
| 3 | `I wanna fuck you` | `want to fuck` |
| 4 | `Oh hey, you should be ashamed of your disgusting self.` | `oh hey ashamed disgusting self` |

---

## 📈 Measured Impact (after latest run)

| Metric | Value |
|--------|-------|
| Total rows processed | 5,978 |
| Original non-empty texts | 5,978 |
| Processed non-empty texts | 5,972 |
| Average length (original) | 56.11 characters |
| Average length (processed) | 36.12 characters |
| Length reduction | 35.63% |

Observations:
- Stopword removal + lemmatization reduce average character length by **~20 characters**.
- Six processed rows are empty strings; these originate from posts that collapse after stopword removal. Downstream modules should treat empty processed text as missing and fall back to the original text when required.

---

## 🔄 Integration Points

| Pipeline Stage | Consumer | Expected Column |
|----------------|---------|-----------------|
| Language detection | `pipeline/language_detector.py` | `Text_processed` preferred; fall back to `Text` when empty. |
| Sentiment analysis | `pipeline/sentiment_analyzer.py` | `Text_processed` (clean input improves VADER/TextBlob accuracy). |
| Elasticsearch indexing | `ingestion_Layer/indexation.py` | Uses original `Text`; consider switching to `Text_processed` or storing both. |
| Kibana dashboards | Visualizes sentiment/type stats derived from processed text. |

To avoid data drift, rerun preprocessing whenever the cleaned dataset or preprocessing logic changes.

---

## 🧪 Testing & Validation Tips

- **Unit tests**: Extend `tests/test_data_cleaner.py` or add `tests/test_preprocessor.py` to cover edge cases (emoji-heavy text, URLs, all-stopword posts).
- **Manual spot checks**: Compare random samples of `Text` vs `Text_processed` to verify semantic preservation.
- **Length anomaly detection**: Flag rows where the processed length is zero but the original length is > 20 characters.
- **Performance**: The current single-threaded pipeline processes ~5.9k posts in under a minute on commodity hardware. For larger datasets, consider batch multiprocessing.

---

## ⚠️ Known Considerations

- BeautifulSoup raises `MarkupResemblesLocatorWarning` when strings resemble file paths; this is harmless and can be suppressed by configuring logging or passing `features="html.parser"` explicitly.
- `get_preprocessing_stats` assumes lists of strings. When NaNs appear, call `.fillna('')` before passing to the helper.
- Ensure `emoji` and `contractions` packages are installed (they are listed in `requirements.txt`).
- The script writes output directories verbatim; create `data/processed/` before launching the CLI.

---

## ✅ Checklist

- [x] Raw cleaned posts ingested (`data/clean/posts.csv`).
- [x] Processed dataset created (`data/processed/preprocessed_posts.csv`).
- [x] Metrics captured for documentation (Oct 19, 2025 run).
- [x] Integration notes shared with NLP and indexing teams.

---

**Maintainer**: Project Data Engineering Team  
**Next review**: Align with any updates to stopword lists or lemmatization strategy.
