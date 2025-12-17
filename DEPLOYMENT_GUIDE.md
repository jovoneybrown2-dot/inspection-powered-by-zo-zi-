# Deployment Guide for IT Department

## Project Overview
Jamaica Ministry of Health Inspection Management System - A Flask-based web application for health and safety inspections on tablets.

## System Requirements

### Server Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **Python**: 3.8 or higher
- **Database**: PostgreSQL 12+
- **Memory**: 2GB RAM minimum (4GB recommended)
- **Storage**: 10GB minimum
- **Web Server**: Gunicorn (included) or Nginx as reverse proxy

### Network Requirements
- **HTTPS**: Required for PWA features and GPS on tablets
- **Port**: 443 (HTTPS) or custom port with SSL certificate
- **Firewall**: Allow inbound connections on web server port

## Pre-Deployment Checklist

- [ ] PostgreSQL database created
- [ ] Database user with full permissions created
- [ ] SSL certificate obtained (Let's Encrypt recommended)
- [ ] Server has internet access for initial setup
- [ ] Python 3.8+ installed
- [ ] pip and virtualenv installed

## Installation Steps

### 1. Copy Project Files
```bash
# Upload all project files to server
cd /opt/
mkdir inspection-system
cd inspection-system
# Copy all files here
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file or set system environment variables:

```bash
# Database Configuration (REQUIRED)
DATABASE_URL=postgresql://username:password@localhost:5432/inspections_db

# Secret Key (REQUIRED - generate a random string)
SECRET_KEY=your-very-long-random-secret-key-here

# Server Configuration (Optional)
PORT=10000
WORKERS=4

# Optional: License Key (if using licensed features)
ZOZI_LICENSE_KEY=your-license-key
```

**To generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Initialize Database
```bash
# Run database initialization
python -c "from database import init_db; init_db()"

# Run migrations
python database.py
```

### 6. Create Admin User
```bash
# Create the first admin user
python reset_admin_password.py YourAdminPassword123

# Verify admin user created
python check_admin.py
```

### 7. Test the Application
```bash
# Test run
python app.py

# Visit http://localhost:5000 in browser
# Login with admin credentials
# Verify all forms load correctly
```

### 8. Production Deployment

#### Option A: Using Gunicorn (Recommended)
```bash
# Start with Gunicorn
gunicorn app:app \
  --bind 0.0.0.0:10000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile access.log \
  --error-logfile error.log \
  --daemon
```

#### Option B: Using Systemd Service (Recommended for Linux)
Create `/etc/systemd/system/inspection-system.service`:

```ini
[Unit]
Description=Jamaica Health Inspection System
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/inspection-system
Environment="DATABASE_URL=postgresql://user:pass@localhost/inspections_db"
Environment="SECRET_KEY=your-secret-key"
ExecStart=/opt/inspection-system/venv/bin/gunicorn app:app \
  --bind 0.0.0.0:10000 \
  --workers 4 \
  --timeout 120
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable inspection-system
sudo systemctl start inspection-system
sudo systemctl status inspection-system
```

#### Option C: Using Nginx as Reverse Proxy
Create `/etc/nginx/sites-available/inspection-system`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    client_max_body_size 50M;  # For photo uploads

    location / {
        proxy_pass http://127.0.0.1:10000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location /static {
        alias /opt/inspection-system/static;
        expires 30d;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/inspection-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Tablet Configuration

### For Inspectors' Tablets:

1. **Access the System:**
   - Open Chrome/Safari on tablet
   - Navigate to `https://your-server-address`

2. **Install as PWA:**
   - Tap "Share" → "Add to Home Screen" (iOS)
   - Tap "Menu" → "Add to Home Screen" (Android)

3. **Enable Permissions:**
   - Allow location access (for GPS coordinates)
   - Allow camera access (for photo attachments)

4. **Login:**
   - Username: (provided by admin)
   - Password: (provided by admin)

### Offline Capability:
- Forms work offline via JavaScript
- Data syncs when connection restored
- Photos stored locally until upload

## Database Backup (IMPORTANT!)

### Daily Backup Script:
```bash
#!/bin/bash
# /opt/inspection-system/backup.sh

BACKUP_DIR="/opt/backups/inspection-db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

pg_dump -h localhost -U dbuser inspections_db | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

Add to crontab:
```bash
# Run daily at 2 AM
0 2 * * * /opt/inspection-system/backup.sh
```

## Monitoring & Maintenance

### Check Application Status:
```bash
sudo systemctl status inspection-system
```

### View Logs:
```bash
# Application logs
tail -f /opt/inspection-system/error.log
tail -f /opt/inspection-system/access.log

# System logs
sudo journalctl -u inspection-system -f
```

### Restart Application:
```bash
sudo systemctl restart inspection-system
```

### Update Application:
```bash
cd /opt/inspection-system
source venv/bin/activate
git pull  # or upload new files
pip install -r requirements.txt
sudo systemctl restart inspection-system
```

## Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] Firewall configured (only ports 80, 443 open)
- [ ] Strong admin password set
- [ ] Database password is strong and secure
- [ ] SECRET_KEY is random and not shared
- [ ] Regular database backups configured
- [ ] Server OS and packages updated
- [ ] PostgreSQL configured to only accept local connections
- [ ] File permissions set correctly (no world-writable files)

## Troubleshooting

### Application won't start:
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
pip list

# Check database connection
python -c "from database import get_db_connection; conn = get_db_connection(); print('DB OK')"
```

### Database connection fails:
```bash
# Test PostgreSQL connection
psql -h localhost -U dbuser -d inspections_db

# Check DATABASE_URL format
echo $DATABASE_URL
```

### Tablets can't connect:
- Verify HTTPS is enabled (required for PWA)
- Check firewall allows connections
- Verify DNS/IP address is correct
- Try from browser first before PWA

### Photos not uploading:
- Check `client_max_body_size` in Nginx (increase if needed)
- Verify disk space available
- Check file permissions on upload directory

## Support Contacts

- **Technical Issues**: Contact system administrator
- **Developer Support**: [Your contact info]
- **Database Issues**: Contact DBA

## Additional Files Included

- `reset_admin_password.py` - Reset admin password
- `check_admin.py` - Verify admin users exist
- `sync_barbershop_checklist.py` - Sync barbershop form data
- `requirements.txt` - Python dependencies
- `CLAUDE.md` - Project documentation

## Production Readiness Status

✅ **Ready for Deployment:**
- All inspection forms functional
- Multi-user authentication
- PDF report generation
- Photo attachments
- GPS tracking
- Offline capability
- Mobile responsive
- PostgreSQL support

⚠️ **Recommended Before Go-Live:**
- Load testing with expected number of tablets
- SSL certificate installation
- Backup strategy confirmed
- User training completed
- Admin user accounts created

---

**Last Updated**: December 2025
**Version**: 1.0.0
