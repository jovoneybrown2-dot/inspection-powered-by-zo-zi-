# Security Dashboard Access

## Overview
The Security Dashboard requires a 6-digit passcode for access. This adds an extra layer of protection to sensitive security monitoring features.

## Default Passcode
- **Default Code:** `123456`

## Setting a Custom Passcode

### For Local Development
Add this to your environment:
```bash
export SECURITY_DASHBOARD_CODE="your_6_digit_code"
```

### For Render Deployment
1. Go to your Render dashboard
2. Select your web service
3. Navigate to **Environment** tab
4. Add a new environment variable:
   - **Key:** `SECURITY_DASHBOARD_CODE`
   - **Value:** Your 6-digit passcode (e.g., `987654`)
5. Click **Save Changes** (this will trigger a redeploy)

### For Production (Recommended)
**IMPORTANT:** Change the default passcode in production!

Example secure codes:
- Generate random: `python -c "import random; print(''.join([str(random.randint(0,9)) for _ in range(6)]))"`
- Or use a memorable but secure code

## How It Works

1. Admin clicks "🛡️ Security Dashboard" button in Admin Tools
2. A modal popup appears requesting the 6-digit code
3. Admin enters the code and clicks "Verify"
4. If correct: Access granted, redirected to Security Dashboard
5. If incorrect: Access denied, error message displayed

## Session Management
- Authorization is stored in the user's session
- Authorization is cleared when the user logs out
- Each admin must authorize separately

## Security Features
- Code must be exactly 6 digits
- Only numeric characters accepted
- Failed attempts are not rate-limited (consider adding if needed)
- Authorization required for all security API endpoints

## Accessing Protected Routes
The following routes require security authorization:
- `/admin/security` - Main security dashboard
- `/api/admin/security/integrity-check` - File integrity check API
- `/api/admin/security/acknowledge-alert/<id>` - Alert acknowledgment API
