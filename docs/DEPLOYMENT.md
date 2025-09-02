# Deployment Guide

## Overview

This guide covers deployment options for the Disaster Management Predictive Analytics system, from development to production environments.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ with PostGIS extension
- Redis 7+
- Docker and Docker Compose (recommended)
- Nginx (for production)

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd disaster-analytics
```

### 2. Environment Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/disaster_analytics
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENWEATHER_API_KEY=your_openweather_api_key
USGS_API_KEY=your_usgs_api_key
NOAA_API_KEY=your_noaa_api_key

# Application
DEBUG=False
SECRET_KEY=your_secret_key_here
API_HOST=0.0.0.0
API_PORT=8000

# Alerts
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
SENDGRID_API_KEY=your_sendgrid_api_key
ALERT_EMAIL_FROM=alerts@yourdomain.com
```

## Development Deployment

### Quick Start

```bash
# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Activate virtual environment
source venv/bin/activate

# Setup database
python scripts/setup_db.py --sample-data

# Start application
python -m src.main
```

Access the application:
- Dashboard: http://localhost:8000/dashboard/
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Manual Setup

1. **Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Setup Database**
```bash
# PostgreSQL
createdb disaster_analytics
python scripts/setup_db.py

# Or SQLite (for development)
export DATABASE_URL=sqlite:///./disaster_analytics.db
python scripts/setup_db.py
```

3. **Run Application**
```bash
python -m src.main
```

## Docker Deployment

### Development with Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Production with Docker

1. **Update Environment**
```bash
# Copy production environment
cp .env.example .env.production
# Edit with production values
```

2. **Build and Deploy**
```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

3. **Setup SSL (Optional)**
```bash
# Generate SSL certificates
mkdir ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private.key -out ssl/certificate.crt

# Update nginx configuration for HTTPS
```

## Production Deployment

### Server Requirements

**Minimum:**
- 2 CPU cores
- 4 GB RAM
- 50 GB storage
- Ubuntu 20.04+ or CentOS 8+

**Recommended:**
- 4+ CPU cores
- 8+ GB RAM
- 100+ GB SSD storage
- Load balancer for high availability

### System Setup

1. **Install Dependencies**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql-15 postgresql-15-postgis-3 \
  redis-server nginx supervisor curl

# CentOS/RHEL
sudo dnf install -y python3.11 postgresql15-server postgresql15-contrib \
  redis nginx supervisor curl
```

2. **Database Setup**
```bash
# PostgreSQL
sudo -u postgres createuser -s disaster_user
sudo -u postgres createdb -O disaster_user disaster_analytics
sudo -u postgres psql -d disaster_analytics -c "CREATE EXTENSION postgis;"
```

3. **Application Setup**
```bash
# Create application directory
sudo mkdir -p /opt/disaster-analytics
sudo chown $USER:$USER /opt/disaster-analytics
cd /opt/disaster-analytics

# Clone and setup
git clone <repository-url> .
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup database
python scripts/setup_db.py
```

4. **Systemd Service**
```bash
# Copy service file
sudo cp disaster-analytics.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable disaster-analytics
sudo systemctl start disaster-analytics
```

5. **Nginx Configuration**
```bash
# Copy nginx config
sudo cp config/nginx.conf /etc/nginx/sites-available/disaster-analytics
sudo ln -s /etc/nginx/sites-available/disaster-analytics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Monitoring Setup

1. **Prometheus**
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-*/prometheus /usr/local/bin/
sudo mv prometheus-*/promtool /usr/local/bin/

# Copy configuration
sudo mkdir -p /etc/prometheus
sudo cp config/prometheus.yml /etc/prometheus/
```

2. **Grafana**
```bash
# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

## High Availability Setup

### Load Balancer Configuration

```nginx
upstream disaster_app {
    server app1.example.com:8000;
    server app2.example.com:8000;
    server app3.example.com:8000;
}

server {
    listen 80;
    server_name disaster.example.com;
    
    location / {
        proxy_pass http://disaster_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Database Replication

1. **Master-Slave Setup**
```bash
# On master server
sudo -u postgres psql -c "CREATE USER replicator REPLICATION LOGIN CONNECTION LIMIT 1 ENCRYPTED PASSWORD 'password';"

# Configure postgresql.conf
wal_level = replica
max_wal_senders = 3
wal_keep_segments = 64

# Configure pg_hba.conf
host replication replicator slave_ip/32 md5
```

2. **Backup Strategy**
```bash
# Daily backups
0 2 * * * pg_dump disaster_analytics | gzip > /backup/disaster_$(date +\%Y\%m\%d).sql.gz

# Retention policy (keep 30 days)
0 3 * * * find /backup -name "disaster_*.sql.gz" -mtime +30 -delete
```

## Security Considerations

### Application Security

1. **Environment Variables**
```bash
# Use secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Restrict API access
API_ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
```

2. **Database Security**
```sql
-- Create restricted user
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE disaster_analytics TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

3. **Firewall Configuration**
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # PostgreSQL (internal only)
sudo ufw deny 6379/tcp  # Redis (internal only)
sudo ufw enable
```

### SSL/TLS Setup

```bash
# Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Maintenance

### Regular Tasks

1. **Database Maintenance**
```bash
# Weekly vacuum
0 1 * * 0 sudo -u postgres vacuumdb -a -z

# Monthly reindex
0 2 1 * * sudo -u postgres reindexdb disaster_analytics
```

2. **Log Rotation**
```bash
# Configure logrotate
sudo tee /etc/logrotate.d/disaster-analytics << EOF
/opt/disaster-analytics/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload disaster-analytics
    endscript
}
EOF
```

3. **Updates**
```bash
# Application updates
cd /opt/disaster-analytics
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart disaster-analytics
```

### Monitoring

1. **Health Checks**
```bash
# Application health
curl -f http://localhost:8000/health || echo "Application down"

# Database health
sudo -u postgres pg_isready -d disaster_analytics
```

2. **Performance Monitoring**
```bash
# System resources
htop
iotop
nethogs

# Application metrics
curl http://localhost:8000/api/v1/status
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

2. **Application Errors**
```bash
# Check application logs
sudo journalctl -u disaster-analytics -f

# Check application status
sudo systemctl status disaster-analytics

# Check disk space
df -h
```

3. **Performance Issues**
```bash
# Check system resources
free -h
top
iostat

# Check database performance
sudo -u postgres psql -d disaster_analytics -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Recovery Procedures

1. **Database Recovery**
```bash
# From backup
sudo -u postgres dropdb disaster_analytics
sudo -u postgres createdb disaster_analytics
gunzip -c /backup/disaster_20240101.sql.gz | sudo -u postgres psql disaster_analytics
```

2. **Application Recovery**
```bash
# Restart services
sudo systemctl restart disaster-analytics
sudo systemctl restart nginx
sudo systemctl restart postgresql
sudo systemctl restart redis
```

## Scaling

### Horizontal Scaling

1. **Multiple Application Instances**
```bash
# Deploy on multiple servers
# Use load balancer to distribute traffic
# Share database and Redis instances
```

2. **Database Scaling**
```bash
# Read replicas for read-heavy workloads
# Connection pooling with PgBouncer
# Database sharding for very large datasets
```

### Vertical Scaling

1. **Resource Optimization**
```bash
# Increase server resources
# Optimize database configuration
# Tune application settings
```

For more detailed information, see the individual component documentation in the `docs/` directory.
