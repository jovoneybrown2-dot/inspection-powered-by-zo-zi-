#!/usr/bin/env python3
"""
Verification script to check Food Establishment checklist items
"""
import sqlite3

def verify_checklist():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Get template ID
    c.execute("SELECT id FROM form_templates WHERE form_type = 'Food Establishment' AND active = 1")
    template = c.fetchone()

    if not template:
        print("❌ No Food Establishment template found!")
        return

    template_id = template[0]
    print(f"✓ Food Establishment template ID: {template_id}\n")

    # Get all items
    c.execute("""
        SELECT item_order, category, description, weight, is_critical
        FROM form_items
        WHERE form_template_id = ?
        ORDER BY item_order
    """, (template_id,))

    items = c.fetchall()

    print(f"{'='*80}")
    print(f"FOOD ESTABLISHMENT CHECKLIST - {len(items)} ITEMS")
    print(f"{'='*80}\n")

    # Show first 5 items
    print("First 5 items:")
    for item in items[:5]:
        print(f"  #{item[0]}: {item[2][:60]}... (wt={item[3]}, cat={item[1]})")

    print(f"\nLast 5 items:")
    for item in items[-5:]:
        print(f"  #{item[0]}: {item[2][:60]}... (wt={item[3]}, cat={item[1]})")

    # Check for missing items
    item_numbers = [item[0] for item in items]
    missing = [i for i in range(1, 45) if i not in item_numbers]

    print(f"\n{'='*80}")
    if missing:
        print(f"❌ MISSING ITEMS: {missing}")
    else:
        print(f"✅ ALL 44 ITEMS PRESENT (1-44)")
    print(f"{'='*80}\n")

    # Verify item #1 specifically
    c.execute("""
        SELECT item_order, description, weight, category
        FROM form_items
        WHERE form_template_id = ? AND item_order = 1
    """, (template_id,))

    item_1 = c.fetchone()
    if item_1:
        print(f"✅ Item #1 verified:")
        print(f"   Description: {item_1[1]}")
        print(f"   Weight: {item_1[2]}")
        print(f"   Category: {item_1[3]}")
    else:
        print(f"❌ Item #1 NOT FOUND!")

    conn.close()

if __name__ == '__main__':
    verify_checklist()
