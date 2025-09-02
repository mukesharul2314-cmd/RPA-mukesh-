#!/bin/bash

# Disaster Management System Setup Script
set -e

echo "🌊 Setting up Disaster Management Predictive Analytics System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check system requirements
print_status "Checking system requirements..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    print_success "Docker found"
else
    print_warning "Docker not found. Installing Docker is recommended for production deployment"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    print_success "Docker Compose found"
else
    print_warning "Docker Compose not found. Installing Docker Compose is recommended"
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Dependencies installed"

# Create necessary directories
print_status "Creating directory structure..."
mkdir -p data/{raw,processed,models}
mkdir -p logs
mkdir -p config
mkdir -p ssl
print_success "Directory structure created"

# Copy environment file
print_status "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success "Environment file created from template"
    print_warning "Please edit .env file with your configuration"
else
    print_warning ".env file already exists"
fi

# Generate secret key
print_status "Generating secret key..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
if grep -q "SECRET_KEY=your_secret_key_here" .env; then
    sed -i "s/SECRET_KEY=your_secret_key_here/SECRET_KEY=$SECRET_KEY/" .env
    print_success "Secret key generated and updated in .env"
fi

# Setup database (if PostgreSQL is available)
print_status "Checking database setup..."
if command -v psql &> /dev/null; then
    print_status "PostgreSQL found. You can run the database setup script:"
    print_status "  ./scripts/setup_db.py"
else
    print_warning "PostgreSQL not found. Using SQLite for development"
    # Update .env to use SQLite
    sed -i 's|DATABASE_URL=postgresql://.*|DATABASE_URL=sqlite:///./disaster_analytics.db|' .env
fi

# Create nginx configuration
print_status "Creating nginx configuration..."
cat > config/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # Serve static files
        location /dashboard/ {
            alias /usr/share/nginx/html/dashboard/;
            try_files $uri $uri/ /dashboard/index.html;
        }

        # Proxy API requests
        location /api/ {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://app;
        }

        # Root redirect
        location / {
            return 301 /dashboard/;
        }
    }
}
EOF
print_success "Nginx configuration created"

# Create Prometheus configuration
print_status "Creating Prometheus configuration..."
cat > config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'disaster-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
print_success "Prometheus configuration created"

# Create systemd service file (for production)
print_status "Creating systemd service file..."
cat > disaster-analytics.service << 'EOF'
[Unit]
Description=Disaster Management Predictive Analytics
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/disaster-analytics
Environment=PATH=/opt/disaster-analytics/venv/bin
ExecStart=/opt/disaster-analytics/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
print_success "Systemd service file created"

# Run tests
print_status "Running tests to verify installation..."
if python -m pytest tests/ -v --tb=short; then
    print_success "All tests passed"
else
    print_warning "Some tests failed. Check the output above."
fi

# Final instructions
print_success "Setup completed successfully!"
echo ""
print_status "Next steps:"
echo "1. Edit .env file with your API keys and configuration"
echo "2. For development:"
echo "   python -m src.main"
echo "3. For production with Docker:"
echo "   docker-compose up -d"
echo "4. Access the dashboard at: http://localhost:8000/dashboard/"
echo "5. API documentation at: http://localhost:8000/docs"
echo ""
print_status "For more information, see the README.md file"
