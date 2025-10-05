# Alert Sidebar System - Final Implementation

## Overview
A comprehensive alert management system that allows admins to monitor, filter, acknowledge, and manage threshold alerts for all inspection types through a dedicated sidebar panel.

## Features

### 1. Alert Sidebar Panel

**Access**: Click the **"🚨 Alerts"** button (bottom-right corner)

**Components**:
- **Header**: Title with close button
- **Filters**: Status and inspection type filters
- **Alert List**: Scrollable list of all alerts
- **Bulk Actions**: Acknowledge all or clear acknowledged

### 2. Alert Card Display

Each alert shows:
- **Status Icon**: ⚠️ (unacknowledged) or ✓ (acknowledged)
- **Inspection Type**: Food, Residential, Burial, etc.
- **Inspector Name**: Who performed the inspection
- **Score Information**: Actual score vs threshold
- **Timestamp**: Relative time (e.g., "2h ago")
- **Inspection ID**: For tracking
- **Actions**: Acknowledge and View buttons (for unacknowledged)

### 3. Filtering Options

**Status Filters**:
- All - Show all alerts
- Unacknowledged - Show only pending alerts
- Acknowledged - Show completed alerts

**Inspection Type Filters**:
- Food - Food Establishment inspections
- Residential - Residential inspections
- Burial - Burial Site inspections
- Spirit - Spirit Licence inspections

### 4. Alert Actions

**Individual Actions**:
- **✓ Acknowledge**: Mark single alert as reviewed
- **👁️ View**: Open the inspection detail page

**Bulk Actions**:
- **✓ Acknowledge All**: Mark all unacknowledged alerts at once
- **🗑️ Clear Acknowledged**: Delete all acknowledged alerts

### 5. Badge Notification

**Alert Badge** (on toggle button):
- Red circular badge
- Shows count of unacknowledged alerts
- Auto-updates every 30 seconds
- Hides when count is 0

## How to Set Alert Threshold

**Location**: Inside the Alert Sidebar

**Steps**:
1. Click "🚨 Alerts" button (bottom-right)
2. Sidebar opens
3. At the top, you'll see "Alert Threshold Setting"
4. Set value: "Alert when score below: [70] %"
5. Change the number to your desired threshold
6. Setting saves automatically
7. Green confirmation message appears

**Default**: 70% (inspections scoring below 70% trigger alerts)

**How Alerts Are Created**:
- Alerts are created automatically when an inspection score is below your set threshold
- System checks every submitted inspection
- If score < threshold → Alert created in database
- Alert appears in sidebar automatically

## How to Use

### For Admins:

**1. Open Alert Sidebar**
```
- Click "🚨 Alerts" button (bottom-right)
- Sidebar slides in from the right
- See all current alerts
```

**2. Filter Alerts**
```
- Click status filter (All/Unacknowledged/Acknowledged)
- Click type filter (Food/Residential/Burial/Spirit)
- Alerts update immediately
```

**3. Review Alert Details**
```
Each alert card shows:
⚠️ FOOD ESTABLISHMENT        2h ago
Inspector: John Smith
Score: 65.0% (Threshold: 70%)
📋 ID: 123
[✓ Acknowledge]  [👁️ View]
```

**4. Acknowledge Single Alert**
```
- Click "✓ Acknowledge" button
- Alert turns green with checkmark
- Badge count decreases
- Alert moves to acknowledged section
```

**5. View Inspection**
```
- Click "👁️ View" button
- Opens full inspection detail page
- Review complete inspection data
```

**6. Bulk Operations**
```
- Click "Acknowledge All" at bottom
- Confirm the action
- All unacknowledged alerts marked as complete

OR

- Click "Clear Acknowledged" at bottom
- Confirm the action
- All acknowledged alerts permanently deleted
```

## Workflow Example

**Scenario**: Multiple inspections submitted with low scores

```
1. Inspector submits Food inspection (Score: 65%)
         ↓
2. System creates alert (below 70% threshold)
         ↓
3. Alert badge shows "1" on alerts button
         ↓
4. Admin clicks "🚨 Alerts" button
         ↓
5. Sidebar opens showing:
   ⚠️ FOOD ESTABLISHMENT     Just now
   Inspector: John Smith
   Score: 65.0% (Threshold: 70%)
         ↓
6. Admin clicks "👁️ View"
         ↓
7. Reviews full inspection details
         ↓
8. Returns to sidebar, clicks "✓ Acknowledge"
         ↓
9. Alert turns green, badge count = 0
         ↓
10. Later, clicks "Clear Acknowledged" to clean up
```

## Auto-Refresh

The system automatically:
- Refreshes alert list every 30 seconds
- Updates badge count in real-time
- Shows new alerts without page reload
- Maintains current filter selection

## Alert States

**Unacknowledged** (Red border):
- New alerts requiring review
- Shows action buttons
- Counts toward badge number
- Appears at top of list

**Acknowledged** (Green border):
- Reviewed alerts
- No action buttons
- 60% opacity (dimmed)
- Appears at bottom of list
- Shows who acknowledged and when

## Technical Details

### API Endpoints

**GET /api/admin/threshold_alerts/list**
- Returns all alerts with details
- Ordered by: unacknowledged first, then by date

**POST /api/admin/threshold_alerts**
- Creates new alert (called by system)
- Includes inspection details and scores

**POST /api/admin/threshold_alerts/acknowledge/{id}**
- Marks specific alert as acknowledged
- Records who acknowledged

**POST /api/admin/threshold_alerts/clear_acknowledged**
- Deletes all acknowledged alerts
- Returns count of deleted records

### Database Schema

**threshold_alerts table**:
```sql
id INTEGER PRIMARY KEY
inspection_id INTEGER
inspector_name TEXT
form_type TEXT
score REAL
threshold_value REAL
acknowledged INTEGER (0 or 1)
acknowledged_by TEXT
acknowledged_at TEXT
created_at TEXT
```

## Files Modified

### Frontend (templates/admin.html)

**Alert Sidebar HTML** (Lines 1189-1218):
- Sidebar structure
- Filter buttons
- Alert list container
- Bulk action buttons

**Alert Sidebar CSS** (Lines 607-869):
- Dark theme styling
- Card layouts
- Button states
- Animations

**Alert Sidebar JavaScript** (Lines 3422-3626):
- Toggle functionality
- Alert rendering
- Filtering logic
- Acknowledgment actions
- Badge updates

### Backend (app.py)

**Alert Endpoints** (Lines 8549-8607):
- List alerts
- Acknowledge alert
- Clear acknowledged alerts

## Styling

**Color Scheme** (Dark Theme):
- Background: #1e222d
- Cards: #2a2e39
- Text: #d1d4dc
- Unacknowledged: #ef5350 (red)
- Acknowledged: #4caf50 (green)
- Active filters: #2962ff (blue)

**Responsive Design**:
- 400px sidebar width
- Full viewport height
- Scrollable alert list
- Fixed header and footer

## Best Practices

### For Admins:
1. Check alerts daily or when badge appears
2. Review inspection details before acknowledging
3. Use filters to focus on specific types
4. Clear acknowledged alerts periodically
5. Use "Acknowledge All" for bulk processing

### For System Managers:
1. Monitor alert frequency
2. Adjust thresholds if too many/few alerts
3. Track inspector performance via alerts
4. Use alert history for training
5. Review acknowledgment patterns

## Troubleshooting

**Issue**: Alerts not showing
- Check if sidebar is open
- Verify filters (change to "All")
- Refresh page if needed

**Issue**: Badge not updating
- Wait 30 seconds for auto-refresh
- Manually close and reopen sidebar
- Check network connection

**Issue**: Cannot acknowledge
- Verify you're logged in as admin
- Check alert is unacknowledged
- Try refreshing the page

## Future Enhancements (Optional)

Potential additions:
- Email notifications for new alerts
- Export alerts to CSV/PDF
- Custom alert thresholds per inspection type
- Alert analytics dashboard
- SMS notifications for critical alerts
- Alert assignment to specific admins

## Summary

The Alert Sidebar System provides:
- ✅ Centralized alert management
- ✅ Easy filtering and sorting
- ✅ Quick acknowledgment workflow
- ✅ Visual status indicators
- ✅ Auto-refresh capabilities
- ✅ Bulk operations
- ✅ Audit trail (who/when acknowledged)
- ✅ Clean, intuitive interface

**Result**: Admins can efficiently monitor and manage all threshold violations across all inspection types from a single, dedicated interface.
