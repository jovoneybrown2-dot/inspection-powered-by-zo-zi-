# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based inspection management system for health and safety inspections in Jamaica. The application handles multiple types of inspections including food establishments, residential properties, burial sites, swimming pools, barbershops, small hotels, spirit licenses, and institutional facilities.

## Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Run with Gunicorn (production)
gunicorn app:app
```

### Database Operations
```bash
# Initialize database (SQLite - development)
python -c "from database import init_db; init_db()"

# Initialize database (PostgreSQL - production)
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
python -c "from database import init_db; init_db()"

# Generate PostgreSQL schema file
python generate_postgres_schema.py

# Check database schema
python check_schema.py

# Add database columns (if needed)
python add_column.py
```

### Deployment Package Creation
```bash
# Create protected deployment package for client server
python create_deployment_package.py

# This will:
# - Generate PostgreSQL schema
# - Build PyInstaller executable (code is protected)
# - Create deployment package in WRHA_Deployment_Package/
# - Include setup documentation

# Create zip for transfer
zip -r WRHA_Deployment_Package.zip WRHA_Deployment_Package/
```

## Architecture Overview

### Core Components

**Main Application (`app.py`)**
- Flask web server with session management
- Route handlers for all inspection types
- PDF generation using ReportLab
- Authentication system with role-based access (admin, inspector, medical_officer)
- SQLite database integration

**Database Layer (`database.py` + `db_config.py`)**
- Supports both SQLite (development) and PostgreSQL (production)
- Automatic database detection via DATABASE_URL environment variable
- Connection pooling for PostgreSQL (500+ concurrent users)
- Table definitions for inspections, inspection_items, burial_site_inspections, etc.
- CRUD operations for all inspection types
- Database initialization and schema management

**Form Management (`form_management_system.py`)**
- Dynamic form creation and management
- Form templates and items system
- Support for multiple inspection types with configurable checklists

### Database Schema

The system supports both SQLite (development) and PostgreSQL (production) with the following key tables:
- `inspections` - Main inspection records
- `inspection_items` - Individual checklist items for each inspection
- `burial_site_inspections` - Specialized burial site inspections
- `form_templates` - Dynamic form definitions
- `form_items` - Configurable checklist items

### Inspection Types

The system supports multiple inspection forms with predefined checklists:
- Food Establishment (45-item checklist with weighted scoring)
- Residential Properties
- Burial Sites
- Swimming Pools
- Barbershops
- Small Hotels
- Spirit License
- Institutional Facilities

### Frontend Structure

**Templates (`templates/`)**
- Form templates for each inspection type
- Detail views for inspection results
- Admin dashboard and management interfaces
- Authentication pages (login, dashboard)

**Static Assets (`static/`)**
- Offline forms functionality (`js/offline-forms.js`)
- Images and media files for the application

### Key Features

- **Multi-role Authentication**: Admin, inspector, and medical officer roles
- **PDF Report Generation**: Automatic PDF creation for inspection reports
- **Offline Capability**: JavaScript-based offline form functionality
- **Parish-based Organization**: Inspections organized by Jamaican parishes
- **Weighted Scoring System**: Configurable scoring for different inspection criteria
- **Digital Signatures**: Support for inspector and manager signatures

### Database Configuration

**Development (SQLite)**:
- Database file: `inspections.db`
- Automatic creation on first run
- No DATABASE_URL needed

**Production (PostgreSQL)**:
- Set DATABASE_URL environment variable
- Format: `postgresql://user:pass@host:5432/dbname`
- Supports connection pooling for concurrent users
- Import schema: `psql -U user -d dbname -f schema_postgres.sql`

### Deployment Strategy

**For client servers (code protection)**:
1. Run `python create_deployment_package.py`
2. This creates a PyInstaller executable with protected source code
3. Package includes PostgreSQL schema and setup docs
4. Client receives executable only, no source code access
5. They install PostgreSQL on their server
6. Configure via `.env` file only

**For cloud platforms (like Render)**:
1. Create PostgreSQL database
2. Set DATABASE_URL environment variable
3. Deploy directly from source code (Dockerfile included)
4. App auto-detects PostgreSQL and initializes schema