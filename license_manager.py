"""
Zo-Zi Inspection System - License Management
Validates license keys and tracks installations
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from integrity_check import get_installation_id

# Your license validation server (you'll deploy this separately)
LICENSE_SERVER = os.environ.get('ZOZI_LICENSE_SERVER', 'https://api.zozi-inspections.com')
GRACE_PERIOD_DAYS = 7

# Valid license keys (for testing - in production, check with your server)
VALID_LICENSES = {
    'ZOZI-DEMO-2024-TEST': {
        'institution': 'Demo Institution',
        'type': 'demo',
        'expires': None
    },
    'ZOZI-KINGSTON-2024-PROD': {
        'institution': 'Kingston Health Department',
        'type': 'production',
        'expires': '2025-12-31'
    },
    'ZOZI-STJAMES-2024-PROD': {
        'institution': 'St. James Health Department',
        'type': 'production',
        'expires': '2025-12-31'
    }
}

def validate_license_local(license_key):
    """Validate license locally (offline mode)"""
    if not license_key:
        return False, None, "No license key provided"

    # Check against local valid licenses
    if license_key in VALID_LICENSES:
        license_info = VALID_LICENSES[license_key]

        # Check expiration
        if license_info.get('expires'):
            expiry = datetime.strptime(license_info['expires'], '%Y-%m-%d')
            if datetime.now() > expiry:
                return False, None, f"License expired on {license_info['expires']}"

        return True, license_info['institution'], "Valid"

    return False, None, "Invalid license key"

def validate_license_remote(license_key):
    """Validate license with your remote server"""
    try:
        import requests

        response = requests.post(
            f"{LICENSE_SERVER}/api/license/validate",
            json={
                'license_key': license_key,
                'installation_id': get_installation_id(),
                'timestamp': datetime.utcnow().isoformat(),
                'app_version': get_app_version()
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Save validation result for grace period
            save_last_validation(data)

            return data.get('valid', False), data.get('institution_name'), data.get('message', 'Unknown')

        return False, None, f"Server returned {response.status_code}"

    except Exception as e:
        print(f"⚠️ Remote license validation failed: {e}")
        # Fall back to grace period check
        return check_grace_period()

def validate_license(license_key):
    """
    Main license validation function
    Tries remote first, falls back to local/grace period
    """
    # Try remote validation first
    valid, institution, message = validate_license_remote(license_key)

    if valid:
        return valid, institution, message

    # If remote fails, try local validation
    print("⚠️ Remote validation failed, checking local...")
    valid, institution, message = validate_license_local(license_key)

    if valid:
        return valid, institution, message

    # Check grace period as last resort
    print("⚠️ Local validation failed, checking grace period...")
    return check_grace_period()

def check_grace_period():
    """Allow operation if within grace period since last validation"""
    last_validation = load_last_validation()

    if last_validation:
        last_date = datetime.fromisoformat(last_validation['timestamp'])
        days_since = (datetime.utcnow() - last_date).days

        if days_since < GRACE_PERIOD_DAYS:
            days_left = GRACE_PERIOD_DAYS - days_since
            return True, last_validation.get('institution_name', 'Unknown'), f"Grace period: {days_left} days remaining"

        return False, None, f"Grace period expired ({days_since} days since last validation)"

    return False, None, "No previous validation found"

def save_last_validation(data):
    """Save validation result for grace period"""
    validation_file = 'last_validation.json'

    validation_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'institution_name': data.get('institution_name', 'Unknown'),
        'valid': data.get('valid', False)
    }

    with open(validation_file, 'w') as f:
        json.dump(validation_data, f, indent=2)

def load_last_validation():
    """Load last validation result"""
    validation_file = 'last_validation.json'

    try:
        if os.path.exists(validation_file):
            with open(validation_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading validation: {e}")

    return None

def send_telemetry(event_type, data=None):
    """Send anonymous usage telemetry to your server"""
    try:
        import requests

        telemetry_data = {
            'installation_id': get_installation_id(),
            'event': event_type,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat(),
            'app_version': get_app_version()
        }

        requests.post(
            f"{LICENSE_SERVER}/api/telemetry",
            json=telemetry_data,
            timeout=5
        )

    except Exception as e:
        # Fail silently - don't break app if telemetry fails
        print(f"Telemetry send failed: {e}")

def send_integrity_report(integrity_result):
    """Report code integrity status to your server"""
    try:
        import requests

        report_data = {
            'installation_id': get_installation_id(),
            'license_key': os.environ.get('ZOZI_LICENSE_KEY', 'none'),
            'integrity_result': integrity_result,
            'timestamp': datetime.utcnow().isoformat()
        }

        requests.post(
            f"{LICENSE_SERVER}/api/integrity-report",
            json=report_data,
            timeout=5
        )

    except Exception as e:
        print(f"Integrity report failed: {e}")

def get_app_version():
    """Get application version from integrity manifest"""
    try:
        if os.path.exists('integrity_manifest.json'):
            with open('integrity_manifest.json', 'r') as f:
                manifest = json.load(f)
                return manifest.get('version', '1.0.0')
    except:
        pass

    return '1.0.0-dev'

def generate_license_key(institution_name, expiry_date='2025-12-31'):
    """
    Generate a license key for an institution
    (You would use this on YOUR server to create licenses)
    """
    secret_salt = os.environ.get('ZOZI_LICENSE_SALT', 'zozi-secret-salt-change-this')
    data = f"{institution_name}:{expiry_date}:{secret_salt}"
    hash_key = hashlib.sha256(data.encode()).hexdigest()[:16].upper()

    # Format: ZOZI-XXXX-XXXX-XXXX
    formatted = f"ZOZI-{hash_key[0:4]}-{hash_key[4:8]}-{hash_key[8:12]}"

    return {
        'license_key': formatted,
        'institution': institution_name,
        'expires': expiry_date,
        'generated_at': datetime.now().isoformat()
    }

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'generate':
            # Generate license key
            institution = sys.argv[2] if len(sys.argv) > 2 else 'Test Institution'
            expiry = sys.argv[3] if len(sys.argv) > 3 else '2025-12-31'

            license_data = generate_license_key(institution, expiry)

            print(f"\n🔑 Generated License Key:")
            print(f"   Key: {license_data['license_key']}")
            print(f"   Institution: {license_data['institution']}")
            print(f"   Expires: {license_data['expires']}")

        elif sys.argv[1] == 'validate':
            # Test validation
            test_key = sys.argv[2] if len(sys.argv) > 2 else 'ZOZI-DEMO-2024-TEST'

            print(f"\n🔍 Testing License: {test_key}")
            valid, institution, message = validate_license(test_key)

            print(f"   Valid: {valid}")
            print(f"   Institution: {institution}")
            print(f"   Message: {message}")
    else:
        print("Usage:")
        print("  python license_manager.py generate 'Institution Name' 2025-12-31")
        print("  python license_manager.py validate ZOZI-XXXX-XXXX-XXXX")
