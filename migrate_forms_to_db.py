#!/usr/bin/env python3
"""
Migration script to populate form_items table with hardcoded checklists
This preserves existing forms while enabling database-driven form management
"""

import sqlite3
from datetime import datetime

# Import the hardcoded checklists from app.py
import sys
sys.path.insert(0, '.')
from app import (
    FOOD_CHECKLIST_ITEMS,
    RESIDENTIAL_CHECKLIST_ITEMS,
    SPIRIT_LICENCE_CHECKLIST_ITEMS,
    SWIMMING_POOL_CHECKLIST_ITEMS,
    SMALL_HOTELS_CHECKLIST_ITEMS,
    BARBERSHOP_CHECKLIST_ITEMS,
    INSTITUTIONAL_CHECKLIST_ITEMS,
    MEAT_PROCESSING_CHECKLIST_ITEMS
)

def migrate_forms():
    """Migrate all hardcoded form checklists to database"""
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Check if migration already done
    c.execute("SELECT COUNT(*) FROM form_items")
    if c.fetchone()[0] > 0:
        print("⚠️  Migration already completed. form_items table has data.")
        response = input("Do you want to clear and re-migrate? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            conn.close()
            return
        c.execute("DELETE FROM form_items")
        print("✓ Cleared existing form_items")

    # Mapping of form types to their template IDs and checklists
    form_mappings = [
        {
            'template_id': 1,
            'form_type': 'Food Establishment',
            'checklist': FOOD_CHECKLIST_ITEMS,
            'categories': {
                1: 'FOOD',
                3: 'FOOD PROTECTION',
                11: 'FOOD EQUIPMENT & UTENSILS',
                24: 'TOILET & HANDWASHING FACILITIES',
                26: 'SOLID WASTE MANAGEMENT',
                28: 'INSECT, RODENT, ANIMAL CONTROL',
                29: 'PERSONNEL',
                32: 'LIGHTING',
                33: 'VENTILATION',
                34: 'DRESSING ROOMS',
                35: 'WATER',
                36: 'SEWAGE',
                37: 'FLOORS, WALLS, CEILINGS',
                40: 'MISCELLANEOUS'
            }
        },
        {
            'template_id': 2,
            'form_type': 'Residential',
            'checklist': RESIDENTIAL_CHECKLIST_ITEMS,
            'categories': {
                1: 'GENERAL',
                5: 'WATER SUPPLY',
                10: 'SANITATION',
                15: 'STRUCTURE'
            }
        },
        {
            'template_id': 4,
            'form_type': 'Spirit Licence Premises',
            'checklist': SPIRIT_LICENCE_CHECKLIST_ITEMS,
            'categories': {
                1: 'GENERAL REQUIREMENTS',
                12: 'CRITICAL ITEMS',
                25: 'ADDITIONAL REQUIREMENTS'
            }
        },
        {
            'template_id': 5,
            'form_type': 'Swimming Pool',
            'checklist': SWIMMING_POOL_CHECKLIST_ITEMS,
            'categories': {
                1: 'GENERAL'
            }
        },
        {
            'template_id': 6,
            'form_type': 'Small Hotel',
            'checklist': SMALL_HOTELS_CHECKLIST_ITEMS,
            'categories': {
                1: 'GENERAL'
            }
        },
        {
            'template_id': 493,
            'form_type': 'Barbershop',
            'checklist': BARBERSHOP_CHECKLIST_ITEMS,
            'categories': {
                1: 'GENERAL'
            }
        },
        {
            'template_id': 494,
            'form_type': 'Institutional',
            'checklist': INSTITUTIONAL_CHECKLIST_ITEMS,
            'categories': {
                1: 'GENERAL'
            }
        },
        {
            'template_id': 495,
            'form_type': 'Meat Processing',
            'checklist': MEAT_PROCESSING_CHECKLIST_ITEMS,
            'categories': {
                1: 'GROUNDS AND FACILITIES',
                5: 'BUILDINGS',
                20: 'EQUIPMENT',
                35: 'SANITARY OPERATIONS',
                50: 'GENERAL'
            }
        }
    ]

    total_items = 0

    for mapping in form_mappings:
        template_id = mapping['template_id']
        form_type = mapping['form_type']
        checklist = mapping['checklist']
        categories = mapping['categories']

        print(f"\n📝 Migrating {form_type} ({len(checklist)} items)...")

        current_category = 'GENERAL'
        for item in checklist:
            item_id = item['id']

            # Convert item_id to int for comparison (handle both string and int IDs)
            try:
                item_id_num = int(str(item_id).strip())
            except (ValueError, AttributeError):
                item_id_num = 1  # Default to 1 if can't convert

            # Determine category based on item ID
            for cat_id, cat_name in sorted(categories.items(), reverse=True):
                if item_id_num >= cat_id:
                    current_category = cat_name
                    break

            # Determine if critical (weight >= 4 is typically critical)
            is_critical = 1 if item.get('wt', 0) >= 4 else 0

            # Handle both 'desc' and 'description' keys
            description = item.get('desc') or item.get('description', 'No description')

            c.execute('''
                INSERT INTO form_items (
                    form_template_id, item_order, category, description,
                    weight, is_critical, active, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template_id,
                item_id,
                current_category,
                description,
                item.get('wt', 1),
                is_critical,
                1,  # active
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            total_items += 1

        print(f"   ✓ Migrated {len(checklist)} items")

    conn.commit()

    # Verify migration
    print(f"\n✅ Migration complete! Total items migrated: {total_items}")
    print("\nVerification:")
    c.execute('''
        SELECT ft.name, COUNT(fi.id) as item_count
        FROM form_templates ft
        LEFT JOIN form_items fi ON ft.id = fi.form_template_id
        WHERE ft.id IN (1, 2, 4, 5, 6, 493, 494, 495)
        GROUP BY ft.name
        ORDER BY ft.id
    ''')

    for row in c.fetchall():
        print(f"   • {row[0]}: {row[1]} items")

    conn.close()
    print("\n🎉 Form migration successful! Forms are now database-driven.")

if __name__ == '__main__':
    print("=" * 60)
    print("FORM CHECKLIST MIGRATION")
    print("=" * 60)
    print("\nThis will migrate hardcoded checklists to the database.")
    print("This enables the Form Builder feature for admins.")
    print()

    try:
        migrate_forms()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
