"""
Zo-Zi Inspection System - Support Access Management
Allows temporary support access for troubleshooting
"""

import os
import secrets
import string
from datetime import datetime, timedelta
from audit_log import audit_support_access

# Global state (in production, store in database)
_support_access_code = None
_support_access_expires = None
_support_access_enabled_by = None

def generate_support_code():
    """Generate a secure random support access code"""
    # Format: ZOZI-####-####-####
    parts = []
    for _ in range(3):
        part = ''.join(secrets.choice(string.digits) for _ in range(4))
        parts.append(part)

    return f"ZOZI-{'-'.join(parts)}"

def enable_support_access(admin_user, duration_hours=4):
    """
    Enable temporary support access

    Args:
        admin_user: Username of admin enabling access
        duration_hours: How long access should last

    Returns:
        Dict with access code and expiration
    """
    global _support_access_code, _support_access_expires, _support_access_enabled_by

    # Generate new code
    _support_access_code = generate_support_code()
    _support_access_expires = datetime.utcnow() + timedelta(hours=duration_hours)
    _support_access_enabled_by = admin_user

    # Log this action
    audit_support_access('enabled', admin_user, {
        'code': _support_access_code[:12] + '****',  # Partially redacted for security
        'expires': _support_access_expires.isoformat(),
        'duration_hours': duration_hours
    })

    # Notify your server
    notify_support_access_granted()

    result = {
        'code': _support_access_code,
        'expires': _support_access_expires.isoformat(),
        'expires_in_hours': duration_hours,
        'enabled_by': admin_user
    }

    print(f"🔓 Support access enabled by {admin_user}")
    print(f"   Code: {_support_access_code}")
    print(f"   Expires: {_support_access_expires}")

    return result

def disable_support_access(user):
    """Disable support access immediately"""
    global _support_access_code, _support_access_expires, _support_access_enabled_by

    if _support_access_code:
        audit_support_access('disabled', user, {
            'code_was': _support_access_code[:12] + '****'
        })

        print(f"🔒 Support access disabled by {user}")

    _support_access_code = None
    _support_access_expires = None
    _support_access_enabled_by = None

def validate_support_code(code):
    """
    Check if support access code is valid

    Returns:
        Tuple of (valid: bool, message: str, time_remaining: str or None)
    """
    global _support_access_code, _support_access_expires

    if not _support_access_code:
        return False, "No support access code active", None

    if code != _support_access_code:
        # Log failed attempt
        audit_support_access('invalid_attempt', 'unknown', {
            'attempted_code': code[:12] + '****'
        })
        return False, "Invalid support code", None

    if not _support_access_expires:
        return False, "No expiration set", None

    now = datetime.utcnow()

    if now > _support_access_expires:
        # Code expired
        return False, f"Support code expired at {_support_access_expires.isoformat()}", None

    # Valid code
    time_remaining = _support_access_expires - now
    hours_remaining = time_remaining.total_seconds() / 3600

    return True, "Valid support code", f"{hours_remaining:.1f} hours"

def get_support_access_status():
    """Get current status of support access"""
    global _support_access_code, _support_access_expires, _support_access_enabled_by

    if not _support_access_code:
        return {
            'enabled': False,
            'code': None,
            'expires': None,
            'enabled_by': None
        }

    now = datetime.utcnow()
    is_expired = _support_access_expires and now > _support_access_expires

    status = {
        'enabled': not is_expired,
        'code': _support_access_code if not is_expired else None,
        'expires': _support_access_expires.isoformat() if _support_access_expires else None,
        'enabled_by': _support_access_enabled_by,
        'expired': is_expired
    }

    if not is_expired and _support_access_expires:
        time_remaining = _support_access_expires - now
        status['hours_remaining'] = time_remaining.total_seconds() / 3600

    return status

def notify_support_access_granted():
    """Notify your server that support access was granted"""
    try:
        import requests
        from integrity_check import get_installation_id

        server_url = os.environ.get('ZOZI_LICENSE_SERVER', 'https://api.zozi-inspections.com')

        requests.post(
            f"{server_url}/api/support-access-granted",
            json={
                'installation_id': get_installation_id(),
                'code': _support_access_code,
                'expires': _support_access_expires.isoformat() if _support_access_expires else None,
                'enabled_by': _support_access_enabled_by
            },
            timeout=5
        )

        print("  ✓ Notified Zo-Zi server of support access")

    except Exception as e:
        print(f"  ⚠️ Failed to notify server: {e}")

def cleanup_expired_access():
    """Clean up expired access codes (call periodically)"""
    global _support_access_code, _support_access_expires

    if _support_access_expires and datetime.utcnow() > _support_access_expires:
        print(f"🔒 Support access code expired, cleaning up")
        _support_access_code = None
        _support_access_expires = None

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'enable':
            # Enable support access
            admin = sys.argv[2] if len(sys.argv) > 2 else 'test_admin'
            hours = int(sys.argv[3]) if len(sys.argv) > 3 else 4

            result = enable_support_access(admin, hours)

            print(f"\n🔓 Support Access Enabled:")
            print(f"   Code: {result['code']}")
            print(f"   Expires: {result['expires']}")
            print(f"   Duration: {result['expires_in_hours']} hours")
            print(f"\n   Give this code to Zo-Zi Support to access your system")

        elif sys.argv[1] == 'disable':
            disable_support_access('admin')
            print("\n🔒 Support access disabled")

        elif sys.argv[1] == 'status':
            status = get_support_access_status()

            print(f"\n📊 Support Access Status:")
            print(f"   Enabled: {status['enabled']}")

            if status['enabled']:
                print(f"   Code: {status['code']}")
                print(f"   Expires: {status['expires']}")
                print(f"   Hours Remaining: {status.get('hours_remaining', 0):.1f}")
                print(f"   Enabled By: {status['enabled_by']}")
            else:
                if status.get('expired'):
                    print(f"   Status: Expired")
                else:
                    print(f"   Status: Not Active")

        elif sys.argv[1] == 'validate':
            # Test code validation
            test_code = sys.argv[2] if len(sys.argv) > 2 else ''

            valid, message, time_left = validate_support_code(test_code)

            print(f"\n🔍 Validation Result:")
            print(f"   Valid: {valid}")
            print(f"   Message: {message}")
            if time_left:
                print(f"   Time Remaining: {time_left}")
    else:
        print("Usage:")
        print("  python support_access.py enable [admin_user] [hours]")
        print("  python support_access.py disable")
        print("  python support_access.py status")
        print("  python support_access.py validate [code]")
