#!/usr/bin/env python3
"""Fix missing item_id values in form_items table"""

from db_config import get_db_connection, execute_query

FOOD_CHECKLIST_ITEMS = [
    # FOOD (1-2)
    {"id": 1, "desc": "Source, Sound Condition, No Spoilage", "wt": 5},
    {"id": 2, "desc": "Original Container, Properly Labeled", "wt": 1},

    # FOOD PROTECTION (3-10)
    {"id": 3, "desc": "Potentially Hazardous Food Meets Temcjblperature Requirements During Storage, Preparation, Display, Service, Transportation", "wt": 5},
    {"id": 4, "desc": "Facilities to Maintain Product Temperature", "wt": 4},
    {"id": 5, "desc": "Thermometers Provided and Conspicuous", "wt": 1},
    {"id": 6, "desc": "Potentially Hazardous Food Properly Thawed", "wt": 2},
    {"id": 7, "desc": "Unwrapped and Potentially Hazardous Food Not Re-Served", "wt": 4},
    {"id": 8, "desc": "Food Protection During Storage, Preparation, Display, Service, Transportation", "wt": 2},
    {"id": 9, "desc": "Handling of Food (Ice) Minimized", "wt": 1},
    {"id": 10, "desc": "In Use Food (Ice) Dispensing Utensils Properly Stored", "wt": 1},

    # FOOD EQUIPMENT & UTENSILS (11-23)
    {"id": 11, "desc": "Food Contact Surfaces Designed, Constructed, Maintained, Installed, Located", "wt": 2},
    {"id": 12, "desc": "Non-Food Contact Surfaces Designed, Constructed, Maintained, Installed, Located", "wt": 1},
    {"id": 13, "desc": "Dishwashing Facilities Designed, Constructed, Maintained, Installed, Located, Operated", "wt": 2},
    {"id": 14, "desc": "Accurate Thermometers, Chemical Test Kits Provided", "wt": 1},
    {"id": 15, "desc": "Single Service Articles Storage, Dispensing", "wt": 1},
    {"id": 16, "desc": "No Re-Use of Single Serve Articles", "wt": 2},
    {"id": 17, "desc": "Pre-Flushed, Scraped, Soaked", "wt": 1},
    {"id": 18, "desc": "Wash, Rinse Water Clean, Proper Temperature", "wt": 2},
    {"id": 19, "desc": "Sanitization Rinse Clean, Temperature, Concentration, Exposure Time, Equipment, Utensils Sanitized", "wt": 4},
    {"id": 20, "desc": "Wiping Cloths Clean, Use Restricted", "wt": 1},
    {"id": 21, "desc": "Food Contact Surfaces of Equipment and Utensils Clean, Free of Abrasives, Detergents", "wt": 2},
    {"id": 22, "desc": "Non-Food Contact Surfaces of Equipment and Utensils Clean", "wt": 1},
    {"id": 23, "desc": "Storage, Handling of Clean Equipment/Utensils", "wt": 1},

    # TOILET & HANDWASHING FACILITIES (24-25)
    {"id": 24, "desc": "Number, Convenient, Accessible, Designed, Installed", "wt": 4},
    {"id": 25, "desc": "Toilet Rooms Enclosed, Self-Closing Doors, Fixtures: Good Repair, Clean, Hand Cleanser, Sanitary Towels, Hand Drying Devices Provided, Proper Waste Receptacles", "wt": 2},

    # SOLID WASTE MANAGEMENT (26-27)
    {"id": 26, "desc": "Containers or Receptacles: Covered, Adequate Number, Insect/Rodent Proof, Frequency, Clean", "wt": 2},
    {"id": 27, "desc": "Outside Storage Area Enclosures Properly Constructed, Clean, Controlled Incineration", "wt": 1},

    # INSECT, RODENT, ANIMAL CONTROL (28)
    {"id": 28, "desc": "Evidence of Insects/Rodents - Outer Openings, Protected, No Birds, Turtles, Other Animals", "wt": 4},

    # PERSONNEL (29-31)
    {"id": 29, "desc": "Personnel with Infections Restricted", "wt": 5},
    {"id": 30, "desc": "Hands Washed and Clean, Good Hygienic Practices", "wt": 5},
    {"id": 31, "desc": "Clean Clothes, Hair Restraints", "wt": 2},

    # LIGHTING (32)
    {"id": 32, "desc": "Lighting Provided as Required, Fixtures Shielded", "wt": 1},

    # VENTILATION (33)
    {"id": 33, "desc": "Rooms and Equipment - Venting as Required", "wt": 1},

    # DRESSING ROOMS (34)
    {"id": 34, "desc": "Rooms Clean, Lockers Provided, Facilities Clean", "wt": 1},

    # WATER (35)
    {"id": 35, "desc": "Water Source Safe, Hot & Cold Under Pressure", "wt": 5},

    # SEWAGE (36)
    {"id": 36, "desc": "Sewage and Waste Water Disposal", "wt": 4},

    # PLUMBING (37-38)
    {"id": 37, "desc": "Installed, Maintained", "wt": 1},
    {"id": 38, "desc": "Cross Connection, Back Siphonage, Backflow", "wt": 5},

    # FLOORS, WALLS, & CEILINGS (39-40)
    {"id": 39, "desc": "Floors: Constructed, Drained, Clean, Good Repair, Covering Installation, Dustless Cleaning Methods", "wt": 1},
    {"id": 40, "desc": "Walls, Ceiling, Attached Equipment: Constructed, Good Repair, Clean Surfaces, Dustless Cleaning Methods", "wt": 1},

    # OTHER OPERATIONS (41-44)
    {"id": 41, "desc": "Toxic Items Properly Stored, Labeled, Used", "wt": 5},
    {"id": 42, "desc": "Premises Maintained Free of Litter, Unnecessary Articles, Cleaning Maintenance Equipment Properly Stored, Authorized Personnel", "wt": 1},
    {"id": 43, "desc": "Complete Separation for Living/Sleeping Quarters, Laundry", "wt": 1},
    {"id": 44, "desc": "Clean, Soiled Linen Properly Stored", "wt": 1},
]

def fix_food_establishment_item_ids():
    conn = get_db_connection()

    # Get template ID
    result = execute_query(conn, 'SELECT id FROM form_templates WHERE form_type = ? AND active = 1', ('Food Establishment',))
    template_row = result.fetchone()

    if not template_row:
        print('❌ Food Establishment template not found')
        conn.close()
        return

    template_id = template_row[0]

    # Get all items ordered by item_order
    result = execute_query(conn, '''
        SELECT id, description FROM form_items
        WHERE form_template_id = ?
        ORDER BY item_order, id
    ''', (template_id,))

    db_items = result.fetchall()

    if len(db_items) != len(FOOD_CHECKLIST_ITEMS):
        print(f'⚠️  Warning: Database has {len(db_items)} items, expected {len(FOOD_CHECKLIST_ITEMS)}')

    # Update each item with correct item_id
    updated_count = 0
    for i, db_item in enumerate(db_items):
        if i < len(FOOD_CHECKLIST_ITEMS):
            item_id = FOOD_CHECKLIST_ITEMS[i]['id']
            execute_query(conn, 'UPDATE form_items SET item_id = ? WHERE id = ?', (item_id, db_item[0]))
            updated_count += 1
            print(f'✓ Item {item_id}: {db_item[1][:60]}...')

    conn.commit()
    conn.close()

    print(f'\n✅ Updated {updated_count} items with proper item_id values')

if __name__ == '__main__':
    fix_food_establishment_item_ids()