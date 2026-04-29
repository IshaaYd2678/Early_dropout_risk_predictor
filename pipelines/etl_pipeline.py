"""
ETL Pipeline for Student Data Ingestion
Implements SRS Section 3: Data Engineering Requirements
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    records_validated: int
    records_passed: int
    records_failed: int


class DataValidator:
    """Validates data against schema contracts."""
    
    def __init__(self):
        self.schema = {
            'student_id': {'type': str, 'nullable': False, 'pattern': r'^STU\d{5}$'},
            'attendance_rate': {'type': float, 'nullable': False, 'min': 0.0, 'max': 1.0},
            'gpa': {'type': float, 'nullable': False, 'min': 0.0, 'max': 4.0},
            'assignment_submission_rate': {'type': float, 'nullable': False, 'min': 0.0, 'max': 1.0},
            'exam_scores': {'type': float, 'nullable': False, 'min': 0.0, 'max': 100.0},
            'lms_login_frequency': {'type': int, 'nullable': False, 'min': 0},
            'late_submissions': {'type': int, 'nullable': False, 'min': 0},
            'participation_score': {'type': float, 'nullable': False, 'min': 0.0, 'max': 100.0},
            'forum_posts': {'type': int, 'nullable': False, 'min': 0},
            'resource_access_count': {'type': int, 'nullable': False, 'min': 0},
            'time_spent_hours': {'type': float, 'nullable': False, 'min': 0.0},
        }
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate dataframe against schema."""
        errors = []
        warnings = []
        records_failed = 0
        
        logger.info(f"Validating {len(df)} records...")
        
        # Check required columns
        missing_cols = set(self.schema.keys()) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return ValidationResult(False, errors, warnings, len(df), 0, len(df))
        
        # Validate each field
        for col, rules in self.schema.items():
            if col not in df.columns:
                continue
            
            # Check nullability
            null_count = df[col].isnull().sum()
            if not rules.get('nullable', True) and null_count > 0:
                errors.append(f"{col}: {null_count} null values found (not allowed)")
                records_failed += null_count
            
            # Check data type and range
            if rules['type'] == float:
                # Check range
                if 'min' in rules:
                    invalid = df[df[col] < rules['min']]
                    if len(invalid) > 0:
                        errors.append(f"{col}: {len(invalid)} values below minimum {rules['min']}")
                        records_failed += len(invalid)
                
                if 'max' in rules:
                    invalid = df[df[col] > rules['max']]
                    if len(invalid) > 0:
                        errors.append(f"{col}: {len(invalid)} values above maximum {rules['max']}")
                        records_failed += len(invalid)
            
            elif rules['type'] == int:
                if 'min' in rules:
                    invalid = df[df[col] < rules['min']]
                    if len(invalid) > 0:
                        errors.append(f"{col}: {len(invalid)} negative values found")
                        records_failed += len(invalid)
        
        # Completeness threshold check (SRS 3.3.2)
        for col in self.schema.keys():
            if col in df.columns:
                missing_pct = df[col].isnull().sum() / len(df)
                if missing_pct > 0.15:
                    warnings.append(f"{col}: {missing_pct:.1%} missing values exceeds 15% threshold")
        
        records_passed = len(df) - records_failed
        is_valid = len(errors) == 0
        
        logger.info(f"Validation complete: {records_passed}/{len(df)} records passed")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            records_validated=len(df),
            records_passed=records_passed,
            records_failed=records_failed
        )


class DataCleaner:
    """Cleans and normalizes data."""
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data according to SRS 3.3.3."""
        logger.info("Cleaning data...")
        df_clean = df.copy()
        
        # Handle missing values
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df_clean[col].isnull().sum() > 0:
                # Impute with median for numeric columns
                median_val = df_clean[col].median()
                df_clean[col].fillna(median_val, inplace=True)
                logger.info(f"Imputed {col} missing values with median: {median_val:.2f}")
        
        # Remove duplicates
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['student_id'], keep='last')
        removed = initial_count - len(df_clean)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate records")
        
        # Normalize text fields
        text_cols = df_clean.select_dtypes(include=['object']).columns
        for col in text_cols:
            df_clean[col] = df_clean[col].str.strip().str.upper()
        
        logger.info(f"Cleaning complete: {len(df_clean)} records")
        return df_clean


class ETLPipeline:
    """Complete ETL pipeline for student data."""
    
    def __init__(self, landing_zone: str = "data/raw", 
                 processed_zone: str = "data/processed"):
        self.landing_zone = Path(landing_zone)
        self.processed_zone = Path(processed_zone)
        self.validator = DataValidator()
        self.cleaner = DataCleaner()
        
        # Create directories
        self.landing_zone.mkdir(parents=True, exist_ok=True)
        self.processed_zone.mkdir(parents=True, exist_ok=True)
    
    def extract(self, source_file: str) -> pd.DataFrame:
        """Extract data from source file."""
        logger.info(f"Extracting data from {source_file}...")
        
        file_path = self.landing_zone / source_file
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        # Read CSV
        df = pd.read_csv(file_path)
        logger.info(f"Extracted {len(df)} records")
        
        return df
    
    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, ValidationResult]:
        """Transform and validate data."""
        logger.info("Transforming data...")
        
        # Validate
        validation_result = self.validator.validate(df)
        
        if not validation_result.is_valid:
            logger.error("Validation failed:")
            for error in validation_result.errors:
                logger.error(f"  - {error}")
            raise ValueError("Data validation failed")
        
        # Log warnings
        for warning in validation_result.warnings:
            logger.warning(f"  - {warning}")
        
        # Clean
        df_clean = self.cleaner.clean(df)
        
        return df_clean, validation_result
    
    def load(self, df: pd.DataFrame, output_file: str) -> str:
        """Load processed data to destination."""
        logger.info(f"Loading data to {output_file}...")
        
        output_path = self.processed_zone / output_file
        df.to_csv(output_path, index=False)
        
        # Generate data hash for audit
        data_hash = hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()
        
        logger.info(f"Data loaded successfully: {output_path}")
        logger.info(f"Data hash: {data_hash}")
        
        return str(output_path)
    
    def run(self, source_file: str, output_file: Optional[str] = None) -> Dict:
        """Run complete ETL pipeline."""
        logger.info("=" * 80)
        logger.info("Starting ETL Pipeline")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Extract
            df_raw = self.extract(source_file)
            
            # Transform
            df_clean, validation_result = self.transform(df_raw)
            
            # Load
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"students_processed_{timestamp}.csv"
            
            output_path = self.load(df_clean, output_file)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'status': 'success',
                'records_processed': len(df_clean),
                'output_path': output_path,
                'duration_seconds': duration,
                'validation': {
                    'records_validated': validation_result.records_validated,
                    'records_passed': validation_result.records_passed,
                    'records_failed': validation_result.records_failed,
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings
                }
            }
            
            logger.info("=" * 80)
            logger.info("ETL Pipeline Complete")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {str(e)}")
            raise


if __name__ == "__main__":
    # Run ETL pipeline
    pipeline = ETLPipeline()
    result = pipeline.run("students.csv")
    print(f"\nPipeline result: {result}")
