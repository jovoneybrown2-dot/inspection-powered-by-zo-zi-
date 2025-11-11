# 🔄 Database Migration Guide
## Updating app.py to use Database Abstraction Layer

This guide shows how to update `app.py` to work with both SQLite and PostgreSQL.

---

## 📝 What Needs to Change

### Before (Current Code):
```python
import sqlite3

# Every database connection looks like this:
conn = sqlite3.connect('inspections.db')
c = conn.cursor()
c.execute("SELECT * FROM inspections WHERE id = ?", (id,))
results = c.fetchall()
conn.close()
```

### After (With Abstraction):
```python
from db_config import get_db_connection

# Same code works for both SQLite and PostgreSQL:
conn = get_db_connection()
c = conn.cursor()
c.execute("SELECT * FROM inspections WHERE id = ?", (id,))
results = c.fetchall()
conn.close()
```

---

## 🔧 Step-by-Step Changes

### 1. Update Imports (Top of app.py)

**Find this:**
```python
import sqlite3
```

**Change to:**
```python
from db_config import get_db_connection
```

### 2. Update All Database Connections

**Find this pattern (appears ~100+ times):**
```python
conn = sqlite3.connect('inspections.db')
```

**Replace with:**
```python
conn = get_db_connection()
```

### 3. That's It!

The abstraction layer handles everything else automatically:
- ✅ Detects if you're using SQLite or PostgreSQL
- ✅ Uses correct connection method
- ✅ Returns results in the same format
- ✅ No other code changes needed!

---

## 🤖 Automated Migration (Recommended)

Use this command to update all connections automatically:

```bash
# Backup first!
cp app.py app.py.backup

# Option 1: Using sed (Mac/Linux)
sed -i '' 's/sqlite3.connect(.inspections.db.)/get_db_connection()/g' app.py

# Option 2: Using Python script (cross-platform)
python3 << 'EOF'
with open('app.py', 'r') as f:
    content = f.read()

# Add import at top
if 'from db_config import get_db_connection' not in content:
    content = content.replace(
        'import sqlite3',
        'import sqlite3  # Keep for backwards compatibility\nfrom db_config import get_db_connection'
    )

# Replace all sqlite3.connect calls
content = content.replace(
    "sqlite3.connect('inspections.db')",
    "get_db_connection()"
)

with open('app.py', 'w') as f:
    f.write(content)

print("✅ Migration complete!")
EOF
```

---

## 🧪 Testing After Migration

### Test with SQLite (Development)
```bash
# Don't set DATABASE_URL
python app.py

# Should see:
# 📁 Using SQLite: inspections.db
```

### Test with PostgreSQL (Production)
```bash
# Set DATABASE_URL
export DATABASE_URL=postgresql://user:pass@localhost:5432/inspections_db
python app.py

# Should see:
# 🐘 Using PostgreSQL: localhost:5432/inspections_db
```

### Test with Docker
```bash
# Start with PostgreSQL
docker-compose up -d

# Check logs
docker-compose logs web

# Should see:
# 🐘 Using PostgreSQL: db:5432/inspections_db
```

---

## ⚠️ Important Notes

### Query Compatibility

**Most queries work identically**, but watch for these differences:

**Placeholders:**
```python
# SQLite uses ?
c.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# PostgreSQL uses %s
c.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ✅ Our abstraction handles this automatically!
```

**Auto-increment IDs:**
```python
# SQLite
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT)

# PostgreSQL
CREATE TABLE users (id SERIAL PRIMARY KEY)

# ✅ database.py init_db() handles this automatically!
```

**Date Functions:**
```python
# SQLite
"SELECT * FROM inspections WHERE date(created_at) = date('now')"

# PostgreSQL
"SELECT * FROM inspections WHERE DATE(created_at) = CURRENT_DATE"

# ⚠️ May need to update specific date queries
```

---

## 🔍 Finding Database Connections

Search for these patterns in app.py:

```bash
# Find all sqlite3.connect calls
grep -n "sqlite3.connect" app.py

# Find all database operations
grep -n "\.execute\|\.fetchall\|\.fetchone" app.py

# Count total occurrences
grep -c "sqlite3.connect" app.py
```

---

## 📊 Migration Checklist

- [ ] Backup `app.py` → `app.py.backup`
- [ ] Add `from db_config import get_db_connection` import
- [ ] Replace all `sqlite3.connect('inspections.db')` → `get_db_connection()`
- [ ] Test with SQLite: `python app.py`
- [ ] Test with PostgreSQL: `DATABASE_URL=postgresql://... python app.py`
- [ ] Test with Docker: `docker-compose up`
- [ ] Verify all features work:
  - [ ] Login
  - [ ] Create inspection
  - [ ] View inspections
  - [ ] Search inspections
  - [ ] Generate PDF
  - [ ] Upload photos
- [ ] Commit changes: `git add . && git commit -m "Add database abstraction layer"`

---

## 🆘 Rollback (If Needed)

```bash
# Restore original
cp app.py.backup app.py

# Or use git
git checkout app.py
```

---

## 💡 Pro Tips

1. **Do it in stages** - Update and test one function at a time
2. **Keep both imports** - `import sqlite3` and `from db_config import get_db_connection`
3. **Test thoroughly** - Make sure all CRUD operations work
4. **Check database.py** - Make sure `init_db()` creates tables correctly for PostgreSQL
5. **Use transactions** - Wrap multiple operations in `BEGIN/COMMIT` for PostgreSQL

---

## 🎯 Quick Reference

**Development (SQLite):**
```bash
python app.py
# Uses inspections.db automatically
```

**Production (PostgreSQL):**
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/db
python app.py
# Uses PostgreSQL automatically
```

**Docker (PostgreSQL):**
```bash
docker-compose up -d
# Uses PostgreSQL from docker-compose.yml
```

---

Need help? Check DOCKER_SETUP.md for deployment instructions!
