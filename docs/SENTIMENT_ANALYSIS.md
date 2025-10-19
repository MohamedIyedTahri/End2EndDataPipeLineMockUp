# 🎭 Sentiment Analysis Pipeline Documentation

**Module**: `pipeline/sentiment_analyzer.py`  
**Input**: `data/processed/posts_with_language.csv`  
**Output**: `data/processed/posts_with_sentiment.csv`  
**Last run**: October 19, 2025

---

## 🎯 Objective

Augment every post with sentiment insights derived from social-media-optimized and general-purpose analyzers so downstream consumers can:
- Monitor community mood and toxicity trends in dashboards.
- Trigger alerts for highly negative conversations.
- Feed language-aware NLP models with sentiment-aware features.

The script wraps **VADER**, **TextBlob**, and an **ensemble** strategy into a reproducible CLI microservice.

---

## 🛠️ Core Components

### `SentimentAnalysisService`

| Method | Description |
|--------|-------------|
| `analyze_vader_sentiment(text)` | Returns VADER compound/pos/neg/neu scores. |
| `analyze_textblob_sentiment(text)` | Returns TextBlob polarity, subjectivity, and label. |
| `analyze_ensemble_sentiment(text)` | Blends VADER and TextBlob for a final label and confidence. |
| `process_dataframe_vader(df, ...)` | Adds VADER scores and labels to a DataFrame. |
| `process_dataframe_comprehensive(df, ...)` | Runs VADER, TextBlob, and ensemble analyses (default in CLI). |
| `get_sentiment_statistics(df, ...)` | Computes descriptive metrics over VADER outputs. |

### `AdvancedSentimentAnalyzer`

Adds customizable thresholds via `set_custom_thresholds()` and plugs into the same CLI through `--advanced` when different polarity cutoffs are needed.

Internally the pipeline safeguards against empty/invalid text, defaulting to neutral scores without interrupting execution.

---

## ▶️ Execution (Latest Run)

```bash
python3 pipeline/sentiment_analyzer.py \
  --csv-input data/processed/posts_with_language.csv \
  --csv-output data/processed/posts_with_sentiment.csv \
  --text-column Text_processed
```

Result:
```
Enriched CSV saved to data/processed/posts_with_sentiment.csv
```

Notes:
- The script preserves existing columns and appends VADER, TextBlob, and ensemble outputs.
- Use `--advanced --positive-threshold ... --negative-threshold ...` to tune polarity boundaries.
- Input column defaults to `Text`; override via `--text-column` when using the cleaned/preprocessed text.

---

## 📦 Output Schema

`data/processed/posts_with_sentiment.csv` includes language enrichment plus the following sentiment columns:

| Column | Type | Description |
|--------|------|-------------|
| `Sentiment_VADER_Score` | float | Compound score in [-1, 1]. |
| `Sentiment_VADER_Label` | string | `positive`/`neutral`/`negative` via VADER thresholds (±0.05). |
| `Sentiment_VADER_Positive` | float | Positive proportion in [0, 1]. |
| `Sentiment_VADER_Negative` | float | Negative proportion in [0, 1]. |
| `Sentiment_VADER_Neutral` | float | Neutral proportion in [0, 1]. |
| `Sentiment_TextBlob_Polarity` | float | TextBlob polarity [-1, 1]. |
| `Sentiment_TextBlob_Subjectivity` | float | TextBlob subjectivity [0, 1]. |
| `Sentiment_TextBlob_Label` | string | TextBlob-derived sentiment label. |
| `Sentiment_Ensemble_Score` | float | Weighted blend (70% VADER, 30% TextBlob). |
| `Sentiment_Ensemble_Label` | string | Final sentiment classification from ensemble score. |
| `Sentiment_Confidence` | float | Absolute ensemble score magnitude (0 to 1). |

---

## 📈 Sentiment Statistics (Oct 19, 2025)

| Metric | Value |
|--------|-------|
| Total documents | 5,978 |
| VADER mean compound | 0.214 |
| Ensemble mean score | 0.183 |
| Mean ensemble confidence | 0.356 |

### Distribution by Model

| Model | Positive | Neutral | Negative |
|-------|----------|---------|----------|
| **VADER** | 3,345 (56.0%) | 1,237 (20.7%) | 1,396 (23.4%) |
| **Ensemble** | 3,488 (58.3%) | 1,073 (17.9%) | 1,417 (23.7%) |
| **TextBlob** | 2,109 (35.3%) | 3,145 (52.6%) | 724 (12.1%) |

Interpretation:
- Ensemble skews slightly more positive than raw VADER, reflecting TextBlob’s conservative polarity.
- Roughly one quarter of posts remain negative across both models; pair with language output to prioritize moderation queues.
- Average confidence is modest (0.36); downstream filters should require `Sentiment_Confidence >= 0.4` for high-certainty insights.

---

## 🎚️ Ensemble Weighting Explanation

The ensemble sentiment score combines VADER and TextBlob outputs using heuristic weights: **70% VADER** and **30% TextBlob**. This weighting reflects VADER’s specialization for social media text, giving it greater influence, while TextBlob’s more conservative and general-purpose scoring contributes moderately. These weights are not derived from formal optimization but were selected to balance complementary strengths. Revisit and adjust them whenever new domain-specific models or lexicons are introduced.

---

## 🔄 Integration Points

| Consumer | Expectation |
|----------|-------------|
| Kibana dashboards | Drive sentiment time-series, sunburst, and alert widgets. |
| `pipeline/language_detector.py` output | Required upstream dependency; ensure language enrichment precedes sentiment run. |
| `pipeline/preprocessor.py` output | Provide sanitized `Text_processed` input for robust sentiment scoring. |
| `tests/test_sentiment_analyzer.py` | Unit coverage for negative/positive edge cases; extend to ensemble thresholds when tuning. |

---

## 🧪 Validation Tips

- **Spot check extremes**: Inspect posts with `Sentiment_VADER_Score` near ±1 to confirm signal strength.
- **Label agreement**: Compare VADER vs ensemble labels; large divergence may signal sarcasm or noisy text.
- **Threshold tuning**: Use `AdvancedSentimentAnalyzer` to adjust cutoffs for domain-specific tolerance levels.
- **Language pairing**: Combine with `Language` column to verify non-English sentiment behaves as expected.

---

## ⚠️ Caveats & Recommendations

- VADER and TextBlob are English-centric; confidence drops on non-English posts despite language detection. Consider per-language sentiment models for high-volume locales.
- Ensemble weighting (0.7/0.3) is heuristic; revisit when introducing domain-specific lexicons.
- Neutral dominance in TextBlob indicates its higher bias toward neutrality on short texts—use ensemble for dashboards, keep raw scores for auditing.
- Maintain original text columns; downstream explainability requires referencing the source content.

---

## ✅ Checklist

- [x] Language-enriched dataset prepared (`posts_with_language.csv`).
- [x] Sentiment analyzer executed on cleaned text.
- [x] Enriched dataset saved (`posts_with_sentiment.csv`).
- [x] Key statistics captured for reporting.

---

**Maintainer**: NLP/Data Engineering Team  
**Next review**: Re-run after updating language detection, adjusting thresholds, or introducing new sentiment models.
