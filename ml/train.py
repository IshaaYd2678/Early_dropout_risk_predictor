"""
Main training script for dropout risk prediction model.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import yaml
from ml.models.trainer import ModelTrainer
from ml.xai.explainer import RiskExplainer
from ml.fairness.evaluator import FairnessEvaluator
import joblib

def main():
    """Train model and evaluate fairness."""
    print("=" * 80)
    print("Early Warning System - Model Training")
    print("=" * 80)
    
    # Load data
    data_path = Path('data/raw/students.csv')
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        print("Please run: python scripts/generate_sample_data.py")
        return
    
    print(f"\nLoading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} student records")
    
    # Load config
    config_path = Path('configs/model_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Train model
    trainer = ModelTrainer(config_path=str(config_path))
    training_results = trainer.train(df)
    
    # Load trained model and feature names
    model_path = Path(training_results['model_path'])
    model = joblib.load(model_path)
    feature_names = joblib.load(model_path.parent / 'feature_names.pkl')
    
    # Prepare test data for explanations and fairness evaluation
    X, y = trainer.prepare_features(df)
    from sklearn.model_selection import train_test_split
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Generate predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Explainable AI - Global explanations
    print("\n" + "=" * 80)
    print("Generating Global Explanations...")
    print("=" * 80)
    explainer = RiskExplainer(model, feature_names, model_type=config['model']['type'])
    global_explanation = explainer.explain_global(X_test, top_k=10)
    
    print("\nTop 10 Drivers of Dropout Risk:")
    for i, driver in enumerate(global_explanation['top_drivers'], 1):
        print(f"{i}. {driver['feature']}: {driver['importance']:.4f}")
    
    # Fairness Evaluation
    print("\n" + "=" * 80)
    print("Evaluating Fairness and Bias...")
    print("=" * 80)
    
    # Prepare sensitive attributes dataframe
    test_indices = X_test.index
    sensitive_df = df.loc[test_indices, config['fairness']['sensitive_attributes']]
    
    fairness_evaluator = FairnessEvaluator(
        sensitive_attributes=config['fairness']['sensitive_attributes']
    )
    fairness_results = fairness_evaluator.evaluate(
        y_test.values,
        y_pred,
        y_pred_proba,
        sensitive_df,
        threshold=config['fairness']['threshold']
    )
    
    # Generate fairness report
    fairness_evaluator.generate_report('data/fairness_report.txt')
    
    print("\n" + "=" * 80)
    print("Training Complete!")
    print("=" * 80)
    print(f"\nModel saved to: {model_path}")
    print("Fairness report saved to: data/fairness_report.txt")

if __name__ == '__main__':
    main()
