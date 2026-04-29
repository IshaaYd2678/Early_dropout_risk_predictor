"""
Comprehensive test script for all system features.
"""
import sys
from pathlib import Path
import json
import urllib.request
import urllib.parse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

API_URL = "http://127.0.0.1:8000"

def test_api_endpoint(method, endpoint, data=None, params=None):
    """Test an API endpoint."""
    url = f"{API_URL}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    try:
        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method=method
            )
        else:
            req = urllib.request.Request(url, method=method)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return True, result, None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        return False, None, f"HTTP {e.code}: {error_body}"
    except Exception as e:
        return False, None, str(e)

def test_health():
    """Test health endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    success, result, error = test_api_endpoint("GET", "/health")
    if success:
        print(f"[OK] Health check passed")
        print(f"  Status: {result.get('status')}")
        print(f"  Model loaded: {result.get('model_loaded')}")
        return True
    else:
        print(f"[FAIL] Health check failed: {error}")
        return False

def test_root():
    """Test root endpoint."""
    print("\n" + "="*60)
    print("TEST 2: Root Endpoint")
    print("="*60)
    success, result, error = test_api_endpoint("GET", "/")
    if success:
        print(f"[OK] Root endpoint accessible")
        print(f"  Message: {result.get('message')}")
        return True
    else:
        print(f"[FAIL] Root endpoint failed: {error}")
        return False

def test_single_prediction():
    """Test single student prediction."""
    print("\n" + "="*60)
    print("TEST 3: Single Student Prediction")
    print("="*60)
    
    student_data = {
        'student_id': 'STU00001',
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
    
    success, result, error = test_api_endpoint("POST", "/predict", student_data)
    if success:
        print(f"[OK] Prediction successful")
        print(f"  Student ID: {result.get('student_id')}")
        print(f"  Risk Score: {result.get('risk_score'):.2%}")
        print(f"  Risk Category: {result.get('risk_category')}")
        if 'explanation' in result:
            exp = result['explanation']
            print(f"  Top Factors:")
            for i, factor in enumerate(exp.get('top_factors', [])[:3], 1):
                print(f"    {i}. {factor['feature']}: {factor['contribution']:.4f} ({factor['direction']} risk)")
        return True
    else:
        print(f"[FAIL] Prediction failed: {error}")
        return False

def test_batch_prediction():
    """Test batch prediction."""
    print("\n" + "="*60)
    print("TEST 4: Batch Prediction")
    print("="*60)
    
    students = [
        {
            'student_id': 'STU00001',
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
        },
        {
            'student_id': 'STU00002',
            'gender': 'Female',
            'department': 'Science',
            'region': 'Rural',
            'socioeconomic_status': 'Low',
            'semester': 2,
            'attendance_rate': 0.6,
            'gpa': 2.2,
            'assignment_submission_rate': 0.5,
            'exam_scores': 55,
            'lms_login_frequency': 3,
            'late_submissions': 5,
            'participation_score': 40,
            'forum_posts': 1,
            'resource_access_count': 5,
            'time_spent_hours': 8
        }
    ]
    
    success, result, error = test_api_endpoint("POST", "/predict/batch", students)
    if success:
        print(f"[OK] Batch prediction successful")
        print(f"  Total predictions: {result.get('count')}")
        for i, pred in enumerate(result.get('predictions', [])[:2], 1):
            print(f"  Student {i}: {pred.get('student_id')} - {pred.get('risk_category')} ({pred.get('risk_score'):.2%})")
        return True
    else:
        print(f"[FAIL] Batch prediction failed: {error}")
        return False

def test_add_intervention():
    """Test adding an intervention."""
    print("\n" + "="*60)
    print("TEST 5: Add Intervention")
    print("="*60)
    
    intervention = {
        'student_id': 'STU00001',
        'intervention_type': 'Counseling',
        'date': '2026-01-29',
        'notes': 'Initial counseling session',
        'mentor_id': 'MENTOR001',
        'outcome': 'pending'
    }
    
    success, result, error = test_api_endpoint("POST", "/interventions", intervention)
    if success:
        print(f"[OK] Intervention added successfully")
        print(f"  Intervention ID: {result.get('intervention_id')}")
        return True, result.get('intervention_id')
    else:
        print(f"[FAIL] Add intervention failed: {error}")
        return False, None

def test_get_interventions():
    """Test getting interventions."""
    print("\n" + "="*60)
    print("TEST 6: Get Interventions")
    print("="*60)
    
    success, result, error = test_api_endpoint("GET", "/interventions")
    if success:
        print(f"[OK] Retrieved interventions")
        print(f"  Total interventions: {result.get('count')}")
        interventions = result.get('interventions', [])
        if interventions:
            print(f"  Sample intervention:")
            print(f"    Student: {interventions[0].get('student_id')}")
            print(f"    Type: {interventions[0].get('intervention_type')}")
            print(f"    Outcome: {interventions[0].get('outcome')}")
        return True
    else:
        print(f"[FAIL] Get interventions failed: {error}")
        return False

def test_update_intervention_outcome(intervention_id):
    """Test updating intervention outcome."""
    print("\n" + "="*60)
    print("TEST 7: Update Intervention Outcome")
    print("="*60)
    
    if not intervention_id:
        print("[SKIP] Skipping - no intervention ID available")
        return False
    
    success, result, error = test_api_endpoint(
        "PUT",
        f"/interventions/{intervention_id}/outcome",
        params={'outcome': 'risk_reduced'}
    )
    if success:
        print(f"[OK] Outcome updated successfully")
        print(f"  Message: {result.get('message')}")
        return True
    else:
        print(f"[FAIL] Update outcome failed: {error}")
        return False

def test_intervention_stats():
    """Test intervention statistics."""
    print("\n" + "="*60)
    print("TEST 8: Intervention Statistics")
    print("="*60)
    
    success, result, error = test_api_endpoint("GET", "/interventions/stats")
    if success:
        print(f"[OK] Statistics retrieved")
        print(f"  Total interventions: {result.get('total_interventions')}")
        print(f"  By type: {result.get('by_type')}")
        print(f"  By outcome: {result.get('by_outcome')}")
        return True
    else:
        print(f"[FAIL] Get stats failed: {error}")
        return False

def test_ml_predictor():
    """Test ML predictor directly."""
    print("\n" + "="*60)
    print("TEST 9: ML Predictor (Direct)")
    print("="*60)
    
    try:
        from ml.predict import DropoutRiskPredictor
        
        predictor = DropoutRiskPredictor()
        
        student_data = {
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
        
        result = predictor.predict(student_data)
        print(f"[OK] Direct prediction successful")
        print(f"  Risk Score: {result['risk_score']:.2%}")
        print(f"  Risk Category: {result['risk_category']}")
        if 'explanation' in result:
            print(f"  Top Factors:")
            for i, factor in enumerate(result['explanation'].get('top_factors', [])[:3], 1):
                print(f"    {i}. {factor['feature']}: {factor['contribution']:.4f}")
        return True
    except Exception as e:
        print(f"[FAIL] Direct prediction failed: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("EARLY WARNING SYSTEM - COMPREHENSIVE FEATURE TEST")
    print("="*60)
    print("\nTesting all system features...")
    
    results = []
    
    # API Tests
    results.append(("Health Check", test_health()))
    results.append(("Root Endpoint", test_root()))
    results.append(("Single Prediction", test_single_prediction()))
    results.append(("Batch Prediction", test_batch_prediction()))
    
    # Intervention Tests
    success, intervention_id = test_add_intervention()
    results.append(("Add Intervention", success))
    results.append(("Get Interventions", test_get_interventions()))
    results.append(("Update Outcome", test_update_intervention_outcome(intervention_id)))
    results.append(("Intervention Stats", test_intervention_stats()))
    
    # ML Tests
    results.append(("ML Predictor", test_ml_predictor()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All features are working correctly!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")

if __name__ == '__main__':
    main()
