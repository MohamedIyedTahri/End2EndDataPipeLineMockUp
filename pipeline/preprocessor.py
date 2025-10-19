import pandas as pd
import re
from bs4 import BeautifulSoup
import emoji
import contractions
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """
    A microservice for comprehensive text preprocessing including:
    - HTML tag removal
    - URL removal
    - Lowercasing
    - Special character and digit removal
    - Stopword removal
    - Lemmatization
    - Text normalization
    """
    
    def __init__(self, language: str = "english"):
        self.language = language
        self.stop_words = None
        self.lemmatizer = None
        self._initialize_nltk_resources()
        
    def _initialize_nltk_resources(self):
        """Initialize NLTK resources with error handling."""
        try:
            # Download required NLTK resources if not available
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords')
                
            try:
                nltk.data.find('corpora/wordnet')
            except LookupError:
                nltk.download('wordnet')
                
            # Initialize tools
            self.stop_words = set(stopwords.words(self.language))
            self.lemmatizer = WordNetLemmatizer()
            logger.info("NLTK resources initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLTK resources: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess a single text string according to specifications.
        
        Args:
            text (str): Raw text input
            
        Returns:
            str: Preprocessed text
        """
        if not isinstance(text, str) or not text.strip():
            return ""
        
        try:
            # Step 1: Convert to lowercase
            text = text.lower()
            
            # Step 2: Remove HTML tags
            text = BeautifulSoup(text, "html.parser").get_text()
            
            # Step 3: Remove URLs
            text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            
            # Step 4: Remove \n and \t
            text = text.replace('\n', ' ').replace('\t', ' ')
            
            # Step 5: Remove special characters and punctuation
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Step 6: Remove digits
            text = re.sub(r'\d+', '', text)
            
            # Step 7: Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Step 8: Remove stopwords and lemmatize
            words = text.split()
            filtered_words = [word for word in words if word not in self.stop_words]
            lemmatized_words = [self.lemmatizer.lemmatize(word) for word in filtered_words]
            
            # Reconstruct text
            processed_text = ' '.join(lemmatized_words)
            
            return processed_text
            
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return ""
    
    def preprocess_dataframe(self, df: pd.DataFrame, text_column: str = "Text", 
                           output_column: str = "Text_processed", 
                           keep_original: bool = False) -> pd.DataFrame:
        """
        Preprocess text data in a DataFrame.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            text_column (str): Name of the text column to preprocess
            output_column (str): Name of the output column
            keep_original (bool): Whether to keep the original text column
            
        Returns:
            pd.DataFrame: DataFrame with preprocessed text
        """
        logger.info(f"Starting text preprocessing on DataFrame with {len(df)} rows")
        
        # Create a copy to avoid modifying original
        processed_df = df.copy()
        
        # Apply preprocessing
        processed_df[output_column] = processed_df[text_column].apply(self.preprocess_text)
        
        # Remove original column if requested
        if not keep_original and output_column != text_column:
            processed_df = processed_df.drop(columns=[text_column])
            # Rename processed column to original name if output is different
            if output_column != text_column:
                processed_df = processed_df.rename(columns={output_column: text_column})
        
        # Statistics
        original_non_empty = (df[text_column].str.len() > 0).sum()
        processed_non_empty = (processed_df[text_column if keep_original else output_column].str.len() > 0).sum()
        
        logger.info(f"Text preprocessing completed: {processed_non_empty}/{original_non_empty} non-empty texts after processing")
        
        return processed_df
    
    def batch_preprocess(self, texts: List[str]) -> List[str]:
        """
        Preprocess a list of texts in batch.
        
        Args:
            texts (List[str]): List of raw texts
            
        Returns:
            List[str]: List of preprocessed texts
        """
        logger.info(f"Batch preprocessing {len(texts)} texts")
        return [self.preprocess_text(text) for text in texts]
    
    def get_preprocessing_stats(self, original_texts: List[str], processed_texts: List[str]) -> Dict[str, Any]:
        """
        Get statistics about the preprocessing results.
        
        Args:
            original_texts (List[str]): Original texts
            processed_texts (List[str]): Processed texts
            
        Returns:
            Dict[str, Any]: Preprocessing statistics
        """
        stats = {
            "total_texts": len(original_texts),
            "original_non_empty": sum(1 for text in original_texts if text and text.strip()),
            "processed_non_empty": sum(1 for text in processed_texts if text and text.strip()),
            "average_length_original": sum(len(text) for text in original_texts) / len(original_texts) if original_texts else 0,
            "average_length_processed": sum(len(text) for text in processed_texts) / len(processed_texts) if processed_texts else 0,
        }
        
        stats["reduction_rate"] = (
            (stats["average_length_original"] - stats["average_length_processed"]) / 
            stats["average_length_original"] * 100
        ) if stats["average_length_original"] > 0 else 0
        
        return stats


class AdvancedTextPreprocessor(TextPreprocessor):
    """
    Extended text preprocessor with additional features:
    - Emoji handling
    - Contraction expansion
    - Sentiment analysis
    """
    
    def __init__(self, language: str = "english", handle_emojis: bool = True, 
                 expand_contractions: bool = True):
        super().__init__(language)
        self.handle_emojis = handle_emojis
        self.expand_contractions = expand_contractions
    
    def preprocess_text(self, text: str, analyze_sentiment: bool = False) -> str:
        """
        Advanced text preprocessing with optional features.
        
        Args:
            text (str): Raw text input
            analyze_sentiment (bool): Whether to perform sentiment analysis
            
        Returns:
            str: Preprocessed text
        """
        if not isinstance(text, str) or not text.strip():
            return ""
        
        try:
            # Apply basic preprocessing from parent class
            text = super().preprocess_text(text)
            
            # Additional advanced processing
            if self.expand_contractions:
                text = contractions.fix(text)
            
            if self.handle_emojis:
                text = self._handle_emojis(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error in advanced text preprocessing: {e}")
            return ""
    
    def _handle_emojis(self, text: str) -> str:
        """Convert emojis to text descriptions."""
        return emoji.demojize(text)
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Perform sentiment analysis on text.
        
        Args:
            text (str): Input text
            
        Returns:
            Dict[str, float]: Sentiment scores
        """
        try:
            blob = TextBlob(text)
            return {
                "polarity": blob.sentiment.polarity,
                "subjectivity": blob.sentiment.subjectivity
            }
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {"polarity": 0.0, "subjectivity": 0.0}


# Factory functions
def create_text_preprocessor(language: str = "english") -> TextPreprocessor:
    """Factory function to create a basic TextPreprocessor."""
    return TextPreprocessor(language=language)

def create_advanced_preprocessor(language: str = "english", 
                               handle_emojis: bool = True,
                               expand_contractions: bool = True) -> AdvancedTextPreprocessor:
    """Factory function to create an AdvancedTextPreprocessor."""
    return AdvancedTextPreprocessor(
        language=language,
        handle_emojis=handle_emojis,
        expand_contractions=expand_contractions
    )

if __name__ == "__main__":
    import argparse

    # Setup CLI argument parser
    parser = argparse.ArgumentParser(description="Preprocess a CSV file containing social media text.")
    parser.add_argument('--input', required=True, help="Path to the input CSV file (e.g., clean.csv)")
    parser.add_argument('--output', required=True, help="Path to save the output CSV file (e.g., preprocessed.csv)")
    parser.add_argument('--text_column', default='Text', help="Name of the text column to preprocess (default: 'Text')")
    parser.add_argument('--keep_original', action='store_true', help="Whether to keep the original text column")

    args = parser.parse_args()

    # Run preprocessing
    try:
        df = pd.read_csv(args.input)
        preprocessor = create_advanced_preprocessor()
        processed_df = preprocessor.preprocess_dataframe(
            df,
            text_column=args.text_column,
            keep_original=args.keep_original
        )
        processed_df.to_csv(args.output, index=False)
        print(f"[✔] Preprocessing complete. Output saved to {args.output}")
    except Exception as e:
        print(f"[✖] Error during preprocessing: {e}")
