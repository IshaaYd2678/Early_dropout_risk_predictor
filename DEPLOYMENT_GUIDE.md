# Deployment Guide - Early Warning System

Complete guide for deploying the Early Warning System for Student Dropout Risk to production.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Application Deployment](#application-deployment)
5. [Security Configuration](#security-configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows Server 2019+
- **CPU**: 4+ cores
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 100GB+ SSD
- **Python**: 3.9 or higher
- **Node.js**: 16+ (for React frontend)
- **Database**: PostgreSQL 13+ or SQLite (development)

### Required Software
```bash
# Python and pip
python3 --version  # Should be 3.9+
pip3 --version

# Node.js and npm (for React frontend)
node --version  # Should be 16+
npm --version

# PostgreSQL (production)
psql --version  # Should be 13+
```

---

## Environment Setup

### 1. Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd early-warning-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (if using React)
cd frontend
npm install
cd ..
```

### 2. Environment Variables

Create `.env` file in project root:

```bash
# Application
APP_NAME="Early Warning System"
APP_ENV=production
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ews_db
# Or for SQLite: sqlite:///./data/ews.db

# Security
SECRET_KEY=<generate-secure-random-key>
JWT_SECRET_KEY=<generate-secure-random-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# ML Model
MODEL_PATH=data/models/xgboost_model.pkl
FEATURE_NAMES_PATH=data/models/feature_names.pkl

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=<app-password>

# Monitoring
SENTRY_DSN=<your-sentry-dsn>  # Optional
```

### 3. Generate Secure Keys

```python
# Generate SECRET_KEY and JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Database Configuration

### PostgreSQL Setup (Production)

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE ews_db;
CREATE USER ews_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ews_db TO ews_user;
\q
```

### Initialize Database Schema

```bash
# Run migrations
python scripts/init_database.py

# Or use Alembic (if configured)
alembic upgrade head
```

### Load Sample Data (Optional)

```bash
python scripts/generate_sample_data.py
```

---

## Application Deployment

### Option 1: Docker Deployment (Recommended)

#### Build and Run with Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Docker Compose Configuration

The `docker-compose.yml` includes:
- FastAPI backend (port 8000)
- Streamlit dashboard (port 8501)
- PostgreSQL database (port 5432)
- Redis cache (optional, port 6379)

### Option 2: Manual Deployment

#### 1. Train ML Model

```bash
# Generate training data
python scripts/generate_sample_data.py

# Train model
python ml/train.py

# Verify model files exist
ls -la data/models/
```

#### 2. Start Backend API

```bash
# Using uvicorn directly
uvicorn backend.enhanced_server:app --host 0.0.0.0 --port 8000 --workers 4

# Or using gunicorn (production)
gunicorn backend.enhanced_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info
```

#### 3. Start Streamlit Dashboard

```bash
streamlit run dashboard/enhanced_working_app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
```

#### 4. Start React Frontend (Optional)

```bash
cd frontend

# Build for production
npm run build

# Serve with nginx or use serve
npm install -g serve
serve -s dist -l 3000
```

### Option 3: Systemd Services (Linux)

Create service files for automatic startup:

#### Backend Service

```bash
sudo nano /etc/systemd/system/ews-backend.service
```

```ini
[Unit]
Description=Early Warning System Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/early-warning-system
Environment="PATH=/opt/early-warning-system/venv/bin"
ExecStart=/opt/early-warning-system/venv/bin/gunicorn \
  backend.enhanced_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Dashboard Service

```bash
sudo nano /etc/systemd/system/ews-dashboard.service
```

```ini
[Unit]
Description=Early Warning System Dashboard
After=network.target ews-backend.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/early-warning-system
Environment="PATH=/opt/early-warning-system/venv/bin"
ExecStart=/opt/early-warning-system/venv/bin/streamlit run \
  dashboard/enhanced_working_app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable ews-backend ews-dashboard
sudo systemctl start ews-backend ews-dashboard
sudo systemctl status ews-backend ews-dashboard
```

---

## Security Configuration

### 1. Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/ews

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # API Backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Dashboard
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

### 2. SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo certbot renew --dry-run  # Test renewal
```

### 3. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

### 4. Database Security

```bash
# PostgreSQL configuration
sudo nano /etc/postgresql/13/main/pg_hba.conf
```

```
# Only allow local connections
local   all             all                                     peer
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

---

## Monitoring & Maintenance

### 1. Application Monitoring

#### Health Check Endpoints

```bash
# Backend health
curl https://yourdomain.com/api/health

# Expected response:
# {"status": "healthy", "model_loaded": true, "students_loaded": 1247}
```

#### Log Monitoring

```bash
# View backend logs
sudo journalctl -u ews-backend -f

# View dashboard logs
sudo journalctl -u ews-dashboard -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Database Backups

```bash
# Create backup script
sudo nano /opt/scripts/backup_db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/ews"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -U ews_user ews_db | gzip > $BACKUP_DIR/ews_db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: ews_db_$DATE.sql.gz"
```

```bash
# Make executable
sudo chmod +x /opt/scripts/backup_db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /opt/scripts/backup_db.sh
```

### 3. Model Retraining

```bash
# Create retraining script
sudo nano /opt/scripts/retrain_model.sh
```

```bash
#!/bin/bash
cd /opt/early-warning-system
source venv/bin/activate

# Backup current model
cp data/models/xgboost_model.pkl data/models/xgboost_model_backup.pkl

# Retrain
python ml/train.py

# Restart services
sudo systemctl restart ews-backend

echo "Model retrained and services restarted"
```

### 4. Performance Monitoring

Use tools like:
- **Prometheus + Grafana**: Metrics and dashboards
- **Sentry**: Error tracking
- **New Relic / DataDog**: APM
- **Uptime Robot**: Uptime monitoring

---

## Troubleshooting

### Common Issues

#### 1. Model Not Loading

```bash
# Check model files exist
ls -la data/models/

# Verify permissions
sudo chown -R www-data:www-data data/models/

# Check logs
sudo journalctl -u ews-backend -n 50
```

#### 2. Database Connection Errors

```bash
# Test database connection
psql -U ews_user -d ews_db -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

#### 3. High Memory Usage

```bash
# Check memory usage
free -h
htop

# Reduce workers if needed
# Edit service file and reduce --workers parameter
sudo systemctl daemon-reload
sudo systemctl restart ews-backend
```

#### 4. Slow Predictions

```bash
# Check model size
ls -lh data/models/xgboost_model.pkl

# Monitor CPU usage during prediction
top

# Consider caching predictions
# Add Redis for caching (see docker-compose.yml)
```

### Performance Tuning

#### Backend Optimization

```python
# In backend/enhanced_server.py
# Add caching for predictions
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_prediction(student_id: str):
    # Prediction logic
    pass
```

#### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_students_risk_level ON students(current_risk_level);
CREATE INDEX idx_students_department ON students(department);
CREATE INDEX idx_interventions_student ON interventions(student_id);
```

---

## Production Checklist

Before going live, verify:

- [ ] All environment variables configured
- [ ] Database backups automated
- [ ] SSL certificates installed and auto-renewal configured
- [ ] Firewall rules configured
- [ ] Nginx reverse proxy configured
- [ ] Services set to auto-start on boot
- [ ] Monitoring and alerting configured
- [ ] Log rotation configured
- [ ] Model trained and loaded successfully
- [ ] Health check endpoints responding
- [ ] Security headers configured
- [ ] CORS origins restricted to production domains
- [ ] Debug mode disabled
- [ ] Strong passwords and secrets configured
- [ ] Database connections secured
- [ ] API rate limiting configured
- [ ] Documentation updated
- [ ] Team trained on system usage
- [ ] Incident response plan documented
- [ ] Data retention policies implemented
- [ ] FERPA/GDPR compliance verified

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor system health and logs
- Check for errors or anomalies
- Review prediction accuracy

**Weekly:**
- Review fairness metrics
- Analyze intervention outcomes
- Check disk space and performance

**Monthly:**
- Retrain ML model with new data
- Update dependencies and security patches
- Review and optimize database queries
- Generate compliance reports

**Quarterly:**
- Comprehensive security audit
- Performance optimization review
- User feedback analysis
- Capacity planning

---

## Additional Resources

- **API Documentation**: https://yourdomain.com/api/docs
- **Architecture Docs**: `docs/ARCHITECTURE.md`
- **Usage Guide**: `docs/USAGE.md`
- **Quick Start**: `QUICKSTART.md`

---

**Last Updated**: February 25, 2026
**Version**: 1.0.0
