"""
Feature Engineering Module
Implements SRS Section 4: Feature Engineering Requirements
Complete feature catalog with academic, behavioral, and temporal features
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature engineering for dropout risk prediction.
    Implements all features from SRS Section 4.2.
    """
    
    def __init__(self):
        self.feature_catalog = self._build_feature_catalog()
    
    def _build_feature_catalog(self) -> Dict:
        """Build complete feature catalog from SRS."""
        return {
            'academic_performance': [
                'current_gpa',
                'gpa_trend_3sem',
                'course_pass_rate',
                'grade_variance',
                'failed_courses_cum',
                'repeat_course_flag'
            ],
            'attendance_engagement': [
                'attendance_rate_current',
                'consec_absences_max',
                'lms_login_weekly_avg',
                'assignment_submit_rate',
                'late_submission_rate',
                'discussion_participation',
                'lms_last_login_days'
            ],
            'temporal_behavioral': [
                'submit_rate_delta_4wk',
                'login_frequency_delta',
                'grade_inflection_flag'
            ],
            'socioeconomic_contextual': [
                'financial_aid_flag',
                'outstanding_balance_flag',
                'first_generation_flag',
                'commuter_student_flag',
                'part_time_enrollment_flag'
            ]
        }
    
    def engineer_academic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer academic performance features (SRS 4.2.1).
        """
        logger.info("Engineering academic performance features...")
        
        df_features = df.copy()
        
        # current_gpa - already exists
        if 'gpa' in df.columns:
            df_features['current_gpa'] = df['gpa']
        
        # gpa_trend_3sem - simulate with random trend for demo
        # In production, this would use historical semester data
        if 'gpa' in df.columns:
            df_features['gpa_trend_3sem'] = np.random.normal(0, 0.3, len(df))
        
        # course_pass_rate - simulate based on GPA
        if 'gpa' in df.columns:
            df_features['course_pass_rate'] = np.clip(df['gpa'] / 4.0 + np.random.normal(0, 0.1, len(df)), 0, 1)
        
        # grade_variance - simulate
        df_features['grade_variance'] = np.random.uniform(0, 1.5, len(df))
        
        # failed_courses_cum - simulate based on GPA
        if 'gpa' in df.columns:
            df_features['failed_courses_cum'] = np.where(df['gpa'] < 2.0, 
                                                         np.random.randint(1, 4, len(df)), 
                                                         np.random.randint(0, 2, len(df)))
        
        # repeat_course_flag
        df_features['repeat_course_flag'] = (df_features.get('failed_courses_cum', 0) > 0).astype(int)
        
        return df_features
    
    def engineer_engagement_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer attendance and engagement features (SRS 4.2.2).
        """
        logger.info("Engineering attendance and engagement features...")
        
        df_features = df.copy()
        
        # attendance_rate_current - already exists
        if 'attendance_rate' in df.columns:
            df_features['attendance_rate_current'] = df['attendance_rate']
        
        # consec_absences_max - simulate based on attendance
        if 'attendance_rate' in df.columns:
            df_features['consec_absences_max'] = np.where(
                df['attendance_rate'] < 0.7,
                np.random.randint(3, 10, len(df)),
                np.random.randint(0, 3, len(df))
            )
        
        # lms_login_weekly_avg
        if 'lms_login_frequency' in df.columns:
            df_features['lms_login_weekly_avg'] = df['lms_login_frequency'] / 4.0  # Assume monthly data
        
        # assignment_submit_rate - already exists
        if 'assignment_submission_rate' in df.columns:
            df_features['assignment_submit_rate'] = df['assignment_submission_rate']
        
        # late_submission_rate
        if 'late_submissions' in df.columns and 'assignment_submission_rate' in df.columns:
            total_assignments = 20  # Assume 20 assignments per semester
            submitted = df['assignment_submission_rate'] * total_assignments
            df_features['late_submission_rate'] = np.clip(df['late_submissions'] / np.maximum(submitted, 1), 0, 1)
        
        # discussion_participation - already exists as forum_posts
        if 'forum_posts' in df.columns:
            df_features['discussion_participation'] = df['forum_posts']
        
        # lms_last_login_days - simulate
        df_features['lms_last_login_days'] = np.random.randint(0, 14, len(df))
        
        return df_features
    
    def engineer_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer temporal and behavioral trend features (SRS 4.2.3).
        """
        logger.info("Engineering temporal and behavioral features...")
        
        df_features = df.copy()
        
        # submit_rate_delta_4wk - change in submission rate
        if 'assignment_submission_rate' in df.columns:
            # Simulate historical rate
            historical_rate = np.clip(df['assignment_submission_rate'] + np.random.normal(0.1, 0.15, len(df)), 0, 1)
            df_features['submit_rate_delta_4wk'] = df['assignment_submission_rate'] - historical_rate
        
        # login_frequency_delta - change in login frequency
        if 'lms_login_frequency' in df.columns:
            avg_login = df['lms_login_frequency'].mean()
            df_features['login_frequency_delta'] = df['lms_login_frequency'] - avg_login
        
        # grade_inflection_flag - sudden grade drop
        if 'exam_scores' in df.columns:
            avg_score = df['exam_scores'].mean()
            std_score = df['exam_scores'].std()
            df_features['grade_inflection_flag'] = (df['exam_scores'] < (avg_score - 1.5 * std_score)).astype(int)
        
        return df_features
    
    def engineer_contextual_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer socioeconomic and contextual features (SRS 4.2.4).
        """
        logger.info("Engineering socioeconomic and contextual features...")
        
        df_features = df.copy()
        
        # financial_aid_flag
        if 'socioeconomic_status' in df.columns:
            df_features['financial_aid_flag'] = (df['socioeconomic_status'] == 'LOW').astype(int)
        else:
            df_features['financial_aid_flag'] = np.random.binomial(1, 0.4, len(df))
        
        # outstanding_balance_flag - simulate
        df_features['outstanding_balance_flag'] = np.random.binomial(1, 0.15, len(df))
        
        # first_generation_flag - simulate
        df_features['first_generation_flag'] = np.random.binomial(1, 0.3, len(df))
        
        # commuter_student_flag - simulate
        df_features['commuter_student_flag'] = np.random.binomial(1, 0.35, len(df))
        
        # part_time_enrollment_flag - simulate based on time spent
        if 'time_spent_hours' in df.columns:
            df_features['part_time_enrollment_flag'] = (df['time_spent_hours'] < 10).astype(int)
        else:
            df_features['part_time_enrollment_flag'] = np.random.binomial(1, 0.2, len(df))
        
        return df_features
    
    def engineer_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer all features from the complete catalog.
        """
        logger.info("=" * 80)
        logger.info("Feature Engineering Pipeline")
        logger.info("=" * 80)
        logger.info(f"Input records: {len(df)}")
        logger.info(f"Input features: {len(df.columns)}")
        
        # Apply all feature engineering steps
        df_features = df.copy()
        df_features = self.engineer_academic_features(df_features)
        df_features = self.engineer_engagement_features(df_features)
        df_features = self.engineer_temporal_features(df_features)
        df_features = self.engineer_contextual_features(df_features)
        
        logger.info(f"Output features: {len(df_features.columns)}")
        logger.info("=" * 80)
        
        return df_features
    
    def get_feature_list(self) -> List[str]:
        """Get list of all engineered features."""
        all_features = []
        for category, features in self.feature_catalog.items():
            all_features.extend(features)
        return all_features
    
    def get_feature_importance_description(self) -> Dict[str, str]:
        """Get human-readable descriptions of features."""
        return {
            'current_gpa': 'Current semester GPA (0.0-4.0 scale)',
            'gpa_trend_3sem': 'GPA trajectory over last 3 semesters (slope)',
            'course_pass_rate': 'Proportion of courses with passing grades',
            'grade_variance': 'Variability of grades across courses',
            'failed_courses_cum': 'Cumulative number of failed courses',
            'repeat_course_flag': 'Whether student is repeating any course',
            'attendance_rate_current': 'Current semester attendance rate',
            'consec_absences_max': 'Maximum consecutive absence streak',
            'lms_login_weekly_avg': 'Average LMS logins per week',
            'assignment_submit_rate': 'Rate of assignment submissions',
            'late_submission_rate': 'Proportion of late submissions',
            'discussion_participation': 'Number of discussion posts',
            'lms_last_login_days': 'Days since last LMS login',
            'submit_rate_delta_4wk': 'Change in submission rate (4 weeks)',
            'login_frequency_delta': 'Change in login frequency vs average',
            'grade_inflection_flag': 'Sudden grade drop indicator',
            'financial_aid_flag': 'Receiving financial aid',
            'outstanding_balance_flag': 'Has outstanding balance',
            'first_generation_flag': 'First-generation college student',
            'commuter_student_flag': 'Lives >30 miles from campus',
            'part_time_enrollment_flag': 'Enrolled part-time'
        }


if __name__ == "__main__":
    # Test feature engineering
    from pathlib import Path
    
    # Load sample data
    data_path = Path("data/raw/students.csv")
    if data_path.exists():
        df = pd.read_csv(data_path)
        
        # Engineer features
        engineer = FeatureEngineer()
        df_engineered = engineer.engineer_all_features(df)
        
        # Save engineered features
        output_path = Path("data/processed/students_engineered.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_engineered.to_csv(output_path, index=False)
        
        print(f"\nEngineered features saved to: {output_path}")
        print(f"Total features: {len(df_engineered.columns)}")
        print(f"\nNew features added:")
        new_features = set(df_engineered.columns) - set(df.columns)
        for feature in sorted(new_features):
            print(f"  - {feature}")
    else:
        print(f"Data file not found: {data_path}")
        print("Please run: python scripts/generate_sample_data.py")
