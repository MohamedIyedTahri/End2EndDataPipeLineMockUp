import pandas as pd
import pytest

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.language_detector import LanguageDetector
from pipeline.sentiment_analyzer import SentimentAnalysisService


@pytest.fixture
def sample_posts() -> pd.DataFrame:
    """Provide a tiny corpus representative of the NLP pipeline input."""
    return pd.DataFrame(
        {
            "Text": [
                "This platform is really helpful for connecting with friends and family.",
                "I absolutely despise the way you keep talking to people online.",
                "What a delightful surprise to hear from you after all this time!",
            ]
        }
    )


def test_nlp_pipeline_language_then_sentiment(sample_posts: pd.DataFrame) -> None:
    """Validate that language detection precedes sentiment analysis and enriches the dataset."""
    detector = LanguageDetector()
    detected_df = detector.process_dataframe(
        sample_posts,
        text_column="Text",
        language_column="Language",
        confidence_column="Language_Confidence",
    )

    assert "Language" in detected_df.columns
    assert "Language_Confidence" in detected_df.columns
    assert detected_df["Language"].notna().all()
    assert (detected_df["Language_Confidence"] >= 0.0).all()

    analyzer = SentimentAnalysisService()
    enriched_df = analyzer.process_dataframe_comprehensive(detected_df, text_column="Text")

    expected_sentiment_columns = {
        "Sentiment_VADER_Score",
        "Sentiment_VADER_Label",
        "Sentiment_TextBlob_Polarity",
        "Sentiment_TextBlob_Label",
        "Sentiment_Ensemble_Score",
        "Sentiment_Ensemble_Label",
        "Sentiment_Confidence",
    }

    assert expected_sentiment_columns.issubset(enriched_df.columns)
    assert enriched_df["Sentiment_Ensemble_Label"].notna().all()
    assert enriched_df["Sentiment_Confidence"].between(0.0, 1.0, inclusive="both").all()

    # Language columns must persist through the sentiment stage.
    assert enriched_df["Language"].equals(detected_df["Language"])