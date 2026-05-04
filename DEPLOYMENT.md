# Deployment Guide

This guide covers deploying the My Tasks Dashboard to a cloud server with PostgreSQL.

## Prerequisites

- Cloud server (AWS EC2, DigitalOcean, etc.) with Ubuntu/Debian
- PostgreSQL database (local or managed service like AWS RDS, DigitalOcean Managed Database)
- Domain name or IP address (optional but recommended)

## Option 1: Deploy to Your Own Server

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib -y

# Install PostgreSQL (if using local database)
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE mytasks;
CREATE USER mytasks_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE mytasks TO mytasks_user;
\q
```

### 3. Deploy Application

```bash
# Clone or upload your application
cd /var/www
sudo mkdir mytasks
sudo chown $USER:$USER mytasks
cd mytasks

# Upload your files or use git
# Copy all files from /Users/sreekanthchityala/nettools/mytasks to /var/www/mytasks

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://mytasks_user:your_secure_password@localhost:5432/mytasks
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=production
HOST=0.0.0.0
PORT=5000
EOF

# Initialize database
python migrate_db.py
```

### 4. Configure Gunicorn Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/mytasks.service
```

Add this content:

```ini
[Unit]
Description=My Tasks Dashboard
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mytasks
Environment="PATH=/var/www/mytasks/venv/bin"
ExecStart=/var/www/mytasks/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl start mytasks
sudo systemctl enable mytasks
sudo systemctl status mytasks
```

### 5. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/mytasks
```

Add this content:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your server IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/mytasks/static;
        expires 30d;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/mytasks /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Setup SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Option 2: Deploy to Heroku

### 1. Install Heroku CLI

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login
```

### 2. Deploy

```bash
cd /Users/sreekanthchityala/nettools/mytasks

# Initialize git if not already
git init
git add .
git commit -m "Initial commit"

# Create Heroku app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# Run migrations
heroku run python migrate_db.py

# Open app
heroku open
```

## Option 3: Deploy to DigitalOcean App Platform

### 1. Push to GitHub

```bash
cd /Users/sreekanthchityala/nettools/mytasks
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/mytasks.git
git push -u origin main
```

### 2. Create App on DigitalOcean

1. Go to DigitalOcean App Platform
2. Click "Create App"
3. Connect your GitHub repository
4. Configure:
   - **Name**: mytasks
   - **Region**: Choose closest to you
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn wsgi:app`

### 3. Add Database

1. In App Platform, add a PostgreSQL database
2. DigitalOcean will automatically set DATABASE_URL

### 4. Set Environment Variables

In App Settings > Environment Variables:
- `SECRET_KEY`: Generate with `python3 -c 'import secrets; print(secrets.token_hex(32))'`
- `FLASK_ENV`: production

### 5. Deploy

Click "Deploy" and wait for deployment to complete.

## Post-Deployment

### 1. Configure GitHub Token

1. Access your deployed app via URL/IP
2. Go to Settings section
3. Enter your GitHub username and token
4. Save settings

### 2. Create Environments

1. Go to Dashboard Links section
2. Click "Manage Environments"
3. Create environments (Production, Staging, etc.)

### 3. Test Features

- Create tasks
- Set reminders (allow browser notifications)
- Import GitHub issues
- Add dashboard links

## Monitoring

### Check Application Logs

**Own Server:**
```bash
sudo journalctl -u mytasks -f
```

**Heroku:**
```bash
heroku logs --tail
```

**DigitalOcean:**
View logs in App Platform dashboard

## Troubleshooting

### Database Connection Issues

Check DATABASE_URL format:
```
postgresql://username:password@host:port/database
```

### Permission Issues

```bash
sudo chown -R www-data:www-data /var/www/mytasks
```

### Nginx Issues

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## Security Recommendations

1. **Use strong SECRET_KEY**: Generate with `secrets.token_hex(32)`
2. **Enable HTTPS**: Use Let's Encrypt SSL certificates
3. **Firewall**: Only allow ports 80, 443, and SSH
4. **Database**: Use strong passwords, restrict access
5. **Regular Updates**: Keep system and dependencies updated

## Backup

### Database Backup

```bash
# Backup
pg_dump -U mytasks_user mytasks > backup.sql

# Restore
psql -U mytasks_user mytasks < backup.sql
```

## Scaling

For high traffic:
- Increase Gunicorn workers: `--workers 4`
- Use Redis for session management
- Add load balancer
- Use CDN for static files