"""
Zo-Zi Inspection System - Alert System
Sends real-time alerts when security issues are detected
"""

import os
import json
from datetime import datetime
from integrity_check import get_installation_id

ALERT_LOG_FILE = 'security_alerts.jsonl'
ALERT_SERVER = os.environ.get('ZOZI_ALERT_SERVER', 'https://api.zozi-inspections.com')

# Alert severity levels
SEVERITY_INFO = 'info'
SEVERITY_WARNING = 'warning'
SEVERITY_CRITICAL = 'critical'

def create_alert(alert_type, severity, message, details=None):
    """
    Create a security alert

    Args:
        alert_type: Type of alert (e.g., 'code_tampered', 'unauthorized_access')
        severity: 'info', 'warning', or 'critical'
        message: Human-readable message
        details: Dictionary with additional information

    Returns:
        Dict of the alert created
    """
    alert = {
        'id': datetime.utcnow().strftime('%Y%m%d%H%M%S'),
        'timestamp': datetime.utcnow().isoformat(),
        'installation_id': get_installation_id(),
        'alert_type': alert_type,
        'severity': severity,
        'message': message,
        'details': details or {},
        'acknowledged': False
    }

    # Log locally
    write_local_alert(alert)

    # Send to monitoring server
    send_alert_to_server(alert)

    # Print to console for immediate visibility
    severity_icon = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'critical': '🚨'
    }.get(severity, '•')

    print(f"\n{severity_icon} SECURITY ALERT - {severity.upper()}")
    print(f"   Type: {alert_type}")
    print(f"   Message: {message}")
    if details:
        print(f"   Details: {json.dumps(details, indent=6)}")

    return alert

def write_local_alert(alert):
    """Write alert to local JSONL file"""
    try:
        with open(ALERT_LOG_FILE, 'a') as f:
            f.write(json.dumps(alert) + '\n')
    except Exception as e:
        print(f"⚠️ Failed to write local alert: {e}")

def send_alert_to_server(alert):
    """Send alert to your monitoring server"""
    try:
        import requests

        # Add license key for authentication
        requests.post(
            f"{ALERT_SERVER}/api/alerts",
            json=alert,
            headers={
                'X-License-Key': os.environ.get('ZOZI_LICENSE_KEY', 'none'),
                'X-Installation-ID': alert['installation_id']
            },
            timeout=10
        )

    except ImportError:
        # requests not installed - log locally only
        pass
    except Exception as e:
        # Log send failure
        write_local_alert({
            'timestamp': datetime.utcnow().isoformat(),
            'alert_type': 'alert_send_failed',
            'severity': 'warning',
            'message': f'Failed to send alert to server: {str(e)}',
            'acknowledged': False
        })

def read_alerts(limit=50, severity=None, acknowledged=None):
    """
    Read security alerts

    Args:
        limit: Maximum number of alerts to return
        severity: Filter by severity level
        acknowledged: Filter by acknowledgement status

    Returns:
        List of alerts (most recent first)
    """
    alerts = []

    try:
        if not os.path.exists(ALERT_LOG_FILE):
            return []

        with open(ALERT_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    alert = json.loads(line.strip())

                    # Apply filters
                    if severity and alert.get('severity') != severity:
                        continue

                    if acknowledged is not None and alert.get('acknowledged') != acknowledged:
                        continue

                    alerts.append(alert)

                    if len(alerts) >= limit:
                        break

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"Error reading alerts: {e}")

    # Return most recent first
    return list(reversed(alerts))

def acknowledge_alert(alert_id):
    """Mark an alert as acknowledged"""
    try:
        if not os.path.exists(ALERT_LOG_FILE):
            return False

        # Read all alerts
        alerts = []
        with open(ALERT_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    alert = json.loads(line.strip())

                    # Mark as acknowledged if ID matches
                    if alert.get('id') == alert_id:
                        alert['acknowledged'] = True
                        alert['acknowledged_at'] = datetime.utcnow().isoformat()

                    alerts.append(alert)
                except json.JSONDecodeError:
                    continue

        # Rewrite file
        with open(ALERT_LOG_FILE, 'w') as f:
            for alert in alerts:
                f.write(json.dumps(alert) + '\n')

        return True

    except Exception as e:
        print(f"Error acknowledging alert: {e}")
        return False

def get_alert_stats():
    """Get statistics about alerts"""
    stats = {
        'total': 0,
        'critical': 0,
        'warning': 0,
        'info': 0,
        'unacknowledged': 0,
        'by_type': {},
        'latest': None
    }

    try:
        if not os.path.exists(ALERT_LOG_FILE):
            return stats

        with open(ALERT_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    alert = json.loads(line.strip())
                    stats['total'] += 1

                    # Count by severity
                    severity = alert.get('severity', 'info')
                    if severity in stats:
                        stats[severity] += 1

                    # Count unacknowledged
                    if not alert.get('acknowledged', False):
                        stats['unacknowledged'] += 1

                    # Count by type
                    alert_type = alert.get('alert_type', 'unknown')
                    stats['by_type'][alert_type] = stats['by_type'].get(alert_type, 0) + 1

                    # Track latest
                    stats['latest'] = alert.get('timestamp')

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"Error getting alert stats: {e}")

    return stats

# Predefined alert functions for common security events

def alert_code_tampered(modified_files):
    """Alert when code has been tampered with"""
    return create_alert(
        'code_tampered',
        SEVERITY_CRITICAL,
        f'Code integrity check failed - {len(modified_files)} file(s) modified',
        {
            'modified_files': modified_files,
            'action_required': 'Investigate unauthorized modifications immediately'
        }
    )

def alert_unauthorized_login(username, ip_address=None):
    """Alert on suspicious login attempt"""
    return create_alert(
        'unauthorized_login',
        SEVERITY_WARNING,
        f'Failed login attempt for user: {username}',
        {
            'username': username,
            'ip_address': ip_address,
            'action_required': 'Monitor for repeated attempts'
        }
    )

def alert_support_access_requested(admin_user, duration_hours):
    """Alert when support access is enabled"""
    return create_alert(
        'support_access_enabled',
        SEVERITY_INFO,
        f'Support access enabled by {admin_user} for {duration_hours} hours',
        {
            'admin_user': admin_user,
            'duration_hours': duration_hours
        }
    )

def alert_license_invalid():
    """Alert when license is invalid"""
    return create_alert(
        'license_invalid',
        SEVERITY_CRITICAL,
        'License validation failed - System may be running without authorization',
        {
            'action_required': 'Verify license key with Zo-Zi support'
        }
    )

def alert_data_export(user, record_count):
    """Alert on bulk data export"""
    return create_alert(
        'data_export',
        SEVERITY_WARNING,
        f'User {user} exported {record_count} records',
        {
            'user': user,
            'record_count': record_count
        }
    )

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Test alert system
            print("🧪 Testing alert system...")

            alert_code_tampered(['app.py', 'database.py'])
            print("  ✓ Created code tamper alert")

            alert_unauthorized_login('admin', '192.168.1.100')
            print("  ✓ Created unauthorized login alert")

            alert_support_access_requested('admin_user', 4)
            print("  ✓ Created support access alert")

            print(f"\n📊 Alert Stats:")
            stats = get_alert_stats()
            print(f"  Total: {stats['total']}")
            print(f"  Critical: {stats['critical']}")
            print(f"  Warning: {stats['warning']}")
            print(f"  Unacknowledged: {stats['unacknowledged']}")

        elif sys.argv[1] == 'read':
            # Read recent alerts
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10

            print(f"\n🚨 Last {limit} security alerts:")
            alerts = read_alerts(limit=limit)

            for alert in alerts:
                severity_icon = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'critical': '🚨'
                }.get(alert.get('severity'), '•')

                ack_status = '✓' if alert.get('acknowledged') else '•'

                print(f"\n  {severity_icon} [{alert['timestamp']}] {ack_status}")
                print(f"    Type: {alert['alert_type']}")
                print(f"    Message: {alert['message']}")
                if alert.get('details'):
                    print(f"    Details: {alert['details']}")

        elif sys.argv[1] == 'stats':
            # Show statistics
            print("\n📊 Security Alert Statistics:")
            stats = get_alert_stats()

            print(f"\n  Total Alerts: {stats['total']}")
            print(f"  Unacknowledged: {stats['unacknowledged']}")
            print(f"\n  By Severity:")
            print(f"    Critical: {stats['critical']}")
            print(f"    Warning: {stats['warning']}")
            print(f"    Info: {stats['info']}")

            if stats['by_type']:
                print(f"\n  By Type:")
                for alert_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
                    print(f"    {alert_type}: {count}")

    else:
        print("Usage:")
        print("  python alert_system.py test     - Test alert system")
        print("  python alert_system.py read [n] - Read last n alerts")
        print("  python alert_system.py stats    - Show statistics")