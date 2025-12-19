#!/usr/bin/env python3
"""
Sync all form checklists to database.
This ensures all inspection forms have their checklist items populated.
"""

from database import get_db_connection, release_db_connection
from db_config import get_placeholder

def sync_institutional_checklist():
    """Sync institutional checklist (31 items, 100 total weight, 70 critical)"""

    # Define checklist directly to avoid importing app.py
    INSTITUTIONAL_CHECKLIST_ITEMS = [
        {'id': '01', 'desc': 'Absence of overcrowding', 'wt': 5, 'critical': True},
        {'id': '02', 'desc': 'Structural Integrity', 'wt': 2, 'critical': False},
        {'id': '03', 'desc': 'Housekeeping', 'wt': 2, 'critical': False},
        {'id': '04', 'desc': 'Clean Floor', 'wt': 1, 'critical': False},
        {'id': '05', 'desc': 'Clean Walls', 'wt': 1, 'critical': False},
        {'id': '06', 'desc': 'Clean Ceiling', 'wt': 1, 'critical': False},
        {'id': '07', 'desc': 'Lighting', 'wt': 1, 'critical': False},
        {'id': '08', 'desc': 'Ventilation', 'wt': 3, 'critical': False},
        {'id': '09', 'desc': 'Adequacy', 'wt': 5, 'critical': True},
        {'id': '10', 'desc': 'Potability', 'wt': 5, 'critical': True},
        {'id': '11', 'desc': 'Sanitary excreta disposal', 'wt': 5, 'critical': True},
        {'id': '12', 'desc': 'Adequacy', 'wt': 5, 'critical': True},
        {'id': '13', 'desc': 'Food Storage', 'wt': 5, 'critical': True},
        {'id': '14', 'desc': 'Kitchen', 'wt': 5, 'critical': True},
        {'id': '15', 'desc': 'Dining Room', 'wt': 5, 'critical': True},
        {'id': '16', 'desc': 'Food handling practices', 'wt': 5, 'critical': True},
        {'id': '17', 'desc': 'Storage', 'wt': 5, 'critical': True},
        {'id': '18', 'desc': 'Disposal', 'wt': 5, 'critical': True},
        {'id': '19', 'desc': 'Absence', 'wt': 5, 'critical': True},
        {'id': '20', 'desc': 'Control system in place', 'wt': 5, 'critical': True},
        {'id': '21', 'desc': 'General Cleanliness', 'wt': 2, 'critical': False},
        {'id': '22', 'desc': 'Drainage', 'wt': 2, 'critical': False},
        {'id': '23', 'desc': 'Protected from stray animals', 'wt': 2, 'critical': False},
        {'id': '24', 'desc': 'Vegetation', 'wt': 2, 'critical': False},
        {'id': '25', 'desc': 'Provision for physically challenged', 'wt': 2, 'critical': False},
        {'id': '26', 'desc': 'Fire extinguishers', 'wt': 5, 'critical': True},
        {'id': '27', 'desc': 'Access to medical care', 'wt': 2, 'critical': False},
        {'id': '28', 'desc': 'First Aid available', 'wt': 2, 'critical': False},
        {'id': '29', 'desc': 'Emergency exit', 'wt': 2, 'critical': False},
        {'id': '30', 'desc': 'Veterinary certification of pets', 'wt': 1, 'critical': False},
        {'id': '31', 'desc': 'Adequacy', 'wt': 2, 'critical': False}
    ]

    ph = get_placeholder()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get or create institutional template
        cursor.execute(f"SELECT id FROM form_templates WHERE form_type = {ph} AND active = 1", ('Institutional',))
        template = cursor.fetchone()

        if not template:
            print("  Creating Institutional template...")
            cursor.execute(f"""
                INSERT INTO form_templates (form_type, name, description, active)
                VALUES ({ph}, {ph}, {ph}, 1)
            """, ('Institutional', 'Institutional Inspection', 'Institutional health inspection form'))
            conn.commit()

            cursor.execute(f"SELECT id FROM form_templates WHERE form_type = {ph} AND active = 1", ('Institutional',))
            template = cursor.fetchone()

        template_id = template[0]

        # Sync each item
        for item in INSTITUTIONAL_CHECKLIST_ITEMS:
            item_id = item['id']

            cursor.execute(f"""
                SELECT id FROM form_items
                WHERE form_template_id = {ph} AND item_id = {ph}
            """, (template_id, item_id))
            existing = cursor.fetchone()

            if existing:
                cursor.execute(f"""
                    UPDATE form_items
                    SET description = {ph}, weight = {ph}, is_critical = {ph},
                        item_order = {ph}, active = 1
                    WHERE form_template_id = {ph} AND item_id = {ph}
                """, (item['desc'], item['wt'], 1 if item['critical'] else 0,
                      int(item_id), template_id, item_id))
            else:
                cursor.execute(f"""
                    INSERT INTO form_items
                    (form_template_id, item_order, category, description, weight, is_critical, active, item_id)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, 1, {ph})
                """, (template_id, int(item_id), '', item['desc'], item['wt'],
                      1 if item['critical'] else 0, item_id))

        conn.commit()

        # Verify
        cursor.execute(f"""
            SELECT COUNT(*), SUM(weight), SUM(CASE WHEN is_critical = 1 THEN weight ELSE 0 END)
            FROM form_items
            WHERE form_template_id = {ph} AND active = 1
        """, (template_id,))
        result = cursor.fetchone()
        count, total, critical = result[0] or 0, result[1] or 0, result[2] or 0

        print(f"✓ Institutional: {count} items, {total} total weight, {critical} critical weight")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ Institutional sync failed: {e}")
        return False
    finally:
        release_db_connection(conn)


def sync_barbershop_checklist():
    """Sync barbershop checklist"""
    try:
        from sync_barbershop_checklist import sync_barbershop_checklist as sync_func
        sync_func()
        return True
    except Exception as e:
        print(f"❌ Barbershop sync failed: {e}")
        return False


def sync_all_checklists():
    """Sync all form checklists to database"""
    print("=" * 60)
    print("SYNCING ALL FORM CHECKLISTS TO DATABASE")
    print("=" * 60)

    results = []

    # Sync Institutional
    print("\n1. Institutional Health Form...")
    results.append(('Institutional', sync_institutional_checklist()))

    # Sync Barbershop
    print("\n2. Barbershop Form...")
    results.append(('Barbershop', sync_barbershop_checklist()))

    # Summary
    print("\n" + "=" * 60)
    print("SYNC SUMMARY")
    print("=" * 60)
    success_count = sum(1 for _, success in results if success)
    print(f"✓ {success_count}/{len(results)} forms synced successfully")

    for form_name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {form_name}")

    return all(success for _, success in results)


if __name__ == '__main__':
    import sys
    success = sync_all_checklists()
    sys.exit(0 if success else 1)
