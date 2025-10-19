import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import logging
import argparse
import sys

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    """
    A comprehensive sentiment analysis microservice supporting multiple models:
    - VADER (optimized for social media)
    - TextBlob (general purpose)
    - Ensemble (combined approach)
    """
    
    def __init__(self):
        """Initialize sentiment analysis models."""
        self.vader_analyzer = SentimentIntensityAnalyzer()
        logger.info("SentimentAnalysisService initialized with VADER and TextBlob models")
    
    def analyze_vader_sentiment(self, text: str) -> Dict[str, float]:
        """
        VADER Sentiment Analysis - Optimized for social media text.
        Scale: -1 (most negative) to +1 (most positive)
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, float]: VADER sentiment scores
        """
        if not isinstance(text, str) or not text.strip():
            return self._get_default_sentiment()
        
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            return {
                'compound': scores['compound'],  # Overall sentiment [-1, 1]
                'positive': scores['pos'],       # Positive score [0, 1]
                'negative': scores['neg'],       # Negative score [0, 1]
                'neutral': scores['neu']         # Neutral score [0, 1]
            }
        except Exception as e:
            logger.error(f"VADER sentiment analysis failed: {e}")
            return self._get_default_sentiment()
    
    def analyze_textblob_sentiment(self, text: str) -> Dict[str, float]:
        """
        TextBlob Sentiment Analysis - General purpose sentiment analysis.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, float]: TextBlob sentiment scores
        """
        if not isinstance(text, str) or not text.strip():
            return {
                'polarity': 0.0,      # [-1, 1]
                'subjectivity': 0.0,  # [0, 1]
                'label': 'neutral'
            }
        
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Determine sentiment label
            if polarity > 0.1:
                label = 'positive'
            elif polarity < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
            
            return {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'label': label
            }
        except Exception as e:
            logger.error(f"TextBlob sentiment analysis failed: {e}")
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'label': 'neutral'
            }
    
    def analyze_ensemble_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Ensemble sentiment analysis combining VADER and TextBlob.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, Any]: Combined sentiment analysis results
        """
        vader_scores = self.analyze_vader_sentiment(text)
        textblob_scores = self.analyze_textblob_sentiment(text)
        
        # Combine scores (weighted average)
        combined_score = (vader_scores['compound'] * 0.7 + 
                         textblob_scores['polarity'] * 0.3)
        
        # Determine final label
        if combined_score >= 0.05:
            final_label = 'positive'
        elif combined_score <= -0.05:
            final_label = 'negative'
        else:
            final_label = 'neutral'
        
        return {
            'vader': vader_scores,
            'textblob': textblob_scores,
            'ensemble_score': combined_score,
            'final_label': final_label,
            'confidence': abs(combined_score)  # Confidence based on magnitude
        }
    
    def get_sentiment_label_vader(self, compound_score: float) -> str:
        """
        Convert VADER compound score to sentiment label.
        
        Args:
            compound_score (float): VADER compound score [-1, 1]
            
        Returns:
            str: Sentiment label ('positive', 'neutral', 'negative')
        """
        if compound_score >= 0.05:
            return 'positive'
        elif compound_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def process_dataframe_vader(self, df: pd.DataFrame, text_column: str = "Text", 
                               score_column: str = "Sentiment_VADER",
                               label_column: str = "Sentiment_Label_VADER") -> pd.DataFrame:
        """
        Process DataFrame with VADER sentiment analysis.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            text_column (str): Name of text column
            score_column (str): Name for sentiment score column
            label_column (str): Name for sentiment label column
            
        Returns:
            pd.DataFrame: DataFrame with sentiment analysis results
        """
        logger.info("🎭 SENTIMENT ANALYSIS - VADER MODEL")
        logger.info("=" * 70)
        
        processed_df = df.copy()
        
        logger.info("📊 Applying VADER sentiment analysis...")
        
        # Apply VADER analysis
        sentiment_results = processed_df[text_column].apply(self.analyze_vader_sentiment)
        
        # Extract compound scores
        processed_df[score_column] = sentiment_results.apply(lambda x: x['compound'])
        
        # Add sentiment labels
        processed_df[label_column] = processed_df[score_column].apply(
            self.get_sentiment_label_vader
        )
        
        logger.info("✅ VADER analysis completed!")
        
        return processed_df
    
    def process_dataframe_comprehensive(self, df: pd.DataFrame, text_column: str = "Text") -> pd.DataFrame:
        """
        Comprehensive sentiment analysis with multiple models.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            text_column (str): Name of text column
            
        Returns:
            pd.DataFrame: DataFrame with comprehensive sentiment analysis
        """
        processed_df = df.copy()
        
        logger.info("🔍 Running comprehensive sentiment analysis...")
        
        # VADER Analysis
        vader_results = processed_df[text_column].apply(self.analyze_vader_sentiment)
        processed_df['Sentiment_VADER_Score'] = vader_results.apply(lambda x: x['compound'])
        processed_df['Sentiment_VADER_Label'] = processed_df['Sentiment_VADER_Score'].apply(
            self.get_sentiment_label_vader
        )
        processed_df['Sentiment_VADER_Positive'] = vader_results.apply(lambda x: x['positive'])
        processed_df['Sentiment_VADER_Negative'] = vader_results.apply(lambda x: x['negative'])
        processed_df['Sentiment_VADER_Neutral'] = vader_results.apply(lambda x: x['neutral'])
        
        # TextBlob Analysis
        textblob_results = processed_df[text_column].apply(self.analyze_textblob_sentiment)
        processed_df['Sentiment_TextBlob_Polarity'] = textblob_results.apply(lambda x: x['polarity'])
        processed_df['Sentiment_TextBlob_Subjectivity'] = textblob_results.apply(lambda x: x['subjectivity'])
        processed_df['Sentiment_TextBlob_Label'] = textblob_results.apply(lambda x: x['label'])
        
        # Ensemble Analysis
        ensemble_results = processed_df[text_column].apply(self.analyze_ensemble_sentiment)
        processed_df['Sentiment_Ensemble_Score'] = ensemble_results.apply(lambda x: x['ensemble_score'])
        processed_df['Sentiment_Ensemble_Label'] = ensemble_results.apply(lambda x: x['final_label'])
        processed_df['Sentiment_Confidence'] = ensemble_results.apply(lambda x: x['confidence'])
        
        logger.info("✅ Comprehensive sentiment analysis completed!")
        
        return processed_df
    
    def get_sentiment_statistics(self, df: pd.DataFrame, score_column: str = "Sentiment_VADER",
                               label_column: str = "Sentiment_Label_VADER") -> Dict[str, Any]:
        """
        Generate comprehensive sentiment analysis statistics.
        
        Args:
            df (pd.DataFrame): DataFrame with sentiment analysis
            score_column (str): Name of sentiment score column
            label_column (str): Name of sentiment label column
            
        Returns:
            Dict[str, Any]: Sentiment analysis statistics
        """
        stats = {
            'mean_score': df[score_column].mean(),
            'median_score': df[score_column].median(),
            'std_score': df[score_column].std(),
            'min_score': df[score_column].min(),
            'max_score': df[score_column].max(),
        }
        
        # Distribution counts
        if label_column in df.columns:
            label_counts = df[label_column].value_counts()
            stats['distribution'] = {
                'positive': label_counts.get('positive', 0),
                'neutral': label_counts.get('neutral', 0),
                'negative': label_counts.get('negative', 0)
            }
            
            # Percentages
            total = len(df)
            stats['percentages'] = {
                'positive': (stats['distribution']['positive'] / total) * 100,
                'neutral': (stats['distribution']['neutral'] / total) * 100,
                'negative': (stats['distribution']['negative'] / total) * 100
            }
        
        return stats
    
    def print_vader_report(self, df: pd.DataFrame, score_column: str = "Sentiment_VADER"):
        """
        Print comprehensive VADER sentiment analysis report.
        
        Args:
            df (pd.DataFrame): DataFrame with VADER sentiment scores
            score_column (str): Name of VADER score column
        """
        stats = self.get_sentiment_statistics(df, score_column)
        
        # Calculate distribution using VADER thresholds
        vader_positive = (df[score_column] >= 0.05).sum()
        vader_negative = (df[score_column] <= -0.05).sum()
        vader_neutral = ((df[score_column] > -0.05) & (df[score_column] < 0.05)).sum()
        
        print("=" * 70)
        print("🎭 SENTIMENT ANALYSIS - VADER MODEL REPORT")
        print("=" * 70)
        
        print(f"\n📈 VADER Statistics:")
        print(f"  • Mean: {stats['mean_score']:.4f}")
        print(f"  • Median: {stats['median_score']:.4f}")
        print(f"  • Std Dev: {stats['std_score']:.4f}")
        print(f"  • Min: {stats['min_score']:.4f}")
        print(f"  • Max: {stats['max_score']:.4f}")
        
        print(f"\n📊 VADER Distribution:")
        print(f"  • Positive (≥0.05): {vader_positive:,} ({vader_positive/len(df)*100:.1f}%)")
        print(f"  • Neutral (-0.05 to 0.05): {vader_neutral:,} ({vader_neutral/len(df)*100:.1f}%)")
        print(f"  • Negative (≤-0.05): {vader_negative:,} ({vader_negative/len(df)*100:.1f}%)")
    
    def _get_default_sentiment(self) -> Dict[str, float]:
        """Return default sentiment scores for invalid inputs."""
        return {
            'compound': 0.0,
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 1.0
        }


class AdvancedSentimentAnalyzer(SentimentAnalysisService):
    """
    Advanced sentiment analyzer with additional features:
    - Domain-specific sentiment
    - Custom thresholds
    - Batch processing optimization
    """
    
    def __init__(self, positive_threshold: float = 0.05, negative_threshold: float = -0.05):
        super().__init__()
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold
    
    def set_custom_thresholds(self, positive: float, negative: float):
        """
        Set custom sentiment classification thresholds.
        
        Args:
            positive (float): Positive sentiment threshold
            negative (float): Negative sentiment threshold
        """
        self.positive_threshold = positive
        self.negative_threshold = negative
        logger.info(f"Custom thresholds set: Positive={positive}, Negative={negative}")
    
    def get_sentiment_label_custom(self, score: float) -> str:
        """
        Get sentiment label using custom thresholds.
        
        Args:
            score (float): Sentiment score
            
        Returns:
            str: Sentiment label
        """
        if score >= self.positive_threshold:
            return 'positive'
        elif score <= self.negative_threshold:
            return 'negative'
        else:
            return 'neutral'


# Factory functions
def create_sentiment_analyzer() -> SentimentAnalysisService:
    """Factory function to create a SentimentAnalysisService instance."""
    return SentimentAnalysisService()

def create_advanced_sentiment_analyzer(positive_threshold: float = 0.05, 
                                     negative_threshold: float = -0.05) -> AdvancedSentimentAnalyzer:
    """Factory function to create an AdvancedSentimentAnalyzer instance."""
    return AdvancedSentimentAnalyzer(
        positive_threshold=positive_threshold,
        negative_threshold=negative_threshold
    )



def main():
    parser = argparse.ArgumentParser(description="Sentiment Analysis Microservice CLI")
    
    parser.add_argument(
        "--csv-input",
        type=str,
        required=True,
        help="Path to input CSV file."
    )
    
    parser.add_argument(
        "--csv-output",
        type=str,
        required=True,
        help="Path to save enriched output CSV."
    )
    
    parser.add_argument(
        "--text-column",
        type=str,
        default="Text",
        help="Name of text column in CSV (default: 'Text')."
    )
    
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Use AdvancedSentimentAnalyzer with custom thresholds."
    )
    
    parser.add_argument(
        "--positive-threshold",
        type=float,
        default=0.05,
        help="Positive sentiment threshold (only used with --advanced)."
    )
    
    parser.add_argument(
        "--negative-threshold",
        type=float,
        default=-0.05,
        help="Negative sentiment threshold (only used with --advanced)."
    )
    
    args = parser.parse_args()
    
    try:
        df = pd.read_csv(args.csv_input)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if args.advanced:
        analyzer = AdvancedSentimentAnalyzer(
            positive_threshold=args.positive_threshold,
            negative_threshold=args.negative_threshold
        )
    else:
        analyzer = SentimentAnalysisService()
    
    # Use comprehensive analysis to enrich dataframe
    enriched_df = analyzer.process_dataframe_comprehensive(df, text_column=args.text_column)
    
    try:
        enriched_df.to_csv(args.csv_output, index=False)
        print(f"Enriched CSV saved to {args.csv_output}")
    except Exception as e:
        print(f"Error saving CSV file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
