import argparse
import logging
from pathlib import Path

import pandas as pd

import os
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.language_detector import LanguageDetector
from pipeline.sentiment_analyzer import SentimentAnalysisService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def run_nlp_pipeline(
    input_csv: Path,
    cleaned_text_column: str,
    language_output_csv: Path,
    sentiment_output_csv: Path,
) -> None:
    """Run language detection followed by sentiment analysis on the provided dataset."""
    logger.info("Loading input CSV: %s", input_csv)
    df = pd.read_csv(input_csv)

    detector = LanguageDetector()
    logger.info("Running language detection on column '%s'", cleaned_text_column)
    detected_df = detector.process_dataframe(
        df,
        text_column=cleaned_text_column,
        language_column="Language",
        confidence_column="Language_Confidence",
    )

    logger.info("Saving intermediate language-enriched dataset to %s", language_output_csv)
    detected_df.to_csv(language_output_csv, index=False)

    analyzer = SentimentAnalysisService()
    logger.info("Running sentiment analysis using column '%s'", cleaned_text_column)
    sentiment_df = analyzer.process_dataframe_comprehensive(
        detected_df,
        text_column=cleaned_text_column,
    )

    logger.info("Saving final sentiment-enriched dataset to %s", sentiment_output_csv)
    sentiment_df.to_csv(sentiment_output_csv, index=False)
    logger.info("NLP pipeline completed successfully")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run language detection and sentiment analysis sequentially.")
    parser.add_argument("--input", required=True, help="Path to the preprocessed CSV file.")
    parser.add_argument(
        "--text-column",
        default="Text_processed",
        help="Column containing cleaned text to analyze (default: Text_processed).",
    )
    parser.add_argument(
        "--language-output",
        default="data/processed/posts_with_language.csv",
        help="Destination CSV for language detection output.",
    )
    parser.add_argument(
        "--sentiment-output",
        default="data/processed/posts_with_sentiment.csv",
        help="Destination CSV for sentiment analysis output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_nlp_pipeline(
        input_csv=Path(args.input),
        cleaned_text_column=args.text_column,
        language_output_csv=Path(args.language_output),
        sentiment_output_csv=Path(args.sentiment_output),
    )


if __name__ == "__main__":
    main()
