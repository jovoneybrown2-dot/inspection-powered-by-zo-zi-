#!/usr/bin/env python3
"""
Script to sync barbershop checklist items to database.
This ensures the PostgreSQL database has the correct weights totaling 100.
"""

from database import get_db_connection, release_db_connection
from db_config import get_placeholder

# Barbershop checklist with correct weights
BARBERSHOP_CHECKLIST_ITEMS = [
    {'id': '01', 'desc': 'Overall Condition', 'wt': 2, 'critical': False},
    {'id': '02', 'desc': 'Floors, walls, ceiling', 'wt': 2, 'critical': False},
    {'id': '03', 'desc': 'Lighting', 'wt': 2, 'critical': False},
    {'id': '04', 'desc': 'Ventilation', 'wt': 2, 'critical': False},
    {'id': '05', 'desc': 'Health Certification', 'wt': 2, 'critical': False},
    {'id': '06', 'desc': 'Tables, counters, chairs', 'wt': 2, 'critical': True},
    {'id': '07', 'desc': 'Shampoo basin', 'wt': 4, 'critical': True},
    {'id': '08', 'desc': 'Hair dryers, steamers, hand dryers, hand held tools', 'wt': 4, 'critical': True},
    {'id': '09', 'desc': 'Wash basin', 'wt': 2, 'critical': True},
    {'id': '10', 'desc': 'Towels and linen', 'wt': 4, 'critical': True},
    {'id': '11', 'desc': 'Soap & hand towels', 'wt': 2, 'critical': True},
    {'id': '12', 'desc': 'Sterile cotton swabs', 'wt': 2, 'critical': True},
    {'id': '13', 'desc': 'Tools', 'wt': 5, 'critical': True},
    {'id': '14', 'desc': 'Equipment', 'wt': 5, 'critical': True},
    {'id': '15', 'desc': 'Linen', 'wt': 5, 'critical': True},
    {'id': '16', 'desc': 'Hot water', 'wt': 5, 'critical': True},
    {'id': '17', 'desc': 'Chemicals', 'wt': 5, 'critical': True},
    {'id': '18', 'desc': 'Health certification', 'wt': 3, 'critical': False},
    {'id': '19', 'desc': 'Personal cleanliness', 'wt': 2, 'critical': False},
    {'id': '20', 'desc': 'Hand washing', 'wt': 2, 'critical': False},
    {'id': '21', 'desc': 'First aid kit provided and stocked', 'wt': 5, 'critical': False},
    {'id': '22', 'desc': 'Potable & adequate water supply', 'wt': 5, 'critical': True},
    {'id': '23', 'desc': 'Lavatories', 'wt': 5, 'critical': True},
    {'id': '24', 'desc': 'Sanitary waste water disposal', 'wt': 5, 'critical': True},
    {'id': '25', 'desc': 'Plumbing maintained', 'wt': 2, 'critical': False},
    {'id': '26', 'desc': 'Drains maintained', 'wt': 2, 'critical': False},
    {'id': '27', 'desc': 'Hair, Towels, Swabs Disposed', 'wt': 2, 'critical': False},
    {'id': '28', 'desc': 'Separation of aerosols', 'wt': 2, 'critical': False},
    {'id': '29', 'desc': 'Garbage receptacles', 'wt': 3, 'critical': False},
    {'id': '30', 'desc': 'Absence of pests', 'wt': 3, 'critical': False},
    {'id': '31', 'desc': 'Approved Insecticides', 'wt': 2, 'critical': False},
    {'id': '32', 'desc': 'General cleanliness', 'wt': 2, 'critical': False}
]

def sync_barbershop_checklist():
    """Sync barbershop checklist to database"""
    ph = get_placeholder()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get or create barbershop template
        cursor.execute(f"SELECT id FROM form_templates WHERE form_type = {ph} AND active = 1", ('Barbershop',))
        template = cursor.fetchone()

        if not template:
            print("❌ No Barbershop template found in database")
            print("   Creating new template...")
            cursor.execute(f"""
                INSERT INTO form_templates (form_type, template_name, active, created_date)
                VALUES ({ph}, {ph}, 1, CURRENT_TIMESTAMP)
            """, ('Barbershop', 'Barbershop Standard'))
            conn.commit()

            cursor.execute(f"SELECT id FROM form_templates WHERE form_type = {ph} AND active = 1", ('Barbershop',))
            template = cursor.fetchone()

        template_id = template[0]
        print(f"✓ Using template ID: {template_id}")

        # Update or insert each item
        updated = 0
        inserted = 0

        for item in BARBERSHOP_CHECKLIST_ITEMS:
            item_id = item['id']  # Keep as string: '01', '02', etc.
            item_order = int(item['id'])

            # Check if item exists (by item_id first, then item_order)
            cursor.execute(f"""
                SELECT id, weight, is_critical FROM form_items
                WHERE form_template_id = {ph} AND (item_id = {ph} OR (item_id IS NULL AND item_order = {ph}))
            """, (template_id, item_id, item_order))
            existing = cursor.fetchone()

            if existing:
                # Update existing item
                cursor.execute(f"""
                    UPDATE form_items
                    SET description = {ph}, weight = {ph}, is_critical = {ph}, item_id = {ph}, active = 1
                    WHERE id = {ph}
                """, (item['desc'], item['wt'], 1 if item['critical'] else 0, item_id, existing[0]))
                updated += 1
                print(f"  Updated item {item['id']}: {item['desc']} (wt={item['wt']})")
            else:
                # Insert new item
                cursor.execute(f"""
                    INSERT INTO form_items
                    (form_template_id, item_order, item_id, category, description, weight, is_critical, active)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, 1)
                """, (template_id, item_order, item_id, '', item['desc'], item['wt'], 1 if item['critical'] else 0))
                inserted += 1
                print(f"  Inserted item {item['id']}: {item['desc']} (wt={item['wt']})")

        conn.commit()

        # Verify total
        cursor.execute(f"""
            SELECT SUM(weight) FROM form_items
            WHERE form_template_id = {ph} AND active = 1
        """, (template_id,))
        total = cursor.fetchone()[0] or 0

        print(f"\n✓ Sync complete!")
        print(f"  Updated: {updated} items")
        print(f"  Inserted: {inserted} items")
        print(f"  Total weight: {total}")

        if total != 100:
            print(f"  ⚠️  WARNING: Total weight is {total}, expected 100")
        else:
            print(f"  ✓ Total weight is correct (100)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    print("Starting barbershop checklist sync...")
    print(f"Total items: {len(BARBERSHOP_CHECKLIST_ITEMS)}")
    print(f"Expected total weight: {sum(item['wt'] for item in BARBERSHOP_CHECKLIST_ITEMS)}")
    print()
    sync_barbershop_checklist()