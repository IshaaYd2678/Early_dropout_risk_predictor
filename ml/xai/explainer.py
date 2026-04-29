"""
Explainable AI utilities using SHAP.
"""
import shap
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

class RiskExplainer:
    """Generate explanations for dropout risk predictions."""
    
    def __init__(self, model, feature_names, model_type='xgboost'):
        """Initialize explainer with trained model."""
        self.model = model
        self.feature_names = feature_names
        self._model_type = model_type
        self._explainer = None
    
    def _init_explainer(self, X_sample):
        """Initialize SHAP explainer with sample data."""
        if self._explainer is not None:
            return
        
        # Initialize SHAP explainer based on model type
        if self._model_type == 'xgboost':
            self._explainer = shap.TreeExplainer(self.model)
        elif self._model_type == 'logistic_regression':
            # Sample data for background
            if len(X_sample) > 100:
                background = X_sample.sample(100, random_state=42)
            else:
                background = X_sample
            self._explainer = shap.LinearExplainer(self.model, background)
        else:
            # Use KernelExplainer as fallback
            if len(X_sample) > 100:
                background = X_sample.sample(100, random_state=42)
            else:
                background = X_sample
            self._explainer = shap.KernelExplainer(self.model.predict_proba, background)
        
        return self._explainer
    
    @property
    def explainer(self):
        """Lazy initialization of explainer."""
        if self._explainer is None:
            raise ValueError("Explainer not initialized. Call _init_explainer() first.")
        return self._explainer
    
    def explain_instance(self, X_instance, top_k=5):
        """
        Explain prediction for a single student instance.
        
        Returns:
            dict: Explanation with risk score, category, and top contributing factors
        """
        # Initialize explainer if needed (use instance as background)
        self._init_explainer(X_instance)
        
        # Get prediction
        risk_score = self.model.predict_proba(X_instance)[0, 1]
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X_instance)
        
        # Handle multi-output models
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Use positive class
        
        # Get feature contributions
        feature_contributions = {}
        for i, feature in enumerate(self.feature_names):
            if i < len(shap_values[0]):
                feature_contributions[feature] = float(shap_values[0][i])
        
        # Sort by absolute contribution
        sorted_features = sorted(
            feature_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        # Get top contributing factors
        top_factors = [
            {
                'feature': feat,
                'contribution': contrib,
                'direction': 'increases' if contrib > 0 else 'decreases'
            }
            for feat, contrib in sorted_features[:top_k]
        ]
        
        # Categorize risk
        if risk_score < 0.3:
            risk_category = 'Low'
        elif risk_score < 0.6:
            risk_category = 'Medium'
        else:
            risk_category = 'High'
        
        return {
            'risk_score': float(risk_score),
            'risk_category': risk_category,
            'top_factors': top_factors,
            'all_contributions': feature_contributions
        }
    
    def explain_global(self, X_sample, top_k=10):
        """
        Generate global explanations showing overall drivers of dropout risk.
        
        Returns:
            dict: Global feature importance and summary statistics
        """
        # Initialize explainer
        self._init_explainer(X_sample)
        
        # Sample data for efficiency
        if len(X_sample) > 1000:
            X_sample = X_sample.sample(1000, random_state=42)
        
        # Get SHAP values for sample
        shap_values = self.explainer.shap_values(X_sample)
        
        # Handle multi-output models
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        # Calculate mean absolute SHAP values (feature importance)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        # Create feature importance dataframe
        importance_df = pd.DataFrame({
            'feature': self.feature_names[:len(mean_abs_shap)],
            'importance': mean_abs_shap
        }).sort_values('importance', ascending=False)
        
        # Get top drivers
        top_drivers = importance_df.head(top_k).to_dict('records')
        
        return {
            'top_drivers': top_drivers,
            'feature_importance': importance_df.to_dict('records')
        }
    
    def visualize_shap(self, X_instance, save_path=None):
        """Generate SHAP visualization plots."""
        # Initialize explainer if needed
        self._init_explainer(X_instance)
        
        shap_values = self.explainer.shap_values(X_instance)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        # Get expected value
        expected_value = self.explainer.expected_value
        if isinstance(expected_value, list):
            expected_value = expected_value[1]
        
        # Waterfall plot
        shap.waterfall_plot(
            shap.Explanation(
                values=shap_values[0],
                base_values=expected_value,
                data=X_instance.values[0],
                feature_names=self.feature_names
            ),
            show=False
        )
        
        if save_path:
            import matplotlib.pyplot as plt
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
