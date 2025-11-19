#!/usr/bin/env python3
"""
Quick script to check actual record counts in the database
"""
from db_config import get_db_connection

def check_counts():
    conn = get_db_connection()
    c = conn.cursor()

    print("=" * 60)
    print("DATABASE RECORD COUNTS")
    print("=" * 60)

    tables = [
        ('inspections', 'Food/Spirit/Swimming/Small Hotel/Barbershop/Institutional'),
        ('residential_inspections', 'Residential'),
        ('burial_site_inspections', 'Burial Site'),
        ('meat_processing_inspections', 'Meat Processing')
    ]

    total_count = 0

    for table, description in tables:
        try:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            total_count += count
            print(f"{description:45} {count:5} records")
        except Exception as e:
            print(f"{description:45} ERROR: {e}")

    print("=" * 60)
    print(f"{'TOTAL INSPECTIONS':45} {total_count:5} records")
    print("=" * 60)

    # Show recent records from each table
    print("\nRecent Records (last 5 from each table):")
    print("-" * 60)

    for table, description in tables:
        try:
            c.execute(f"SELECT id, created_at FROM {table} ORDER BY created_at DESC LIMIT 5")
            records = c.fetchall()
            if records:
                print(f"\n{description}:")
                for record in records:
                    print(f"  ID: {record[0]}, Created: {record[1]}")
        except Exception as e:
            print(f"\n{description}: ERROR - {e}")

    conn.close()

if __name__ == '__main__':
    check_counts()
