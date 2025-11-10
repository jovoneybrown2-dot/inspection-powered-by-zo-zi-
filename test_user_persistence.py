#!/usr/bin/env python3
"""
Test script to verify user persistence in the database
"""
import sqlite3
from datetime import datetime

def test_user_persistence():
    print("="*70)
    print("USER PERSISTENCE TEST")
    print("="*70)

    db_path = 'inspections.db'

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Check current users
    print("\n1. Current Users in Database:")
    c.execute('SELECT id, username, email, role, is_flagged FROM users ORDER BY id')
    users = c.fetchall()
    print(f"   Total users: {len(users)}")
    for user in users:
        print(f"   - ID {user['id']}: {user['username']} ({user['role']}) - Email: {user['email'] or 'N/A'}")

    # 2. Test adding a new user
    print("\n2. Testing User Creation:")
    test_username = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_email = f"{test_username}@test.com"
    test_password = "test123456"
    test_role = "inspector"

    try:
        c.execute('''
            INSERT INTO users (username, email, password, role, is_flagged)
            VALUES (?, ?, ?, ?, 0)
        ''', (test_username, test_email, test_password, test_role))

        conn.commit()
        new_user_id = c.lastrowid
        print(f"   ✓ Created test user: {test_username} (ID: {new_user_id})")
    except Exception as e:
        print(f"   ✗ Error creating user: {e}")
        conn.close()
        return False

    # 3. Verify user was saved
    print("\n3. Verifying User Persistence:")
    c.execute('SELECT id, username, email, role FROM users WHERE id = ?', (new_user_id,))
    saved_user = c.fetchone()

    if saved_user:
        print(f"   ✓ User found in database after creation")
        print(f"     - Username: {saved_user['username']}")
        print(f"     - Email: {saved_user['email']}")
        print(f"     - Role: {saved_user['role']}")
    else:
        print(f"   ✗ User NOT found in database!")
        conn.close()
        return False

    # 4. Close and reopen connection to test persistence
    print("\n4. Testing Persistence After Connection Close:")
    conn.close()

    # Reopen connection
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT id, username, email, role FROM users WHERE id = ?', (new_user_id,))
    persistent_user = c.fetchone()

    if persistent_user:
        print(f"   ✓ User STILL exists after connection reopen")
        print(f"     This confirms data is being saved to disk!")
    else:
        print(f"   ✗ User disappeared after connection reopen")
        conn.close()
        return False

    # 5. Final count
    print("\n5. Final User Count:")
    c.execute('SELECT COUNT(*) as count FROM users')
    final_count = c.fetchone()['count']
    print(f"   Total users now: {final_count}")

    # 6. Cleanup - remove test user
    print("\n6. Cleanup:")
    c.execute('DELETE FROM users WHERE id = ?', (new_user_id,))
    conn.commit()
    print(f"   ✓ Removed test user (ID: {new_user_id})")

    conn.close()

    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - Users are persisting correctly!")
    print("="*70)
    print("\n💡 If users are disappearing in the UI:")
    print("   1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)")
    print("   2. Check browser console for JavaScript errors")
    print("   3. Verify you're clicking 'Refresh' button after adding users")
    print("   4. Make sure flask app is running without restarts")
    return True

if __name__ == '__main__':
    test_user_persistence()
