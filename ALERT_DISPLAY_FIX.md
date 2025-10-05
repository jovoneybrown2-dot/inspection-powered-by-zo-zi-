# Alert Display Issue - FIXED

## Problem
- Badge showed "1" (alert exists) ✓
- Clicking alerts button opened sidebar ✓
- **BUT: Alert list was empty** ❌
- Inspector name, institution, and score were not showing

## Root Cause
**Duplicate Element IDs**

There were TWO elements with `id="alertList"`:
1. Line 1102: Old alert dropdown (legacy) - `<div id="alertList" class="p-2"></div>`
2. Line 1221: New alert sidebar - `<div class="alert-list" id="alertList">`

JavaScript `document.getElementById('alertList')` was finding the WRONG element (the old dropdown instead of the sidebar), so alerts were being rendered to the wrong place!

## Fix Applied

### 1. Renamed Sidebar Element ID
**Before**:
```html
<div class="alert-list" id="alertList">
```

**After**:
```html
<div class="alert-list" id="sidebarAlertList">
```

### 2. Updated JavaScript Functions

**renderAlerts()** - Changed from `alertList` to `sidebarAlertList`:
```javascript
function renderAlerts(alerts) {
    const alertList = document.getElementById('sidebarAlertList');  // Fixed!
    // ... rest of function
}
```

**showEmptyAlerts()** - Changed from `alertList` to `sidebarAlertList`:
```javascript
function showEmptyAlerts() {
    const alertList = document.getElementById('sidebarAlertList');  // Fixed!
    // ... rest of function
}
```

### 3. Added Debug Logging
Added console.log statements to help troubleshoot:
- "Loading alert sidebar..."
- "Alert data received: [data]"
- "Number of alerts: X"
- "Rendering alerts. Element found: true/false"
- "Current filter: all/acknowledged/etc."
- "Filtered alerts: X"

## How to Test

### 1. Check Console (for debugging)
Open browser console (F12) and you should see:
```
Loading alert sidebar...
Alert data received: {success: true, alerts: [...]}
Number of alerts: 1
Alerts: [{id: 1, inspector_name: "T. Morrison", ...}]
Rendering alerts. Element found: true
Total alerts to render: 1
Current filter: all
Filtered alerts: 1
```

### 2. Visual Check
1. Login as admin
2. Click 🚨 Alerts button
3. Sidebar opens
4. **You should now see**:
```
⚠️ SPIRIT LICENCE PREMISES    Just now
Inspector: T. Morrison
Score: 0.0% (Threshold: 36%)
📋 ID: 98
[✓ Acknowledge]  [👁️ View]
```

## Database Verification

Alert exists in database:
```sql
SELECT * FROM threshold_alerts;
-- Result:
-- id=1, inspection_id=98, inspector_name="T. Morrison",
-- form_type="Spirit Licence Premises", score=0.0,
-- threshold_value=36.0, acknowledged=0, created_at="2025-10-05 21:24:01"
```

## Files Modified

### templates/admin.html

**HTML Change** (Line 1221):
- Changed: `<div class="alert-list" id="alertList">`
- To: `<div class="alert-list" id="sidebarAlertList">`

**JavaScript Changes**:

**renderAlerts()** (Line 3526):
- Changed: `document.getElementById('alertList')`
- To: `document.getElementById('sidebarAlertList')`

**showEmptyAlerts()** (Line 3597):
- Changed: `document.getElementById('alertList')`
- To: `document.getElementById('sidebarAlertList')`

**loadAlertSidebar()** (Lines 3502-3523):
- Added debug console.log statements

## Result

✅ **Alert sidebar now displays alerts correctly**
✅ **Shows inspector name: "T. Morrison"**
✅ **Shows form type: "Spirit Licence Premises"**
✅ **Shows score: 0.0% vs threshold: 36%**
✅ **Shows inspection ID: 98**
✅ **Shows action buttons: Acknowledge and View**
✅ **Badge count accurate: 1**

## What You'll See Now

When you click the 🚨 Alerts button with threshold at 36% and inspector scored 0%:

```
┌─────────────────────────────────────┐
│  🚨 Threshold Alerts           [×]  │
├─────────────────────────────────────┤
│  Alert Threshold Setting            │
│  Alert when score below: [36] %     │
├─────────────────────────────────────┤
│  [All] [Unacknowledged] [Ack...]   │
│  [Food] [Residential] [Burial] [...] │
├─────────────────────────────────────┤
│  ⚠️ SPIRIT LICENCE PREMISES         │
│  Just now                           │
│                                      │
│  Inspector: T. Morrison             │
│  Score: 0.0% (Threshold: 36%)      │
│                                      │
│  📋 ID: 98                          │
│                                      │
│  [✓ Acknowledge]  [👁️ View]        │
└─────────────────────────────────────┘
```

The alert list is now properly populated with all inspection details!
