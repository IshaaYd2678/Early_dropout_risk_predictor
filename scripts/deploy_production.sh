#!/bin/bash
# Production deployment script for Early Warning System

set -e  # Exit on error

echo "========================================="
echo "Early Warning System - Production Deploy"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Do not run this script as root${NC}"
    exit 1
fi

# Check required files
echo -e "\n${YELLOW}Checking required files...${NC}"
required_files=(".env.production" "Dockerfile" "docker-compose.production.yml" "requirements.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Missing required file: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Found: $file${NC}"
done

# Check Docker
echo -e "\n${YELLOW}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose is installed${NC}"

# Load environment variables
echo -e "\n${YELLOW}Loading environment variables...${NC}"
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
fi

# Check if model exists
echo -e "\n${YELLOW}Checking ML model...${NC}"
if [ ! -f "data/models/xgboost_model.pkl" ]; then
    echo -e "${YELLOW}⚠️  ML model not found. Training model...${NC}"
    python ml/train.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Model trained successfully${NC}"
    else
        echo -e "${RED}❌ Model training failed${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ ML model found${NC}"
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p logs data/models data/raw ssl
echo -e "${GREEN}✅ Directories created${NC}"

# Generate SSL certificates (self-signed for testing)
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo -e "\n${YELLOW}Generating self-signed SSL certificates...${NC}"
    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -days 365 \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo -e "${GREEN}✅ SSL certificates generated${NC}"
    echo -e "${YELLOW}⚠️  For production, replace with real certificates from Let's Encrypt${NC}"
fi

# Build Docker images
echo -e "\n${YELLOW}Building Docker images...${NC}"
docker-compose -f docker-compose.production.yml build
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker images built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Stop existing containers
echo -e "\n${YELLOW}Stopping existing containers...${NC}"
docker-compose -f docker-compose.production.yml down
echo -e "${GREEN}✅ Existing containers stopped${NC}"

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
docker-compose -f docker-compose.production.yml up -d
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check health
echo -e "\n${YELLOW}Checking service health...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo -e "${YELLOW}⏳ Waiting for backend... (${attempt}/${max_attempts})${NC}"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo -e "${YELLOW}Showing logs:${NC}"
    docker-compose -f docker-compose.production.yml logs backend
    exit 1
fi

# Show running containers
echo -e "\n${YELLOW}Running containers:${NC}"
docker-compose -f docker-compose.production.yml ps

# Show logs
echo -e "\n${YELLOW}Recent logs:${NC}"
docker-compose -f docker-compose.production.yml logs --tail=20

echo -e "\n========================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "========================================="
echo -e "\n${GREEN}Services:${NC}"
echo -e "  Backend API: http://localhost:8000"
echo -e "  API Docs: http://localhost:8000/api/docs"
echo -e "  Health Check: http://localhost:8000/health"
echo -e "\n${YELLOW}Useful commands:${NC}"
echo -e "  View logs: docker-compose -f docker-compose.production.yml logs -f"
echo -e "  Stop services: docker-compose -f docker-compose.production.yml down"
echo -e "  Restart: docker-compose -f docker-compose.production.yml restart"
echo -e "  Check status: docker-compose -f docker-compose.production.yml ps"
echo ""
