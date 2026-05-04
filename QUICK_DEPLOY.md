# Quick Deployment Guide - Existing Server with PostgreSQL

This guide is for deploying to your server that already has PostgreSQL installed.

## Prerequisites
- Server with PostgreSQL already installed
- SSH access to your server
- Git installed on server

## Step-by-Step Deployment

### Step 1: Connect to Your Server

```bash
ssh your-username@your-server-ip
```

### Step 2: Install Required System Packages

```bash
# Update system
sudo apt update

# Install Python and required packages
sudo apt install python3 python3-pip python3-venv nginx -y

# Install PostgreSQL development files (needed for psycopg2)
sudo apt install libpq-dev python3-dev -y
```

### Step 3: Create PostgreSQL Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# In PostgreSQL prompt, run these commands:
CREATE DATABASE mytasks;
CREATE USER mytasks_user WITH PASSWORD 'YourSecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE mytasks TO mytasks_user;
\q
```

**Note down your database credentials:**
- Database: `mytasks`
- Username: `mytasks_user`
- Password: `YourSecurePassword123!` (change this!)
- Host: `localhost`
- Port: `5432`

### Step 4: Clone Your Application

```bash
# Create directory
sudo mkdir -p /var/www/mytasks
sudo chown $USER:$USER /var/www/mytasks

# Clone from GitHub
cd /var/www/mytasks
git clone https://github.com/sreekanthops/mytasks.git .
```

### Step 5: Set Up Python Virtual Environment

```bash
cd /var/www/mytasks

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables

```bash
# Create .env file
nano .env
```

**Add this content** (replace with your actual values):

```env
DATABASE_URL=postgresql://mytasks_user:YourSecurePassword123!@localhost:5432/mytasks
SECRET_KEY=your-generated-secret-key-here
FLASK_ENV=production
HOST=0.0.0.0
PORT=5000
```

**To generate a secure SECRET_KEY:**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Copy the output and paste it as your SECRET_KEY in .env file.

Save and exit (Ctrl+X, then Y, then Enter)

### Step 7: Initialize Database

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run migration
python migrate_db.py
```

You should see:
```
Starting database migration...
Adding environment_id column to dashboard_link table...
✓ Column added successfully
✓ Environment table created/verified
✓ Migration completed successfully!
```

### Step 8: Test the Application

```bash
# Test run
python app.py
```

Open another terminal and test:
```bash
curl http://localhost:5000
```

If you see HTML output, it's working! Press Ctrl+C to stop.

### Step 9: Set Up Gunicorn Service

```bash
# Deactivate virtual environment first
deactivate

# Create systemd service file
sudo nano /etc/systemd/system/mytasks.service
```

**Add this content:**

```ini
[Unit]
Description=My Tasks Dashboard
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mytasks
Environment="PATH=/var/www/mytasks/venv/bin"
EnvironmentFile=/var/www/mytasks/.env
ExecStart=/var/www/mytasks/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app --access-logfile /var/log/mytasks/access.log --error-logfile /var/log/mytasks/error.log

[Install]
WantedBy=multi-user.target
```

Save and exit.

```bash
# Create log directory
sudo mkdir -p /var/log/mytasks
sudo chown www-data:www-data /var/log/mytasks

# Set correct permissions
sudo chown -R www-data:www-data /var/www/mytasks

# Reload systemd
sudo systemctl daemon-reload

# Start the service
sudo systemctl start mytasks

# Check status
sudo systemctl status mytasks

# Enable to start on boot
sudo systemctl enable mytasks
```

### Step 10: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/mytasks
```

**Add this content** (replace `your-domain.com` with your actual domain or server IP):

```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your server IP

    # Increase timeout for long-running requests
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /var/www/mytasks/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Save and exit.

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/mytasks /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# If test is successful, restart Nginx
sudo systemctl restart nginx
```

### Step 11: Configure Firewall (if UFW is enabled)

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### Step 12: Access Your Application

Open your browser and go to:
- `http://your-server-ip`
- or `http://your-domain.com`

You should see your dashboard!

### Step 13: Configure GitHub Token

1. Go to Settings section in the dashboard
2. Enter your GitHub username: `Sreekanth-Chityala`
3. Enter your GitHub token
4. Save settings

### Step 14: (Optional) Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Certbot will automatically configure Nginx for HTTPS
```

## Useful Commands

### Check Application Status
```bash
sudo systemctl status mytasks
```

### View Application Logs
```bash
# Real-time logs
sudo journalctl -u mytasks -f

# Last 100 lines
sudo journalctl -u mytasks -n 100

# Application logs
sudo tail -f /var/log/mytasks/access.log
sudo tail -f /var/log/mytasks/error.log
```

### Restart Application
```bash
sudo systemctl restart mytasks
```

### Update Application (when you push new code)
```bash
cd /var/www/mytasks
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python migrate_db.py  # if database changes
deactivate
sudo systemctl restart mytasks
```

### Check Nginx Status
```bash
sudo systemctl status nginx
sudo nginx -t  # Test configuration
```

### Database Backup
```bash
# Backup
pg_dump -U mytasks_user -h localhost mytasks > backup_$(date +%Y%m%d).sql

# Restore
psql -U mytasks_user -h localhost mytasks < backup_20260504.sql
```

## Troubleshooting

### Application won't start
```bash
# Check logs
sudo journalctl -u mytasks -n 50

# Check if port 5000 is in use
sudo netstat -tulpn | grep 5000

# Check permissions
ls -la /var/www/mytasks
```

### Database connection error
```bash
# Test database connection
psql -U mytasks_user -h localhost -d mytasks

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check .env file has correct credentials
cat /var/www/mytasks/.env
```

### Nginx 502 Bad Gateway
```bash
# Check if application is running
sudo systemctl status mytasks

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Permission denied errors
```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/mytasks
sudo chmod -R 755 /var/www/mytasks
```

## Security Checklist

- ✅ Strong database password
- ✅ Secure SECRET_KEY generated
- ✅ Firewall configured (UFW)
- ✅ SSL certificate installed (optional but recommended)
- ✅ Application running as www-data user
- ✅ .env file not accessible via web
- ✅ Regular backups configured

## Performance Tuning

### Increase Gunicorn Workers
Edit `/etc/systemd/system/mytasks.service`:
```ini
ExecStart=/var/www/mytasks/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart mytasks
```

### PostgreSQL Optimization
```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Adjust based on your server RAM:
```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
```

```bash
sudo systemctl restart postgresql
```

## Done! 🎉

Your application is now running at:
- HTTP: `http://your-server-ip` or `http://your-domain.com`
- HTTPS: `https://your-domain.com` (if SSL configured)

All features are working:
- ✅ Desktop notifications with sound
- ✅ GitHub issue import
- ✅ Environment management
- ✅ Task tracking
- ✅ Reminders