"""
Model training utilities with advanced techniques.
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import (classification_report, confusion_matrix, roc_auc_score, 
                            precision_recall_curve, f1_score, recall_score, precision_score)
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
import yaml
import warnings
warnings.filterwarnings('ignore')

class ModelTrainer:
    """Train and evaluate dropout risk prediction models."""
    
    def __init__(self, config_path='configs/model_config.yaml'):
        """Initialize trainer with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model_type = self.config['model']['type']
        self.model = None
        self.feature_names = None
        self.scaler = None
        
    def prepare_features(self, df):
        """Prepare features for training."""
        # Select feature columns
        feature_cols = []
        for category in self.config['features'].values():
            feature_cols.extend(category)
        
        # Handle missing columns
        available_cols = [col for col in feature_cols if col in df.columns]
        
        # One-hot encode categorical variables
        categorical_cols = ['gender', 'department', 'region', 'socioeconomic_status']
        df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
        
        # Get all feature columns (including encoded ones)
        all_feature_cols = available_cols + [col for col in df_encoded.columns 
                                            if col not in df.columns and col != 'dropped_out']
        
        X = df_encoded[all_feature_cols]
        y = df['dropped_out']
        
        self.feature_names = X.columns.tolist()
        return X, y
    
    def train(self, df, save_path='data/models'):
        """Train the model with advanced techniques."""
        print(f"\n{'='*80}")
        print(f"Training {self.model_type} model with enhanced features...")
        print(f"{'='*80}")
        
        # Prepare data
        X, y = self.prepare_features(df)
        
        print(f"\n📊 Dataset Info:")
        print(f"   Total samples: {len(X)}")
        print(f"   Features: {len(X.columns)}")
        print(f"   Dropout rate: {y.mean():.2%}")
        print(f"   Class distribution: {y.value_counts().to_dict()}")
        
        # Split data
        test_size = self.config['training']['test_size']
        val_size = self.config['training']['validation_size']
        random_state = self.config['training']['random_state']
        
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=val_size/(test_size), 
            random_state=random_state, stratify=y_temp
        )
        
        print(f"\n📈 Data Split:")
        print(f"   Training: {len(X_train)} samples")
        print(f"   Validation: {len(X_val)} samples")
        print(f"   Test: {len(X_test)} samples")
        
        # Feature scaling
        if self.config['training'].get('scale_features', False):
            print(f"\n⚙️  Applying feature scaling...")
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Convert back to DataFrame
            X_train = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
            X_val = pd.DataFrame(X_val_scaled, columns=X_val.columns, index=X_val.index)
            X_test = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
        
        # Handle class imbalance with SMOTE
        if self.config['training'].get('use_smote', False):
            print(f"\n⚖️  Applying SMOTE for class imbalance...")
            print(f"   Before SMOTE: {y_train.value_counts().to_dict()}")
            smote = SMOTE(random_state=random_state)
            X_train, y_train = smote.fit_resample(X_train, y_train)
            print(f"   After SMOTE: {y_train.value_counts().to_dict()}")
        
        # Calculate scale_pos_weight for XGBoost
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
        
        # Initialize model
        if self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                max_depth=self.config['xgboost']['max_depth'],
                learning_rate=self.config['xgboost']['learning_rate'],
                n_estimators=self.config['xgboost']['n_estimators'],
                subsample=self.config['xgboost']['subsample'],
                colsample_bytree=self.config['xgboost']['colsample_bytree'],
                min_child_weight=self.config['xgboost'].get('min_child_weight', 1),
                gamma=self.config['xgboost'].get('gamma', 0),
                reg_alpha=self.config['xgboost'].get('reg_alpha', 0),
                reg_lambda=self.config['xgboost'].get('reg_lambda', 1),
                scale_pos_weight=scale_pos_weight,
                objective=self.config['xgboost']['objective'],
                eval_metric=self.config['xgboost']['eval_metric'],
                random_state=random_state,
                n_jobs=-1
            )
        elif self.model_type == 'logistic_regression':
            self.model = LogisticRegression(
                random_state=random_state, 
                max_iter=1000,
                class_weight='balanced'
            )
        elif self.model_type == 'decision_tree':
            self.model = DecisionTreeClassifier(
                random_state=random_state, 
                max_depth=10,
                class_weight='balanced'
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Train model
        print(f"\n🚀 Training model...")
        if self.model_type == 'xgboost':
            # Simple fit without early stopping for compatibility
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train)
        
        # Evaluate
        print(f"\n{'='*80}")
        print(f"📊 Model Performance")
        print(f"{'='*80}")
        
        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)
        test_score = self.model.score(X_test, y_test)
        
        # Predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Comprehensive metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        print(f"\n🎯 Accuracy Scores:")
        print(f"   Train Accuracy: {train_score:.4f}")
        print(f"   Validation Accuracy: {val_score:.4f}")
        print(f"   Test Accuracy: {test_score:.4f}")
        
        print(f"\n📈 Advanced Metrics:")
        print(f"   AUC-ROC: {auc_score:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall: {recall:.4f}")
        print(f"   F1-Score: {f1:.4f}")
        
        print(f"\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Retained', 'Dropped Out']))
        
        print(f"\n🔢 Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(f"   True Negatives:  {cm[0][0]:>6}")
        print(f"   False Positives: {cm[0][1]:>6}")
        print(f"   False Negatives: {cm[1][0]:>6}")
        print(f"   True Positives:  {cm[1][1]:>6}")
        
        # Cross-validation
        print(f"\n🔄 Cross-Validation (5-fold)...")
        cv_scores = cross_val_score(self.model, X_train, y_train, 
                                   cv=self.config['training']['cv_folds'],
                                   scoring='roc_auc')
        print(f"   CV AUC-ROC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Feature importance (for tree-based models)
        if hasattr(self.model, 'feature_importances_'):
            print(f"\n🌟 Top 10 Most Important Features:")
            feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            for idx, row in feature_importance.head(10).iterrows():
                print(f"   {row['feature']:.<40} {row['importance']:.4f}")
        
        # Save model
        print(f"\n💾 Saving model...")
        Path(save_path).mkdir(parents=True, exist_ok=True)
        model_path = Path(save_path) / f'{self.model_type}_model.pkl'
        joblib.dump(self.model, model_path)
        print(f"   ✅ Model saved to {model_path}")
        
        # Save feature names
        feature_path = Path(save_path) / 'feature_names.pkl'
        joblib.dump(self.feature_names, feature_path)
        print(f"   ✅ Feature names saved")
        
        # Save scaler if used
        if self.scaler is not None:
            scaler_path = Path(save_path) / 'scaler.pkl'
            joblib.dump(self.scaler, scaler_path)
            print(f"   ✅ Scaler saved")
        
        print(f"\n{'='*80}")
        print(f"✅ Training Complete!")
        print(f"{'='*80}")
        
        return {
            'train_score': train_score,
            'val_score': val_score,
            'test_score': test_score,
            'auc_score': auc_score,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'cv_score': cv_scores.mean(),
            'model_path': str(model_path)
        }
    
    def predict_risk_score(self, X):
        """Predict dropout risk probability."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        return self.model.predict_proba(X)[:, 1]
    
    def categorize_risk(self, risk_score):
        """Categorize risk score into Low/Medium/High."""
        thresholds = self.config['model']['risk_thresholds']
        if risk_score < thresholds['low']:
            return 'Low'
        elif risk_score < thresholds['medium']:
            return 'Medium'
        else:
            return 'High'
