"""
Test script to verify the system is working correctly.
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import pandas as pd
        import numpy as np
        import sklearn
        import xgboost
        import shap
        print("[OK] Core ML imports successful")
        # Optional imports
        try:
            import fastapi
            import streamlit
            print("[OK] Backend/Dashboard imports successful")
        except ImportError:
            print("[INFO] Backend/Dashboard packages not installed (optional)")
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

def test_data_files():
    """Test that data files exist."""
    print("\nTesting data files...")
    data_path = Path('data/raw/students.csv')
    if data_path.exists():
        print(f"[OK] Data file found: {data_path}")
        return True
    else:
        print(f"[ERROR] Data file not found: {data_path}")
        print("  Run: python scripts/generate_sample_data.py")
        return False

def test_model_files():
    """Test that model files exist."""
    print("\nTesting model files...")
    model_path = Path('data/models/xgboost_model.pkl')
    feature_path = Path('data/models/feature_names.pkl')
    
    if model_path.exists() and feature_path.exists():
        print(f"[OK] Model files found")
        return True
    else:
        print(f"[ERROR] Model files not found")
        print("  Run: python ml/train.py")
        return False

def test_predictor():
    """Test that predictor can be initialized."""
    print("\nTesting predictor...")
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from ml.predict import DropoutRiskPredictor
        predictor = DropoutRiskPredictor()
        print("[OK] Predictor initialized successfully")
        return True
    except FileNotFoundError as e:
        print(f"[ERROR] Predictor initialization failed: {e}")
        print("  Run: python ml/train.py")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_prediction():
    """Test making a prediction."""
    print("\nTesting prediction...")
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from ml.predict import DropoutRiskPredictor
        predictor = DropoutRiskPredictor()
        
        sample_student = {
            'student_id': 'TEST001',
            'gender': 'Male',
            'department': 'Computer Science',
            'region': 'Urban',
            'socioeconomic_status': 'Medium',
            'semester': 3,
            'attendance_rate': 0.75,
            'gpa': 2.8,
            'assignment_submission_rate': 0.7,
            'exam_scores': 65,
            'lms_login_frequency': 5,
            'late_submissions': 3,
            'participation_score': 60,
            'forum_posts': 2,
            'resource_access_count': 10,
            'time_spent_hours': 12
        }
        
        result = predictor.predict(sample_student)
        print(f"[OK] Prediction successful")
        print(f"  Risk Score: {result['risk_score']:.2%}")
        print(f"  Risk Category: {result['risk_category']}")
        return True
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Early Warning System - System Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Data Files", test_data_files()))
    results.append(("Model Files", test_model_files()))
    
    if results[1][1] and results[2][1]:  # If data and model exist
        results.append(("Predictor", test_predictor()))
        results.append(("Prediction", test_prediction()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[SUCCESS] All tests passed! System is ready to use.")
    else:
        print("\n[WARNING] Some tests failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  - Missing data: python scripts/generate_sample_data.py")
        print("  - Missing model: python ml/train.py")
        print("  - Missing dependencies: pip install -r requirements.txt")

if __name__ == '__main__':
    main()
