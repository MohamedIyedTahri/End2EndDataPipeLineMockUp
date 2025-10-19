import pandas as pd
from typing import Tuple, List, Dict, Any, Optional
import langdetect
from langdetect import DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import logging
import argparse
import sys

# Ensure consistent language detection results
DetectorFactory.seed = 42

logger = logging.getLogger(__name__)

class LanguageDetector:
    """
    A microservice for language detection with confidence scoring.
    Handles text language identification using langdetect library.
    """
    
    def __init__(self, min_text_length: int = 10, default_language: str = "unknown"):
        """
        Initialize the Language Detector.
        
        Args:
            min_text_length (int): Minimum text length for reliable detection
            default_language (str): Default language when detection fails
        """
        self.min_text_length = min_text_length
        self.default_language = default_language
        self.supported_languages = {
            'af', 'ar', 'bg', 'bn', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'es', 
            'et', 'fa', 'fi', 'fr', 'gu', 'he', 'hi', 'hr', 'hu', 'id', 'it', 'ja', 
            'kn', 'ko', 'lt', 'lv', 'mk', 'ml', 'mr', 'ne', 'nl', 'no', 'pa', 'pl', 
            'pt', 'ro', 'ru', 'sk', 'sl', 'so', 'sq', 'sv', 'sw', 'ta', 'te', 'th', 
            'tl', 'tr', 'uk', 'ur', 'vi', 'zh-cn', 'zh-tw'
        }
        logger.info("LanguageDetector initialized with seed=42 for consistent results")
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of the text using langdetect.
        Returns ISO 639-1 language code (e.g., 'en', 'fr', 'es').
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            str: Detected language code or 'unknown' if detection fails
        """
        if not self._is_valid_text(text):
            return self.default_language
        
        try:
            detected_lang = langdetect.detect(text)
            return detected_lang if detected_lang in self.supported_languages else self.default_language
        except LangDetectException as e:
            logger.debug(f"Language detection failed for text: {e}")
            return self.default_language
        except Exception as e:
            logger.error(f"Unexpected error in language detection: {e}")
            return self.default_language
    
    def detect_language_with_confidence(self, text: str) -> Tuple[str, float]:
        """
        Detect language with confidence score.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Tuple[str, float]: (language_code, confidence_score)
        """
        if not self._is_valid_text(text):
            return (self.default_language, 0.0)
        
        try:
            lang_probs = langdetect.detect_langs(text)
            if lang_probs:
                best_match = lang_probs[0]
                if best_match.lang in self.supported_languages:
                    return (best_match.lang, best_match.prob)
            return (self.default_language, 0.0)
        except LangDetectException as e:
            logger.debug(f"Language detection with confidence failed: {e}")
            return (self.default_language, 0.0)
        except Exception as e:
            logger.error(f"Unexpected error in confidence-based language detection: {e}")
            return (self.default_language, 0.0)
    
    def detect_multiple_languages(self, texts: List[str]) -> List[str]:
        """
        Detect languages for multiple texts in batch.
        
        Args:
            texts (List[str]): List of texts to analyze
            
        Returns:
            List[str]: List of detected language codes
        """
        logger.info(f"Batch detecting languages for {len(texts)} texts")
        return [self.detect_language(text) for text in texts]
    
    def detect_multiple_languages_with_confidence(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Detect languages with confidence for multiple texts in batch.
        
        Args:
            texts (List[str]): List of texts to analyze
            
        Returns:
            List[Tuple[str, float]]: List of (language_code, confidence_score) tuples
        """
        logger.info(f"Batch detecting languages with confidence for {len(texts)} texts")
        return [self.detect_language_with_confidence(text) for text in texts]
    
    def process_dataframe(self, df: pd.DataFrame, text_column: str = "Text", 
                         language_column: str = "Language", 
                         confidence_column: str = "Language_Confidence") -> pd.DataFrame:
        """
        Process a DataFrame to add language detection columns.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            text_column (str): Name of the text column
            language_column (str): Name for the language column
            confidence_column (str): Name for the confidence column
            
        Returns:
            pd.DataFrame: DataFrame with added language columns
        """
        logger.info(f"Processing language detection for DataFrame with {len(df)} rows")
        
        # Create a copy to avoid modifying original
        processed_df = df.copy()
        
        # Detect languages
        processed_df[language_column] = processed_df[text_column].apply(self.detect_language)
        
        # Detect languages with confidence
        lang_confidence = processed_df[text_column].apply(self.detect_language_with_confidence)
        processed_df[language_column] = lang_confidence.apply(lambda x: x[0])
        processed_df[confidence_column] = lang_confidence.apply(lambda x: x[1])
        
        logger.info("✅ Language detection completed!")
        return processed_df
    
    def get_detection_statistics(self, df: pd.DataFrame, language_column: str = "Language", 
                               confidence_column: str = "Language_Confidence") -> Dict[str, Any]:
        """
        Generate statistics about language detection results.
        
        Args:
            df (pd.DataFrame): DataFrame with language detection results
            language_column (str): Name of the language column
            confidence_column (str): Name of the confidence column
            
        Returns:
            Dict[str, Any]: Language detection statistics
        """
        stats = {
            "total_documents": len(df),
            "unique_languages_detected": df[language_column].nunique(),
            "average_confidence": df[confidence_column].mean() if confidence_column in df else 0.0,
            "language_distribution": df[language_column].value_counts().to_dict(),
            "unknown_count": (df[language_column] == self.default_language).sum(),
            "unknown_percentage": ((df[language_column] == self.default_language).sum() / len(df)) * 100
        }
        
        # Top languages with confidence
        top_languages = df[language_column].value_counts().head(10)
        stats["top_languages"] = {}
        for lang, count in top_languages.items():
            lang_data = {
                "count": count,
                "percentage": (count / len(df)) * 100
            }
            if confidence_column in df:
                lang_data["average_confidence"] = df[df[language_column] == lang][confidence_column].mean()
            stats["top_languages"][lang] = lang_data
        
        return stats
    
    def filter_by_language(self, df: pd.DataFrame, target_languages: List[str], 
                          language_column: str = "Language") -> pd.DataFrame:
        """
        Filter DataFrame to include only specified languages.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            target_languages (List[str]): List of language codes to include
            language_column (str): Name of the language column
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        logger.info(f"Filtering DataFrame for languages: {target_languages}")
        return df[df[language_column].isin(target_languages)].copy()
    
    def _is_valid_text(self, text: str) -> bool:
        """
        Check if text is valid for language detection.
        
        Args:
            text (str): Text to validate
            
        Returns:
            bool: True if text is valid for detection
        """
        return isinstance(text, str) and len(text.strip()) >= self.min_text_length
    
    def get_supported_languages(self) -> set:
        """
        Get set of supported language codes.
        
        Returns:
            set: Supported language codes
        """
        return self.supported_languages.copy()


class AdvancedLanguageDetector(LanguageDetector):
    """
    Extended language detector with additional features:
    - Fallback detection methods
    - Language family grouping
    - Performance optimization
    """
    
    def __init__(self, min_text_length: int = 10, default_language: str = "unknown",
                 enable_fallback: bool = True):
        super().__init__(min_text_length, default_language)
        self.enable_fallback = enable_fallback
        self.language_families = {
            'germanic': {'en', 'de', 'nl', 'sv', 'no', 'da'},
            'romance': {'es', 'fr', 'it', 'pt', 'ro'},
            'slavic': {'ru', 'pl', 'cs', 'sk', 'uk', 'bg'},
            'asian': {'zh-cn', 'zh-tw', 'ja', 'ko', 'vi', 'th'},
            'semitic': {'ar', 'he'},
            'indic': {'hi', 'bn', 'pa', 'gu', 'mr', 'ne'}
        }
    
    def detect_language_with_fallback(self, text: str, fallback_method: str = "character") -> str:
        """
        Detect language with fallback method if primary fails.
        
        Args:
            text (str): Input text
            fallback_method (str): Fallback method ('character' or 'simple')
            
        Returns:
            str: Detected language
        """
        primary_result = self.detect_language(text)
        
        if primary_result != self.default_language or not self.enable_fallback:
            return primary_result
        
        # Fallback to character-based detection
        if fallback_method == "character":
            return self._character_based_detection(text)
        else:
            return self._simple_pattern_detection(text)
    
    def _character_based_detection(self, text: str) -> str:
        """Simple character-based language detection as fallback."""
        if not text:
            return self.default_language
        
        text_lower = text.lower()
        
        # Common character patterns
        if any(char in text_lower for char in 'äöüß'):
            return 'de'  # German
        elif any(char in text_lower for char in 'áéíóúñ'):
            return 'es'  # Spanish
        elif any(char in text_lower for char in 'àâæçéèêëîïôœùûüÿ'):
            return 'fr'  # French
        elif any(char in text_lower for char in 'àèéìíîòóùú'):
            return 'it'  # Italian
        elif any(char in text_lower for char in 'ãçõ'):
            return 'pt'  # Portuguese
        elif any(char in text_lower for char in 'αβγδεζηθικλμνξοπρστυφχψω'):
            return 'el'  # Greek
        elif any(char in text_lower for char in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'):
            return 'ru'  # Russian
        
        return self.default_language
    
    def _simple_pattern_detection(self, text: str) -> str:
        """Simple keyword-based language detection."""
        common_words = {
            'the': 'en', 'and': 'en', 'is': 'en',
            'der': 'de', 'die': 'de', 'das': 'de',
            'el': 'es', 'la': 'es', 'de': 'es',
            'le': 'fr', 'la': 'fr', 'et': 'fr',
            'il': 'it', 'la': 'it', 'e': 'it'
        }
        
        words = text.lower().split()
        for word in words[:10]:  # Check first 10 words
            if word in common_words:
                return common_words[word]
        
        return self.default_language
    
    def get_language_family(self, language_code: str) -> str:
        """
        Get the language family for a given language code.
        
        Args:
            language_code (str): ISO 639-1 language code
            
        Returns:
            str: Language family name or 'unknown'
        """
        for family, languages in self.language_families.items():
            if language_code in languages:
                return family
        return "unknown"


# Factory functions
def create_language_detector(min_text_length: int = 10, 
                           default_language: str = "unknown") -> LanguageDetector:
    """Factory function to create a LanguageDetector instance."""
    return LanguageDetector(
        min_text_length=min_text_length,
        default_language=default_language
    )

def create_advanced_language_detector(min_text_length: int = 10,
                                    default_language: str = "unknown",
                                    enable_fallback: bool = True) -> AdvancedLanguageDetector:
    """Factory function to create an AdvancedLanguageDetector instance."""
    return AdvancedLanguageDetector(
        min_text_length=min_text_length,
        default_language=default_language,
        enable_fallback=enable_fallback
    )

def detect_language_in_csv(input_csv: str, output_csv: str, text_column: str = "Text",
                           language_column: str = "Language", confidence_column: str = "Language_Confidence",
                           advanced: bool = False, min_length: int = 10):
    import pandas as pd

    # Instantiate detector
    detector_cls = AdvancedLanguageDetector if advanced else LanguageDetector
    detector = detector_cls(min_text_length=min_length)

    # Read CSV
    df = pd.read_csv(input_csv)

    # Check column exists
    if text_column not in df.columns:
        raise ValueError(f"Text column '{text_column}' not found in CSV.")

    # Detect languages with confidence
    lang_confidence = df[text_column].apply(detector.detect_language_with_confidence)

    # Add columns
    df[language_column] = lang_confidence.apply(lambda x: x[0])
    df[confidence_column] = lang_confidence.apply(lambda x: x[1])

    # Save enriched CSV
    df.to_csv(output_csv, index=False)
    print(f"Enriched CSV saved to: {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Language Detection Microservice CLI")

    parser.add_argument(
        "-t", "--text",
        type=str,
        help="Text string to detect language for."
    )

    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Path to a text file with one sentence per line to detect languages in batch."
    )

    parser.add_argument(
        "--csv-input",
        type=str,
        help="Path to input CSV file for language detection"
    )

    parser.add_argument(
        "--csv-output",
        type=str,
        help="Path to save enriched CSV output"
    )

    parser.add_argument(
        "--text-column",
        type=str,
        default="Text",
        help="Text column name in CSV for language detection (default: 'Text')"
    )

    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Use AdvancedLanguageDetector with fallback"
    )

    parser.add_argument(
        "--min-length",
        type=int,
        default=10,
        help="Minimum text length for detection (default: 10)"
    )

    parser.add_argument(
        "--confidence",
        action="store_true",
        help="Show confidence score for detection"
    )

    args = parser.parse_args()

    # Instantiate detector class
    detector_cls = AdvancedLanguageDetector if args.advanced else LanguageDetector
    detector = detector_cls(min_text_length=args.min_length)

    # Handle CSV input/output mode
    if args.csv_input and args.csv_output:
        import pandas as pd

        try:
            df = pd.read_csv(args.csv_input)
        except Exception as e:
            print(f"Error reading CSV file: {e}", file=sys.stderr)
            sys.exit(1)

        if args.text_column not in df.columns:
            print(f"Error: Text column '{args.text_column}' not found in CSV.", file=sys.stderr)
            sys.exit(1)

        # Detect language with confidence for each row
        lang_confidence = df[args.text_column].apply(detector.detect_language_with_confidence)
        df["Language"] = lang_confidence.apply(lambda x: x[0])
        df["Language_Confidence"] = lang_confidence.apply(lambda x: x[1])

        try:
            df.to_csv(args.csv_output, index=False)
            print(f"Enriched CSV saved to: {args.csv_output}")
        except Exception as e:
            print(f"Error writing CSV file: {e}", file=sys.stderr)
            sys.exit(1)

    # Handle single text detection
    elif args.text:
        if args.confidence:
            lang, conf = detector.detect_language_with_confidence(args.text)
            print(f"Detected language: {lang}, confidence: {conf:.4f}")
        else:
            lang = detector.detect_language(args.text)
            print(f"Detected language: {lang}")

    # Handle text file detection (one sentence per line)
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

        if args.confidence:
            results = detector.detect_multiple_languages_with_confidence(lines)
            for i, (lang, conf) in enumerate(results, 1):
                print(f"{i}: {lang} (confidence: {conf:.4f})")
        else:
            results = detector.detect_multiple_languages(lines)
            for i, lang in enumerate(results, 1):
                print(f"{i}: {lang}")

    else:
        print("Please provide either --text, --file, or both --csv-input and --csv-output arguments.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
