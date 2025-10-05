# Alert System - Issues Fixed

## Issue 1: Chart Title Blocking Data ✅ FIXED

**Problem**: "INSPECTION METRICS" text was overlaying the chart data

**Solution**:
- Made chart title smaller (14px instead of 18px)
- Positioned absolutely in top-left corner
- Added semi-transparent background
- Added padding for readability

**Result**: Chart title now appears in corner without blocking data

## Issue 2: Where to Set Alert Threshold ✅ ADDED

**Problem**: No visible way to set the alert threshold

**Solution**: Added threshold setting inside Alert Sidebar

**Location**:
1. Click "🚨 Alerts" button (bottom-right)
2. Sidebar opens
3. Top section shows: "Alert Threshold Setting"
4. Input field: "Alert when score below: [70] %"

**Features**:
- Default value: 70%
- Min: 0%, Max: 100%
- Auto-saves on change
- Green confirmation message
- Loads saved value when sidebar opens

**Visual**:
```
┌─────────────────────────────────────┐
│  🚨 Threshold Alerts           [×]  │
├─────────────────────────────────────┤
│  Alert Threshold Setting            │
│  Alert when score below: [70] %     │
│  This sets the threshold for all    │
│  inspection types                   │
├─────────────────────────────────────┤
│  [All] [Unacknowledged] [...]      │
│                                      │
│  Alert cards appear here...         │
└─────────────────────────────────────┘
```

## How It Works

### Setting Threshold:
1. Open alert sidebar
2. Change threshold value (e.g., 70 → 80)
3. Green message: "✓ Alert threshold set to 80%"
4. Setting saved to database

### Alert Creation (Automatic):
1. Inspector submits inspection
2. Backend checks score vs threshold
3. If score < threshold → Create alert
4. Alert appears in sidebar
5. Badge shows unacknowledged count

### Alert Management:
1. Click "🚨 Alerts" to review
2. Filter by status or type
3. Click "View" to see inspection
4. Click "Acknowledge" to mark as reviewed
5. Use bulk actions for multiple alerts

## Files Modified

### templates/admin.html

**Chart Title CSS** (Lines 388-399):
```css
.chart-title {
    font-size: 14px;
    position: absolute;
    top: 8px;
    left: 12px;
    z-index: 10;
    background: rgba(19, 23, 34, 0.8);
    padding: 4px 8px;
    border-radius: 4px;
}
```

**Threshold Setting HTML** (Lines 1203-1217):
```html
<div style="padding: 16px 20px; ...">
    <div>Alert Threshold Setting</div>
    <div>
        <label>Alert when score below:</label>
        <input type="number" id="globalThreshold" value="70" ...>
        <span>%</span>
    </div>
    <div>This sets the threshold for all inspection types</div>
</div>
```

**Threshold Functions** (Lines 3474-3512):
- `updateGlobalThreshold(value)` - Saves threshold setting
- `loadGlobalThreshold()` - Loads saved threshold

### ALERT_SYSTEM_DOCUMENTATION.md

**Added Section**: "How to Set Alert Threshold" with step-by-step instructions

## Testing Checklist

- [x] Chart title visible but not blocking data
- [x] Threshold setting appears in sidebar
- [x] Default value 70% loads correctly
- [x] Changing value saves to database
- [x] Confirmation message appears
- [x] Saved value loads on reopen
- [x] Alert creation respects threshold

## Quick Reference

**Set Alert Threshold**:
- Location: Alert Sidebar (top section)
- Button: 🚨 Alerts (bottom-right)
- Field: "Alert when score below: [__] %"
- Saves: Automatically on change

**Chart Display**:
- Title: Top-left corner, small font
- Background: Semi-transparent
- Data: Fully visible, not blocked
