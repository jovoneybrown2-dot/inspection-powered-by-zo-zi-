# 🔐 Zo-Zi Inspection System - Security Testing Guide

This guide explains how the new security features work and how to test them.

---

## 📋 What Was Implemented

### 1. **Code Integrity Checking**
- Detects if anyone modifies your code
- Shows warning banner if code is tampered with
- Reports modifications to your monitoring server

### 2. **License Key System**
- Validates license keys on startup
- Tracks which institution is using the software
- Can run in grace period mode if server is unreachable

### 3. **Audit Logging**
- Records all important actions (logins, inspections, form edits)
- Stored locally in `audit_log.jsonl`
- Sent to your monitoring server

### 4. **Support Access System**
- Admins can temporarily enable access for Zo-Zi support
- Time-limited access codes (4 hours by default)
- All support access is logged

---

## 🚀 How To Test

### **Test 1: Check Security on Startup**

**What it does:** When your app starts, it performs security checks.

**How to test:**

```bash
# Start your app
python app.py
```

**What you'll see:**

```
======================================================================
🔐 ZO-ZI INSPECTION SYSTEM - SECURITY CHECK
======================================================================

📋 Installation ID: a1b2c3d4-e5f6-7890-1234-567890abcdef

🔍 Checking code integrity...
   ✅ Code integrity verified - Version 1.0.0

🔑 Checking license...
   License key found: ZOZI-DEMO-20...
   ✅ License valid
      Institution: Demo Institution
      Status: Valid

📡 Sending startup telemetry...
   ✅ Telemetry sent

======================================================================
✅ SECURITY CHECK COMPLETE
======================================================================
```

**What this means:**
- ✅ **Installation ID**: Unique identifier for this install
- ✅ **Code Integrity**: Verified nobody changed your code
- ✅ **License**: Valid license key found
- ✅ **Telemetry**: Sent status to your monitoring server

---

### **Test 2: License Key Validation**

**What it does:** Checks if the license key is valid.

**Test with valid license:**

```bash
# Set environment variable
export ZOZI_LICENSE_KEY=ZOZI-DEMO-2024-TEST

# Test validation
python license_manager.py validate ZOZI-DEMO-2024-TEST
```

**Expected output:**
```
🔍 Testing License: ZOZI-DEMO-2024-TEST
   Valid: True
   Institution: Demo Institution
   Message: Valid
```

**Test with invalid license:**

```bash
python license_manager.py validate ZOZI-FAKE-BAD-KEY
```

**Expected output:**
```
🔍 Testing License: ZOZI-FAKE-BAD-KEY
   Valid: False
   Institution: None
   Message: Invalid license key
```

**Test app without license:**

```bash
# Unset license key
unset ZOZI_LICENSE_KEY

# Start app
python app.py
```

**What you'll see:**
```
🔑 Checking license...
   ⚠️  No license key found (ZOZI_LICENSE_KEY environment variable)
      Running in DEMO MODE
```

---

### **Test 3: Code Integrity Detection**

**What it does:** Detects if someone modifies your code.

**Test tampering detection:**

```bash
# 1. Start app normally (integrity valid)
python app.py
# You'll see: ✅ Code integrity verified

# 2. Stop the app (Ctrl+C)

# 3. Modify a critical file
echo "# TEST MODIFICATION" >> app.py

# 4. Start app again
python app.py
```

**Expected output:**
```
🔍 Checking code integrity...
   ❌ CODE INTEGRITY FAILED!
      Reason: Modified: app.py
      Modified files: app.py
```

**What happens:**
- Red warning banner appears on ALL pages
- Watermark: "MODIFIED - NOT OFFICIAL ZO-ZI VERSION"
- Your monitoring server is notified

**To fix:**
```bash
# Undo the modification
git checkout app.py

# Or regenerate manifest
python integrity_check.py generate 1.0.0
```

---

### **Test 4: Audit Logging**

**What it does:** Records all important actions.

**Test audit logging:**

```bash
# 1. Create some test log entries
python audit_log.py test
```

**Expected output:**
```
🧪 Testing audit logging...
  ✓ Logged test action
  ✓ Logged inspection creation

📊 Audit Log Stats:
  Total entries: 2
  Actions by type: {'test_action': 1, 'inspection_created': 1}
```

**Read audit log:**

```bash
# Read last 10 entries
python audit_log.py read 10
```

**Expected output:**
```
📋 Last 10 audit entries:

  [2025-11-21T18:30:00.000Z]
    Action: inspection_created
    User: inspector1
    Details: {'inspection_id': 123, 'form_type': 'Food Establishment', ...}

  [2025-11-21T18:29:00.000Z]
    Action: test_action
    User: test_user
    Details: {'test': 'data'}
```

**View statistics:**

```bash
python audit_log.py stats
```

**Expected output:**
```
📊 Audit Log Statistics:

  Total Entries: 45
  First Entry: 2025-11-20T10:00:00.000Z
  Last Entry: 2025-11-21T18:30:00.000Z

  Actions by Type:
    user_login: 15
    inspection_created: 20
    form_modified: 5
    user_created: 3
    support_access_enabled: 2

  Actions by User:
    admin: 10
    inspector1: 20
    inspector2: 15
```

---

### **Test 5: Support Access System**

**What it does:** Allows temporary access for Zo-Zi support.

**Test enabling support access:**

```bash
# Enable support access for 4 hours
python support_access.py enable admin_user 4
```

**Expected output:**
```
🔓 Support Access Enabled:
   Code: ZOZI-1234-5678-9012
   Expires: 2025-11-21T22:30:00.000Z
   Duration: 4 hours

   Give this code to Zo-Zi Support to access your system
```

**Test checking status:**

```bash
python support_access.py status
```

**Expected output:**
```
📊 Support Access Status:
   Enabled: True
   Code: ZOZI-1234-5678-9012
   Expires: 2025-11-21T22:30:00.000Z
   Hours Remaining: 3.8
   Enabled By: admin_user
```

**Test code validation:**

```bash
# Test with correct code
python support_access.py validate ZOZI-1234-5678-9012
```

**Expected output:**
```
🔍 Validation Result:
   Valid: True
   Message: Valid support code
   Time Remaining: 3.8 hours
```

**Test with wrong code:**

```bash
python support_access.py validate ZOZI-WRONG-CODE-HERE
```

**Expected output:**
```
🔍 Validation Result:
   Valid: False
   Message: Invalid support code
   Time Remaining: None
```

**Test disabling:**

```bash
python support_access.py disable
```

**Expected output:**
```
🔒 Support access disabled
```

---

### **Test 6: Support Access via Web Interface**

**What it does:** Admin can enable support access through web interface.

**Test steps:**

1. **Start your app:**
   ```bash
   python app.py
   ```

2. **Log in as admin:**
   - Go to `http://localhost:5000`
   - Login with admin credentials

3. **Go to support access page:**
   - Navigate to `/admin/support-access`
   - Or add link to admin panel

4. **Enable support access:**
   - Click "Enable Support Access"
   - Choose duration (4 hours)
   - Click "Generate Code"

5. **You'll see:**
   - Support code displayed: `ZOZI-1234-5678-9012`
   - Expiration time
   - Copy button to share with Zo-Zi support

6. **Test Zo-Zi support login:**
   - Open new browser/incognito window
   - Go to `http://localhost:5000/zozi-support-login`
   - Enter the support code
   - You should be logged in as support user

---

### **Test 7: Generate License Keys**

**What it does:** Creates license keys for institutions.

**Generate a license key:**

```bash
python license_manager.py generate "Kingston Health Department" 2025-12-31
```

**Expected output:**
```
🔑 Generated License Key:
   Key: ZOZI-A3B7-C9D2-E1F4
   Institution: Kingston Health Department
   Expires: 2025-12-31
```

**Use the generated key:**

```bash
# Set it as environment variable
export ZOZI_LICENSE_KEY=ZOZI-A3B7-C9D2-E1F4

# Start app
python app.py
```

**You'll see:**
```
🔑 Checking license...
   License key found: ZOZI-A3B7-C9...
   ✅ License valid
      Institution: Kingston Health Department
      Status: Valid
```

---

## 📊 What You Can Monitor

### **Files Created:**

1. **`installation_id.txt`** - Unique ID for this installation
2. **`integrity_manifest.json`** - File hashes for integrity checking
3. **`audit_log.jsonl`** - Complete audit trail (one JSON per line)
4. **`last_validation.json`** - Last license validation (for grace period)

### **What Gets Sent to Your Server:**

**On Startup:**
```json
{
  "event": "app_started",
  "installation_id": "a1b2c3d4-...",
  "version": "1.0.0",
  "integrity_valid": true,
  "license_valid": true,
  "institution": "Demo Institution"
}
```

**Integrity Report:**
```json
{
  "installation_id": "a1b2c3d4-...",
  "integrity_result": {
    "valid": false,
    "modified_files": ["app.py"],
    "version": "1.0.0"
  }
}
```

**Audit Events:**
```json
{
  "installation_id": "a1b2c3d4-...",
  "action_type": "user_login",
  "user": "inspector1",
  "details": {"success": true, "ip_address": "192.168.1.100"},
  "timestamp": "2025-11-21T18:30:00.000Z"
}
```

---

## 🧪 Full Integration Test

**Complete test scenario:**

```bash
# 1. Generate integrity manifest
python integrity_check.py generate 1.0.0

# 2. Set license key
export ZOZI_LICENSE_KEY=ZOZI-DEMO-2024-TEST

# 3. Start app
python app.py

# Expected: All checks pass ✅

# 4. In browser: http://localhost:5000
# - Log in as admin
# - Check footer: Shows "Demo Institution" + Installation ID
# - No warning banners

# 5. Enable support access
# - Go to /admin/support-access
# - Enable 4-hour access
# - Copy the code

# 6. Test support login
# - Open incognito window
# - Go to /zozi-support-login
# - Enter code
# - Should access dashboard

# 7. Check audit log
python audit_log.py stats
# Should show login events

# 8. Test code tampering
echo "# test" >> app.py
python app.py
# Expected: ❌ Code integrity failed

# 9. View in browser
# Expected: Red warning banner + watermark

# 10. Restore code
git checkout app.py
python app.py
# Expected: ✅ All checks pass again
```

---

## 🎯 What Happens When You Give to Institution

**When institution deploys your Docker container:**

1. **First Startup:**
   - Generates unique `installation_id.txt`
   - Checks for `ZOZI_LICENSE_KEY` environment variable
   - Validates code integrity
   - Sends "app_started" telemetry to your server

2. **Your Monitoring Dashboard Shows:**
   ```
   ✅ Kingston Health Dept (abc123)
      Status: Running
      Version: 1.0.0
      Code: Valid ✅
      Last Seen: 2 mins ago
   ```

3. **If They Modify Code:**
   ```
   ⚠️ Kingston Health Dept (abc123)
      Status: Running
      Version: 1.0.0
      Code: MODIFIED ❌
      Modified: app.py
      Last Seen: 5 mins ago
   ```

4. **If They Need Help:**
   - Admin enables support access
   - Calls you with code: `ZOZI-1234-5678-9012`
   - You go to `/zozi-support-login`
   - Enter code
   - Access their system for 4 hours
   - All your actions are logged

---

## 🔒 Security Best Practices

### **For You (Zo-Zi):**

1. ✅ **Keep `ZOZI_SIGNING_SECRET` secret** - Used to sign integrity manifest
2. ✅ **Monitor your dashboard** - Check installations daily
3. ✅ **Rotate license keys yearly** - Expire old keys
4. ✅ **Review audit logs** - Investigate suspicious activity
5. ✅ **Use VPN for support access** - Don't expose ports publicly

### **For Institutions:**

1. ✅ **Don't modify code** - Breaks integrity, voids support
2. ✅ **Keep license key secure** - Don't share publicly
3. ✅ **Enable support access only when needed** - Time-limited
4. ✅ **Review audit logs** - Monitor who's doing what
5. ✅ **Report issues** - Don't try to "fix" code yourself

---

## 🆘 Troubleshooting

### **Issue: "No license key found"**

**Fix:**
```bash
export ZOZI_LICENSE_KEY=ZOZI-DEMO-2024-TEST
python app.py
```

### **Issue: "Code integrity failed"**

**Causes:**
- Someone modified your code
- You updated files without regenerating manifest

**Fix:**
```bash
# Regenerate manifest after legitimate changes
python integrity_check.py generate 1.0.0
```

### **Issue: "License validation failed: Grace period expired"**

**Means:**
- Can't reach your license server
- Grace period (7 days) has passed

**Fix:**
- Check internet connection
- Verify `ZOZI_LICENSE_SERVER` URL is accessible
- Or use local validation for testing

### **Issue: "Support code invalid"**

**Causes:**
- Code expired (past 4 hours)
- Wrong code entered
- Support access was disabled

**Fix:**
- Admin generates new code
- Check expiration time
- Verify code is exactly correct (case-sensitive)

---

## 📝 Quick Reference

### **Environment Variables:**

```bash
# Required
ZOZI_LICENSE_KEY=ZOZI-XXXX-XXXX-XXXX

# Optional (defaults provided)
ZOZI_SIGNING_SECRET=your-secret-key
ZOZI_LICENSE_SERVER=https://api.zozi-inspections.com
```

### **Command Line Tools:**

```bash
# Integrity
python integrity_check.py generate 1.0.0  # Generate manifest
python integrity_check.py                   # Check integrity

# License
python license_manager.py generate "Institution" 2025-12-31
python license_manager.py validate ZOZI-XXXX-XXXX-XXXX

# Audit
python audit_log.py test                # Test logging
python audit_log.py read 10             # Read last 10 entries
python audit_log.py stats               # Show statistics

# Support Access
python support_access.py enable admin_user 4
python support_access.py disable
python support_access.py status
python support_access.py validate ZOZI-XXXX-XXXX-XXXX
```

### **Web Routes:**

- `/admin/support-access` - Manage support access
- `/zozi-support-login` - Support staff login
- `/zozi-support-logout` - Support staff logout

---

## ✅ Success Checklist

Before giving to institution:

- [ ] Integrity manifest generated
- [ ] License key created for institution
- [ ] Tested code tampering detection
- [ ] Tested support access system
- [ ] Verified audit logging works
- [ ] Tested startup security checks
- [ ] Documentation provided
- [ ] Contract signed

---

**Questions? Contact Zo-Zi Systems: jovoney@zozi-inspections.com**
