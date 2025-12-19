#!/usr/bin/env python3
"""
Script to sync meat processing checklist items to database.
This ensures item 45 and others have the correct critical/non-critical status.
"""

from database import get_db_connection, release_db_connection
from db_config import get_placeholder

# Meat Processing checklist with correct weights and critical status (50 items, 100 total weight)
MEAT_PROCESSING_CHECKLIST_ITEMS = [
    # PREMISES (01-04)
    {"id": "01", "desc": "Free of improperly stored equipment, litter, waste, refuse, and uncut weeds or grass", "wt": 1, "category": "PREMISES", "critical": False},
    {"id": "02", "desc": "Clean, accessible roads, yards, and parking", "wt": 1, "category": "PREMISES", "critical": False},
    {"id": "03", "desc": "Proper drainage", "wt": 1, "category": "PREMISES", "critical": False},
    {"id": "04", "desc": "Effective control of birds, stray animals, pests, & filth from entering the plant", "wt": 2, "category": "PREMISES", "critical": False},

    # ANTEMORTEM (05-10)
    {"id": "05", "desc": "Animals subject to antemortem inspection", "wt": 1, "category": "ANTEMORTEM", "critical": False},
    {"id": "06", "desc": "Slaughter animals free from infectious disease", "wt": 2, "category": "ANTEMORTEM", "critical": True},
    {"id": "07", "desc": "Source & origin of animal records in place", "wt": 2, "category": "ANTEMORTEM", "critical": True},
    {"id": "08", "desc": "Holding pen - clean, access to potable water", "wt": 1, "category": "ANTEMORTEM", "critical": False},
    {"id": "09", "desc": "Holding pen - rails strong state of good repair", "wt": 1, "category": "ANTEMORTEM", "critical": False},
    {"id": "10", "desc": "Holding pen - floor rugged, sloped for drainage", "wt": 1, "category": "ANTEMORTEM", "critical": False},

    # STUNNING AREA (11)
    {"id": "11", "desc": "Animal restrained adequately; proper stunning effected", "wt": 2, "category": "STUNNING AREA", "critical": False},

    # KILL FLOOR (12-17)
    {"id": "12", "desc": "Floor/walls/ceiling easy to clean, free from accumulation of fat, blood, faeces, odour; sloped to drain", "wt": 2, "category": "KILL FLOOR", "critical": False},
    {"id": "13", "desc": "Made of impervious, durable material & sanitary", "wt": 1, "category": "KILL FLOOR", "critical": False},
    {"id": "14", "desc": "Handwashing stations, foot operated, adequate number", "wt": 3, "category": "KILL FLOOR", "critical": True},
    {"id": "15", "desc": "Edible product containers made of stainless steel", "wt": 1, "category": "KILL FLOOR", "critical": False},
    {"id": "16", "desc": "Adequate space provided for activities such as skinning, evisceration, carcass splitting so as to avoid cross contamination", "wt": 3, "category": "KILL FLOOR", "critical": True},
    {"id": "17", "desc": "Area free of sites that promote microbial multiplication", "wt": 2, "category": "KILL FLOOR", "critical": True},

    # LIGHTING (18-19)
    {"id": "18", "desc": "Lighting permits effective dressing of carcass and performing inspection", "wt": 1, "category": "LIGHTING", "critical": False},
    {"id": "19", "desc": "Light shielded to prevent contamination", "wt": 1, "category": "LIGHTING", "critical": False},

    # STORAGE OF RAW MATERIALS (20-21)
    {"id": "20", "desc": "Room/area used for storing raw materials, maintained in a clean & sanitary manner", "wt": 1, "category": "STORAGE OF RAW MATERIALS", "critical": False},
    {"id": "21", "desc": "Items in storage properly labeled and packed", "wt": 2, "category": "STORAGE OF RAW MATERIALS", "critical": False},

    # EQUIPMENT (22-23)
    {"id": "22", "desc": "Viscera table, skinning cradle, hooks, saw, knives, rails, slicers, tenderizers, etc. in good repair; made from cleanable & non-corrosive material; no excess accumulation of blood, meat, fat, faeces, & odour", "wt": 3, "category": "EQUIPMENT", "critical": True},
    {"id": "23", "desc": "Properly maintained, cleaned, & sanitized after each use with approved chemicals and sanitizing agents; procedure and frequency of use written pre-operational and post-operational activity; located to prevent contamination and adequately spaced for operation, inspection, & maintenance", "wt": 3, "category": "EQUIPMENT", "critical": True},

    # CHILL ROOM (24-27)
    {"id": "24", "desc": "Chill room maintained at required temperature (4°C)", "wt": 3, "category": "CHILL ROOM", "critical": True},
    {"id": "25", "desc": "Carcass stored to facilitate air flow", "wt": 2, "category": "CHILL ROOM", "critical": False},
    {"id": "26", "desc": "Absence of condensation, mold, etc. and properly maintained and operated", "wt": 2, "category": "CHILL ROOM", "critical": False},
    {"id": "27", "desc": "Chill room fitted with functional thermometer", "wt": 1, "category": "CHILL ROOM", "critical": False},

    # FREEZER ROOM (28-29)
    {"id": "28", "desc": "Meat held at -18°C; functional thermometers installed and displayed", "wt": 3, "category": "FREEZER ROOM", "critical": True},
    {"id": "29", "desc": "Meat products stored on pallets under proper maintenance, operation, & packaging", "wt": 3, "category": "FREEZER ROOM", "critical": True},

    # PEST CONTROL (30)
    {"id": "30", "desc": "No evidence of vermin/pests; effective pest control program in place", "wt": 3, "category": "PEST CONTROL", "critical": True},

    # PERSONNEL (31-35)
    {"id": "31", "desc": "All staff trained in hygiene with valid food handler's permit", "wt": 2, "category": "PERSONNEL", "critical": True},
    {"id": "32", "desc": "Protective & sanitary clothing used where required and otherwise appropriately attired", "wt": 1, "category": "PERSONNEL", "critical": False},
    {"id": "33", "desc": "Staff take necessary precaution to prevent contamination of meat", "wt": 2, "category": "PERSONNEL", "critical": True},
    {"id": "34", "desc": "Valid butcher's license", "wt": 2, "category": "PERSONNEL", "critical": True},
    {"id": "35", "desc": "Habits, i.e. smoking, spitting not observed; no uncovered cuts or sores; no evidence of communicable disease or injuries", "wt": 2, "category": "PERSONNEL", "critical": False},

    # WASTE (36-38)
    {"id": "36", "desc": "Drains clear, equipped with traps & vents", "wt": 2, "category": "WASTE", "critical": False},
    {"id": "37", "desc": "Proper arrangement for wastewater disposal; waste containers clearly identified & emptied at frequent intervals and in a sanitary manner", "wt": 3, "category": "WASTE", "critical": True},
    {"id": "38", "desc": "Waste storage adequate, waste does not pose cross contamination risk", "wt": 3, "category": "WASTE", "critical": True},

    # VENTILATION (39-41)
    {"id": "39", "desc": "Lack of condensates, contaminants, or mold in processing areas", "wt": 1, "category": "VENTILATION", "critical": False},
    {"id": "40", "desc": "Absence of objectionable odours", "wt": 2, "category": "VENTILATION", "critical": False},
    {"id": "41", "desc": "Air filters/dust collectors, checked, cleaned/replaced regularly", "wt": 2, "category": "VENTILATION", "critical": False},

    # SANITARY FACILITIES (42-44)
    {"id": "42", "desc": "Adequate handwashing stations properly placed with directing signs and foot/knee operated taps", "wt": 2, "category": "SANITARY FACILITIES", "critical": True},
    {"id": "43", "desc": "Toilets do not open directly into processing area & adequately operated & maintained", "wt": 1, "category": "SANITARY FACILITIES", "critical": False},
    {"id": "44", "desc": "Adequate soap, sanitizer & sanitary drying equipment or paper towels; availability of potable water", "wt": 2, "category": "SANITARY FACILITIES", "critical": True},

    # WATER, ICE (45-46)
    {"id": "45", "desc": "Ice in adequate quantity & generated from potable water", "wt": 2, "category": "WATER, ICE", "critical": False},
    {"id": "46", "desc": "Record of water treatment maintained; adequate quantity/pressure for all operations", "wt": 3, "category": "WATER, ICE", "critical": True},

    # TRANSPORTATION (47-48)
    {"id": "47", "desc": "Constructed and operated to protect meat and meat products from contamination and deterioration", "wt": 3, "category": "TRANSPORTATION", "critical": True},
    {"id": "48", "desc": "Capable of maintaining 4°C for chilled products; capable of maintaining -18°C for frozen products", "wt": 3, "category": "TRANSPORTATION", "critical": True},

    # STORAGE OF CHEMICALS (49)
    {"id": "49", "desc": "Insecticides, rodenticides, & cleaning agents properly labeled and stored to avoid cross contamination", "wt": 3, "category": "STORAGE OF CHEMICALS", "critical": True},

    # DOCUMENTATION (50)
    {"id": "50", "desc": "Processing plant quality assurance records, analytical results, cleaning and sanitation manuals, and sampling plans in place", "wt": 4, "category": "DOCUMENTATION", "critical": True},
]

def sync_meat_processing_checklist():
    """Sync meat processing checklist to database"""
    ph = get_placeholder()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get or create meat processing template
        cursor.execute(f"SELECT id FROM form_templates WHERE form_type = {ph} AND active = 1", ('Meat Processing',))
        template = cursor.fetchone()

        if not template:
            print("❌ No Meat Processing template found in database")
            print("   Creating new template...")
            cursor.execute(f"""
                INSERT INTO form_templates (form_type, template_name, active, created_date)
                VALUES ({ph}, {ph}, 1, CURRENT_TIMESTAMP)
            """, ('Meat Processing', 'Meat Processing Standard'))
            conn.commit()

            cursor.execute(f"SELECT id FROM form_templates WHERE form_type = {ph} AND active = 1", ('Meat Processing',))
            template = cursor.fetchone()

        template_id = template[0]
        print(f"✓ Using template ID: {template_id}")

        # Deactivate old numeric-ID items (from before string IDs were used)
        cursor.execute(f"""
            UPDATE form_items
            SET active = 0
            WHERE form_template_id = {ph}
            AND (item_id IS NULL OR item_id NOT LIKE '0%')
            AND item_id NOT IN ('45', '46', '47', '48', '49', '50')
        """, (template_id,))
        deactivated = cursor.rowcount
        if deactivated > 0:
            print(f"  Deactivated {deactivated} old numeric-ID items")

        # Update or insert each item
        updated = 0
        inserted = 0

        for item in MEAT_PROCESSING_CHECKLIST_ITEMS:
            item_id = item['id']  # Keep as string (e.g., '01', '45')

            # Check if item exists
            cursor.execute(f"""
                SELECT id, weight, is_critical FROM form_items
                WHERE form_template_id = {ph} AND item_id = {ph}
            """, (template_id, item_id))
            existing = cursor.fetchone()

            if existing:
                # Update existing item
                cursor.execute(f"""
                    UPDATE form_items
                    SET description = {ph}, weight = {ph}, is_critical = {ph}, category = {ph}, active = 1
                    WHERE form_template_id = {ph} AND item_id = {ph}
                """, (item['desc'], item['wt'], 1 if item['critical'] else 0, item.get('category', ''), template_id, item_id))
                updated += 1
                critical_status = "CRITICAL" if item['critical'] else "non-critical"
                print(f"  Updated item {item['id']}: {item['desc'][:50]}... (wt={item['wt']}, {critical_status})")
            else:
                # Insert new item - use item_id field for proper string IDs
                cursor.execute(f"""
                    INSERT INTO form_items
                    (form_template_id, item_order, item_id, category, description, weight, is_critical, active)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, 1)
                """, (template_id, int(item['id']), item['id'], item.get('category', ''), item['desc'], item['wt'], 1 if item['critical'] else 0))
                inserted += 1
                critical_status = "CRITICAL" if item['critical'] else "non-critical"
                print(f"  Inserted item {item['id']}: {item['desc'][:50]}... (wt={item['wt']}, {critical_status})")

        conn.commit()

        # Verify total
        cursor.execute(f"""
            SELECT SUM(weight), SUM(CASE WHEN is_critical = 1 THEN weight ELSE 0 END)
            FROM form_items
            WHERE form_template_id = {ph} AND active = 1
        """, (template_id,))
        result = cursor.fetchone()
        total = result[0] or 0
        critical_total = result[1] or 0

        print(f"\n✓ Sync complete!")
        print(f"  Updated: {updated} items")
        print(f"  Inserted: {inserted} items")
        print(f"  Total weight: {total}")
        print(f"  Critical weight: {critical_total}")

        if total != 100:
            print(f"  ⚠️  WARNING: Total weight is {total}, expected 100")
        else:
            print(f"  ✓ Total weight is correct (100)")

        # Verify item 45 is non-critical
        cursor.execute(f"""
            SELECT is_critical FROM form_items
            WHERE form_template_id = {ph} AND item_id = {ph}
        """, (template_id, '45'))
        item_45 = cursor.fetchone()
        if item_45:
            is_crit = item_45[0]
            if is_crit == 0:
                print(f"  ✓ Item 45 is correctly set as NON-CRITICAL (unshaded)")
            else:
                print(f"  ⚠️  WARNING: Item 45 is still marked as CRITICAL (shaded)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    print("Starting meat processing checklist sync...")
    print(f"Total items: {len(MEAT_PROCESSING_CHECKLIST_ITEMS)}")
    print(f"Expected total weight: {sum(item['wt'] for item in MEAT_PROCESSING_CHECKLIST_ITEMS)}")
    critical_count = sum(1 for item in MEAT_PROCESSING_CHECKLIST_ITEMS if item['critical'])
    critical_weight = sum(item['wt'] for item in MEAT_PROCESSING_CHECKLIST_ITEMS if item['critical'])
    print(f"Critical items: {critical_count} items, {critical_weight} weight")
    print(f"Item 45 critical status: {next((item['critical'] for item in MEAT_PROCESSING_CHECKLIST_ITEMS if item['id'] == '45'), 'NOT FOUND')}")
    print()
    sync_meat_processing_checklist()
