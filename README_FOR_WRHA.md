# WRHA Inspection Management System
## Deployment Package - Version 1.0.0

---

## 📦 What You Received

This package contains the **complete WRHA Inspection Management System** ready for deployment on your server.

### Package Contents:

1. **`wrha_inspection/`** - Protected executable application (115MB)
   - Your Python code is **compiled and protected**
   - Cannot be viewed or modified
   - Ready to run on Linux servers

2. **`schema_postgres.sql`** - PostgreSQL database schema

3. **`integrity_manifest.json`** - Code integrity verification

4. **Documentation:**
   - `EXECUTABLE_DEPLOYMENT_GUIDE.md` - Complete installation instructions
   - `LICENSE_AGREEMENT.md` - Legal agreement and terms
   - `PARISH_LICENSE_KEYS.txt` - License keys for each parish

---

## 🚀 Quick Start (5 Steps)

### 1. Install PostgreSQL
```bash
sudo apt install postgresql postgresql-contrib
```

### 2. Create Database
```bash
sudo -u postgres psql
CREATE DATABASE wrha_inspections;
CREATE USER wrha_admin WITH PASSWORD 'YourPassword';
GRANT ALL PRIVILEGES ON DATABASE wrha_inspections TO wrha_admin;
\q
```

### 3. Load Schema
```bash
psql -U wrha_admin -d wrha_inspections -f schema_postgres.sql
```

### 4. Configure `.env` File
```env
DATABASE_URL=postgresql://wrha_admin:YourPassword@localhost:5432/wrha_inspections
ZOZI_LICENSE_KEY=ZOZI-XXXX-XXXX-XXXX
SECRET_KEY=your-secret-here
```

### 5. Run Application
```bash
chmod +x wrha_inspection
./wrha_inspection
```

Access at: **http://localhost:5000**

Default login: `admin` / `admin123`

---

## 🔑 Parish License Keys

Each parish has a unique license key (valid until Dec 31, 2026):

- **Westmoreland**: `ZOZI-3515-124D-1AD4`
- **Hanover**: `ZOZI-336B-BD96-22EB`
- **St. James**: `ZOZI-39D2-0A50-C06A`
- **Trelawny**: `ZOZI-65C4-833E-AC66`

⚠️ Use the correct key for your parish in the `.env` file.

---

## 📱 Tablet Optimization

The application is **fully optimized for tablets**:

✅ Works on all tablet sizes (iPad, Android tablets)
✅ Maintains professional desktop layout
✅ Touch-optimized buttons and controls
✅ Smooth scrolling and performance
✅ Tested on tablets from 7" to 12.9"

---

## 🔒 Code Protection Features

Your application includes built-in protection:

1. **Compiled Executable** - Source code is not accessible
2. **License Validation** - Requires valid license key to run
3. **Integrity Monitoring** - Detects tampering attempts
4. **Installation Tracking** - Unique ID per installation
5. **Remote Verification** - Phones home for validation

---

## 📋 System Requirements

- **OS**: Ubuntu 20.04+ (or similar Linux)
- **RAM**: 2GB minimum (4GB recommended)
- **Storage**: 1GB for app + 10GB for database
- **PostgreSQL**: Version 12+
- **Internet**: Required for license validation

---

## 📖 Documentation

For complete instructions, see:

- **`EXECUTABLE_DEPLOYMENT_GUIDE.md`** - Full setup guide
- **`LICENSE_AGREEMENT.md`** - Terms and conditions

---

## 🆘 Support

**Developer**: Jovoney Brown (Zo-Zi Inspection Systems)

**Contact**:
- Email: support@zozi-inspections.com
- Phone: [Your Contact Number]

**For Support, Provide**:
- Parish name
- Installation ID (auto-generated in `installation_id.txt`)
- Error description and logs

---

## ⚠️ Important Reminders

1. **Change default password** immediately after first login
2. **Backup database daily** (instructions in deployment guide)
3. **Do NOT modify** the executable - this will break the application
4. **Keep license key confidential** - do not share between parishes
5. **Contact Zo-Zi** for all updates, customizations, and support

---

## 🔄 License Renewal

- **Current License**: Valid until December 31, 2026
- **Grace Period**: 7 days after expiration
- **Renewal**: Contact Zo-Zi 30 days before expiration

---

## ✅ What's Protected

✅ All Python source code - compiled into executable
✅ Business logic and algorithms - not accessible
✅ Database queries and operations - protected
✅ Report generation code - encrypted
✅ Form validation rules - compiled

You can only configure via `.env` file and PostgreSQL connection.

---

## 📞 Next Steps

1. Read `EXECUTABLE_DEPLOYMENT_GUIDE.md` completely
2. Install PostgreSQL on your server
3. Follow the 5-step Quick Start above
4. Test with default credentials
5. Create user accounts for your team
6. Contact Zo-Zi if you need help

---

**Developed by**: Zo-Zi Inspection Systems (Jovoney Brown)
**Version**: 1.0.0
**Build Date**: February 2026
**Package Type**: PyInstaller Executable (Protected)

---

## 📄 License Agreement

By using this software, you agree to:

- Use the software only as licensed
- Not attempt to reverse engineer or modify
- Report all issues to Zo-Zi for official fixes
- Not share license keys or installation files

See `LICENSE_AGREEMENT.md` for complete terms.

---

**Thank you for choosing Zo-Zi Inspection Systems!**
