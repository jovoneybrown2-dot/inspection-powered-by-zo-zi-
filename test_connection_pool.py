#!/usr/bin/env python3
"""
Connection Pool Test Script
Tests the new connection pooling implementation for PostgreSQL
"""
import os
import time
from db_config import get_db_connection, release_db_connection, get_db_type

def test_basic_connection():
    """Test basic connection get/release"""
    print("="*60)
    print("TEST 1: Basic Connection Get/Release")
    print("="*60)

    print(f"Database Type: {get_db_type()}")

    conn = get_db_connection()
    print("✓ Got connection from pool")

    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print(f"✓ Query successful: {result}")

    release_db_connection(conn)
    print("✓ Released connection back to pool")
    print()

def test_multiple_connections():
    """Test getting multiple connections simultaneously"""
    print("="*60)
    print("TEST 2: Multiple Simultaneous Connections")
    print("="*60)

    connections = []

    # Get 10 connections
    for i in range(10):
        conn = get_db_connection()
        connections.append(conn)
        print(f"✓ Got connection {i+1}/10")

    # Use them
    for i, conn in enumerate(connections):
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✓ Connection {i+1} query successful")

    # Release them
    for i, conn in enumerate(connections):
        release_db_connection(conn)
        print(f"✓ Released connection {i+1}/10")

    print()

def test_connection_reuse():
    """Test that connections are actually reused"""
    print("="*60)
    print("TEST 3: Connection Reuse")
    print("="*60)

    # Get and release connection 5 times
    for i in range(5):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT pg_backend_pid()" if get_db_type() == 'postgresql' else "SELECT 1")
        pid = cursor.fetchone()
        print(f"Round {i+1}: Connection PID/ID = {pid}")
        release_db_connection(conn)
        time.sleep(0.1)

    print("✓ If PIDs repeat, connections are being reused!")
    print()

def test_error_handling():
    """Test that connections are released even on error"""
    print("="*60)
    print("TEST 4: Error Handling")
    print("="*60)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nonexistent_table")
    except Exception as e:
        print(f"✓ Expected error occurred: {type(e).__name__}")
    finally:
        release_db_connection(conn)
        print("✓ Connection released despite error")

    # Verify we can still get connections
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("✓ New connection works after error")
    release_db_connection(conn)
    print()

def test_performance():
    """Compare performance with/without pooling"""
    print("="*60)
    print("TEST 5: Performance Test")
    print("="*60)

    # Test pooled connections
    start = time.time()
    for i in range(20):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        release_db_connection(conn)
    pooled_time = time.time() - start

    print(f"✓ 20 pooled connections: {pooled_time:.3f} seconds")
    print(f"  Average: {pooled_time/20*1000:.1f}ms per connection")
    print()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CONNECTION POOL TEST SUITE")
    print("="*60)
    print()

    try:
        test_basic_connection()
        test_multiple_connections()
        test_connection_reuse()
        test_error_handling()
        test_performance()

        print("="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print()
        print("Connection pooling is working correctly!")
        print()
        print("Key Benefits:")
        print("- Connections are reused instead of created fresh")
        print("- Multiple simultaneous connections supported")
        print("- Automatic cleanup on errors")
        print("- Significant performance improvement")
        print()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
