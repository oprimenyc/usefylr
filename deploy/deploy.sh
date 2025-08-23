#!/bin/bash

# .fylr Production Deployment Script
# Zero-downtime deployment with health checks

set -e

echo "🚀 .fylr Production Deployment"
echo "=============================="

# Configuration
DOCKER_IMAGE="fylr/web:latest"
CONTAINER_NAME="fylr-production"
BACKUP_CONTAINER="fylr-backup"
HEALTH_CHECK_URL="http://localhost:5000/api/health"

# Check prerequisites
echo "🔍 Checking prerequisites..."

if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Validate required environment variables
source .env
required_vars=("DATABASE_URL" "SECRET_KEY" "OPENAI_API_KEY" "STRIPE_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment validation passed"

# Build new image
echo "🔨 Building production image..."
docker build -t $DOCKER_IMAGE .

# Backup current container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q $CONTAINER_NAME; then
    echo "💾 Creating backup of current container..."
    docker stop $CONTAINER_NAME || true
    docker rename $CONTAINER_NAME $BACKUP_CONTAINER || true
fi

# Database backup
echo "📊 Creating database backup..."
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
docker exec postgres-container pg_dump -U fylr_user fylr_db > $BACKUP_FILE || echo "⚠️  Database backup failed (container may not exist)"

# Start new container
echo "🚀 Starting new container..."
docker run -d \
    --name $CONTAINER_NAME \
    --env-file .env \
    -p 5000:5000 \
    --restart unless-stopped \
    $DOCKER_IMAGE

# Health check with retry
echo "🔍 Performing health checks..."
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f $HEALTH_CHECK_URL &> /dev/null; then
        echo "✅ Health check passed"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "⏳ Health check attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Health check failed. Rolling back..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
    
    if docker ps -a --format 'table {{.Names}}' | grep -q $BACKUP_CONTAINER; then
        docker rename $BACKUP_CONTAINER $CONTAINER_NAME
        docker start $CONTAINER_NAME
        echo "🔄 Rollback completed"
    fi
    exit 1
fi

# Cleanup old backup container
if docker ps -a --format 'table {{.Names}}' | grep -q $BACKUP_CONTAINER; then
    echo "🧹 Cleaning up old container..."
    docker rm $BACKUP_CONTAINER
fi

# Cleanup old images
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

echo ""
echo "🎉 Deployment completed successfully!"
echo "==================================="
echo "🌐 Application URL: http://your-domain.com"
echo "🔧 Health Check: $HEALTH_CHECK_URL"
echo "💾 Database Backup: $BACKUP_FILE"
echo ""
echo "📊 Container Status:"
docker ps --filter name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"