# System Architecture

## Overview

The Early Warning System for Student Dropout Risk is an end-to-end AI-driven system designed to identify at-risk students early and enable timely interventions.

## Architecture Components

### 1. Data Layer

- **Raw Data Storage**: `data/raw/` - Contains original student data
- **Processed Data**: `data/processed/` - Contains cleaned and feature-engineered data
- **Model Artifacts**: `data/models/` - Stores trained models and feature names
- **Interventions Database**: SQLite database for tracking interventions

### 2. Machine Learning Layer

#### Models (`ml/models/`)
- **ModelTrainer**: Handles training of multiple model types (XGBoost, Logistic Regression, Decision Trees)
- Supports risk categorization (Low/Medium/High)
- Cross-validation and performance evaluation

#### Explainable AI (`ml/xai/`)
- **RiskExplainer**: SHAP-based explanations
  - Instance-level explanations (per-student)
  - Global explanations (overall drivers)
  - Feature contribution analysis

#### Fairness (`ml/fairness/`)
- **FairnessEvaluator**: Comprehensive bias evaluation
  - Demographic Parity
  - Equalized Odds
  - Group-level performance metrics
  - Bias detection and reporting

### 3. Data Engineering (`pipelines/`)

- **DataPipeline**: ETL pipeline for data processing
  - Extract: Load from raw sources
  - Transform: Clean, handle missing values, engineer features
  - Load: Save processed data

### 4. Backend API (`backend/`)

- **FastAPI Server**: RESTful API endpoints
  - `/predict`: Single student prediction
  - `/predict/batch`: Batch predictions
  - `/interventions`: CRUD operations for interventions
  - `/interventions/stats`: Intervention statistics

### 5. Frontend Dashboard (`dashboard/`)

- **Streamlit Dashboard**: Interactive web interface
  - Overview: Key metrics and visualizations
  - Student Risk Analysis: Individual student predictions with explanations
  - Intervention Tracking: Record and monitor interventions
  - Fairness Report: View bias evaluation results

## Data Flow

```
Raw Data → ETL Pipeline → Processed Data → Model Training → Trained Model
                                                                    ↓
Student Data → Feature Engineering → Prediction → Risk Score + Explanation
                                                                    ↓
                                                          Dashboard/API
```

## Model Training Pipeline

1. Load raw student data
2. Feature engineering and preparation
3. Train model (XGBoost/Logistic Regression/Decision Tree)
4. Evaluate performance (accuracy, AUC-ROC)
5. Generate global explanations
6. Evaluate fairness across demographics
7. Save model artifacts

## Prediction Pipeline

1. Receive student data
2. Feature engineering (one-hot encoding, normalization)
3. Model prediction (risk probability)
4. Risk categorization (Low/Medium/High)
5. SHAP explanation generation
6. Return prediction + explanation

## Fairness Evaluation

- Evaluates model performance across:
  - Gender
  - Socioeconomic status
  - Department
  - Region
- Metrics:
  - Demographic Parity Difference
  - Equalized Odds Difference
  - Group-level accuracy, precision, recall

## Intervention Tracking

- SQLite database stores:
  - Student ID
  - Intervention type
  - Date and notes
  - Mentor ID
  - Outcome (risk_reduced/retained/dropped_out/pending)
- Tracks intervention effectiveness
- Enables outcome monitoring

## Technology Stack

- **ML**: scikit-learn, XGBoost, SHAP
- **Fairness**: Fairlearn, AIF360
- **Backend**: FastAPI, SQLite
- **Frontend**: Streamlit, Plotly
- **Data**: Pandas, NumPy

## Security & Privacy

- Data anonymization support
- Secure API endpoints
- Access control (can be extended)
- No sensitive attributes used directly as predictors

## Scalability Considerations

- Model can be retrained periodically
- Batch prediction support
- Efficient SHAP computation
- Database indexing for interventions
