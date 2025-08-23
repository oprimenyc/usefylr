#!/bin/bash

# .fylr Quick Start Script
# Development environment setup

set -e

echo "🚀 .fylr Quick Start Setup"
echo "=========================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before continuing."
    echo "   Required: OPENAI_API_KEY, STRIPE_SECRET_KEY, SECRET_KEY"
    read -p "Press Enter when you've updated the .env file..."
fi

# Generate random SECRET_KEY if not set
if ! grep -q "SECRET_KEY=your-super-secret" .env; then
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/SECRET_KEY=your-super-secret.*/SECRET_KEY=$SECRET_KEY/" .env
    echo "✅ Generated random SECRET_KEY"
fi

# Build and start services
echo "🔨 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if curl -f http://localhost:5000/api/health &> /dev/null; then
    echo "✅ Backend API is healthy"
else
    echo "❌ Backend API is not responding"
    docker-compose logs web
    exit 1
fi

# Run database migrations (if implemented)
echo "📊 Setting up database..."
# docker-compose exec web python -m alembic upgrade head

echo ""
echo "🎉 .fylr is now running!"
echo "========================"
echo "🌐 Web App: http://localhost:5000"
echo "🔧 API Health: http://localhost:5000/api/health"
echo "📊 Database: localhost:5432"
echo "🔄 Redis: localhost:6379"
echo ""
echo "📝 To stop: docker-compose down"
echo "📜 To view logs: docker-compose logs -f"