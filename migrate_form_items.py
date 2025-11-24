#!/usr/bin/env python3
"""
Migration Script: Populate Form Checklist Items
Adds all checklist items for all 9 form types to the database.
Run this once on Render to enable Form Builder for all forms.
"""

import sqlite3
import sys
from pathlib import Path

# Database connection
def get_db_connection():
    """Get database connection"""
    # Try common database paths
    db_paths = [
        'inspections.db',
        '/tmp/inspections.db',
        str(Path(__file__).parent / 'inspections.db')
    ]

    for db_path in db_paths:
        if Path(db_path).exists():
            print(f"✓ Found database at: {db_path}")
            return sqlite3.connect(db_path)

    # If no existing DB found, create at first path
    print(f"Creating new database at: {db_paths[0]}")
    return sqlite3.connect(db_paths[0])


# Form checklist items definitions
FORM_CHECKLISTS = {
    'Food Establishment': [
        {"id": "01", "category": "Food", "desc": "Food from approved source, sound condition, no spoilage", "wt": 5, "critical": 1},
        {"id": "02", "category": "Food", "desc": "Original container, properly labelled", "wt": 1, "critical": 0},
        {"id": "03", "category": "Food Protection", "desc": "Food protected from contamination during storage, preparation, display, service, and transport", "wt": 5, "critical": 1},
        {"id": "04", "category": "Food Protection", "desc": "Food contact surfaces of equipment and utensils clean, sanitized", "wt": 2, "critical": 0},
        {"id": "05", "category": "Food Protection", "desc": "Toxic materials properly stored, labeled, and used", "wt": 2, "critical": 0},
        {"id": "06", "category": "Personnel", "desc": "No person working with symptoms of disease", "wt": 5, "critical": 1},
        {"id": "07", "category": "Personnel", "desc": "Hands washed and clean, good hygiene practices", "wt": 5, "critical": 1},
        {"id": "08", "category": "Personnel", "desc": "Clean outer garments, hair restraint", "wt": 1, "critical": 0},
        {"id": "09", "category": "Food Equipment and Utensils", "desc": "Food contact surfaces designed, constructed, maintained, installed, located", "wt": 2, "critical": 0},
        {"id": "10", "category": "Food Equipment and Utensils", "desc": "Non-food contact surfaces designed, constructed, maintained, installed, located", "wt": 1, "critical": 0},
        {"id": "11", "category": "Food Equipment and Utensils", "desc": "Dishwashing facilities properly designed, maintained, accessible", "wt": 2, "critical": 0},
        {"id": "12", "category": "Food Equipment and Utensils", "desc": "Accurate thermometers, chemical test kits provided, accessible", "wt": 1, "critical": 0},
        {"id": "13", "category": "Food Equipment and Utensils", "desc": "Adequate facilities for storage and handling of equipment and utensils", "wt": 1, "critical": 0},
        {"id": "14", "category": "Single Service", "desc": "Single service articles: stored, handled; not reused", "wt": 1, "critical": 0},
        {"id": "15", "category": "Water Supply", "desc": "Water source approved, adequate, hot and cold", "wt": 4, "critical": 1},
        {"id": "16", "category": "Sewage", "desc": "Sewage and waste water disposal approved", "wt": 4, "critical": 1},
        {"id": "17", "category": "Plumbing", "desc": "Installed, maintained; cross connection; backflow; back siphonage", "wt": 2, "critical": 0},
        {"id": "18", "category": "Toilet and Handwashing", "desc": "Toilets, enclosed, adequate, accessible, designed, installed", "wt": 2, "critical": 0},
        {"id": "19", "category": "Toilet and Handwashing", "desc": "Handwash facilities adequate, accessible, designed, installed, maintained, supplied", "wt": 4, "critical": 1},
        {"id": "20", "category": "Garbage and Refuse", "desc": "Containers or receptacles covered, adequate, insect/rodent proof, frequency of disposal", "wt": 2, "critical": 0},
        {"id": "21", "category": "Garbage and Refuse", "desc": "Storage area and enclosure properly constructed, clean, and pest controlled", "wt": 2, "critical": 0},
        {"id": "22", "category": "Garbage and Refuse", "desc": "Disposal method approved", "wt": 1, "critical": 0},
        {"id": "23", "category": "Vermin Control", "desc": "Presence of insects/rodents; outer openings protected; no birds, turtles, other animals", "wt": 4, "critical": 1},
        {"id": "24", "category": "Floors", "desc": "Constructed, drained, clean, good repair, covering, installation, dustless methods", "wt": 2, "critical": 0},
        {"id": "25", "category": "Walls and Ceilings", "desc": "Walls, ceiling, attached equipment constructed, good repair, clean, surfaces, dustless methods", "wt": 2, "critical": 0},
        {"id": "26", "category": "Lighting", "desc": "Lighting provided as required, fixtures shielded", "wt": 1, "critical": 0},
        {"id": "27", "category": "Ventilation", "desc": "Rooms and equipment - vented as required", "wt": 1, "critical": 0},
        {"id": "28", "category": "Dressing Rooms", "desc": "Rooms clean, located, lockers provided, facilities", "wt": 1, "critical": 0},
        {"id": "29", "category": "Premises", "desc": "Maintained free of litter, unnecessary articles, cleaning/maintenance equipment properly stored, no animals", "wt": 1, "critical": 0},
        {"id": "30", "category": "Storage", "desc": "Dry storage area clean, dry, free of rodents and insects, shelving; temperature; no toxic storage", "wt": 2, "critical": 0},
        {"id": "31", "category": "Compliance", "desc": "Compliance with plans, licence conditions, NRCA requirements", "wt": 2, "critical": 0},
        {"id": "32", "category": "Other", "desc": "Animals properly slaughtered; no carcasses of animals that died otherwise than by slaughter", "wt": 4, "critical": 1},
        {"id": "33", "category": "Other", "desc": "Other violations as noted on violation report", "wt": 2, "critical": 0},
        {"id": "34", "category": "Food", "desc": "Potentially hazardous food meets temperature requirements during storage, preparation, display, service and transport", "wt": 5, "critical": 1},
        {"id": "35", "category": "Food Protection", "desc": "Thermometers provided and conspicuously placed in refrigerated units and hot holding units", "wt": 1, "critical": 0},
        {"id": "36", "category": "Personnel", "desc": "Unnecessary persons allowed in food preparation, storage, equipment washing areas", "wt": 1, "critical": 0},
        {"id": "37", "category": "Personnel", "desc": "Food handlers have food handlers permits", "wt": 2, "critical": 0},
        {"id": "38", "category": "Food Equipment and Utensils", "desc": "Cutting boards, blocks in good repair", "wt": 1, "critical": 0},
        {"id": "39", "category": "Food Equipment and Utensils", "desc": "Manual dishwashing - wash, rinse, sanitize, rinse procedures", "wt": 2, "critical": 0},
        {"id": "40", "category": "Food Equipment and Utensils", "desc": "Wiping cloths clean, used properly", "wt": 1, "critical": 0},
        {"id": "41", "category": "Toilet and Handwashing", "desc": "Toilet doors self-closing, toilet tissue provided, waste receptacles covered", "wt": 1, "critical": 0},
        {"id": "42", "category": "Garbage and Refuse", "desc": "Covered containers or plastic bags used for storage inside establishment", "wt": 1, "critical": 0},
        {"id": "43", "category": "Premises", "desc": "Unnecessary use of poisonous materials for cleaning, maintenance or pest control", "wt": 2, "critical": 0},
        {"id": "44", "category": "Other", "desc": "Licence not displayed", "wt": 1, "critical": 0},
    ],

    'Barbershop': [
        {"id": "01", "category": "Building", "desc": "Location: shop isolated from domestic premises", "wt": 2, "critical": 0},
        {"id": "02", "category": "Building", "desc": "Floors: clean, smooth, easily cleanable surfaces; not cracked/broken", "wt": 2, "critical": 0},
        {"id": "03", "category": "Building", "desc": "Walls: clean, smooth, easily cleanable surfaces", "wt": 2, "critical": 0},
        {"id": "04", "category": "Building", "desc": "Ceilings: clean, good repair", "wt": 2, "critical": 0},
        {"id": "05", "category": "Building", "desc": "Lighting and ventilation adequate", "wt": 2, "critical": 0},
        {"id": "06", "category": "Fixtures, Equipment & Supplies", "desc": "Barber chairs: cleanable, good condition", "wt": 2, "critical": 0},
        {"id": "07", "category": "Fixtures, Equipment & Supplies", "desc": "Cabinets: clean, good condition, properly used for storage", "wt": 2, "critical": 0},
        {"id": "08", "category": "Fixtures, Equipment & Supplies", "desc": "Work surfaces: clean, in good condition", "wt": 2, "critical": 0},
        {"id": "09", "category": "Fixtures, Equipment & Supplies", "desc": "Hand mirror: clean, unbroken", "wt": 1, "critical": 0},
        {"id": "10", "category": "Fixtures, Equipment & Supplies", "desc": "Headrests: clean, covered", "wt": 2, "critical": 0},
        {"id": "11", "category": "Fixtures, Equipment & Supplies", "desc": "Combs, brushes: clean, sanitized, properly stored", "wt": 3, "critical": 1},
        {"id": "12", "category": "Fixtures, Equipment & Supplies", "desc": "Adequate supply of clean towels", "wt": 2, "critical": 0},
        {"id": "13", "category": "Cleaning & Sanitization", "desc": "Clippers, scissors, razors: clean, sanitized after each use", "wt": 5, "critical": 1},
        {"id": "14", "category": "Cleaning & Sanitization", "desc": "Neck dusters: clean, sanitized", "wt": 2, "critical": 0},
        {"id": "15", "category": "Cleaning & Sanitization", "desc": "Capes/cloths: clean, laundered after each use", "wt": 3, "critical": 1},
        {"id": "16", "category": "Type of Sanitizing Agent", "desc": "70% alcohol used", "wt": 2, "critical": 0},
        {"id": "17", "category": "Type of Sanitizing Agent", "desc": "EPA registered hospital level disinfectant", "wt": 2, "critical": 0},
        {"id": "18", "category": "Personnel", "desc": "Staff health: no evidence of communicable disease", "wt": 3, "critical": 1},
        {"id": "19", "category": "Personnel", "desc": "Clean outer garments", "wt": 2, "critical": 0},
        {"id": "20", "category": "Personnel", "desc": "Hands washed before serving each customer", "wt": 3, "critical": 1},
        {"id": "21", "category": "First Aid Kit", "desc": "First aid supplies: styptic powder/pencil, bandages, antiseptic", "wt": 2, "critical": 0},
        {"id": "22", "category": "Water Supply", "desc": "Hot and cold potable water supply", "wt": 3, "critical": 1},
        {"id": "23", "category": "Sanitary Facilities", "desc": "Toilet: accessible, good condition, adequate supplies", "wt": 2, "critical": 0},
        {"id": "24", "category": "Sanitary Facilities", "desc": "Handwashing facilities: accessible, properly equipped", "wt": 3, "critical": 1},
        {"id": "25", "category": "Plumbing and Drainage", "desc": "All sinks with hot/cold water, proper drainage", "wt": 2, "critical": 0},
        {"id": "26", "category": "Plumbing and Drainage", "desc": "No cross-connections, backflow prevention", "wt": 2, "critical": 0},
        {"id": "27", "category": "Waste Disposal", "desc": "Covered waste receptacles provided", "wt": 2, "critical": 0},
        {"id": "28", "category": "Waste Disposal", "desc": "Hair properly swept and disposed", "wt": 2, "critical": 0},
        {"id": "29", "category": "Waste Disposal", "desc": "Sharps container for disposal of razor blades", "wt": 3, "critical": 1},
        {"id": "30", "category": "Pest Control", "desc": "No evidence of insects, rodents", "wt": 3, "critical": 1},
        {"id": "31", "category": "Pest Control", "desc": "Proper screening of openings", "wt": 2, "critical": 0},
        {"id": "32", "category": "Compound", "desc": "Yard/surrounding area clean, well maintained", "wt": 2, "critical": 0},
    ],

    'Burial': [
        {"id": "01", "category": "Burial Site", "desc": "Location appropriate", "wt": 2, "critical": 0},
        {"id": "02", "category": "Burial Site", "desc": "Plot demarcation/Registry of plots", "wt": 1, "critical": 0},
        {"id": "03", "category": "Burial Site", "desc": "Septic disposal for services", "wt": 1, "critical": 0},
        {"id": "04", "category": "Burial Site", "desc": "Parking area maintained", "wt": 1, "critical": 0},
        {"id": "05", "category": "Burial Site", "desc": "Waste disposal adequate", "wt": 1, "critical": 0},
        {"id": "06", "category": "Burial Site", "desc": "Burial depth adequate (6 feet)", "wt": 2, "critical": 1},
        {"id": "07", "category": "Burial Site", "desc": "Cemetery properly fenced", "wt": 1, "critical": 0},
        {"id": "08", "category": "Burial Site", "desc": "Grounds properly maintained", "wt": 1, "critical": 0},
        {"id": "09", "category": "Burial Site", "desc": "Water supply available", "wt": 1, "critical": 0},
        {"id": "10", "category": "Burial Site", "desc": "Sanitary facilities provided", "wt": 1, "critical": 0},
    ],

    'Institutional': [
        {"id": "1a", "category": "Documentation", "desc": "Action plan for foodborne illness occurrence", "wt": 1, "critical": 0},
        {"id": "1b", "category": "Documentation", "desc": "Food Handlers have valid food handlers permits", "wt": 1, "critical": 0},
        {"id": "1c", "category": "Documentation", "desc": "Relevant policy in place to restrict activities of sick employees", "wt": 1, "critical": 0},
        {"id": "1d", "category": "Documentation", "desc": "Establishments have a written policy for the proper disposal of waste", "wt": 1, "critical": 0},
        {"id": "1e", "category": "Documentation", "desc": "Cleaning schedule for equipment utensil etc available", "wt": 1, "critical": 0},
        {"id": "1f", "category": "Documentation", "desc": "Material safety data sheet available for record of hazardous chemicals used", "wt": 1, "critical": 0},
        {"id": "1g", "category": "Documentation", "desc": "Record of hazardous chemicals used", "wt": 1, "critical": 0},
        {"id": "1h", "category": "Documentation", "desc": "Food suppliers list available", "wt": 1, "critical": 0},
        {"id": "2a", "category": "Food Handlers", "desc": "Clean appropriate protective garments worn", "wt": 1, "critical": 1},
        {"id": "2b", "category": "Food Handlers", "desc": "Hands free of jewellery", "wt": 1, "critical": 0},
        {"id": "2c", "category": "Food Handlers", "desc": "Suitable hair restraints", "wt": 1, "critical": 0},
        {"id": "2d", "category": "Food Handlers", "desc": "Nails clean, short and unpolished", "wt": 1, "critical": 0},
        {"id": "2e", "category": "Food Handlers", "desc": "Hands washed as required", "wt": 1, "critical": 1},
        {"id": "3a", "category": "Food Storage", "desc": "Approved source", "wt": 2, "critical": 1},
        {"id": "3b", "category": "Food Storage", "desc": "Correct stocking procedures practiced", "wt": 1, "critical": 0},
        {"id": "3c", "category": "Food Storage", "desc": "Food stored on pallets or shelves off the floor", "wt": 1, "critical": 0},
        {"id": "3d", "category": "Food Storage", "desc": "No cats, rodents or other animals present in the store", "wt": 2, "critical": 1},
        {"id": "3e", "category": "Food Storage", "desc": "Products free of infestation", "wt": 1, "critical": 0},
        {"id": "3f", "category": "Food Storage", "desc": "No pesticides or other hazardous chemicals in food stores", "wt": 2, "critical": 1},
        {"id": "3g", "category": "Food Storage", "desc": "Satisfactory condition of refrigeration units", "wt": 1, "critical": 0},
        {"id": "3h", "category": "Food Storage", "desc": "Refrigerated foods < 4°C", "wt": 2, "critical": 1},
        {"id": "3i", "category": "Food Storage", "desc": "Frozen foods -18°C", "wt": 2, "critical": 1},
        {"id": "4a", "category": "Food Holding and Preparation", "desc": "Foods thawed according to recommended procedures", "wt": 2, "critical": 1},
        {"id": "4b", "category": "Food Holding and Preparation", "desc": "No evidence of cross-contamination during preparation", "wt": 2, "critical": 1},
        {"id": "4c", "category": "Food Holding and Preparation", "desc": "No evidence of cross-contamination during holding in refrigerators/coolers", "wt": 2, "critical": 1},
        {"id": "4d", "category": "Food Holding and Preparation", "desc": "Foods cooled according to recommended procedures", "wt": 2, "critical": 1},
        {"id": "4e", "category": "Food Holding and Preparation", "desc": "Manual dishwashing wash, rinse, sanitize, rinse technique", "wt": 2, "critical": 1},
        {"id": "4f", "category": "Food Holding and Preparation", "desc": "Food contact surfaces washed-rinsed-sanitized before & after each use", "wt": 1, "critical": 0},
        {"id": "4g", "category": "Food Holding and Preparation", "desc": "Wiping cloths handled properly (sanitizing solution used)", "wt": 1, "critical": 0},
        {"id": "5a", "category": "Post preparation", "desc": "Food protected during transportation", "wt": 2, "critical": 1},
        {"id": "5b", "category": "Post preparation", "desc": "Dishes identified and labelled", "wt": 1, "critical": 0},
        {"id": "5c", "category": "Post preparation", "desc": "Food covered or protected from contamination", "wt": 2, "critical": 1},
    ],

    'Meat Processing': [
        {"id": "01", "category": "Premises", "desc": "Building walls, floor, ceiling maintained in proper condition", "wt": 2, "critical": 0},
        {"id": "02", "category": "Premises", "desc": "General housekeeping and maintenance satisfactory", "wt": 1, "critical": 0},
        {"id": "03", "category": "Premises", "desc": "Building designed to prevent entrance of insects, rodents", "wt": 2, "critical": 0},
        {"id": "04", "category": "Premises", "desc": "Building allows adequate space for operations", "wt": 1, "critical": 0},
        {"id": "05", "category": "Antemortem", "desc": "Animals subject to antemortem inspection", "wt": 1, "critical": 0},
        {"id": "06", "category": "Antemortem", "desc": "Slaughter free from infectious disease", "wt": 2, "critical": 1},
        {"id": "07", "category": "Antemortem", "desc": "Source & origin of animal records in place", "wt": 2, "critical": 1},
        {"id": "08", "category": "Antemortem", "desc": "Holding pen - clean, access to potable water", "wt": 1, "critical": 0},
        {"id": "09", "category": "Antemortem", "desc": "Holding pen - rails strong state of good repair", "wt": 1, "critical": 0},
        {"id": "10", "category": "Antemortem", "desc": "Holding pen - floor rugged, sloped for drainage", "wt": 1, "critical": 0},
        {"id": "11", "category": "Stunning", "desc": "Animal restrained adequately; proper stunning effected", "wt": 2, "critical": 0},
        {"id": "13", "category": "Kill Floor", "desc": "Floor/walls/ceiling easy to clean, free from accumulation of fat, blood, feaces, odour; sloped to drain", "wt": 2, "critical": 1},
        {"id": "14", "category": "Kill Floor", "desc": "Made of impervious, durable material & sanitary", "wt": 1, "critical": 0},
        {"id": "15", "category": "Kill Floor", "desc": "Handwashing stations; foot operated; adequate number", "wt": 3, "critical": 1},
        {"id": "16", "category": "Kill Floor", "desc": "Edible product containers made of stainless steel", "wt": 1, "critical": 0},
        {"id": "17", "category": "Kill Floor", "desc": "Adequate space provided for activities such as skinning, evisceration, carcass splitting; so as to avoid cross contamination", "wt": 3, "critical": 1},
        {"id": "18", "category": "Kill Floor", "desc": "Area free of slime that promote microbial multiplication", "wt": 2, "critical": 1},
        {"id": "19", "category": "Lighting", "desc": "Lighting permits effective dressing of carcass and performing inspection", "wt": 1, "critical": 0},
        {"id": "20", "category": "Lighting", "desc": "Light shielded to prevent contamination", "wt": 1, "critical": 0},
        {"id": "21", "category": "Storage of Raw Materials", "desc": "Room/area used for storing raw materials, maintained in a clean & sanitary manner", "wt": 1, "critical": 0},
        {"id": "22", "category": "Storage of Raw Materials", "desc": "Items in storage properly labeled and packed", "wt": 2, "critical": 0},
        {"id": "23", "category": "Equipment", "desc": "Equipment of sanitary design", "wt": 2, "critical": 0},
        {"id": "24", "category": "Equipment", "desc": "Equipment and utensils properly cleaned and sanitized", "wt": 2, "critical": 0},
        {"id": "25", "category": "Chill Room", "desc": "Chill maintained at 4 degree C or lower for 24 hours; thermometer provided for measurement", "wt": 3, "critical": 1},
        {"id": "26", "category": "Chill Room", "desc": "Carcass stored to facilitate air flow", "wt": 2, "critical": 0},
        {"id": "27", "category": "Chill Room", "desc": "Absence of condensation, mold, etc. and properly maintained and operated", "wt": 2, "critical": 0},
        {"id": "28", "category": "Chill Room", "desc": "Chill room fitted with functional thermometer", "wt": 1, "critical": 0},
        {"id": "29", "category": "Freezer Room", "desc": "Meat held at -18°C; functional thermometers installed and displayed", "wt": 3, "critical": 1},
        {"id": "30", "category": "Freezer Room", "desc": "Meat products stored on pallets under proper maintenance, operation, & packaging", "wt": 3, "critical": 1},
        {"id": "31", "category": "Pest Control", "desc": "No evidence of vermin/pests; effective pest control program in place", "wt": 3, "critical": 0},
        {"id": "32", "category": "Personnel", "desc": "All staff trained in hygiene with valid food handlers permit", "wt": 2, "critical": 1},
        {"id": "33", "category": "Personnel", "desc": "Protective & sanitary clothing used where required and otherwise appropriately attired", "wt": 1, "critical": 0},
        {"id": "34", "category": "Personnel", "desc": "Staff take necessary precaution to prevent contamination of meat", "wt": 1, "critical": 0},
        {"id": "35", "category": "Personnel", "desc": "Valid butcher's license", "wt": 1, "critical": 0},
        {"id": "36", "category": "Personnel", "desc": "Habits, i.e. smoking, spitting not observed; no uncovered cuts or sores; no evidence of communicable disease or injuries", "wt": 2, "critical": 0},
        {"id": "37", "category": "Waste", "desc": "Drains clear, equipped with traps & vents", "wt": 2, "critical": 0},
        {"id": "38", "category": "Waste", "desc": "Proper arrangement for wastewater disposal; waste containers clearly identified & emptied at frequent intervals; and in a sanitary manner", "wt": 3, "critical": 0},
        {"id": "39", "category": "Waste", "desc": "Waste storage adequate; waste does not pose cross contamination risk", "wt": 3, "critical": 0},
        {"id": "40", "category": "Ventilation", "desc": "Lack of condensates, contaminants, or mold in processing areas", "wt": 1, "critical": 0},
        {"id": "41", "category": "Ventilation", "desc": "Absence of objectionable odours", "wt": 2, "critical": 0},
        {"id": "42", "category": "Ventilation", "desc": "Air filters/dust collectors, checked, cleaned/replaced regularly", "wt": 2, "critical": 0},
        {"id": "43", "category": "Sanitary Facilities", "desc": "Adequate handwashing facilities properly placed with directing signs and hot/cold running taps", "wt": 2, "critical": 0},
        {"id": "44", "category": "Sanitary Facilities", "desc": "Toilets do not open directly into processing area & adequately operated & maintained", "wt": 1, "critical": 0},
        {"id": "45", "category": "Sanitary Facilities", "desc": "Adequate soap, sanitizer & sanitary drying equipment or paper/towels; availability of potable water", "wt": 2, "critical": 1},
        {"id": "46", "category": "Water, Ice", "desc": "Ice in adequate quantity & generated from potable water", "wt": 2, "critical": 1},
        {"id": "47", "category": "Water, Ice", "desc": "Record of water treatment maintained; adequate quantity/pressure for all operations", "wt": 3, "critical": 1},
        {"id": "48", "category": "Transportation", "desc": "Constructed and operated to protect meat and meat products from contamination and deterioration", "wt": 3, "critical": 1},
        {"id": "49", "category": "Transportation", "desc": "Capable of maintaining 4° C for chilled products; capable of maintaining -18° C for frozen products", "wt": 3, "critical": 1},
        {"id": "50", "category": "Storage of Chemicals", "desc": "Insecticides, rodenticides, & cleaning agents properly labeled and stored to avoid cross contamination", "wt": 3, "critical": 1},
        {"id": "51", "category": "Documentation", "desc": "Processing plant quality assurance records; analytical results, cleaning and sanitation manuals; and sampling plans in place", "wt": 3, "critical": 0},
    ],

    'Residential': [
        {"id": "01", "category": "Water Supply", "desc": "Approved source, adequate pressure/volume", "wt": 3, "critical": 1},
        {"id": "02", "category": "Water Supply", "desc": "Potable quality maintained", "wt": 3, "critical": 1},
        {"id": "03", "category": "Water Supply", "desc": "Treatment adequate where needed", "wt": 2, "critical": 0},
        {"id": "04", "category": "Water Supply", "desc": "Proper storage/distribution", "wt": 2, "critical": 0},
        {"id": "05", "category": "Sewage Disposal", "desc": "Adequate system installed", "wt": 3, "critical": 1},
        {"id": "06", "category": "Sewage Disposal", "desc": "System functioning properly", "wt": 3, "critical": 1},
        {"id": "07", "category": "Sewage Disposal", "desc": "No overflow/surface contamination", "wt": 3, "critical": 1},
        {"id": "08", "category": "Sewage Disposal", "desc": "Proper maintenance evident", "wt": 2, "critical": 0},
        {"id": "09", "category": "Solid Waste", "desc": "Adequate refuse storage provided", "wt": 2, "critical": 0},
        {"id": "10", "category": "Solid Waste", "desc": "Regular collection maintained", "wt": 2, "critical": 0},
        {"id": "11", "category": "Solid Waste", "desc": "Storage area sanitary", "wt": 2, "critical": 0},
        {"id": "12", "category": "Vector Control", "desc": "No breeding sites on premises", "wt": 2, "critical": 0},
        {"id": "13", "category": "Vector Control", "desc": "Adequate screening of openings", "wt": 2, "critical": 0},
        {"id": "14", "category": "Vector Control", "desc": "No evidence of rodent/insect infestation", "wt": 3, "critical": 1},
        {"id": "15", "category": "Housing Structure", "desc": "Structurally sound", "wt": 2, "critical": 0},
        {"id": "16", "category": "Housing Structure", "desc": "Weathertight", "wt": 2, "critical": 0},
        {"id": "17", "category": "Housing Structure", "desc": "Adequate ventilation", "wt": 2, "critical": 0},
        {"id": "18", "category": "Housing Structure", "desc": "Adequate natural lighting", "wt": 1, "critical": 0},
        {"id": "19", "category": "Sanitation", "desc": "Interior clean and sanitary", "wt": 2, "critical": 0},
        {"id": "20", "category": "Sanitation", "desc": "Kitchen facilities adequate", "wt": 2, "critical": 0},
        {"id": "21", "category": "Sanitation", "desc": "Toilet facilities adequate", "wt": 3, "critical": 1},
        {"id": "22", "category": "Sanitation", "desc": "Bathing facilities adequate", "wt": 2, "critical": 0},
        {"id": "23", "category": "Hazards", "desc": "No safety hazards present", "wt": 3, "critical": 1},
        {"id": "24", "category": "Hazards", "desc": "Fire safety adequate", "wt": 2, "critical": 0},
        {"id": "25", "category": "Drainage", "desc": "Storm water drainage adequate", "wt": 2, "critical": 0},
        {"id": "26", "category": "Drainage", "desc": "No standing water/flooding", "wt": 2, "critical": 0},
    ],

    'Small Hotel': [
        {"id": "1a", "category": "Documentation", "desc": "Action plan for foodborne illness occurrence", "wt": 1, "critical": 0},
        {"id": "1b", "category": "Documentation", "desc": "Food Handlers have valid food handlers permits", "wt": 1, "critical": 1},
        {"id": "1c", "category": "Documentation", "desc": "Relevant policy in place to restrict activities of sick employees", "wt": 1, "critical": 0},
        {"id": "1d", "category": "Documentation", "desc": "Establishments have a written policy for the proper disposal of waste", "wt": 1, "critical": 0},
        {"id": "1e", "category": "Documentation", "desc": "Cleaning schedule for equipment utensil etc available", "wt": 1, "critical": 0},
        {"id": "1f", "category": "Documentation", "desc": "Material safety data sheet available for record of hazardous chemicals used", "wt": 1, "critical": 0},
        {"id": "1g", "category": "Documentation", "desc": "Record of hazardous chemicals used", "wt": 1, "critical": 0},
        {"id": "1h", "category": "Documentation", "desc": "Food suppliers list available", "wt": 1, "critical": 0},
        {"id": "2a", "category": "Food Handlers", "desc": "Clean appropriate protective garments worn", "wt": 1, "critical": 1},
        {"id": "2b", "category": "Food Handlers", "desc": "Hands free of jewellery", "wt": 1, "critical": 0},
        {"id": "2c", "category": "Food Handlers", "desc": "Suitable hair restraints", "wt": 1, "critical": 0},
        {"id": "2d", "category": "Food Handlers", "desc": "Nails clean, short and unpolished", "wt": 1, "critical": 0},
        {"id": "2e", "category": "Food Handlers", "desc": "Hands washed as required", "wt": 1, "critical": 1},
        {"id": "3a", "category": "Food Storage", "desc": "Approved source", "wt": 2, "critical": 1},
        {"id": "3b", "category": "Food Storage", "desc": "Correct stocking procedures practiced", "wt": 1, "critical": 0},
        {"id": "3c", "category": "Food Storage", "desc": "Food stored on pallets or shelves off the floor", "wt": 1, "critical": 0},
        {"id": "3d", "category": "Food Storage", "desc": "No cats, rodents or other animals present in the store", "wt": 2, "critical": 1},
        {"id": "3e", "category": "Food Storage", "desc": "Products free of infestation", "wt": 1, "critical": 0},
        {"id": "3f", "category": "Food Storage", "desc": "No pesticides or other hazardous chemicals in food stores", "wt": 2, "critical": 1},
        {"id": "3g", "category": "Food Storage", "desc": "Satisfactory condition of refrigeration units", "wt": 1, "critical": 0},
        {"id": "3h", "category": "Food Storage", "desc": "Refrigerated foods < 4°C", "wt": 2, "critical": 1},
        {"id": "3i", "category": "Food Storage", "desc": "Frozen foods -18°C", "wt": 2, "critical": 1},
        {"id": "4a", "category": "Food Holding and Preparation", "desc": "Foods thawed according to recommended procedures", "wt": 2, "critical": 1},
        {"id": "4b", "category": "Food Holding and Preparation", "desc": "No evidence of cross-contamination during preparation", "wt": 2, "critical": 1},
        {"id": "4c", "category": "Food Holding and Preparation", "desc": "No evidence of cross-contamination during holding in refrigerators/coolers", "wt": 2, "critical": 1},
        {"id": "4d", "category": "Food Holding and Preparation", "desc": "Foods cooled according to recommended procedures", "wt": 2, "critical": 1},
        {"id": "4e", "category": "Food Holding and Preparation", "desc": "Manual dishwashing wash, rinse, sanitize, rinse technique", "wt": 2, "critical": 1},
        {"id": "4f", "category": "Food Holding and Preparation", "desc": "Food contact surfaces washed-rinsed-sanitized before & after each use", "wt": 1, "critical": 0},
        {"id": "4g", "category": "Food Holding and Preparation", "desc": "Wiping cloths handled properly (sanitizing solution used)", "wt": 1, "critical": 0},
        {"id": "5a", "category": "Post preparation", "desc": "Food protected during transportation", "wt": 2, "critical": 1},
        {"id": "5b", "category": "Post preparation", "desc": "Dishes identified and labelled", "wt": 1, "critical": 0},
        {"id": "5c", "category": "Post preparation", "desc": "Food covered or protected from contamination", "wt": 2, "critical": 1},
        {"id": "5d", "category": "Post preparation", "desc": "Sufficient, appropriate utensils on service line", "wt": 2, "critical": 1},
        {"id": "5e", "category": "Post preparation", "desc": "Hot holding temperatures > 63°C", "wt": 2, "critical": 1},
        {"id": "5f", "category": "Post preparation", "desc": "Cold holding temperatures ≤ 5°C", "wt": 2, "critical": 1},
        {"id": "6a", "category": "Hand Washing Facilities", "desc": "Hand washing facility installed and maintained for every 40 square meters of floor space or in each principal food area", "wt": 2, "critical": 1},
        {"id": "6b", "category": "Hand Washing Facilities", "desc": "Equipped with hot and cold water, soap dispenser and hand drying facility", "wt": 1, "critical": 0},
        {"id": "7a", "category": "Building", "desc": "Provides adequate space for satisfactory performance of all operations", "wt": 1, "critical": 0},
        {"id": "7b", "category": "Building", "desc": "Food areas kept clean, free from vermin and unpleasant odours", "wt": 2, "critical": 1},
        {"id": "7c", "category": "Building", "desc": "Floor, walls and ceiling clean, in good repair", "wt": 1, "critical": 0},
        {"id": "7d", "category": "Building", "desc": "Mechanical ventilation operable where required", "wt": 1, "critical": 0},
        {"id": "7e", "category": "Building", "desc": "Lighting adequate for food preparation and cleaning", "wt": 1, "critical": 0},
        {"id": "7f", "category": "Building", "desc": "General housekeeping satisfactory", "wt": 1, "critical": 0},
        {"id": "7g", "category": "Building", "desc": "Animals, insect and pest excluded", "wt": 2, "critical": 0},
        {"id": "8a", "category": "Food contact surfaces", "desc": "Made from material which is non-absorbent and non-toxic", "wt": 1, "critical": 0},
        {"id": "8b", "category": "Food contact surfaces", "desc": "Smooth, cleanable, corrosion resistant", "wt": 1, "critical": 1},
        {"id": "8c", "category": "Food contact surfaces", "desc": "Proper storage and use of clean utensils", "wt": 1, "critical": 1},
        {"id": "9a", "category": "Food flow", "desc": "Employee traffic pattern avoids food cross-contamination", "wt": 2, "critical": 1},
        {"id": "9b", "category": "Food flow", "desc": "Product flow not at risk for cross-contamination", "wt": 2, "critical": 1},
        {"id": "9c", "category": "Food flow", "desc": "Living quarters, toilets, washrooms, locker separated from areas where food is handled", "wt": 2, "critical": 1},
        {"id": "10a", "category": "Equipment and utensils sanitization", "desc": "Mechanical dishwashing: Wash-rinse water clean", "wt": 1, "critical": 0},
        {"id": "10b", "category": "Equipment and utensils sanitization", "desc": "Proper water temperature", "wt": 2, "critical": 1},
        {"id": "10c", "category": "Equipment and utensils sanitization", "desc": "Proper timing of cycles", "wt": 1, "critical": 0},
        {"id": "10d", "category": "Equipment and utensils sanitization", "desc": "Sanitizer for low temperature", "wt": 1, "critical": 0},
        {"id": "10e", "category": "Equipment and utensils sanitization", "desc": "Proper handling of hazardous materials", "wt": 2, "critical": 1},
        {"id": "11a", "category": "Waste Management", "desc": "Appropriate design, convenient placement", "wt": 1, "critical": 1},
        {"id": "11b", "category": "Waste Management", "desc": "Kept covered when not in continuous use", "wt": 1, "critical": 0},
        {"id": "11c", "category": "Waste Management", "desc": "Emptied as often as necessary", "wt": 1, "critical": 1},
        {"id": "12a", "category": "Solid Waste Storage Area", "desc": "Insect and vermin-proof containers provided where required", "wt": 1, "critical": 1},
        {"id": "12b", "category": "Solid Waste Storage Area", "desc": "The area around each waste container kept clean", "wt": 1, "critical": 0},
        {"id": "12c", "category": "Solid Waste Storage Area", "desc": "Effluent from waste bins disposed of in a sanitary manner", "wt": 1, "critical": 0},
        {"id": "12d", "category": "Solid Waste Storage Area", "desc": "Frequency of garbage removal adequate", "wt": 1, "critical": 0},
        {"id": "13a", "category": "Disposal of solid waste", "desc": "Garbage, refuse properly disposed of, facilities maintained", "wt": 2, "critical": 1},
        {"id": "13b", "category": "Hazardous Materials", "desc": "Stored away from living quarters and food areas", "wt": 2, "critical": 1},
        {"id": "14a", "category": "Hazardous Materials", "desc": "Hazardous materials stored in properly labelled containers", "wt": 1, "critical": 0},
        {"id": "15a", "category": "Sanitary Facilities", "desc": "Approved Sewage Disposal System", "wt": 2, "critical": 1},
        {"id": "15b", "category": "Sanitary Facilities", "desc": "Sanitary maintenance of and provision of required supplies in staff public bathrooms", "wt": 2, "critical": 1},
        {"id": "16a", "category": "Pest Control", "desc": "Adequate provision against the entrance of insects, vermin, rodents, dust and fumes", "wt": 1, "critical": 0},
        {"id": "16b", "category": "Pest Control", "desc": "Suitable post control programme", "wt": 1, "critical": 0},
        {"id": "17a", "category": "Water Supply", "desc": "Approved source(s) sufficient pressure and capacity", "wt": 2, "critical": 1},
        {"id": "17b", "category": "Water Supply", "desc": "Water quality satisfactory", "wt": 1, "critical": 0},
        {"id": "18a", "category": "Ice", "desc": "Satisfactory ice storage conditions", "wt": 1, "critical": 0},
        {"id": "19a", "category": "Grey Water Facilities", "desc": "Traps and vent in good condition", "wt": 1, "critical": 1},
        {"id": "19b", "category": "Grey Water Facilities", "desc": "Floor drains clear and drain freely", "wt": 1, "critical": 1},
        {"id": "20a", "category": "Manholes", "desc": "Properly constructed with vents and traps where necessary", "wt": 1, "critical": 0},
    ],

    'Spirit Licence Premises': [
        {"id": "01", "category": "Building", "desc": "Location appropriate", "wt": 2, "critical": 0},
        {"id": "02", "category": "Building", "desc": "Building structurally sound", "wt": 3, "critical": 1},
        {"id": "03", "category": "Building", "desc": "Floor maintained - clean, good repair", "wt": 2, "critical": 0},
        {"id": "04", "category": "Building", "desc": "Walls maintained - clean, good repair", "wt": 2, "critical": 0},
        {"id": "05", "category": "Building", "desc": "Ceiling maintained - clean, good repair", "wt": 2, "critical": 0},
        {"id": "06", "category": "Building", "desc": "Adequate lighting", "wt": 2, "critical": 0},
        {"id": "07", "category": "Building", "desc": "Adequate ventilation", "wt": 2, "critical": 0},
        {"id": "08", "category": "Sanitary Facilities", "desc": "Toilet(s) available, adequate, clean", "wt": 3, "critical": 1},
        {"id": "09", "category": "Sanitary Facilities", "desc": "Handwashing facilities available", "wt": 3, "critical": 1},
        {"id": "10", "category": "Sanitary Facilities", "desc": "Adequate toilet supplies provided", "wt": 2, "critical": 0},
        {"id": "11", "category": "Water Supply", "desc": "Adequate potable water supply", "wt": 3, "critical": 1},
        {"id": "12", "category": "Sewage Disposal", "desc": "Approved sewage disposal system", "wt": 3, "critical": 1},
        {"id": "13", "category": "Solid Waste", "desc": "Adequate waste storage containers", "wt": 2, "critical": 0},
        {"id": "14", "category": "Solid Waste", "desc": "Waste properly stored and disposed", "wt": 2, "critical": 0},
        {"id": "15", "category": "Solid Waste", "desc": "Waste area maintained clean", "wt": 2, "critical": 0},
        {"id": "16", "category": "Vector Control", "desc": "No evidence of pest infestation", "wt": 3, "critical": 1},
        {"id": "17", "category": "Vector Control", "desc": "Adequate screening of openings", "wt": 2, "critical": 0},
        {"id": "18", "category": "Vector Control", "desc": "Pest control program in place", "wt": 2, "critical": 0},
        {"id": "19", "category": "Food Service", "desc": "If food served: proper food handling", "wt": 3, "critical": 1},
        {"id": "20", "category": "Food Service", "desc": "If food served: food handlers permits", "wt": 3, "critical": 1},
        {"id": "21", "category": "Food Service", "desc": "If food served: adequate storage", "wt": 2, "critical": 0},
        {"id": "22", "category": "Food Service", "desc": "If food served: proper refrigeration", "wt": 3, "critical": 1},
        {"id": "23", "category": "Bar Area", "desc": "Bar area clean and maintained", "wt": 2, "critical": 0},
        {"id": "24", "category": "Bar Area", "desc": "Bar equipment clean", "wt": 2, "critical": 0},
        {"id": "25", "category": "Bar Area", "desc": "Glassware properly washed", "wt": 2, "critical": 0},
        {"id": "26", "category": "Bar Area", "desc": "Ice handling proper", "wt": 2, "critical": 0},
        {"id": "27", "category": "Seating Area", "desc": "Seating area clean", "wt": 2, "critical": 0},
        {"id": "28", "category": "Seating Area", "desc": "Adequate seating provided", "wt": 1, "critical": 0},
        {"id": "29", "category": "Safety", "desc": "Fire safety equipment present", "wt": 3, "critical": 1},
        {"id": "30", "category": "Safety", "desc": "Emergency exits marked and accessible", "wt": 3, "critical": 1},
        {"id": "31", "category": "Safety", "desc": "No safety hazards observed", "wt": 3, "critical": 1},
        {"id": "32", "category": "Premises", "desc": "Compound/exterior maintained", "wt": 2, "critical": 0},
        {"id": "33", "category": "Premises", "desc": "Adequate parking area", "wt": 1, "critical": 0},
        {"id": "34", "category": "License", "desc": "Valid license displayed", "wt": 2, "critical": 0},
    ],

    'Swimming Pool': [
        {"id": "01", "category": "Pool Structure", "desc": "Pool structure sound, no cracks or leaks", "wt": 3, "critical": 1},
        {"id": "02", "category": "Pool Structure", "desc": "Pool deck adequate, non-slip, clean", "wt": 2, "critical": 0},
        {"id": "03", "category": "Pool Structure", "desc": "Adequate depth markings visible", "wt": 2, "critical": 0},
        {"id": "04", "category": "Pool Structure", "desc": "Safety equipment present and accessible", "wt": 3, "critical": 1},
        {"id": "05", "category": "Pool Structure", "desc": "Proper fencing/barriers in place", "wt": 3, "critical": 1},
        {"id": "06", "category": "Water Quality", "desc": "Water clear and free of debris", "wt": 2, "critical": 0},
        {"id": "07", "category": "Water Quality", "desc": "Free chlorine 1-3 ppm", "wt": 3, "critical": 1},
        {"id": "08", "category": "Water Quality", "desc": "pH 7.2-7.8", "wt": 3, "critical": 1},
        {"id": "09", "category": "Water Quality", "desc": "Total alkalinity 80-120 ppm", "wt": 2, "critical": 0},
        {"id": "10", "category": "Water Quality", "desc": "Cyanuric acid (if used) 30-50 ppm", "wt": 2, "critical": 0},
        {"id": "11", "category": "Water Quality", "desc": "Water temperature appropriate", "wt": 1, "critical": 0},
        {"id": "12", "category": "Filtration System", "desc": "Filter operational and adequate", "wt": 3, "critical": 1},
        {"id": "13", "category": "Filtration System", "desc": "Filter cleaned regularly", "wt": 2, "critical": 0},
        {"id": "14", "category": "Filtration System", "desc": "Pressure gauge functional", "wt": 1, "critical": 0},
        {"id": "15", "category": "Filtration System", "desc": "Turnover rate adequate (6 hours)", "wt": 2, "critical": 0},
        {"id": "16", "category": "Chemical Storage", "desc": "Chemicals properly stored and labeled", "wt": 3, "critical": 1},
        {"id": "17", "category": "Chemical Storage", "desc": "Storage area secure and ventilated", "wt": 2, "critical": 0},
        {"id": "18", "category": "Chemical Storage", "desc": "MSDS sheets available", "wt": 2, "critical": 0},
        {"id": "19", "category": "Testing", "desc": "Test kit available and adequate", "wt": 2, "critical": 0},
        {"id": "20", "category": "Testing", "desc": "Testing records maintained", "wt": 2, "critical": 0},
        {"id": "21", "category": "Testing", "desc": "Testing frequency adequate (min 2x daily)", "wt": 3, "critical": 1},
        {"id": "22", "category": "Sanitary Facilities", "desc": "Toilets adequate, clean, accessible", "wt": 3, "critical": 1},
        {"id": "23", "category": "Sanitary Facilities", "desc": "Showers provided and functional", "wt": 2, "critical": 0},
        {"id": "24", "category": "Sanitary Facilities", "desc": "Changing rooms adequate and clean", "wt": 2, "critical": 0},
        {"id": "25", "category": "Sanitary Facilities", "desc": "Handwashing facilities provided", "wt": 2, "critical": 0},
        {"id": "26", "category": "Sanitary Facilities", "desc": "Adequate supplies (soap, paper)", "wt": 2, "critical": 0},
        {"id": "27", "category": "Drainage", "desc": "Pool drainage adequate", "wt": 2, "critical": 0},
        {"id": "28", "category": "Drainage", "desc": "Deck drainage adequate", "wt": 2, "critical": 0},
        {"id": "29", "category": "Drainage", "desc": "No standing water on deck", "wt": 2, "critical": 0},
        {"id": "30", "category": "Waste Management", "desc": "Adequate waste containers provided", "wt": 2, "critical": 0},
        {"id": "31", "category": "Waste Management", "desc": "Waste area maintained clean", "wt": 2, "critical": 0},
        {"id": "32", "category": "Safety", "desc": "Lifeguard on duty (if required)", "wt": 3, "critical": 1},
        {"id": "33", "category": "Safety", "desc": "First aid kit available", "wt": 3, "critical": 1},
        {"id": "34", "category": "Safety", "desc": "Emergency procedures posted", "wt": 2, "critical": 0},
        {"id": "35", "category": "Safety", "desc": "Safety rules posted and visible", "wt": 2, "critical": 0},
        {"id": "36", "category": "Safety", "desc": "No diving in shallow areas marked", "wt": 2, "critical": 0},
        {"id": "37", "category": "Maintenance", "desc": "Regular maintenance schedule followed", "wt": 2, "critical": 0},
        {"id": "38", "category": "Maintenance", "desc": "Equipment in good working order", "wt": 2, "critical": 0},
        {"id": "39", "category": "Maintenance", "desc": "Pool surfaces smooth, no sharp edges", "wt": 2, "critical": 0},
        {"id": "40", "category": "Documentation", "desc": "Operator license/training current", "wt": 2, "critical": 0},
        {"id": "41", "category": "Documentation", "desc": "Pool registration current", "wt": 2, "critical": 0},
    ],
}


def migrate_form_items():
    """Main migration function"""
    print("=" * 70)
    print("🚀 FORM ITEMS MIGRATION SCRIPT")
    print("=" * 70)
    print()

    conn = get_db_connection()
    c = conn.cursor()

    # Get all form templates
    c.execute('SELECT id, form_type, name FROM form_templates WHERE active = 1')
    templates = c.fetchall()

    if not templates:
        print("❌ No form templates found! Please ensure form_templates table is populated.")
        conn.close()
        return False

    print(f"✓ Found {len(templates)} form templates")
    print()

    total_added = 0
    total_skipped = 0

    for template in templates:
        template_id, form_type, form_name = template

        # Check if items already exist
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        existing_count = c.fetchone()[0]

        if form_type not in FORM_CHECKLISTS:
            print(f"⚠️  {form_name} ({form_type}): No checklist defined - skipping")
            continue

        checklist = FORM_CHECKLISTS[form_type]

        if existing_count > 0:
            print(f"⏭️  {form_name}: {existing_count} items already exist - skipping")
            total_skipped += existing_count
            continue

        # Insert items
        items_added = 0
        for idx, item in enumerate(checklist, 1):
            try:
                c.execute('''INSERT INTO form_items
                            (form_template_id, item_order, category, description, weight, is_critical, item_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (template_id, idx, item['category'], item['desc'],
                          item['wt'], item.get('critical', 0), item['id']))
                items_added += 1
            except Exception as e:
                print(f"   ⚠️  Error adding item {item['id']}: {e}")

        conn.commit()
        total_added += items_added
        print(f"✅ {form_name}: Added {items_added} items")

    conn.close()

    print()
    print("=" * 70)
    print(f"✅ MIGRATION COMPLETE!")
    print(f"   • Items added: {total_added}")
    print(f"   • Items skipped (already exist): {total_skipped}")
    print("=" * 70)
    print()
    print("📋 All form types now have checklist items in the database")
    print("🔧 Admin can now edit ALL forms in Form Builder")
    print("👁️  Inspectors will see correct critical shading for all forms")
    print()

    return True


if __name__ == '__main__':
    print()
    print("This script will populate checklist items for all form types.")
    print("It will NOT duplicate items if they already exist.")
    print()

    response = input("Continue? (yes/no): ").strip().lower()
    if response == 'yes':
        success = migrate_form_items()
        sys.exit(0 if success else 1)
    else:
        print("Migration cancelled.")
        sys.exit(0)
