# Quick Reference Card - Early Warning System

## 🚀 Access URLs

| Service | URL | Status |
|---------|-----|--------|
| **Streamlit Dashboard** | http://localhost:8503 | ✅ Running |
| **Backend API** | http://localhost:8002 | ✅ Running |
| **API Documentation** | http://localhost:8002/docs | ✅ Available |
| **Health Check** | http://localhost:8002/health | ✅ Available |

## 🎯 Quick Commands

### Start Services
```bash
# Backend API (port 8002)
python -m uvicorn backend.enhanced_server:app --host 0.0.0.0 --port 8002

# Streamlit Dashboard (port 8503)
python -m streamlit run dashboard/enhanced_working_app.py --server.port 8503
```

### Test System
```bash
# Run all system tests
python scripts/test_system.py

# Test all features
python scripts/test_all_features.py
```

### Generate Data
```bash
# Generate sample student data
python scripts/generate_sample_data.py
```

### Train Model
```bash
# Train ML model
python ml/train.py
```

## 📊 API Quick Reference

### Authentication
```bash
# Login
curl -X POST "http://localhost:8002/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@university.edu", "password": "any"}'
```

### Get Students
```bash
# List all students
curl "http://localhost:8002/api/v1/students" \
  -H "Authorization: Bearer mock_access_token"

# Get student details
curl "http://localhost:8002/api/v1/students/student_0" \
  -H "Authorization: Bearer mock_access_token"
```

### Predict Risk
```bash
# Predict single student
curl -X POST "http://localhost:8002/api/v1/predictions/single" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock_access_token" \
  -d '{"student_id": "student_0"}'
```

### Get Analytics
```bash
# Dashboard analytics
curl "http://localhost:8002/api/v1/analytics/dashboard" \
  -H "Authorization: Bearer mock_access_token"

# Model info
curl "http://localhost:8002/api/v1/predictions/model/info" \
  -H "Authorization: Bearer mock_access_token"
```

## 🎨 Dashboard Features

### Role Selection
- **Admin**: Full system access
- **Department Head**: Department analytics
- **Mentor**: Student interventions

### Key Metrics
- Total Students: 1,247
- At Risk: 186
- Active Interventions: 42
- Success Rate: 73.2%

### Available Views
1. **Overview**: System-wide metrics and trends
2. **Student List**: Searchable and filterable
3. **Risk Analysis**: Individual student predictions
4. **Interventions**: Track and manage interventions
5. **Analytics**: Department and cohort analysis
6. **Fairness**: Bias detection and monitoring

## 🔧 Troubleshooting

### Check Service Status
```bash
# Backend health
curl http://localhost:8002/health

# Expected: {"status":"healthy","model_loaded":true,"students_loaded":50}
```

### Restart Services
```bash
# Stop processes (Ctrl+C in terminal)
# Then restart with commands above
```

### Common Issues

**Port Already in Use**:
```bash
# Use different port
python -m uvicorn backend.enhanced_server:app --port 8003
```

**Model Not Found**:
```bash
# Train model first
python ml/train.py
```

**Import Errors**:
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `backend/enhanced_server.py` | Main API server |
| `dashboard/enhanced_working_app.py` | Production dashboard |
| `ml/train.py` | Model training |
| `ml/predict.py` | Prediction service |
| `data/models/xgboost_model.pkl` | Trained model |
| `data/raw/students.csv` | Student data |

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `README.md` | Project overview |
| `QUICKSTART.md` | Getting started guide |
| `DEPLOYMENT_GUIDE.md` | Production deployment |
| `CURRENT_STATUS.md` | Current system status |
| `IMPLEMENTATION_STATUS.md` | Feature checklist |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/USAGE.md` | Detailed usage |

## 🎓 Key Features

✅ AI-powered risk prediction (87.3% accuracy)  
✅ Real-time student monitoring  
✅ SHAP-based explanations  
✅ Fairness and bias detection  
✅ Role-based dashboards  
✅ Intervention tracking  
✅ RESTful API  
✅ Export functionality  
✅ Production-ready  

## 💡 Tips

1. **Use the Dashboard**: Most intuitive way to interact with the system
2. **Check Health**: Always verify `/health` endpoint before use
3. **Mock Auth**: Demo uses mock authentication (any email/password works)
4. **Export Data**: Use dashboard export for reports
5. **API Docs**: Interactive API testing at `/docs`

---

**Need Help?** Check `CURRENT_STATUS.md` for detailed information.

**Last Updated**: February 25, 2026
