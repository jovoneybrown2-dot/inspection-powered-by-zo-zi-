# WRHA Inspection System - Deployment Instructions

## System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **Python**: 3.8 or higher
- **PostgreSQL**: 12 or higher
- **Memory**: Minimum 2GB RAM
- **Storage**: Minimum 10GB available disk space

---

## Step 1: Install PostgreSQL

### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### On Windows Server:
Download and install PostgreSQL from: https://www.postgresql.org/download/windows/

---

## Step 2: Create Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE wrha_inspections;

# Create user with password
CREATE USER wrha_admin WITH PASSWORD 'your_secure_password_here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE wrha_inspections TO wrha_admin;

# Exit
\q
```

---

## Step 3: Initialize Database Schema

```bash
# Import schema
psql -U wrha_admin -d wrha_inspections -f schema_postgres.sql
```

---

## Step 4: Install Python Dependencies

```bash
# Install Python 3 and pip (if not already installed)
sudo apt install python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Step 5: Configure Environment Variables

Create a `.env` file in the application directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://wrha_admin:your_secure_password_here@localhost:5432/wrha_inspections

# License Configuration (Provided by Zo-Zi)
ZOZI_LICENSE_KEY=ZOZI-XXXX-XXXX-XXXX

# Security Keys (DO NOT SHARE)
ZOZI_SIGNING_SECRET=your_signing_secret_here
SECRET_KEY=your_flask_secret_key_here

# Optional: Remote License Server
ZOZI_LICENSE_SERVER=https://api.zozi-inspections.com
```

---

## Step 6: License Key Assignment

Each parish has been assigned a unique license key:

- **Westmoreland Parish**: `ZOZI-3515-124D-1AD4`
- **Hanover Parish**: `ZOZI-336B-BD96-22EB`
- **St. James Parish**: `ZOZI-39D2-0A50-C06A`
- **Trelawny Parish**: `ZOZI-65C4-833E-AC66`

**IMPORTANT**: Use the correct license key for your parish in the `.env` file.

---

## Step 7: Run the Application

### Development Mode (Testing):
```bash
source venv/bin/activate
python app.py
```

Access at: http://localhost:5000

### Production Mode (Recommended):
```bash
source venv/bin/activate
gunicorn -c gunicorn_config.py app:app
```

---

## Step 8: Setup Systemd Service (Linux - Production)

Create `/etc/systemd/system/wrha-inspection.service`:

```ini
[Unit]
Description=WRHA Inspection System
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/wrha-inspection
Environment="PATH=/opt/wrha-inspection/venv/bin"
ExecStart=/opt/wrha-inspection/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wrha-inspection
sudo systemctl start wrha-inspection
sudo systemctl status wrha-inspection
```

---

## Default Admin Credentials

**Username**: `admin`
**Password**: `admin123`

**⚠️ IMPORTANT**: Change the admin password immediately after first login!

---

## Firewall Configuration

Open port 8000 (or your chosen port):
```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

---

## Backup Recommendations

### Daily Database Backup:
```bash
# Create backup script
cat > /opt/wrha-inspection/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/wrha-inspection/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U wrha_admin wrha_inspections > "$BACKUP_DIR/backup_$DATE.sql"
find $BACKUP_DIR -mtime +30 -delete  # Keep 30 days
EOF

chmod +x /opt/wrha-inspection/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /opt/wrha-inspection/backup.sh
```

---

## Troubleshooting

### Database Connection Issues:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U wrha_admin -d wrha_inspections -c "SELECT 1;"
```

### License Validation Issues:
- Verify license key in `.env` file
- Check internet connection (for remote validation)
- Contact Zo-Zi support if license is invalid

### Application Logs:
```bash
# View application logs
sudo journalctl -u wrha-inspection -f
```

---

## Support

For technical support or issues:
- **Developer**: Jovoney Brown (Zo-Zi)
- **Email**: support@zozi-inspections.com
- **Phone**: [Your Contact Number]

**⚠️ IMPORTANT LICENSE TERMS**:
- This software is licensed, not sold
- Modification of source code is strictly prohibited
- Only authorized personnel may access the server
- All issues must be reported to Zo-Zi for official fixes
- See LICENSE_AGREEMENT.md for complete terms

---

## Security Best Practices

1. ✅ Use strong passwords for all accounts
2. ✅ Keep the system updated: `sudo apt update && sudo apt upgrade`
3. ✅ Enable firewall and allow only necessary ports
4. ✅ Regularly backup the database
5. ✅ Do NOT share license keys between installations
6. ✅ Do NOT modify application files (integrity monitoring is active)
7. ✅ Review audit logs regularly for suspicious activity

---

## Code Integrity Monitoring

This application includes built-in code integrity monitoring:
- Any modifications to application files will be detected
- Tampering will be reported to Zo-Zi licensing server
- License may be revoked if unauthorized changes are detected
- Contact Zo-Zi for all updates and modifications

**Installation ID**: Auto-generated on first run and stored in `installation_id.txt`

---

**Deployment Date**: February 2026
**Version**: 1.0.0
**Developed by**: Zo-Zi Inspection Systems
