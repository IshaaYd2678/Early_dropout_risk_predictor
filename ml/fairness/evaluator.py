"""
Fairness and bias evaluation using Fairlearn and AIF360.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from fairlearn.metrics import (
    demographic_parity_difference,
    equalized_odds_difference,
    equalized_odds_ratio
)

# Optional AIF360 import
try:
    from aif360.datasets import BinaryLabelDataset
    from aif360.metrics import BinaryLabelDatasetMetric
    from aif360.algorithms.preprocessing import Reweighing
    AIF360_AVAILABLE = True
except ImportError:
    AIF360_AVAILABLE = False

class FairnessEvaluator:
    """Evaluate model fairness across demographic groups."""
    
    def __init__(self, sensitive_attributes=None):
        """Initialize fairness evaluator."""
        self.sensitive_attributes = sensitive_attributes or [
            'gender', 'socioeconomic_status', 'department', 'region'
        ]
        self.results = {}
    
    def evaluate(self, y_true, y_pred, y_pred_proba, sensitive_df, threshold=0.1):
        """
        Evaluate fairness metrics across sensitive attributes.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities
            sensitive_df: DataFrame with sensitive attributes
            threshold: Maximum allowed difference for fairness metrics
        
        Returns:
            dict: Fairness evaluation results
        """
        results = {
            'overall_metrics': {},
            'group_metrics': {},
            'fairness_metrics': {},
            'bias_detected': {}
        }
        
        # Overall performance metrics
        results['overall_metrics'] = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0)
        }
        
        # Evaluate for each sensitive attribute
        for attr in self.sensitive_attributes:
            if attr not in sensitive_df.columns:
                continue
            
            attr_results = self._evaluate_attribute(
                y_true, y_pred, y_pred_proba, sensitive_df[attr], attr, threshold
            )
            results['group_metrics'][attr] = attr_results['group_metrics']
            results['fairness_metrics'][attr] = attr_results['fairness_metrics']
            results['bias_detected'][attr] = attr_results['bias_detected']
        
        self.results = results
        return results
    
    def _evaluate_attribute(self, y_true, y_pred, y_pred_proba, sensitive_values, attr_name, threshold):
        """Evaluate fairness for a specific sensitive attribute."""
        results = {
            'group_metrics': {},
            'fairness_metrics': {},
            'bias_detected': {}
        }
        
        unique_groups = sensitive_values.unique()
        
        # Group-level metrics
        group_metrics = {}
        for group in unique_groups:
            group_mask = sensitive_values == group
            group_y_true = y_true[group_mask]
            group_y_pred = y_pred[group_mask]
            
            if len(group_y_true) > 0:
                group_metrics[group] = {
                    'size': len(group_y_true),
                    'accuracy': accuracy_score(group_y_true, group_y_pred),
                    'precision': precision_score(group_y_true, group_y_pred, zero_division=0),
                    'recall': recall_score(group_y_true, group_y_pred, zero_division=0),
                    'f1_score': f1_score(group_y_true, group_y_pred, zero_division=0),
                    'positive_rate': group_y_pred.mean()
                }
        
        results['group_metrics'] = group_metrics
        
        # Fairness metrics using Fairlearn
        try:
            # Demographic Parity Difference
            dp_diff = demographic_parity_difference(
                y_true, y_pred, sensitive_features=sensitive_values
            )
            
            # Equalized Odds Difference
            eo_diff = equalized_odds_difference(
                y_true, y_pred, sensitive_features=sensitive_values
            )
            
            # Equalized Odds Ratio
            eo_ratio = equalized_odds_ratio(
                y_true, y_pred, sensitive_features=sensitive_values
            )
            
            results['fairness_metrics'] = {
                'demographic_parity_difference': dp_diff,
                'equalized_odds_difference': eo_diff,
                'equalized_odds_ratio': eo_ratio
            }
            
            # Check for bias
            results['bias_detected'] = {
                'demographic_parity': abs(dp_diff) > threshold,
                'equalized_odds': abs(eo_diff) > threshold
            }
            
        except Exception as e:
            print(f"Error calculating fairness metrics for {attr_name}: {e}")
            results['fairness_metrics'] = {}
            results['bias_detected'] = {}
        
        return results
    
    def generate_report(self, output_path='data/fairness_report.txt'):
        """Generate a fairness evaluation report."""
        if not self.results:
            raise ValueError("No evaluation results. Call evaluate() first.")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("FAIRNESS EVALUATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Overall metrics
        report_lines.append("Overall Model Performance:")
        report_lines.append("-" * 40)
        for metric, value in self.results['overall_metrics'].items():
            report_lines.append(f"  {metric.capitalize()}: {value:.4f}")
        report_lines.append("")
        
        # Group metrics and fairness
        for attr, group_metrics in self.results['group_metrics'].items():
            report_lines.append(f"\nSensitive Attribute: {attr}")
            report_lines.append("=" * 80)
            
            # Group-level performance
            report_lines.append("\nGroup-Level Performance:")
            for group, metrics in group_metrics.items():
                report_lines.append(f"\n  {group} (n={metrics['size']}):")
                report_lines.append(f"    Accuracy: {metrics['accuracy']:.4f}")
                report_lines.append(f"    Precision: {metrics['precision']:.4f}")
                report_lines.append(f"    Recall: {metrics['recall']:.4f}")
                report_lines.append(f"    F1-Score: {metrics['f1_score']:.4f}")
                report_lines.append(f"    Positive Rate: {metrics['positive_rate']:.4f}")
            
            # Fairness metrics
            if attr in self.results['fairness_metrics']:
                report_lines.append("\nFairness Metrics:")
                fairness = self.results['fairness_metrics'][attr]
                for metric, value in fairness.items():
                    report_lines.append(f"  {metric}: {value:.4f}")
            
            # Bias detection
            if attr in self.results['bias_detected']:
                report_lines.append("\nBias Detection:")
                bias = self.results['bias_detected'][attr]
                for metric, detected in bias.items():
                    status = "[WARNING] BIAS DETECTED" if detected else "[OK] No bias"
                    report_lines.append(f"  {metric}: {status}")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        
        # Save report
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        # Print report (handle encoding for Windows)
        try:
            print(report_text)
        except UnicodeEncodeError:
            # Fallback: print without special characters
            import sys
            if sys.stdout.encoding != 'utf-8':
                print(report_text.encode('ascii', 'ignore').decode('ascii'))
            else:
                print(report_text)
        
        return report_text
