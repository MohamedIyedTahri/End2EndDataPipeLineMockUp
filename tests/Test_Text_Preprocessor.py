import pandas as pd
import pytest

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.preprocessor import TextPreprocessor


@pytest.fixture(scope="module")
def preprocessor() -> TextPreprocessor:
    """Instantiate the base text preprocessor once per test module."""
    return TextPreprocessor()


@pytest.fixture
def raw_sample_df() -> pd.DataFrame:
    """Provide representative raw inputs covering common preprocessing steps."""
    return pd.DataFrame(
        {
            "Text": [
                "<p>Hello WORLD!</p> Visit https://example.com NOW!!!",
                "Numbers 12345 and punctuation?! should vanish...",
                "Here's a test\nwith newlines\tand tabs 😊",
                "   ",  # whitespace only
                None,  # missing value
            ]
        }
    )


def test_preprocess_dataframe_basic(preprocessor: TextPreprocessor, raw_sample_df: pd.DataFrame) -> None:
    """Ensure the dataframe-level preprocessing pipeline cleans and normalizes text."""
    processed_df = preprocessor.preprocess_dataframe(
        raw_sample_df,
        text_column="Text",
        output_column="Text_processed",
        keep_original=True,
    )

    # Expect the output column to exist with string dtype and no Nones.
    assert "Text_processed" in processed_df.columns
    assert processed_df["Text_processed"].apply(lambda x: isinstance(x, str)).all()

    # Verify specific transformations on representative rows.
    assert processed_df.loc[0, "Text_processed"] == "hello world visit"
    assert processed_df.loc[1, "Text_processed"] == "number punctuation vanish"
    assert processed_df.loc[2, "Text_processed"] == "test newlines tab"

    # Empty and None inputs should yield empty strings.
    assert processed_df.loc[3, "Text_processed"] == ""
    assert processed_df.loc[4, "Text_processed"] == ""


def test_batch_preprocess(preprocessor: TextPreprocessor) -> None:
    """Validate batch API mirrors single-text preprocessing behaviour."""
    texts = ["HTML <b>bold</b>", "Noisy!!! TEXT??"]
    results = preprocessor.batch_preprocess(texts)

    assert results == ["html bold", "noisy text"]


def test_get_preprocessing_stats(preprocessor: TextPreprocessor) -> None:
    """Confirm statistics helper reports expected aggregates."""
    originals = ["Text One", "Second Text", ""]
    processed = [preprocessor.preprocess_text(text) for text in originals]

    stats = preprocessor.get_preprocessing_stats(originals, processed)

    assert stats["total_texts"] == 3
    assert stats["original_non_empty"] == 2
    assert stats["processed_non_empty"] <= stats["original_non_empty"]
    assert stats["average_length_processed"] <= stats["average_length_original"]
