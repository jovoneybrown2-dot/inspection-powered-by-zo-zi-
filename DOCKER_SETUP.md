# 🐳 Docker Setup Guide
## Food Inspection Management System

This guide will help you deploy the Food Inspection Management System using Docker with PostgreSQL.

---

## 📋 Prerequisites

1. **Docker** installed ([Download here](https://www.docker.com/get-started))
2. **Docker Compose** installed (comes with Docker Desktop)
3. Basic command line knowledge

---

## 🚀 Quick Start (For IT Team)

### Option 1: Docker Compose (Recommended - Includes PostgreSQL)

```bash
# 1. Clone the repository
git clone https://github.com/Jovoney5/Powered_by_Zo-Zi_Inspection.git
cd Powered_by_Zo-Zi_Inspection

# 2. Create environment file (optional)
cp .env.example .env
# Edit .env if needed (default settings work fine)

# 3. Start everything (app + database)
docker-compose up -d

# 4. Initialize database (first time only)
docker-compose exec web python init_docker_db.py

# 5. Open browser
# Application: http://localhost:5000
# Database Admin (optional): http://localhost:5050
```

**That's it! 🎉 The system is now running with PostgreSQL!**

---

### Option 2: Docker Only (Without PostgreSQL)

If you have an existing PostgreSQL server:

```bash
# 1. Build the Docker image
docker build -t inspections-app .

# 2. Run with your PostgreSQL connection
docker run -d \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/dbname \
  -e SECRET_KEY=your-secret-key \
  --name inspections-app \
  inspections-app

# 3. Initialize database (first time only)
docker exec inspections-app python init_docker_db.py
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://inspections_user:inspections_password@db:5432/inspections_db

# Database (SQLite - for development only)
# Leave DATABASE_URL unset to use SQLite automatically

# Application
SECRET_KEY=change-this-to-a-random-secret-key
FLASK_ENV=production
PORT=5000
```

### Database Options

**PostgreSQL (Production - Recommended):**
- Set `DATABASE_URL` to your PostgreSQL connection string
- Supports multiple concurrent users
- Data persists across restarts
- Better performance

**SQLite (Development):**
- Don't set `DATABASE_URL` (or leave it blank)
- Single file database
- Perfect for testing
- Not recommended for production with multiple users

---

## 📊 Database Management

### Initialize Database
```bash
# If using docker-compose
docker-compose exec web python init_docker_db.py

# If using docker run
docker exec inspections-app python init_docker_db.py
```

### Access PostgreSQL Database
```bash
# Connect to database
docker-compose exec db psql -U inspections_user -d inspections_db

# Backup database
docker-compose exec db pg_dump -U inspections_user inspections_db > backup.sql

# Restore database
docker-compose exec -T db psql -U inspections_user -d inspections_db < backup.sql
```

### pgAdmin (Database UI)
```bash
# Start with pgAdmin
docker-compose --profile dev up -d

# Access at: http://localhost:5050
# Email: admin@inspections.local
# Password: admin

# Add PostgreSQL server:
# - Host: db
# - Port: 5432
# - Database: inspections_db
# - Username: inspections_user
# - Password: inspections_password
```

---

## 🔒 Production Deployment

### 1. Security Checklist

```bash
# Change default passwords in docker-compose.yml:
- POSTGRES_PASSWORD
- SECRET_KEY
- PGADMIN_DEFAULT_PASSWORD

# Use strong passwords (generate with):
openssl rand -base64 32
```

### 2. Environment-Specific Settings

```bash
# Production
FLASK_ENV=production
FLASK_DEBUG=0

# Development
FLASK_ENV=development
FLASK_DEBUG=1
```

### 3. Port Configuration

```yaml
# docker-compose.yml
services:
  web:
    ports:
      - "80:5000"  # Change left side for different external port
```

### 4. SSL/HTTPS

Use a reverse proxy like Nginx or Traefik:

```yaml
# Example with Traefik labels
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.inspections.rule=Host(`inspections.yourdomain.com`)"
  - "traefik.http.routers.inspections.tls=true"
  - "traefik.http.routers.inspections.tls.certresolver=letsencrypt"
```

---

## 📝 Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Just the app
docker-compose logs -f web

# Just the database
docker-compose logs -f db
```

### Start/Stop Services
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Stop and remove volumes (⚠️ deletes database!)
docker-compose down -v
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# View logs
docker-compose logs -f web
```

---

## 🐛 Troubleshooting

### Application won't start
```bash
# Check logs
docker-compose logs web

# Restart services
docker-compose restart

# Rebuild from scratch
docker-compose down
docker-compose up -d --build
```

### Database connection issues
```bash
# Check if database is running
docker-compose ps

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec web python -c "from db_config import get_db_connection; conn = get_db_connection(); print('✅ Connected!')"
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8000:5000"  # Use 8000 instead of 5000

# Or stop conflicting service
lsof -ti:5000 | xargs kill -9
```

### Database is empty
```bash
# Initialize database
docker-compose exec web python init_docker_db.py

# Check database type being used
docker-compose exec web python -c "from db_config import get_db_type; print(get_db_type())"
```

---

## 📦 Data Persistence

### Where is data stored?

**PostgreSQL:**
- Data is stored in Docker volume: `postgres_data`
- Persists even if containers are deleted
- View volumes: `docker volume ls`

**Uploaded Files:**
- Stored in: `./static/uploads/`
- Mounted as volume in docker-compose.yml

### Backup Everything
```bash
# Backup database
docker-compose exec db pg_dump -U inspections_user inspections_db > backup_$(date +%Y%m%d).sql

# Backup uploaded files
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz static/uploads/

# Backup volumes
docker run --rm -v inspections_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/volume_backup.tar.gz -C /data .
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Docker Compose Stack            │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │   Flask     │───▶│  PostgreSQL  │  │
│  │ Application │    │   Database   │  │
│  │  (Port 5000)│    │  (Port 5432) │  │
│  └─────────────┘    └──────────────┘  │
│         │                    │         │
│         │                    │         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │   Uploads   │    │    pgAdmin   │  │
│  │   Volume    │    │  (Port 5050) │  │
│  └─────────────┘    └──────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

---

## 💡 Tips for IT Team

1. **Use environment variables** - Never hardcode passwords
2. **Set up automated backups** - Use cron jobs for pg_dump
3. **Monitor logs** - Set up log aggregation (e.g., ELK stack)
4. **Resource limits** - Add memory/CPU limits in docker-compose.yml
5. **Use secrets** - For production, use Docker secrets instead of environment variables
6. **Health checks** - Already configured, monitor with `docker-compose ps`
7. **Scale workers** - Adjust Gunicorn workers in Dockerfile based on CPU cores
8. **Load balancer** - For high traffic, add Nginx or HAProxy in front

---

## 🆘 Support

For issues or questions:
- GitHub Issues: https://github.com/Jovoney5/Powered_by_Zo-Zi_Inspection/issues
- Review logs: `docker-compose logs -f`
- Check database: `docker-compose exec web python init_docker_db.py`

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/latest/deploying/)

---

**Built with ❤️ by the Zo-Zi Team**
