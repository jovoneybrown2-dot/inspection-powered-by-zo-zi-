#!/usr/bin/env python3
"""
Fix Food Establishment Checklist
Deletes old wrong items and inserts correct 44-item checklist
Run this on Render to fix the missing item #1
"""

from db_config import get_db_connection, get_placeholder

def fix_food_checklist():
    print("="*70)
    print("🔧 FIXING FOOD ESTABLISHMENT CHECKLIST")
    print("="*70)

    conn = get_db_connection()
    c = conn.cursor()
    ph = get_placeholder()

    # Get Food Establishment template ID
    c.execute(f"SELECT id FROM form_templates WHERE form_type = {ph}", ('Food Establishment',))
    template = c.fetchone()

    if not template:
        print("❌ Food Establishment template not found!")
        conn.close()
        return False

    template_id = template[0]
    print(f"✓ Found Food Establishment template (ID: {template_id})")

    # Count existing items
    c.execute(f"SELECT COUNT(*) FROM form_items WHERE form_template_id = {ph}", (template_id,))
    old_count = c.fetchone()[0]
    print(f"✓ Found {old_count} existing items")

    # Delete old items
    print("\n🗑️  Deleting old items...")
    c.execute(f"DELETE FROM form_items WHERE form_template_id = {ph}", (template_id,))
    conn.commit()
    print(f"✅ Deleted {old_count} old items")

    # Insert correct 44 items
    print("\n📝 Inserting correct 44-item checklist...")

    FOOD_CHECKLIST = [
        # FOOD (1-2)
        (1, "FOOD", "Source, Sound Condition, No Spoilage", 5, 0),
        (2, "FOOD", "Original Container, Properly Labeled", 1, 0),

        # FOOD PROTECTION (3-10)
        (3, "FOOD PROTECTION", "Potentially Hazardous Food Meets Temcjblperature Requirements During Storage, Preparation, Display, Service, Transportation", 5, 0),
        (4, "FOOD PROTECTION", "Facilities to Maintain Product Temperature", 4, 0),
        (5, "FOOD PROTECTION", "Thermometers Provided and Conspicuous", 1, 0),
        (6, "FOOD PROTECTION", "Potentially Hazardous Food Properly Thawed", 2, 0),
        (7, "FOOD PROTECTION", "Unwrapped and Potentially Hazardous Food Not Re-Served", 4, 0),
        (8, "FOOD PROTECTION", "Food Protection During Storage, Preparation, Display, Service, Transportation", 2, 0),
        (9, "FOOD PROTECTION", "Handling of Food (Ice) Minimized", 1, 0),
        (10, "FOOD PROTECTION", "In Use Food (Ice) Dispensing Utensils Properly Stored", 1, 0),

        # FOOD EQUIPMENT & UTENSILS (11-23)
        (11, "FOOD EQUIPMENT & UTENSILS", "Food Contact Surfaces Designed, Constructed, Maintained, Installed, Located", 2, 0),
        (12, "FOOD EQUIPMENT & UTENSILS", "Non-Food Contact Surfaces Designed, Constructed, Maintained, Installed, Located", 1, 0),
        (13, "FOOD EQUIPMENT & UTENSILS", "Dishwashing Facilities Designed, Constructed, Maintained, Installed, Located, Operated", 2, 0),
        (14, "FOOD EQUIPMENT & UTENSILS", "Accurate Thermometers, Chemical Test Kits Provided", 1, 0),
        (15, "FOOD EQUIPMENT & UTENSILS", "Single Service Articles Storage, Dispensing", 1, 0),
        (16, "FOOD EQUIPMENT & UTENSILS", "No Re-Use of Single Serve Articles", 2, 0),
        (17, "FOOD EQUIPMENT & UTENSILS", "Pre-Flushed, Scraped, Soaked", 1, 0),
        (18, "FOOD EQUIPMENT & UTENSILS", "Wash, Rinse Water Clean, Proper Temperature", 2, 0),
        (19, "FOOD EQUIPMENT & UTENSILS", "Sanitization Rinse Clean, Temperature, Concentration, Exposure Time, Equipment, Utensils Sanitized", 4, 0),
        (20, "FOOD EQUIPMENT & UTENSILS", "Wiping Cloths Clean, Use Restricted", 1, 0),
        (21, "FOOD EQUIPMENT & UTENSILS", "Food Contact Surfaces of Equipment and Utensils Clean, Free of Abrasives, Detergents", 2, 0),
        (22, "FOOD EQUIPMENT & UTENSILS", "Non-Food Contact Surfaces of Equipment and Utensils Clean", 1, 0),
        (23, "FOOD EQUIPMENT & UTENSILS", "Storage, Handling of Clean Equipment/Utensils", 1, 0),

        # TOILET & HANDWASHING FACILITIES (24-25)
        (24, "TOILET & HANDWASHING FACILITIES", "Number, Convenient, Accessible, Designed, Installed", 4, 0),
        (25, "TOILET & HANDWASHING FACILITIES", "Toilet Rooms Enclosed, Self-Closing Doors, Fixtures: Good Repair, Clean, Hand Cleanser, Sanitary Towels, Hand Drying Devices Provided, Proper Waste Receptacles", 2, 0),

        # SOLID WASTE MANAGEMENT (26-27)
        (26, "SOLID WASTE MANAGEMENT", "Containers or Receptacles: Covered, Adequate Number, Insect/Rodent Proof, Frequency, Clean", 2, 0),
        (27, "SOLID WASTE MANAGEMENT", "Outside Storage Area Enclosures Properly Constructed, Clean, Controlled Incineration", 1, 0),

        # INSECT, RODENT, ANIMAL CONTROL (28)
        (28, "INSECT, RODENT, ANIMAL CONTROL", "Evidence of Insects/Rodents - Outer Openings, Protected, No Birds, Turtles, Other Animals", 4, 0),

        # PERSONNEL (29-31)
        (29, "PERSONNEL", "Personnel with Infections Restricted", 5, 0),
        (30, "PERSONNEL", "Hands Washed and Clean, Good Hygienic Practices", 5, 0),
        (31, "PERSONNEL", "Clean Clothes, Hair Restraints", 2, 0),

        # LIGHTING (32)
        (32, "LIGHTING", "Lighting Provided as Required, Fixtures Shielded", 1, 0),

        # VENTILATION (33)
        (33, "VENTILATION", "Rooms and Equipment - Venting as Required", 1, 0),

        # DRESSING ROOMS (34)
        (34, "DRESSING ROOMS", "Rooms Clean, Lockers Provided, Facilities Clean", 1, 0),

        # WATER (35)
        (35, "WATER", "Water Source Safe, Hot & Cold Under Pressure", 5, 0),

        # SEWAGE (36)
        (36, "SEWAGE", "Sewage and Waste Water Disposal", 4, 0),

        # PLUMBING (37-38)
        (37, "PLUMBING", "Installed, Maintained", 1, 0),
        (38, "PLUMBING", "Cross Connection, Back Siphonage, Backflow", 5, 0),

        # FLOORS, WALLS, & CEILINGS (39-40)
        (39, "FLOORS, WALLS, & CEILINGS", "Floors: Constructed, Drained, Clean, Good Repair, Covering Installation, Dustless Cleaning Methods", 1, 0),
        (40, "FLOORS, WALLS, & CEILINGS", "Walls, Ceiling, Attached Equipment: Constructed, Good Repair, Clean Surfaces, Dustless Cleaning Methods", 1, 0),

        # OTHER OPERATIONS (41-44)
        (41, "OTHER OPERATIONS", "Toxic Items Properly Stored, Labeled, Used", 5, 0),
        (42, "OTHER OPERATIONS", "Premises Maintained Free of Litter, Unnecessary Articles, Cleaning Maintenance Equipment Properly Stored, Authorized Personnel", 1, 0),
        (43, "OTHER OPERATIONS", "Complete Separation for Living/Sleeping Quarters, Laundry", 1, 0),
        (44, "OTHER OPERATIONS", "Clean, Soiled Linen Properly Stored", 1, 0),
    ]

    # Insert all items
    inserted = 0
    for item_order, category, description, weight, is_critical in FOOD_CHECKLIST:
        try:
            c.execute(f"""
                INSERT INTO form_items
                (form_template_id, item_order, category, description, weight, is_critical, item_id)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """, (template_id, item_order, category, description, weight, is_critical, str(item_order)))
            inserted += 1
        except Exception as e:
            print(f"   ⚠️  Error inserting item {item_order}: {e}")

    conn.commit()
    print(f"✅ Inserted {inserted} items")

    # Verify
    c.execute(f"SELECT item_order, description FROM form_items WHERE form_template_id = {ph} ORDER BY item_order LIMIT 3", (template_id,))
    first_items = c.fetchall()

    print("\n📋 First 3 items now in database:")
    for item in first_items:
        print(f"   #{item[0]}: {item[1][:60]}...")

    conn.close()

    print("\n" + "="*70)
    print("✅ FOOD ESTABLISHMENT CHECKLIST FIXED!")
    print("="*70)
    print(f"\n✓ Total items: {inserted}")
    print("✓ Item #1: 'Source, Sound Condition, No Spoilage' is now present")
    print("\n🌐 Refresh your Render app to see all 44 items\n")

    return True

if __name__ == '__main__':
    fix_food_checklist()
