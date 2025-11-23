"""
Security Monitoring System
Provides file integrity monitoring, audit logging, and security analytics
"""

import os
import hashlib
import json
from datetime import datetime
from db_config import get_db_connection, get_db_type, execute_query

class SecurityMonitor:
    """Comprehensive security monitoring and audit logging"""

    def __init__(self):
        self.critical_files = [
            'app.py',
            'database.py',
            'db_config.py',
            'security_monitoring.py',
            'alert_system.py',
            'form_management_system.py'
        ]
        self.init_security_tables()

    def get_auto_increment(self):
        """Return the correct auto-increment syntax for the current database"""
        return 'SERIAL PRIMARY KEY' if get_db_type() == 'postgresql' else 'INTEGER PRIMARY KEY AUTOINCREMENT'

    def get_timestamp_default(self):
        """Return the correct timestamp default for the current database"""
        return 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP' if get_db_type() == 'postgresql' else 'TEXT DEFAULT CURRENT_TIMESTAMP'

    def _execute(self, conn, query, params=None):
        """Helper to execute queries with automatic placeholder conversion"""
        return execute_query(conn, query, params)

    def init_security_tables(self):
        """Initialize security monitoring database tables"""
        conn = get_db_connection()

        auto_inc = self.get_auto_increment()
        timestamp = self.get_timestamp_default()

        # Migration: Rename old audit_log table if it exists with old schema
        try:
            # Check if audit_log exists and has old schema (missing user_role column)
            cursor = self._execute(conn, """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'audit_log' AND column_name = 'user_role'
            """ if get_db_type() == 'postgresql' else """
                SELECT name FROM pragma_table_info('audit_log') WHERE name = 'user_role'
            """)

            if not cursor.fetchone():
                # Old schema detected - rename the table
                print("📋 Migrating old audit_log table to audit_log_legacy...")
                self._execute(conn, "ALTER TABLE audit_log RENAME TO audit_log_legacy")
                conn.commit()
                print("✓ Old audit_log table backed up as audit_log_legacy")
        except Exception as e:
            # Table doesn't exist or other error - that's fine, we'll create it fresh
            pass

        # File integrity monitoring table
        self._execute(conn, f'''CREATE TABLE IF NOT EXISTS file_integrity (
            id {auto_inc},
            file_path TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            file_size INTEGER,
            last_checked {timestamp},
            status TEXT DEFAULT 'verified',
            modified_date TEXT
        )''')

        # Comprehensive audit log table
        self._execute(conn, f'''CREATE TABLE IF NOT EXISTS audit_log (
            id {auto_inc},
            timestamp {timestamp},
            user_id INTEGER,
            username TEXT NOT NULL,
            user_role TEXT,
            action_type TEXT NOT NULL,
            action_description TEXT,
            target_type TEXT,
            target_id INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            before_value TEXT,
            after_value TEXT,
            status TEXT DEFAULT 'success',
            error_message TEXT
        )''')

        # Login attempts tracking
        self._execute(conn, f'''CREATE TABLE IF NOT EXISTS login_attempts (
            id {auto_inc},
            timestamp {timestamp},
            username TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            success INTEGER DEFAULT 0,
            failure_reason TEXT,
            session_id TEXT
        )''')

        # System changes log (file modifications, schema changes, etc.)
        self._execute(conn, f'''CREATE TABLE IF NOT EXISTS system_changes (
            id {auto_inc},
            timestamp {timestamp},
            change_type TEXT NOT NULL,
            file_path TEXT,
            changed_by TEXT,
            change_description TEXT,
            old_hash TEXT,
            new_hash TEXT,
            severity TEXT DEFAULT 'info'
        )''')

        # Security alerts table
        self._execute(conn, f'''CREATE TABLE IF NOT EXISTS security_alerts (
            id {auto_inc},
            timestamp {timestamp},
            alert_type TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            title TEXT NOT NULL,
            description TEXT,
            related_user TEXT,
            related_file TEXT,
            acknowledged INTEGER DEFAULT 0,
            acknowledged_by TEXT,
            acknowledged_at TIMESTAMP
        )''')

        # Database activity log
        self._execute(conn, f'''CREATE TABLE IF NOT EXISTS database_activity (
            id {auto_inc},
            timestamp {timestamp},
            username TEXT NOT NULL,
            operation TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            changes TEXT,
            ip_address TEXT
        )''')

        conn.commit()
        conn.close()

    def calculate_file_hash(self, filepath):
        """Calculate SHA-256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            return None

    def initialize_file_integrity_baseline(self):
        """Create initial baseline of file hashes"""
        conn = get_db_connection()

        for file_path in self.critical_files:
            if os.path.exists(file_path):
                file_hash = self.calculate_file_hash(file_path)
                file_size = os.path.getsize(file_path)
                modified_date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')

                # Check if file already exists in database
                existing = self._execute(conn, 'SELECT id FROM file_integrity WHERE file_path = %s', (file_path,)).fetchone()

                if existing:
                    # Update existing record
                    self._execute(conn, '''UPDATE file_integrity
                               SET file_hash = %s, file_size = %s, last_checked = %s, modified_date = %s, status = 'verified'
                               WHERE file_path = %s''',
                             (file_hash, file_size, datetime.now(), modified_date, file_path))
                else:
                    # Insert new record
                    self._execute(conn, '''INSERT INTO file_integrity (file_path, file_hash, file_size, modified_date, status)
                               VALUES (%s, %s, %s, %s, 'verified')''',
                             (file_path, file_hash, file_size, modified_date))

        conn.commit()
        conn.close()
        return True

    def check_file_integrity(self):
        """Check if any critical files have been modified"""
        conn = get_db_connection()

        violations = []

        for file_path in self.critical_files:
            if not os.path.exists(file_path):
                violations.append({
                    'file': file_path,
                    'status': 'missing',
                    'message': 'File not found'
                })
                continue

            current_hash = self.calculate_file_hash(file_path)
            current_size = os.path.getsize(file_path)
            modified_date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')

            # Get baseline hash
            baseline = self._execute(conn, 'SELECT file_hash, file_size FROM file_integrity WHERE file_path = %s', (file_path,)).fetchone()

            if not baseline:
                # File not in baseline - add it
                self._execute(conn, '''INSERT INTO file_integrity (file_path, file_hash, file_size, modified_date, status)
                           VALUES (%s, %s, %s, %s, 'new_file')''',
                         (file_path, current_hash, current_size, modified_date))
                violations.append({
                    'file': file_path,
                    'status': 'new',
                    'message': 'New file detected (not in baseline)'
                })
            elif current_hash != baseline[0]:
                # File has been modified
                self._execute(conn, '''UPDATE file_integrity
                           SET file_hash = %s, file_size = %s, last_checked = %s, modified_date = %s, status = 'modified'
                           WHERE file_path = %s''',
                         (current_hash, current_size, datetime.now(), modified_date, file_path))

                # Log the change
                self._execute(conn, '''INSERT INTO system_changes (change_type, file_path, change_description, old_hash, new_hash, severity)
                           VALUES (%s, %s, %s, %s, %s, %s)''',
                         ('file_modification', file_path, f'File {file_path} has been modified', baseline[0], current_hash, 'high'))

                # Create security alert
                self._execute(conn, '''INSERT INTO security_alerts (alert_type, severity, title, description, related_file)
                           VALUES (%s, %s, %s, %s, %s)''',
                         ('file_tampering', 'high', f'File Modified: {file_path}',
                          f'Critical file {file_path} has been modified. Last modified: {modified_date}', file_path))

                violations.append({
                    'file': file_path,
                    'status': 'modified',
                    'message': f'File hash mismatch (modified on {modified_date})',
                    'old_hash': baseline[0],
                    'new_hash': current_hash
                })
            else:
                # File is unchanged - update check time
                self._execute(conn, 'UPDATE file_integrity SET last_checked = %s, status = %s WHERE file_path = %s',
                         (datetime.now(), 'verified', file_path))

        conn.commit()
        conn.close()

        return violations

    def log_audit(self, username, action_type, action_description, **kwargs):
        """Log an audit event"""
        conn = get_db_connection()

        self._execute(conn, '''INSERT INTO audit_log (
            username, user_role, action_type, action_description,
            target_type, target_id, ip_address, user_agent,
            before_value, after_value, status, error_message
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
        (
            username,
            kwargs.get('user_role', ''),
            action_type,
            action_description,
            kwargs.get('target_type', ''),
            kwargs.get('target_id', None),
            kwargs.get('ip_address', ''),
            kwargs.get('user_agent', ''),
            kwargs.get('before_value', ''),
            kwargs.get('after_value', ''),
            kwargs.get('status', 'success'),
            kwargs.get('error_message', '')
        ))

        conn.commit()
        conn.close()

    def log_login_attempt(self, username, success, ip_address='', user_agent='', failure_reason='', session_id=''):
        """Log a login attempt"""
        conn = get_db_connection()

        self._execute(conn, '''INSERT INTO login_attempts (username, ip_address, user_agent, success, failure_reason, session_id)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                 (username, ip_address, user_agent, 1 if success else 0, failure_reason, session_id))

        # Check for multiple failed attempts (brute force detection)
        if get_db_type() == 'postgresql':
            failed_count = self._execute(conn, '''SELECT COUNT(*) FROM login_attempts
                       WHERE username = %s AND success = 0
                       AND timestamp > NOW() - INTERVAL '30 minutes' ''',
                     (username,)).fetchone()[0]
        else:
            failed_count = self._execute(conn, '''SELECT COUNT(*) FROM login_attempts
                       WHERE username = %s AND success = 0
                       AND timestamp > datetime('now', '-30 minutes')''',
                     (username,)).fetchone()[0]

        if failed_count >= 5:
            # Create security alert for potential brute force
            self._execute(conn, '''INSERT INTO security_alerts (alert_type, severity, title, description, related_user)
                       VALUES (%s, %s, %s, %s, %s)''',
                     ('brute_force_attempt', 'high', f'Multiple Failed Login Attempts',
                      f'User {username} has {failed_count} failed login attempts in the last 30 minutes', username))

        conn.commit()
        conn.close()

    def log_database_activity(self, username, operation, table_name, record_id=None, changes='', ip_address=''):
        """Log database operations (CREATE, UPDATE, DELETE)"""
        conn = get_db_connection()

        self._execute(conn, '''INSERT INTO database_activity (username, operation, table_name, record_id, changes, ip_address)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                 (username, operation, table_name, record_id, changes, ip_address))

        conn.commit()
        conn.close()

    def get_security_overview(self):
        """Get security overview statistics"""
        conn = get_db_connection()

        # File integrity status
        verified_files = self._execute(conn, 'SELECT COUNT(*) FROM file_integrity WHERE status = %s', ('verified',)).fetchone()[0]
        modified_files = self._execute(conn, 'SELECT COUNT(*) FROM file_integrity WHERE status = %s', ('modified',)).fetchone()[0]

        # Recent login attempts (last 24 hours)
        if get_db_type() == 'postgresql':
            successful_logins = self._execute(conn, 'SELECT COUNT(*) FROM login_attempts WHERE timestamp > NOW() - INTERVAL %s AND success = 1', ('24 hours',)).fetchone()[0]
            failed_logins = self._execute(conn, 'SELECT COUNT(*) FROM login_attempts WHERE timestamp > NOW() - INTERVAL %s AND success = 0', ('24 hours',)).fetchone()[0]
            total_actions = self._execute(conn, 'SELECT COUNT(*) FROM audit_log WHERE timestamp > NOW() - INTERVAL %s', ('24 hours',)).fetchone()[0]
            db_operations = self._execute(conn, 'SELECT COUNT(*) FROM database_activity WHERE timestamp > NOW() - INTERVAL %s', ('24 hours',)).fetchone()[0]
        else:
            successful_logins = self._execute(conn, 'SELECT COUNT(*) FROM login_attempts WHERE timestamp > datetime(%s, %s) AND success = 1', ('now', '-24 hours')).fetchone()[0]
            failed_logins = self._execute(conn, 'SELECT COUNT(*) FROM login_attempts WHERE timestamp > datetime(%s, %s) AND success = 0', ('now', '-24 hours')).fetchone()[0]
            total_actions = self._execute(conn, 'SELECT COUNT(*) FROM audit_log WHERE timestamp > datetime(%s, %s)', ('now', '-24 hours')).fetchone()[0]
            db_operations = self._execute(conn, 'SELECT COUNT(*) FROM database_activity WHERE timestamp > datetime(%s, %s)', ('now', '-24 hours')).fetchone()[0]

        # Unacknowledged alerts
        unacknowledged_alerts = self._execute(conn, 'SELECT COUNT(*) FROM security_alerts WHERE acknowledged = 0').fetchone()[0]

        conn.close()

        return {
            'file_integrity': {
                'verified': verified_files,
                'modified': modified_files,
                'total': verified_files + modified_files
            },
            'login_activity': {
                'successful': successful_logins,
                'failed': failed_logins,
                'total': successful_logins + failed_logins
            },
            'audit_activity': {
                'total_actions': total_actions,
                'db_operations': db_operations
            },
            'alerts': {
                'unacknowledged': unacknowledged_alerts
            }
        }

    def get_recent_audit_logs(self, limit=50):
        """Get recent audit log entries"""
        conn = get_db_connection()

        logs = self._execute(conn, '''SELECT * FROM audit_log
                   ORDER BY timestamp DESC LIMIT %s''', (limit,)).fetchall()
        conn.close()

        return logs

    def get_recent_login_attempts(self, limit=50):
        """Get recent login attempts"""
        conn = get_db_connection()

        attempts = self._execute(conn, '''SELECT * FROM login_attempts
                   ORDER BY timestamp DESC LIMIT %s''', (limit,)).fetchall()
        conn.close()

        return attempts

    def get_database_activity(self, limit=50):
        """Get recent database activity"""
        conn = get_db_connection()

        activity = self._execute(conn, '''SELECT * FROM database_activity
                   ORDER BY timestamp DESC LIMIT %s''', (limit,)).fetchall()
        conn.close()

        return activity

    def get_security_alerts(self, acknowledged=False):
        """Get security alerts"""
        conn = get_db_connection()

        if acknowledged:
            alerts = self._execute(conn, 'SELECT * FROM security_alerts ORDER BY timestamp DESC').fetchall()
        else:
            alerts = self._execute(conn, 'SELECT * FROM security_alerts WHERE acknowledged = 0 ORDER BY timestamp DESC').fetchall()
        conn.close()

        return alerts

    def acknowledge_alert(self, alert_id, acknowledged_by):
        """Acknowledge a security alert"""
        conn = get_db_connection()

        self._execute(conn, '''UPDATE security_alerts
                   SET acknowledged = 1, acknowledged_by = %s, acknowledged_at = %s
                   WHERE id = %s''',
                 (acknowledged_by, datetime.now(), alert_id))

        conn.commit()
        conn.close()

    def get_file_integrity_details(self):
        """Get detailed file integrity information"""
        conn = get_db_connection()

        files = self._execute(conn, 'SELECT * FROM file_integrity ORDER BY last_checked DESC').fetchall()
        conn.close()

        return files

    def get_system_changes(self, limit=50):
        """Get recent system changes"""
        conn = get_db_connection()

        changes = self._execute(conn, '''SELECT * FROM system_changes
                   ORDER BY timestamp DESC LIMIT %s''', (limit,)).fetchall()
        conn.close()

        return changes

# Global instance
security_monitor = SecurityMonitor()