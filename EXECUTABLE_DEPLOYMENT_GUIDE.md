# WRHA Inspection System - Executable Deployment Guide

## Overview

This package contains a **compiled executable version** of the WRHA Inspection Management System. The application code is **protected and cannot be modified**. All Python source code has been compiled into a binary executable.

---

## What's Included

```
wrha_inspection/
├── wrha_inspection          # Main executable (your protected code)
├── _internal/               # Required libraries and dependencies
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JavaScript, images
├── integrity_manifest.json  # Code integrity verification
└── schema_postgres.sql      # Database schema
```

**Total Package Size**: ~115 MB

---

## System Requirements

### Server Requirements:
- **OS**: Ubuntu 20.04+ / Debian 10+ / Windows Server 2019+
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 1GB for application + 10GB for database
- **PostgreSQL**: Version 12 or higher
- **Network**: Internet connection for license validation

### For Linux Deployment (Recommended):
- Ubuntu 20.04 LTS or newer
- PostgreSQL 12+
- Nginx (optional, for reverse proxy)

---

## Step 1: Install PostgreSQL

### On Ubuntu/Debian:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

### On Windows Server:
1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Run installer and follow wizard
3. Remember the postgres user password you set

---

## Step 2: Create Database

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, run:
CREATE DATABASE wrha_inspections;
CREATE USER wrha_admin WITH PASSWORD 'YourSecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE wrha_inspections TO wrha_admin;

# Exit
\q
```

---

## Step 3: Initialize Database Schema

```bash
# Import the schema
psql -U wrha_admin -d wrha_inspections -h localhost -f schema_postgres.sql

# Enter password when prompted
```

---

## Step 4: Configure Environment

Create a `.env` file in the same directory as the executable:

```bash
# Create .env file
nano .env
```

Add the following configuration:

```env
# Database Connection
DATABASE_URL=postgresql://wrha_admin:YourSecurePassword123!@localhost:5432/wrha_inspections

# License Key (Use YOUR parish-specific key)
ZOZI_LICENSE_KEY=ZOZI-XXXX-XXXX-XXXX

# Application Secret (Generate a random string)
SECRET_KEY=your-random-secret-key-here-change-this

# Signing Secret (Keep this confidential)
ZOZI_SIGNING_SECRET=your-signing-secret-here

# License Server (Optional - for remote validation)
ZOZI_LICENSE_SERVER=https://api.zozi-inspections.com

# Application Settings
FLASK_ENV=production
PORT=8000
```

### Parish-Specific License Keys:

- **Westmoreland**: `ZOZI-3515-124D-1AD4`
- **Hanover**: `ZOZI-336B-BD96-22EB`
- **St. James**: `ZOZI-39D2-0A50-C06A`
- **Trelawny**: `ZOZI-65C4-833E-AC66`

⚠️ **Use the correct key for your parish!**

---

## Step 5: Run the Application

### Test Run (Development):
```bash
# Make executable runnable
chmod +x wrha_inspection

# Run the application
./wrha_inspection
```

Access at: http://localhost:5000

Press `CTRL+C` to stop.

---

## Step 6: Production Deployment with Systemd

### Create Systemd Service:

```bash
sudo nano /etc/systemd/system/wrha-inspection.service
```

Add the following content:

```ini
[Unit]
Description=WRHA Inspection Management System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/wrha-inspection
EnvironmentFile=/opt/wrha-inspection/.env
ExecStart=/opt/wrha-inspection/wrha_inspection
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/wrha-inspection

[Install]
WantedBy=multi-user.target
```

### Install and Start Service:

```bash
# Copy files to /opt
sudo mkdir -p /opt/wrha-inspection
sudo cp -r wrha_inspection/ /opt/wrha-inspection/
sudo cp .env /opt/wrha-inspection/
sudo cp schema_postgres.sql /opt/wrha-inspection/
sudo cp integrity_manifest.json /opt/wrha-inspection/

# Set permissions
sudo chown -R www-data:www-data /opt/wrha-inspection
sudo chmod +x /opt/wrha-inspection/wrha_inspection

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable wrha-inspection
sudo systemctl start wrha-inspection

# Check status
sudo systemctl status wrha-inspection
```

---

## Step 7: Configure Firewall

```bash
# Allow application port
sudo ufw allow 8000/tcp

# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Step 8: Setup Nginx Reverse Proxy (Optional but Recommended)

### Install Nginx:
```bash
sudo apt install nginx -y
```

### Configure:
```bash
sudo nano /etc/nginx/sites-available/wrha-inspection
```

Add configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/wrha-inspection /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Default Login Credentials

**Username**: `admin`
**Password**: `admin123`

⚠️ **CRITICAL**: Change this password immediately after first login!

---

## Backup Strategy

### Automated Daily Backup:

```bash
# Create backup script
sudo nano /opt/wrha-inspection/backup.sh
```

Add content:

```bash
#!/bin/bash
BACKUP_DIR="/opt/wrha-inspection/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U wrha_admin -h localhost wrha_inspections | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

Make executable and schedule:

```bash
sudo chmod +x /opt/wrha-inspection/backup.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e

# Add this line:
0 2 * * * /opt/wrha-inspection/backup.sh >> /var/log/wrha-backup.log 2>&1
```

---

## Troubleshooting

### Application Won't Start:
```bash
# Check logs
sudo journalctl -u wrha-inspection -f

# Check PostgreSQL
sudo systemctl status postgresql

# Test database connection
psql -U wrha_admin -d wrha_inspections -h localhost -c "SELECT 1;"
```

### License Validation Fails:
- Verify license key in `.env` is correct
- Check internet connection (for remote validation)
- Verify Installation ID: `cat /opt/wrha-inspection/installation_id.txt`
- Contact Zo-Zi support with Installation ID

### Permission Errors:
```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/wrha-inspection

# Fix executable permission
sudo chmod +x /opt/wrha-inspection/wrha_inspection
```

### Database Connection Fails:
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`
- Test connection manually with psql
- Check PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*-main.log`

---

## Monitoring

### View Application Logs:
```bash
# Real-time logs
sudo journalctl -u wrha-inspection -f

# Last 100 lines
sudo journalctl -u wrha-inspection -n 100

# Logs from today
sudo journalctl -u wrha-inspection --since today
```

### Check Application Status:
```bash
# Service status
sudo systemctl status wrha-inspection

# Check if listening on port
sudo netstat -tulpn | grep 8000

# Process info
ps aux | grep wrha_inspection
```

---

## Code Integrity Protection

**This executable includes built-in tamper detection:**

✅ Code integrity is automatically verified on startup
✅ Modifications to the executable will be detected
✅ Integrity status is reported to Zo-Zi licensing server
✅ Tampering may result in license revocation

**Installation ID**: Auto-generated on first run and stored in `installation_id.txt`

---

## Updates and Maintenance

### Applying Updates:

1. **Stop the service**:
   ```bash
   sudo systemctl stop wrha-inspection
   ```

2. **Backup current version**:
   ```bash
   sudo cp -r /opt/wrha-inspection /opt/wrha-inspection.backup
   ```

3. **Replace executable**:
   ```bash
   sudo cp new_wrha_inspection /opt/wrha-inspection/wrha_inspection
   sudo chmod +x /opt/wrha-inspection/wrha_inspection
   ```

4. **Start service**:
   ```bash
   sudo systemctl start wrha-inspection
   ```

⚠️ **Only install updates provided by Zo-Zi. Do not modify the executable.**

---

## Security Best Practices

✅ Use strong passwords for all accounts
✅ Keep PostgreSQL updated
✅ Enable firewall and allow only necessary ports
✅ Regularly backup database
✅ Monitor logs for suspicious activity
✅ Restrict physical and SSH access to server
✅ Use HTTPS (SSL) in production (via Nginx + Let's Encrypt)
✅ Do NOT share license keys between installations

---

## Support and Contact

**Developer**: Jovoney Brown (Zo-Zi Inspection Systems)
**Email**: support@zozi-inspections.com
**Phone**: [Your Contact Number]

### For Support, Provide:
- Installation ID (from `installation_id.txt`)
- Parish name
- Error logs (from journalctl)
- Description of issue

---

## License Agreement

By running this executable, you agree to the terms in `LICENSE_AGREEMENT.md`:

- ✅ You have a license to USE the software
- ❌ You may NOT modify, reverse engineer, or redistribute
- ❌ Code tampering will void support and may revoke license
- ✅ All updates and fixes must come from Zo-Zi

---

## Important Notes

⚠️ **The executable is COMPILED and PROTECTED**:
- You cannot view or edit the Python source code
- You cannot modify application logic
- All changes must be requested from Zo-Zi

⚠️ **License Expiration**: December 31, 2026
- Contact Zo-Zi for renewal before expiration
- Grace period: 7 days after expiration

⚠️ **No Source Code Provided**:
- This is intentional for code protection
- All customizations must be done by Zo-Zi
- Configuration via `.env` file only

---

**Deployment Date**: February 2026
**Version**: 1.0.0
**Build Type**: PyInstaller Executable
**Developed by**: Zo-Zi Inspection Systems (Jovoney Brown)
