"""
Prediction utilities for dropout risk.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import joblib
import pandas as pd
import numpy as np
from ml.xai.explainer import RiskExplainer

class DropoutRiskPredictor:
    """Predict dropout risk for students."""
    
    def __init__(self, model_path='data/models/xgboost_model.pkl', 
                 feature_names_path='data/models/feature_names.pkl',
                 model_type='xgboost'):
        """Initialize predictor with trained model."""
        self.model_path = Path(model_path)
        self.feature_names_path = Path(feature_names_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        if not self.feature_names_path.exists():
            raise FileNotFoundError(f"Feature names not found at {feature_names_path}")
        
        self.model = joblib.load(self.model_path)
        self.feature_names = joblib.load(self.feature_names_path)
        self.explainer = RiskExplainer(self.model, self.feature_names, model_type=model_type)
    
    def prepare_features(self, student_data):
        """Prepare student data for prediction."""
        # Convert to DataFrame if needed
        if isinstance(student_data, dict):
            df = pd.DataFrame([student_data])
        elif isinstance(student_data, pd.DataFrame):
            df = student_data.copy()
        else:
            raise ValueError("student_data must be dict or DataFrame")
        
        # One-hot encode categorical variables
        categorical_cols = ['gender', 'department', 'region', 'socioeconomic_status']
        existing_cats = [col for col in categorical_cols if col in df.columns]
        
        if existing_cats:
            df_encoded = pd.get_dummies(df, columns=existing_cats, drop_first=True)
        else:
            df_encoded = df.copy()
        
        # Ensure all required features are present
        for feature in self.feature_names:
            if feature not in df_encoded.columns:
                df_encoded[feature] = 0
        
        # Select features in correct order
        X = df_encoded[self.feature_names]
        return X
    
    def predict(self, student_data, include_explanation=True):
        """
        Predict dropout risk for student(s).
        
        Args:
            student_data: dict or DataFrame with student features
            include_explanation: Whether to include SHAP explanations
        
        Returns:
            dict: Prediction results with risk score, category, and explanation
        """
        X = self.prepare_features(student_data)
        
        # Predict
        risk_score = self.model.predict_proba(X)[:, 1]
        
        # Categorize risk
        risk_categories = []
        for score in risk_score:
            if score < 0.3:
                risk_categories.append('Low')
            elif score < 0.6:
                risk_categories.append('Medium')
            else:
                risk_categories.append('High')
        
        results = {
            'risk_score': risk_score.tolist() if len(risk_score) > 1 else float(risk_score[0]),
            'risk_category': risk_categories[0] if len(risk_categories) == 1 else risk_categories
        }
        
        # Add explanations if requested
        if include_explanation:
            if len(X) == 1:
                explanation = self.explainer.explain_instance(X.iloc[0:1], top_k=5)
                results['explanation'] = explanation
            else:
                explanations = []
                for i in range(len(X)):
                    exp = self.explainer.explain_instance(X.iloc[i:i+1], top_k=5)
                    explanations.append(exp)
                results['explanations'] = explanations
        
        return results

def predict_risk(student_data, model_path='data/models/xgboost_model.pkl'):
    """Convenience function for quick predictions."""
    predictor = DropoutRiskPredictor(model_path=model_path)
    return predictor.predict(student_data)
