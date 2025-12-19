# Render Deployment Fix Guide

## Problem Summary

Your Render deployment has two issues:

1. **PostgreSQL connection fails** - Wrong DATABASE_URL format
2. **SQLite fallback fails** - Missing `parish` and `first_login` columns in users table

## Solution 1: Fix PostgreSQL Connection (RECOMMENDED)

### Step 1: Get the Internal Database URL

1. Log in to your Render dashboard
2. Go to your PostgreSQL database: **dpg-d4eadlfpm1nc738nsamg**
3. Look for **"Internal Database URL"** (NOT the external URL)
4. Copy the full internal connection string - it should look like:
   ```
   postgresql://user:password@dpg-d4eadlfpm1nc738nsamg-a.oregon-postgres.render.com:5432/inspections_db
   ```
   (Note: The hostname will be the full `.render.com` domain with a port number)

### Step 2: Update Web Service Environment Variable

1. Go to your **Web Service** (powered-by-zo-zi-inspection)
2. Navigate to **Environment** tab
3. Find or add the `DATABASE_URL` environment variable
4. Paste the **Internal Database URL** from Step 1
5. Click **Save Changes**
6. Your service will automatically redeploy

### Step 3: Verify

Once redeployed, check your logs. You should see:
```
🐘 Using PostgreSQL: dpg-d4eadlfpm1nc738nsamg-a.oregon-postgres.render.com:5432/inspections_db
✅ PostgreSQL connection pool initialized (10-500 connections)
```

## Solution 2: Use SQLite Fallback (NOT RECOMMENDED for Production)

If you want to use SQLite instead of PostgreSQL:

### Option A: Let Database Initialize Automatically

The `database.py` file already has migrations to add the missing columns. Simply:

1. Remove or clear the `DATABASE_URL` environment variable in Render
2. Redeploy
3. The app will use SQLite and run migrations automatically

### Option B: Manual Migration (if needed)

If automatic migration fails, you can run:

```bash
python add_parish_column.py
```

This will add the `parish` and `first_login` columns to the SQLite database.

## Understanding the Error

From your logs:

```
⚠️  PostgreSQL pool initialization failed: could not translate host name "dpg-d4eadlfpm1nc738nsamg-a" to address
```

This happens because:
- The DATABASE_URL is using the **short hostname** instead of the **full internal hostname**
- Render's internal network requires the full `.render.com` domain
- The port shows as `None` which means the URL is malformed

## Recommendation

**Use PostgreSQL (Solution 1)** because:
- ✅ Better performance for multiple concurrent users
- ✅ Connection pooling supports 500+ inspectors
- ✅ ACID compliance for data integrity
- ✅ Better suited for production workloads

SQLite should only be used for:
- Local development
- Testing
- Single-user scenarios

## Common Render PostgreSQL URL Formats

**External URL** (for connecting from outside Render):
```
postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com:5432/dbname
```

**Internal URL** (for web services on Render):
```
postgresql://user:pass@dpg-xxxxx-a:5432/dbname
```

Make sure you're using the **Internal URL** when setting `DATABASE_URL` in your web service.

## Need Help?

If you continue to have issues:

1. Check that your PostgreSQL database is in the same region as your web service
2. Verify the DATABASE_URL is set in the **web service**, not the database
3. Check the database credentials haven't changed
4. Make sure the database name matches (`inspections_db`)

## Testing Locally

To test PostgreSQL connection locally:

```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:pass@host:5432/inspections_db"

# Run the app
python app.py
```

You should see:
```
🐘 Using PostgreSQL: host:5432/inspections_db
```
