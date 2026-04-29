"""
ETL pipeline for student data processing.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipeline:
    """ETL pipeline for processing student data."""
    
    def __init__(self, raw_data_path, processed_data_path):
        """Initialize pipeline with data paths."""
        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = Path(processed_data_path)
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
    
    def extract(self):
        """Extract data from source."""
        logger.info(f"Extracting data from {self.raw_data_path}")
        
        if not self.raw_data_path.exists():
            raise FileNotFoundError(f"Raw data not found at {self.raw_data_path}")
        
        df = pd.read_csv(self.raw_data_path)
        logger.info(f"Extracted {len(df)} records")
        return df
    
    def transform(self, df):
        """Transform and clean data."""
        logger.info("Transforming data...")
        
        df = df.copy()
        
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().sum() > 0:
                df[col].fillna(df[col].median(), inplace=True)
        
        # Handle outliers (cap at 3 standard deviations)
        for col in numeric_cols:
            if col != 'dropped_out':  # Don't cap target variable
                mean = df[col].mean()
                std = df[col].std()
                lower_bound = mean - 3 * std
                upper_bound = mean + 3 * std
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        
        # Feature engineering
        df = self._engineer_features(df)
        
        logger.info(f"Transformed {len(df)} records")
        return df
    
    def _engineer_features(self, df):
        """Engineer additional features."""
        # Academic performance composite score
        if 'gpa' in df.columns and 'exam_scores' in df.columns:
            df['academic_performance'] = (
                (df['gpa'] / 4.0) * 0.6 + 
                (df['exam_scores'] / 100) * 0.4
            )
        
        # Engagement composite score
        engagement_features = [
            'lms_login_frequency', 'forum_posts', 
            'resource_access_count', 'participation_score'
        ]
        available_engagement = [f for f in engagement_features if f in df.columns]
        if available_engagement:
            # Normalize and combine
            for feat in available_engagement:
                df[f'{feat}_normalized'] = (
                    (df[feat] - df[feat].min()) / 
                    (df[feat].max() - df[feat].min() + 1e-6)
                )
            df['engagement_score'] = df[[f'{f}_normalized' for f in available_engagement]].mean(axis=1)
        
        # Risk indicators
        if 'attendance_rate' in df.columns:
            df['low_attendance'] = (df['attendance_rate'] < 0.7).astype(int)
        
        if 'late_submissions' in df.columns:
            df['frequent_late_submissions'] = (df['late_submissions'] > 3).astype(int)
        
        return df
    
    def load(self, df, filename='students_processed.csv'):
        """Load processed data to destination."""
        output_path = self.processed_data_path / filename
        df.to_csv(output_path, index=False)
        logger.info(f"Loaded processed data to {output_path}")
        return output_path
    
    def run(self, filename='students_processed.csv'):
        """Run complete ETL pipeline."""
        logger.info("Starting ETL pipeline...")
        
        # Extract
        df = self.extract()
        
        # Transform
        df = self.transform(df)
        
        # Load
        output_path = self.load(df, filename)
        
        logger.info("ETL pipeline completed successfully")
        return df, output_path

def main():
    """Run data pipeline."""
    pipeline = DataPipeline(
        raw_data_path='data/raw/students.csv',
        processed_data_path='data/processed'
    )
    df, output_path = pipeline.run()
    print(f"Pipeline completed. Processed data saved to {output_path}")

if __name__ == '__main__':
    main()
