# Production Deployment Guide
## Food Inspection Management System

**Prepared for:** IT Director
**Date:** November 12, 2024
**Deployment Time:** 5-10 minutes
**Complexity:** Low

---

## What This Is

A Flask-based web application for managing health and safety inspections in Jamaica. Supports multiple inspection types (food establishments, residential, burial sites, swimming pools, barbershops, hotels, spirit licenses, institutional facilities, and meat processing).

**Current Status:** ✅ Production-ready with Docker deployment

---

## Server Requirements

### Minimum Specifications:
- **CPU:** 2 cores
- **RAM:** 4GB
- **Storage:** 20GB
- **OS:** Any Linux distribution (Ubuntu 20.04+ recommended)

### Required Software:
- **Docker Engine** (20.10+)
- **Docker Compose** (2.0+)
- **Git**

**That's it.** No Python, PostgreSQL, or other dependencies needed.

---

## Deployment Steps

### 1. Clone Repository
```bash
git clone https://github.com/Jovoney5/Powered_by_Zo-Zi_Inspection.git
cd Powered_by_Zo-Zi_Inspection
```

### 2. Configure Environment (Optional but Recommended)
```bash
cp .env.example .env
nano .env
```

**Change these values:**
```bash
POSTGRES_PASSWORD=<use-strong-password-here>
SECRET_KEY=<generate-random-string-here>
```

### 3. Start Application
```bash
docker-compose up -d
```

This command:
- Downloads PostgreSQL database image
- Builds Flask application container
- Starts both services
- Creates persistent data volumes
- Sets up internal networking

### 4. Initialize Database (First Time Only)
```bash
docker-compose exec web python init_docker_db.py
```

### 5. Verify Deployment
```bash
docker-compose ps
```

**Expected output:**
```
NAME                 STATUS              PORTS
inspections_app      Up (healthy)        0.0.0.0:5000->5000/tcp
inspections_db       Up (healthy)        0.0.0.0:5432->5432/tcp
```

### 6. Access Application
```
http://your-server-ip:5000
```

**Default admin credentials:** (Create via application interface)

---

## Architecture

```
┌─────────────────────────────────┐
│   Users (Inspectors/Admins)    │
└────────────┬────────────────────┘
             │
             ↓ HTTP :5000
┌─────────────────────────────────┐
│  Docker Container: WEB          │
│  - Flask Application            │
│  - Gunicorn (4 workers)         │
│  - Python 3.13                  │
└────────────┬────────────────────┘
             │
             ↓ PostgreSQL
┌─────────────────────────────────┐
│  Docker Container: DB           │
│  - PostgreSQL 15                │
│  - Persistent Volume            │
└─────────────────────────────────┘
```

---

## Maintenance Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Web application only
docker-compose logs -f web

# Database only
docker-compose logs -f db
```

### Restart Application
```bash
docker-compose restart
```

### Stop Application
```bash
docker-compose down
```

### Update Application (New Version)
```bash
git pull
docker-compose up -d --build
```

### Database Backup
```bash
# Create backup
docker-compose exec db pg_dump -U inspections_user inspections_db > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T db psql -U inspections_user inspections_db < backup_20241112.sql
```

### Check Container Health
```bash
docker-compose ps
docker stats
```

### Access Database Console
```bash
docker-compose exec db psql -U inspections_user -d inspections_db
```

---

## Port Configuration

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Web App | 5000 | 5000 | HTTP Access |
| PostgreSQL | 5432 | 5432 | Database (internal only) |
| pgAdmin | 80 | 5050 | DB Management (optional) |

**Security Note:** PostgreSQL port 5432 is exposed but should be firewalled. Only Docker containers need access.

---

## Firewall Configuration

### UFW (Ubuntu)
```bash
sudo ufw allow 5000/tcp
sudo ufw enable
```

### Firewalld (RHEL/CentOS)
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

**Do NOT expose port 5432 publicly** - database access is internal only.

---

## SSL/HTTPS Setup (Recommended for Production)

### Option 1: Nginx Reverse Proxy
```bash
# Install nginx
sudo apt install nginx certbot python3-certbot-nginx

# Configure nginx
sudo nano /etc/nginx/sites-available/inspections
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/inspections /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### Option 2: Cloudflare (Easy SSL)
1. Point domain to server IP
2. Enable Cloudflare proxy
3. SSL automatically enabled

---

## Monitoring & Health Checks

### Built-in Health Checks
- **Web container:** HTTP check every 30s on port 5000
- **Database container:** PostgreSQL ready check every 10s

### Container Auto-Restart
Configured with `restart: unless-stopped` - containers restart automatically on failure.

### Check Application Health
```bash
curl http://localhost:5000/
```

**Expected:** HTTP 200 response

---

## Performance Tuning

### For High Traffic (100+ concurrent users)
Edit `docker-compose.yml`:
```yaml
web:
  environment:
    GUNICORN_WORKERS: 8  # Default: 4
```

Then restart:
```bash
docker-compose up -d
```

### Database Performance
For large datasets (10,000+ inspections), consider:
- Increasing PostgreSQL shared_buffers
- Adding database indexes (contact developer)

---

## Troubleshooting

### Problem: Application won't start
```bash
# Check logs
docker-compose logs web

# Common issue: Port already in use
sudo lsof -i :5000
# Kill process using port, then restart
```

### Problem: Database connection errors
```bash
# Check database health
docker-compose exec db pg_isready -U inspections_user

# Restart database
docker-compose restart db
```

### Problem: Out of disk space
```bash
# Check disk usage
df -h

# Clean old Docker images
docker system prune -a
```

### Problem: Slow performance
```bash
# Check resource usage
docker stats

# Increase container resources if needed
```

---

## Backup Strategy

### Recommended Schedule:
- **Daily:** Automated database backups (keep 7 days)
- **Weekly:** Full system backup (keep 4 weeks)
- **Monthly:** Archival backup (keep 12 months)

### Automated Daily Backup Script
Create `/root/backup_inspections.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups/inspections"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR
cd /path/to/Powered_by_Zo-Zi_Inspection

docker-compose exec -T db pg_dump -U inspections_user inspections_db > $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /root/backup_inspections.sh
```

---

## Scaling Options

### Vertical Scaling (More Resources)
Increase server CPU/RAM - application will automatically use additional resources.

### Horizontal Scaling (Load Balancing)
For high availability:
1. Deploy multiple web containers
2. Use nginx or HAProxy for load balancing
3. Share single PostgreSQL instance

**Contact developer for load balancing configuration assistance.**

---

## Security Recommendations

### Before Going Live:

✅ **Change default passwords** in `.env`
✅ **Enable firewall** (only port 5000/80/443)
✅ **Set up SSL/HTTPS** (via nginx or Cloudflare)
✅ **Configure backups** (automated daily)
✅ **Update server** (`sudo apt update && sudo apt upgrade`)
✅ **Disable root SSH** (use sudo user)
✅ **Set up monitoring** (optional: Grafana, Prometheus)

### Ongoing Security:

- Update application monthly: `git pull && docker-compose up -d --build`
- Update Docker images: `docker-compose pull && docker-compose up -d`
- Monitor logs for suspicious activity
- Review user access quarterly

---

## Support & Documentation

### Full Documentation:
- **Docker Setup:** `DOCKER_SETUP.md`
- **Migration Guide:** `MIGRATION_GUIDE.md`
- **Project Info:** `CLAUDE.md`

### Repository:
```
https://github.com/Jovoney5/Powered_by_Zo-Zi_Inspection
```

### Technical Contact:
**Developer:** Jovoney Brown
**GitHub:** Jovoney5

### For Issues:
1. Check logs: `docker-compose logs -f web`
2. Review troubleshooting section above
3. Contact developer via GitHub issues

---

## Quick Reference Card

```bash
# START APPLICATION
docker-compose up -d

# STOP APPLICATION
docker-compose down

# VIEW LOGS
docker-compose logs -f web

# RESTART
docker-compose restart

# UPDATE
git pull && docker-compose up -d --build

# BACKUP DATABASE
docker-compose exec db pg_dump -U inspections_user inspections_db > backup.sql

# CHECK STATUS
docker-compose ps
```

---

## Deployment Checklist

- [ ] Docker & Docker Compose installed
- [ ] Git installed
- [ ] Repository cloned
- [ ] `.env` file configured with secure passwords
- [ ] Firewall configured (port 5000 open)
- [ ] Application started: `docker-compose up -d`
- [ ] Database initialized: `docker-compose exec web python init_docker_db.py`
- [ ] Health check passed: `curl http://localhost:5000/`
- [ ] SSL/HTTPS configured (nginx or Cloudflare)
- [ ] Automated backups configured
- [ ] Monitoring set up (optional)
- [ ] User training completed
- [ ] Go-live approved

---

**System Status:** ✅ Production Ready
**Deployment Complexity:** Low
**Estimated Deployment Time:** 5-10 minutes
**Recommended Go-Live:** After testing with 2-3 users

---

*This document provides complete deployment instructions for IT staff. For developer documentation, see `DOCKER_SETUP.md` and `MIGRATION_GUIDE.md`.*
