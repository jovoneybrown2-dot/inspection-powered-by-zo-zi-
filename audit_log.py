"""
Zo-Zi Inspection System - Audit Logging
Tracks all important actions in the system
"""

import os
import json
from datetime import datetime
from integrity_check import get_installation_id

AUDIT_LOG_FILE = 'audit_log.jsonl'
AUDIT_SERVER = os.environ.get('ZOZI_LICENSE_SERVER', 'https://api.zozi-inspections.com')

def log_action(action_type, user, details=None, local_only=False):
    """
    Log an action to local file and optionally send to server

    Args:
        action_type: Type of action (e.g., 'inspection_created', 'user_added')
        user: Username or identifier of who performed the action
        details: Dictionary with additional information
        local_only: If True, don't send to server (for sensitive data)

    Returns:
        Dict of the log entry created
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'installation_id': get_installation_id(),
        'action_type': action_type,
        'user': user,
        'details': details or {},
    }

    # Always log locally
    write_local_audit_log(log_entry)

    # Send to server unless local_only
    if not local_only:
        send_audit_to_server(log_entry)

    return log_entry

def write_local_audit_log(entry):
    """Write audit entry to local JSONL file"""
    try:
        # Append to JSONL file (one JSON object per line)
        with open(AUDIT_LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    except Exception as e:
        print(f"⚠️ Failed to write local audit log: {e}")

def send_audit_to_server(entry):
    """Send audit entry to your monitoring server"""
    try:
        import requests

        # Remove sensitive data before sending
        safe_entry = sanitize_audit_entry(entry)

        requests.post(
            f"{AUDIT_SERVER}/api/audit",
            json=safe_entry,
            headers={
                'X-License-Key': os.environ.get('ZOZI_LICENSE_KEY', 'none')
            },
            timeout=5
        )

    except Exception as e:
        # Log failure locally
        write_local_audit_log({
            'timestamp': datetime.utcnow().isoformat(),
            'action_type': 'audit_send_failed',
            'error': str(e)
        })

def sanitize_audit_entry(entry):
    """Remove sensitive data before sending to server"""
    safe_entry = entry.copy()

    # Remove passwords from details
    if 'details' in safe_entry and isinstance(safe_entry['details'], dict):
        details = safe_entry['details'].copy()

        # Redact sensitive fields
        sensitive_fields = ['password', 'password_hash', 'ssn', 'credit_card']
        for field in sensitive_fields:
            if field in details:
                details[field] = '[REDACTED]'

        safe_entry['details'] = details

    return safe_entry

def read_audit_log(limit=100, action_type=None, user=None):
    """
    Read audit log entries

    Args:
        limit: Maximum number of entries to return
        action_type: Filter by action type
        user: Filter by user

    Returns:
        List of audit log entries
    """
    entries = []

    try:
        if not os.path.exists(AUDIT_LOG_FILE):
            return []

        with open(AUDIT_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())

                    # Apply filters
                    if action_type and entry.get('action_type') != action_type:
                        continue

                    if user and entry.get('user') != user:
                        continue

                    entries.append(entry)

                    # Limit results
                    if len(entries) >= limit:
                        break

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"Error reading audit log: {e}")

    # Return most recent first
    return list(reversed(entries))

def get_audit_stats():
    """Get statistics about audit log"""
    stats = {
        'total_entries': 0,
        'actions_by_type': {},
        'actions_by_user': {},
        'first_entry': None,
        'last_entry': None
    }

    try:
        if not os.path.exists(AUDIT_LOG_FILE):
            return stats

        with open(AUDIT_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    stats['total_entries'] += 1

                    # Count by action type
                    action_type = entry.get('action_type', 'unknown')
                    stats['actions_by_type'][action_type] = stats['actions_by_type'].get(action_type, 0) + 1

                    # Count by user
                    user = entry.get('user', 'unknown')
                    stats['actions_by_user'][user] = stats['actions_by_user'].get(user, 0) + 1

                    # Track first and last
                    if stats['first_entry'] is None:
                        stats['first_entry'] = entry.get('timestamp')

                    stats['last_entry'] = entry.get('timestamp')

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"Error getting audit stats: {e}")

    return stats

# Common audit action helpers
def audit_user_login(username, success=True, ip_address=None):
    """Log user login attempt"""
    log_action(
        'user_login',
        username,
        {
            'success': success,
            'ip_address': ip_address,
        }
    )

def audit_inspection_created(user, inspection_id, form_type, establishment):
    """Log inspection creation"""
    log_action(
        'inspection_created',
        user,
        {
            'inspection_id': inspection_id,
            'form_type': form_type,
            'establishment': establishment,
        }
    )

def audit_form_modified(user, form_type, change_description):
    """Log form modification"""
    log_action(
        'form_modified',
        user,
        {
            'form_type': form_type,
            'changes': change_description,
        }
    )

def audit_user_created(admin_user, new_username, role):
    """Log user creation"""
    log_action(
        'user_created',
        admin_user,
        {
            'new_user': new_username,
            'role': role,
        }
    )

def audit_support_access(action, user, details=None):
    """Log support access events"""
    log_action(
        f'support_access_{action}',
        user,
        details or {}
    )

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Test logging
            print("🧪 Testing audit logging...")

            log_action('test_action', 'test_user', {'test': 'data'})
            print("  ✓ Logged test action")

            log_action('inspection_created', 'inspector1', {
                'inspection_id': 123,
                'form_type': 'Food Establishment',
                'establishment': 'Test Restaurant'
            })
            print("  ✓ Logged inspection creation")

            print(f"\n📊 Audit Log Stats:")
            stats = get_audit_stats()
            print(f"  Total entries: {stats['total_entries']}")
            print(f"  Actions by type: {stats['actions_by_type']}")

        elif sys.argv[1] == 'read':
            # Read recent entries
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10

            print(f"\n📋 Last {limit} audit entries:")
            entries = read_audit_log(limit=limit)

            for entry in entries:
                print(f"\n  [{entry['timestamp']}]")
                print(f"    Action: {entry['action_type']}")
                print(f"    User: {entry['user']}")
                if entry.get('details'):
                    print(f"    Details: {entry['details']}")

        elif sys.argv[1] == 'stats':
            # Show statistics
            print("\n📊 Audit Log Statistics:")
            stats = get_audit_stats()

            print(f"\n  Total Entries: {stats['total_entries']}")
            print(f"  First Entry: {stats['first_entry']}")
            print(f"  Last Entry: {stats['last_entry']}")

            print(f"\n  Actions by Type:")
            for action, count in sorted(stats['actions_by_type'].items(), key=lambda x: x[1], reverse=True):
                print(f"    {action}: {count}")

            print(f"\n  Actions by User:")
            for user, count in sorted(stats['actions_by_user'].items(), key=lambda x: x[1], reverse=True):
                print(f"    {user}: {count}")
    else:
        print("Usage:")
        print("  python audit_log.py test     - Test logging")
        print("  python audit_log.py read [n] - Read last n entries")
        print("  python audit_log.py stats    - Show statistics")
