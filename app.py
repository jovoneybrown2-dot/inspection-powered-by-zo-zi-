# Standard Library Imports
import os
import sqlite3
import io
from datetime import datetime

# Flask Imports
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, Response


#ReportLab Imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

# Database Imports
from database import (
    get_residential_inspection_details,
    get_residential_inspections,
    init_db,
    save_residential_inspection,
    save_inspection,
    save_burial_inspection,
    get_inspections,
    get_inspections_by_inspector,
    get_burial_inspections,
    get_inspection_details,
    get_burial_inspection_details,
    save_meat_processing_inspection,
    get_meat_processing_inspections,
    get_meat_processing_inspection_details
)

# Database Config Import
from db_config import get_db_connection

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)

# Auto-initialize database if it doesn't exist (for Gunicorn/Render deployment)
if not os.path.exists('inspections.db'):
    print("Database not found. Initializing...")
    init_db()
    print("Database initialized successfully!")
else:
    # Run migrations for existing databases
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Migrate inspections table
        c.execute("PRAGMA table_info(inspections)")
        columns = [column[1] for column in c.fetchall()]
        if 'photo_data' not in columns:
            print("Adding photo_data column to inspections table...")
            c.execute("ALTER TABLE inspections ADD COLUMN photo_data TEXT")
            conn.commit()
            print("Migration completed: photo_data column added to inspections")

        # Migrate burial_site_inspections table
        c.execute("PRAGMA table_info(burial_site_inspections)")
        columns = [column[1] for column in c.fetchall()]
        if 'photo_data' not in columns:
            print("Adding photo_data column to burial_site_inspections table...")
            c.execute("ALTER TABLE burial_site_inspections ADD COLUMN photo_data TEXT")
            conn.commit()
            print("Migration completed: photo_data column added to burial_site_inspections")

        # Migrate residential_inspections table
        c.execute("PRAGMA table_info(residential_inspections)")
        columns = [column[1] for column in c.fetchall()]
        if 'photo_data' not in columns:
            print("Adding photo_data column to residential_inspections table...")
            c.execute("ALTER TABLE residential_inspections ADD COLUMN photo_data TEXT")
            conn.commit()
            print("Migration completed: photo_data column added to residential_inspections")

        # Migrate meat_processing_inspections table
        c.execute("PRAGMA table_info(meat_processing_inspections)")
        columns = [column[1] for column in c.fetchall()]
        if 'photo_data' not in columns:
            print("Adding photo_data column to meat_processing_inspections table...")
            c.execute("ALTER TABLE meat_processing_inspections ADD COLUMN photo_data TEXT")
            conn.commit()
            print("Migration completed: photo_data column added to meat_processing_inspections")

        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

# Corrected Checklist for Food Establishment Inspection Form
# Complete 45-item structure matching the official form

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

    # PERSONNEL (29-31) - REMOVED OLD ITEM 32, RENUMBERED EVERYTHING AFTER
    {"id": 29, "desc": "Personnel with Infections Restricted", "wt": 5},
    {"id": 30, "desc": "Hands Washed and Clean, Good Hygienic Practices", "wt": 5},
    {"id": 31, "desc": "Clean Clothes, Hair Restraints", "wt": 2},  # INCREASED FROM 1 TO 2

    # LIGHTING (32) - RENUMBERED FROM 33
    {"id": 32, "desc": "Lighting Provided as Required, Fixtures Shielded", "wt": 1},

    # VENTILATION (33) - RENUMBERED FROM 34
    {"id": 33, "desc": "Rooms and Equipment - Venting as Required", "wt": 1},

    # DRESSING ROOMS (34) - RENUMBERED FROM 35
    {"id": 34, "desc": "Rooms Clean, Lockers Provided, Facilities Clean", "wt": 1},

    # WATER (35) - RENUMBERED FROM 36
    {"id": 35, "desc": "Water Source Safe, Hot & Cold Under Pressure", "wt": 5},

    # SEWAGE (36) - RENUMBERED FROM 37
    {"id": 36, "desc": "Sewage and Waste Water Disposal", "wt": 4},

    # PLUMBING (37-38) - RENUMBERED FROM 38-39
    {"id": 37, "desc": "Installed, Maintained", "wt": 1},
    {"id": 38, "desc": "Cross Connection, Back Siphonage, Backflow", "wt": 5},

    # FLOORS, WALLS, & CEILINGS (39-40) - RENUMBERED FROM 40-41
    {"id": 39, "desc": "Floors: Constructed, Drained, Clean, Good Repair, Covering Installation, Dustless Cleaning Methods", "wt": 1},
    {"id": 40, "desc": "Walls, Ceiling, Attached Equipment: Constructed, Good Repair, Clean Surfaces, Dustless Cleaning Methods", "wt": 1},

    # OTHER OPERATIONS (41-44) - RENUMBERED FROM 42-45
    {"id": 41, "desc": "Toxic Items Properly Stored, Labeled, Used", "wt": 5},
    {"id": 42, "desc": "Premises Maintained Free of Litter, Unnecessary Articles, Cleaning Maintenance Equipment Properly Stored, Authorized Personnel", "wt": 1},
    {"id": 43, "desc": "Complete Separation for Living/Sleeping Quarters, Laundry", "wt": 1},
    {"id": 44, "desc": "Clean, Soiled Linen Properly Stored", "wt": 1},
]


RESIDENTIAL_CHECKLIST_ITEMS = [
    {"id": 1, "desc": "Sound and clean exterior of building", "wt": 3},
    {"id": 2, "desc": "Sound and clean interior of building", "wt": 3},
    {"id": 3, "desc": "Sound and clean floors", "wt": 2},
    {"id": 4, "desc": "Sound and clean walls", "wt": 2},
    {"id": 5, "desc": "Sound and clean ceiling", "wt": 2},
    {"id": 6, "desc": "Adequate ventilation in rooms", "wt": 3},
    {"id": 7, "desc": "Sufficient lighting", "wt": 2},
    {"id": 8, "desc": "Adequate accommodation", "wt": 4},
    {"id": 9, "desc": "Potability", "wt": 6},
    {"id": 10, "desc": "Accessibility", "wt": 4},
    {"id": 11, "desc": "Graded", "wt": 4},
    {"id": 12, "desc": "Unobstructed", "wt": 6},
    {"id": 13, "desc": "No active breeding", "wt": 5},
    {"id": 14, "desc": "No potential breeding source", "wt": 5},
    {"id": 15, "desc": "No active breeding", "wt": 5},
    {"id": 16, "desc": "No potential breeding source", "wt": 5},
    {"id": 17, "desc": "No active breeding", "wt": 3},
    {"id": 18, "desc": "No potential breeding source", "wt": 3},
    {"id": 19, "desc": "Clean", "wt": 4},
    {"id": 20, "desc": "Safe and sound", "wt": 5},
    {"id": 21, "desc": "Fly/rodentproof", "wt": 4},
    {"id": 22, "desc": "Adequate health and safety provisions", "wt": 4},
    {"id": 23, "desc": "Storage", "wt": 4},
    {"id": 24, "desc": "Disposal", "wt": 4},
    {"id": 25, "desc": "Proper lairage for animals", "wt": 4},
    {"id": 26, "desc": "Controlled vegetation", "wt": 4},
]

MEAT_PROCESSING_CHECKLIST_ITEMS = [
    {"id": 1, "desc": "Free of improperly stored equipment, litter, waste refuse, and unused weeds or grass", "wt": 1},
    {"id": 2, "desc": "Clean, accessible roads, yards, and parking", "wt": 1},
    {"id": 3, "desc": "Proper drainage", "wt": 1},
    {"id": 4, "desc": "Effective control of birds, stray animals, pests, & filth from entering the plant", "wt": 2},
    {"id": 5, "desc": "Animals subject to antemortem inspection", "wt": 1},
    {"id": 6, "desc": "Slaughter free from infectious disease", "wt": 2, "critical": True},
    {"id": 7, "desc": "Source & origin of animal records in place", "wt": 2, "critical": True},
    {"id": 8, "desc": "Holding pen - clean, access to potable water", "wt": 1},
    {"id": 9, "desc": "Holding pen - rails strong state of good repair", "wt": 1},
    {"id": 10, "desc": "Holding pen - floor rugged, sloped for drainage", "wt": 1},
    {"id": 11, "desc": "Animal restrained adequately; proper stunning effected", "wt": 2},
    {"id": 13, "desc": "Floor/walls/ceiling easy to clean, free from accumulation of fat, blood, feaces, odour; sloped to drain", "wt": 2, "critical": True},
    {"id": 14, "desc": "Made of impervious, durable material & sanitary", "wt": 1},
    {"id": 15, "desc": "Handwashing stations; foot operated; adequate number", "wt": 3, "critical": True},
    {"id": 16, "desc": "Edible product containers made of stainless steel", "wt": 1},
    {"id": 17, "desc": "Adequate space provided for activities such as skinning, evisceration, carcass splitting; so as to avoid cross contamination", "wt": 3, "critical": True},
    {"id": 18, "desc": "Area free of slime that promote microbial multiplication", "wt": 2, "critical": True},
    {"id": 19, "desc": "Lighting permits effective dressing of carcass and performing inspection", "wt": 1},
    {"id": 20, "desc": "Light shielded to prevent contamination", "wt": 1},
    {"id": 21, "desc": "Room/area used for storing raw materials, maintained in a clean & sanitary manner", "wt": 1},
    {"id": 22, "desc": "Items in storage properly labeled and packed", "wt": 2},
    {"id": 23, "desc": "Vicora table, skinning cradle, hooks, saw, knives, rails, slicers, tenderizers, etc. in good repair; made from cleanable & non-corrosive material; no excess accumulation of blood, meat, fat, feaces, & odour", "wt": 3, "critical": True},
    {"id": 24, "desc": "Properly maintained, cleaned, & sanitized after each use with approved chemicals or sanitizing agents; procedure and frequency of use written; pre-operational and post-operational activity located to prevent contamination and adequately spaced for operation, inspection, & maintenance", "wt": 3, "critical": True},
    {"id": 25, "desc": "Chill room maintained at required temperature (4° C)", "wt": 2, "critical": True},
    {"id": 26, "desc": "Carcass stored to facilitate air flow", "wt": 2},
    {"id": 27, "desc": "Absence of condensation, mold, etc. and properly maintained and operated", "wt": 2},
    {"id": 28, "desc": "Chill room fitted with functional thermometer", "wt": 1},
    {"id": 29, "desc": "Meat held at -18°C; functional thermometers installed and displayed", "wt": 3, "critical": True},
    {"id": 30, "desc": "Meat products stored on pallets under proper maintenance, operation, & packaging", "wt": 3, "critical": True},
    {"id": 31, "desc": "No evidence of vermin/pests; effective pest control program in place", "wt": 3},
    {"id": 32, "desc": "All staff trained in hygiene with valid food handlers permit", "wt": 2, "critical": True},
    {"id": 33, "desc": "Protective & sanitary clothing used where required and otherwise appropriately attired", "wt": 1},
    {"id": 34, "desc": "Staff take necessary precaution to prevent contamination of meat", "wt": 1},
    {"id": 35, "desc": "Valid butcher's license", "wt": 1},
    {"id": 36, "desc": "Habits, i.e. smoking, spitting not observed; no uncovered cuts or sores; no evidence of communicable disease or injuries", "wt": 2},
    {"id": 37, "desc": "Drains clear, equipped with traps & vents", "wt": 2},
    {"id": 38, "desc": "Proper arrangement for wastewater disposal; waste containers clearly identified & emptied at frequent intervals; and in a sanitary manner", "wt": 3},
    {"id": 39, "desc": "Waste storage adequate; waste does not pose cross contamination risk", "wt": 3},
    {"id": 40, "desc": "Lack of condensates, contaminants, or mold in processing areas", "wt": 1},
    {"id": 41, "desc": "Absence of objectionable odours", "wt": 2},
    {"id": 42, "desc": "Air filters/dust collectors, checked, cleaned/replaced regularly", "wt": 2},
    {"id": 43, "desc": "Adequate handwashing facilities properly placed with directing signs and hot/cold running taps", "wt": 2},
    {"id": 44, "desc": "Toilets do not open directly into processing area & adequately operated & maintained", "wt": 1},
    {"id": 45, "desc": "Adequate soap, sanitizer & sanitary drying equipment or paper/towels; availability of potable water", "wt": 2, "critical": True},
    {"id": 46, "desc": "Ice in adequate quantity & generated from potable water", "wt": 2, "critical": True},
    {"id": 47, "desc": "Record of water treatment maintained; adequate quantity/pressure for all operations", "wt": 3, "critical": True},
    {"id": 48, "desc": "Constructed and operated to protect meat and meat products from contamination and deterioration", "wt": 3, "critical": True},
    {"id": 49, "desc": "Capable of maintaining 4° C for chilled products; capable of maintaining -18° C for frozen products", "wt": 3, "critical": True},
    {"id": 50, "desc": "Insecticides, rodenticides, & cleaning agents properly labeled and stored to avoid cross contamination", "wt": 3, "critical": True},
    {"id": 51, "desc": "Processing plant quality assurance records; analytical results, cleaning and sanitation manuals; and sampling plans in place", "wt": 3},
]

SPIRIT_LICENCE_CHECKLIST_ITEMS = [
    {'id': 1, 'description': 'Sound, clean and in good repair', 'wt': 3},
    {'id': 2, 'description': 'No smoking sign displayed at entrance to premises', 'wt': 3},
    {'id': 3, 'description': 'Walls, clean and in good repair', 'wt': 3},
    {'id': 4, 'description': 'Floors', 'wt': 3},
    {'id': 5, 'description': 'Constructed of impervious, non-slip material', 'wt': 3},
    {'id': 6, 'description': 'Clean, drained and in good repair', 'wt': 3},
    {'id': 7, 'description': 'Service counter', 'wt': 3},
    {'id': 8, 'description': 'Constructed of impervious material', 'wt': 3},
    {'id': 9, 'description': 'Designed, clean and in good repair', 'wt': 3},
    {'id': 10, 'description': 'Lighting', 'wt': 3},
    {'id': 11, 'description': 'Lighting provided as required', 'wt': 3},
    {'id': 12, 'description': 'Washing and Sanitization Facilities', 'wt': 5},
    {'id': 13, 'description': 'Fitted with at least double compartment sink', 'wt': 5},
    {'id': 14, 'description': 'Soap and sanitizer provided', 'wt': 5},
    {'id': 15, 'description': 'Equipped handwashing facility provided', 'wt': 5},
    {'id': 16, 'description': 'Water Supply', 'wt': 5},
    {'id': 17, 'description': 'Potable', 'wt': 5},
    {'id': 18, 'description': 'Piped', 'wt': 5},
    {'id': 19, 'description': 'Storage Facilities', 'wt': 5},
    {'id': 20, 'description': 'Clean and adequate storage of glasses & utensils', 'wt': 5},
    {'id': 21, 'description': 'Free of insects and other vermins', 'wt': 5},
    {'id': 22, 'description': 'Being used for its intended purpose', 'wt': 5},
    {'id': 23, 'description': 'Sanitary Facilities', 'wt': 5},
    {'id': 24, 'description': 'Toilet facility provided', 'wt': 5},
    {'id': 25, 'description': 'Adequate, accessible with lavatory basin and soap', 'wt': 5},
    {'id': 26, 'description': 'Satisfactory', 'wt': 5},
    {'id': 27, 'description': 'Urinal(s) provided', 'wt': 3},
    {'id': 28, 'description': 'Satisfactory', 'wt': 3},
    {'id': 29, 'description': 'Solid Waste Management', 'wt': 4},
    {'id': 30, 'description': 'Covered, adequate, pest proof and clean receptacles', 'wt': 4},
    {'id': 31, 'description': 'Provision made for satisfactory disposal of waste', 'wt': 3},
    {'id': 32, 'description': 'Premises free of litter and unnecessary articles', 'wt': 2},
    {'id': 33, 'description': 'Pest Control', 'wt': 5},
    {'id': 34, 'description': 'Premises free of rodents, insects and vermins', 'wt': 5}
]

# Swimming Pool Checklist - CORRECTED WEIGHTS
SWIMMING_POOL_CHECKLIST_ITEMS = [
    {"id": "1A", "desc": "Written procedures for microbiological monitoring of pool water implemented", "wt": 5, "category": "Documentation"},
    {"id": "1B", "desc": "Microbiological results", "wt": 2.5, "category": "Documentation"},
    {"id": "1C", "desc": "Date of last testing within required frequency", "wt": 2.5, "category": "Documentation"},
    {"id": "1D", "desc": "Acceptable monitoring procedures", "wt": 5, "category": "Documentation"},
    {"id": "1E", "desc": "Daily log books and records up-to-date", "wt": 5, "category": "Documentation"},
    {"id": "1F", "desc": "Written emergency procedures established and implemented", "wt": 5, "category": "Documentation"},
    {"id": "1G", "desc": "Personal liability and accident insurance", "wt": 5, "category": "Documentation"},
    {"id": "1H", "desc": "Lifeguard/Lifesaver certification", "wt": 5, "category": "Documentation"},
    {"id": "2A", "desc": "Defects in pool construction", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2B", "desc": "Evidence of flaking paint and/or mould growth", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2C", "desc": "All surfaces of the deck and pool free from obstruction that can cause accident/injury", "wt": 5, "category": "Physical Condition"},
    {"id": "2D", "desc": "Exposed piping: - identified/colour coded", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2E", "desc": "In good repair", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2F", "desc": "Suction fittings/inlets: - in good repair", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2G", "desc": "At least two suction orifices equipped with anti-vortex plates", "wt": 5, "category": "Physical Condition"},
    {"id": "2H", "desc": "Perimeter drains free of debris", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2I", "desc": "Pool walls and floor clean", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2J", "desc": "Components of the re-circulating system maintained", "wt": 2.5, "category": "Physical Condition"},
    {"id": "3A", "desc": "Clarity", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3B", "desc": "Chlorine residual > 0.5 mg/l", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3C", "desc": "pH value within range of 7.5 and 7.8", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3D", "desc": "Well supplied and equipped", "wt": 2.5, "category": "Pool Chemistry"},
    {"id": "4A", "desc": "Pool chemicals - stored safely", "wt": 5, "category": "Pool Chemicals"},
    {"id": "4B", "desc": "Dispensed automatically or in a safe manner", "wt": 2.5, "category": "Pool Chemicals"},
    {"id": "5A", "desc": "Depth markings clearly visible", "wt": 5, "category": "Safety"},
    {"id": "5B", "desc": "Working emergency phone", "wt": 5, "category": "Safety"},
    {"id": "6A", "desc": "Reaching poles with hook", "wt": 2.5, "category": "Safety Aids"},
    {"id": "6B", "desc": "Two throwing aids", "wt": 2.5, "category": "Safety Aids"},
    {"id": "6C", "desc": "Spine board with cervical collar", "wt": 2.5, "category": "Safety Aids"},
    {"id": "6D", "desc": "Well equipped first aid kit", "wt": 2.5, "category": "Safety Aids"},
    {"id": "7A", "desc": "Caution notices: - pool depth indications", "wt": 1, "category": "Signs and Notices"},
    {"id": "7B", "desc": "Public health notices", "wt": 1, "category": "Signs and Notices"},
    {"id": "7C", "desc": "Emergency procedures", "wt": 1, "category": "Signs and Notices"},
    {"id": "7D", "desc": "Maximum bathing load", "wt": 1, "category": "Signs and Notices"},
    {"id": "7E", "desc": "Lifeguard on duty/bathe at your own risk signs", "wt": 1, "category": "Signs and Notices"},
    {"id": "8A", "desc": "Licensed Lifeguards always on duty during pool opening hours", "wt": 2.5, "category": "Lifeguards/Lifesavers"},
    {"id": "8B", "desc": "If N/A, trained lifesavers readily available", "wt": 5, "category": "Lifeguards/Lifesavers"},
    {"id": "8C", "desc": "Number of lifeguard/lifesavers", "wt": 2.5, "category": "Lifeguards/Lifesavers"},
    {"id": "9A", "desc": "Shower, toilet and dressing rooms: - clean and disinfected as required", "wt": 5, "category": "Sanitary Facilities"},
    {"id": "9B", "desc": "Vented", "wt": 2.5, "category": "Sanitary Facilities"},
    {"id": "9C", "desc": "Well supplied and equipped", "wt": 2.5, "category": "Sanitary Facilities"},
]

# Define checklist items (40 items, 28 critical)
SMALL_HOTELS_CHECKLIST_ITEMS = [
    # 1 - Documentation (8%)
    {"id": "1a", "description": "Action plan for foodborne illness occurrence", "critical": False},
    {"id": "1b", "description": "Food Handlers have valid food handlers permits", "critical": True},
    {"id": "1c", "description": "Relevant policy in place to restrict activities of sick employees", "critical": False},
    {"id": "1d", "description": "Establishments have a written policy for the proper disposal of waste", "critical": False},
    {"id": "1e", "description": "Cleaning schedule for equipment utensil etc available", "critical": False},
    {"id": "1f", "description": "Material safety data sheet available for record of hazardous chemicals used", "critical": False},
    {"id": "1g", "description": "Record of hazardous chemicals used", "critical": False},
    {"id": "1h", "description": "Food suppliers list available", "critical": False},

    # 2 - Food Handlers (5%)
    {"id": "2a", "description": "Clean appropriate protective garments", "critical": True},
    {"id": "2b", "description": "Hands free of jewellery", "critical": False},
    {"id": "2c", "description": "Suitable hair restraints", "critical": False},
    {"id": "2d", "description": "Nails clean, short and unpolished", "critical": False},
    {"id": "2e", "description": "Hands washed as required", "critical": True},

    # 3 - Food Storage (13%)
    {"id": "3a", "description": "Approved source", "critical": True},
    {"id": "3b", "description": "Correct stocking procedures practiced", "critical": False},
    {"id": "3c", "description": "Food stored on pallets or shelves off the floor", "critical": False},
    {"id": "3d", "description": "No cats, rodents or other animals present in the store", "critical": True},
    {"id": "3e", "description": "Products free of infestation", "critical": False},
    {"id": "3f", "description": "No pesticides or other hazardous chemicals in food stores", "critical": True},
    {"id": "3g", "description": "Satisfactory condition of refrigeration units", "critical": False},
    {"id": "3h", "description": "Refrigerated foods < 4°C", "critical": True},
    {"id": "3i", "description": "Frozen foods -18°C", "critical": True},

    # 4 - Food Holding and Preparation Practices (8%)
    {"id": "4a", "description": "Foods thawed according to recommended procedures", "critical": True},
    {"id": "4b", "description": "No evidence of cross-contamination during preparation", "critical": True},
    {"id": "4c", "description": "No evidence of cross-contamination during holding in refrigerators/coolers", "critical": True},
    {"id": "4d", "description": "Foods cooled according to recommended procedures", "critical": True},
    {"id": "4e", "description": "Manual dishwashing wash, rinse, sanitize, rinse technique", "critical": True},
    {"id": "4f", "description": "Food contact surfaces washed-rinsed-sanitized before & after each use", "critical": False},
    {"id": "4g", "description": "Wiping cloths handled properly (sanitizing solution used)", "critical": False},

    # 5 - Post preparation (10%)
    {"id": "5a", "description": "Food protected during transportation", "critical": True},
    {"id": "5b", "description": "Dishes identified and labelled", "critical": False},
    {"id": "5c", "description": "Food covered or protected from contamination", "critical": True},
    {"id": "5d", "description": "Sufficient, appropriate utensils on service line", "critical": True},
    {"id": "5e", "description": "Hot holding temperatures > 63°C", "critical": True},
    {"id": "5f", "description": "Cold holding temperatures ≤ 5°C", "critical": True},

    # 6 - Hand Washing Facilities (3%)
    {"id": "6a", "description": "Hand washing facility installed and maintained for every 40 square meters of floor space or in each principal food area", "critical": True},
    {"id": "6b", "description": "Equipped with hot and cold water, soap dispenser and hand drying facility", "critical": False},

    # 7 - Building (8.5%)
    {"id": "7a", "description": "Provides adequate space", "critical": False},
    {"id": "7b", "description": "Food areas kept clean, free from vermin and unpleasant odours", "critical": True},
    {"id": "7c", "description": "Floor, walls and ceiling clean, in good repair", "critical": False},
    {"id": "7d", "description": "Mechanical ventilation operable where required", "critical": False},
    {"id": "7e", "description": "Lighting adequate for food preparation and cleaning", "critical": False},
    {"id": "7f", "description": "General housekeeping satisfactory", "critical": False},
    {"id": "7g", "description": "Animals, insect and pest excluded", "critical": False},

    # 8 - Food contact surfaces (3%)
    {"id": "8a", "description": "Made from material which is non-absorbent and non-toxic", "critical": False},
    {"id": "8b", "description": "Smooth, cleanable, corrosion resistant", "critical": False},
    {"id": "8c", "description": "Proper storage and use of clean utensils", "critical": False},

    # 9 - Food flow (5.5%)
    {"id": "9a", "description": "Employee traffic pattern avoids food cross-contamination", "critical": True},
    {"id": "9b", "description": "Product flow not at risk for cross-contamination", "critical": True},
    {"id": "9c", "description": "Living quarters, toilets, washrooms, locker separated from areas where food is handled", "critical": True},

    # 10 - Equipment and utensils sanitization (9.5%)
    {"id": "10a", "description": "Mechanical dishwashing: Wash-rinse water clean", "critical": False},
    {"id": "10b", "description": "Proper water temperature", "critical": False},
    {"id": "10c", "description": "Proper timing of cycles", "critical": True},
    {"id": "10d", "description": "Sanitizer for low temperature", "critical": False},
    {"id": "10e", "description": "Proper handling of hazardous materials", "critical": False},

    # 11 - Waste Management: Waste Containers (3%)
    {"id": "11a", "description": "Appropriate design, convenient placement", "critical": False},
    {"id": "11b", "description": "Kept covered when not in continuous use", "critical": False},
    {"id": "11c", "description": "Emptied as often as necessary", "critical": False},

    # 12 - Solid Waste Storage Area (4%)
    {"id": "12d", "description": "Insect and vermin-proof containers provided where required", "critical": False},
    {"id": "12e", "description": "The area around each waste container kept clean", "critical": True},
    {"id": "12f", "description": "Effluent from waste bins disposed of in a sanitary manner", "critical": False},
    {"id": "12g", "description": "Frequency of garbage removal adequate", "critical": False},

    # 13 - Disposal of solid waste
    {"id": "13h", "description": "Garbage, refuse properly disposed of, facilities maintained", "critical": True},

    # 14 - Hazardous Materials Storage, Handling and Disposal (4%)
    {"id": "14a", "description": "Hazardous materials stored in properly labelled containers", "critical": False},
    {"id": "14b", "description": "Stored away from living quarters and food areas", "critical": True},

    # 15 - Sanitary Facilities (4%)
    {"id": "15a", "description": "Approved Sewage Disposal System", "critical": True},
    {"id": "15b", "description": "Sanitary maintenance of facilities and protection against the entrance of vermin, rodents, dust, and fumes", "critical": True},

    # 16 - Pest Control (2%)
    {"id": "16a", "description": "Adequate provision against the entrance of insects, vermin, rodents, dust and fumes", "critical": False},
    {"id": "16b", "description": "Suitable pest control programme", "critical": False},

    # 17 - Sanitary Engineering: Water supply (3%)
    {"id": "17a", "description": "Approved source(s) sufficient pressure and capacity", "critical": False},
    {"id": "17b", "description": "Water quality satisfactory", "critical": False},

    # 18 - Sanitary Engineering: Ice (1.5%)
    {"id": "18a", "description": "Satisfactory ice storage conditions", "critical": False},
]

### Instructions checklist for babershop
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

# Add this after your BARBERSHOP_CHECKLIST_ITEMS
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


# ============================================================================
# DYNAMIC FORM LOADING - Load forms from database
# ============================================================================

def get_form_checklist_items(form_type, fallback_list=None):
    """
    Load form checklist items from database dynamically.
    Falls back to hardcoded list if database is empty.

    Args:
        form_type: Form type name (e.g., 'Food Establishment', 'Residential')
        fallback_list: Hardcoded checklist to use if database is empty

    Returns:
        List of checklist items in the format expected by forms
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get template ID for this form type
        c.execute('SELECT id FROM form_templates WHERE form_type = ? AND active = 1', (form_type,))
        template = c.fetchone()

        if not template:
            print(f"⚠️  No template found for {form_type}, using hardcoded list")
            conn.close()
            return fallback_list if fallback_list else []

        template_id = template[0]

        # Get all active items for this template, ordered
        c.execute('''
            SELECT id, item_order, category, description, weight, is_critical
            FROM form_items
            WHERE form_template_id = ? AND active = 1
            ORDER BY item_order
        ''', (template_id,))

        items = []
        for row in c.fetchall():
            # Convert to format expected by forms
            item = {
                'id': row[1],  # item_order becomes the ID for compatibility
                'desc': row[3],  # description
                'description': row[3],  # alternative key
                'wt': row[4],  # weight
                'category': row[2],  # category
                'is_critical': row[5]  # critical flag
            }
            items.append(item)

        conn.close()

        # If database has items, use them; otherwise use fallback
        if items:
            print(f"✓ Loaded {len(items)} items from database for {form_type}")
            return items
        else:
            print(f"⚠️  No items in database for {form_type}, using hardcoded list")
            return fallback_list if fallback_list else []

    except Exception as e:
        print(f"❌ Error loading form items for {form_type}: {str(e)}")
        # Return fallback on any error
        return fallback_list if fallback_list else []


def get_form_field_properties(form_type):
    """
    Load form field properties from database dynamically.
    Returns a dictionary mapping field names to their properties (label, type, placeholder, etc.)

    Args:
        form_type: Form type name (e.g., 'Food Establishment', 'Residential')

    Returns:
        Dictionary of field properties: {field_name: {label, type, required, placeholder, ...}}
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get template ID for this form type
        c.execute('SELECT id FROM form_templates WHERE form_type = ? AND active = 1', (form_type,))
        template = c.fetchone()

        if not template:
            print(f"⚠️  No template found for {form_type}")
            conn.close()
            return {}

        template_id = template[0]

        # Get all active fields for this template
        c.execute('''
            SELECT field_name, field_label, field_type, required,
                   placeholder, default_value, options, field_group
            FROM form_fields
            WHERE form_template_id = ? AND active = 1
            ORDER BY field_order
        ''', (template_id,))

        fields = {}
        for row in c.fetchall():
            fields[row[0]] = {  # field_name is the key
                'label': row[1],
                'type': row[2],
                'required': bool(row[3]),
                'placeholder': row[4],
                'default_value': row[5],
                'options': row[6].split(',') if row[6] else [],
                'field_group': row[7]
            }

        conn.close()

        if fields:
            print(f"✓ Loaded {len(fields)} field properties from database for {form_type}")
        return fields

    except Exception as e:
        print(f"❌ Error loading form fields for {form_type}: {str(e)}")
        return {}


@app.route('/debug/stats')
def debug_stats():
    if 'admin' not in session and 'inspector' not in session:
        return "Access denied"

    conn = get_db_connection()
    c = conn.cursor()

    # Check what form_types exist
    c.execute("SELECT form_type, COUNT(*) FROM inspections GROUP BY form_type")
    form_types = c.fetchall()

    # Check total count
    c.execute("SELECT COUNT(*) FROM inspections")
    total = c.fetchone()[0]

    # Check each table
    c.execute("SELECT COUNT(*) FROM residential_inspections")
    residential = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM burial_site_inspections")
    burial = c.fetchone()[0]

    conn.close()

    return f"""
    <h2>Debug Stats:</h2>
    <p>Total inspections: {total}</p>
    <p>Residential: {residential}</p>
    <p>Burial: {burial}</p>
    <h3>Form types in database:</h3>
    <ul>
    {''.join([f'<li>{ft[0]}: {ft[1]} records</li>' for ft in form_types])}
    </ul>
    """
def get_establishment_data():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT establishment_name, owner, license_no, id FROM inspections")
    data = c.fetchall()
    conn.close()
    return data

@app.route('/')
def login():
    if 'inspector' in session:
        return render_template('dashboard.html', inspections=get_inspections(), burial_inspections=get_burial_inspections())
    return render_template('login.html')


@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, form_type, inspector_name, created_at, establishment_name, result, owner
        FROM inspections
        WHERE form_type IN (
            'Food Establishment', 'Spirit Licence Premises', 'Swimming Pool',
            'Small Hotel', 'Barbershop', 'Institutional Health'
        )
        UNION
        SELECT id, 'Residential' AS form_type, inspector_name, created_at, premises_name, result, owner
        FROM residential_inspections
        UNION
        SELECT id, 'Burial' AS form_type, '' AS inspector_name, created_at, applicant_name, 'Completed' AS result, deceased_name
        FROM burial_site_inspections
        UNION
        SELECT id, 'Meat Processing' AS form_type, inspector_name, created_at, establishment_name, result, owner_operator
        FROM meat_processing_inspections
        ORDER BY created_at DESC
    """)
    forms = c.fetchall()
    conn.close()
    return render_template('admin.html', forms=forms)


@app.route('/admin_form_scores')
def admin_form_scores():
    form_type = request.args.get('form_type', 'all')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if form_type == 'all':
            cursor.execute("""
                SELECT overall_score FROM inspections
                WHERE overall_score IS NOT NULL AND overall_score > 0
                UNION ALL
                SELECT overall_score FROM residential_inspections
                WHERE overall_score IS NOT NULL AND overall_score > 0
                UNION ALL
                SELECT overall_score FROM meat_processing_inspections
                WHERE overall_score IS NOT NULL AND overall_score > 0
            """)
            scores = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT overall_score FROM inspections 
                WHERE form_type = ? AND overall_score IS NOT NULL AND overall_score > 0
            """, (form_type,))
            scores = cursor.fetchall()

        return jsonify([score[0] for score in scores])

    except Exception as e:
        print(f"Database error: {e}")
        return jsonify([]), 500

    finally:
        conn.close()


def get_table_name_for_form_type(form_type):
    return 'inspections'


@app.route('/admin_metrics', methods=['GET'])
def admin_metrics():
    form_type = request.args.get('form_type', 'all')
    time_frame = request.args.get('time_frame', 'daily')
    conn = get_db_connection()
    c = conn.cursor()

    if form_type == 'all':
        query = """
            SELECT strftime('%Y-%m-%d', created_at) AS date, result, COUNT(*) AS count
            FROM (
                SELECT created_at, result FROM inspections
                WHERE form_type IN ('Food Establishment', 'Spirit Licence Premises', 'Swimming Pool', 'Small Hotel', 'Barbershop', 'Institutional Health')
                UNION
                SELECT created_at, result FROM residential_inspections
                UNION
                SELECT created_at, 'Completed' AS result FROM burial_site_inspections
                UNION
                SELECT created_at, result FROM meat_processing_inspections
            )
            GROUP BY date, result
        """
    else:
        if form_type == 'Residential':
            query = """
                SELECT strftime('%Y-%m-%d', created_at) AS date, result, COUNT(*) AS count
                FROM residential_inspections
                GROUP BY date, result
            """
        elif form_type == 'Burial':
            query = """
                SELECT strftime('%Y-%m-%d', created_at) AS date, 'Completed' AS result, COUNT(*) AS count
                FROM burial_site_inspections
                GROUP BY date, result
            """
        elif form_type == 'Meat Processing':
            query = """
                SELECT strftime('%Y-%m-%d', created_at) AS date, result, COUNT(*) AS count
                FROM meat_processing_inspections
                GROUP BY date, result
            """
        else:
            query = """
                SELECT strftime('%Y-%m-%d', created_at) AS date, result, COUNT(*) AS count
                FROM inspections
                WHERE form_type = ?
                GROUP BY date, result
            """
            c.execute(query, (form_type,))
            results = c.fetchall()
            conn.close()
            return jsonify(process_metrics(results, time_frame))

    c.execute(query)
    results = c.fetchall()
    conn.close()
    return jsonify(process_metrics(results, time_frame))


def process_metrics(results, time_frame):
    data = {'dates': [], 'pass': [], 'fail': []}
    date_format = '%Y-%m-%d' if time_frame == 'daily' else '%Y-%m' if time_frame == 'monthly' else '%Y'

    for date, result, count in results:
        formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime(date_format)
        if formatted_date not in data['dates']:
            data['dates'].append(formatted_date)
            data['pass'].append(0)
            data['fail'].append(0)

        idx = data['dates'].index(formatted_date)
        # Updated to include 'Satisfactory' as a passing result
        if result in ['Pass', 'Completed', 'Satisfactory']:
            data['pass'][idx] += count
        else:
            data['fail'][idx] += count

    return data

@app.route('/view_institutional/<int:form_id>')
def view_institutional(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    return institutional_inspection_detail(form_id)

@app.route('/generate_report', methods=['GET'])
def generate_report():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    metric = request.args.get('metric', 'inspections')
    timeframe = request.args.get('timeframe', 'daily')
    conn = get_db_connection()
    c = conn.cursor()
    if metric == 'inspections':
        query = """
            SELECT strftime('%Y-%m-%d', created_at) AS date, COUNT(*) AS count
            FROM inspections
            GROUP BY date
        """
        c.execute(query)
        results = c.fetchall()
        data = {'dates': [], 'counts': []}
        for date, count in results:
            data['dates'].append(date)
            data['counts'].append(count)
        conn.close()
        return jsonify(data)
    conn.close()
    return jsonify({'error': 'Invalid metric'}), 400

@app.route('/api/system_health', methods=['GET'])
def system_health():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    # Simulated data; replace with actual metrics
    data = {
        'uptime': 99.9,
        'db_response': 50,
        'error_rate': 0.1,
        'history': {
            'labels': ['1h', '2h', '3h', '4h', '5h'],
            'uptime': [99.8, 99.9, 99.7, 99.9, 99.9],
            'db_response': [45, 50, 55, 48, 50],
            'error_rate': [0.2, 0.1, 0.3, 0.1, 0.1]
        }
    }
    return jsonify(data)


@app.route('/logout', methods=['POST'])
def logout():
    # Mark user session as inactive before logging out
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            # Get username from session
            username = session.get('inspector') or session.get('admin') or session.get('medical_officer')
            if username:
                c.execute("UPDATE user_sessions SET is_active = 0, logout_time = ? WHERE username = ? AND is_active = 1",
                          (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating user session on logout: {e}")

    session.clear()  # Clear all session data
    return redirect(url_for('login'))  # Redirect to login page



@app.route('/new_residential_form')
def new_residential_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    # Load checklist from database (falls back to hardcoded if empty)
    checklist = get_form_checklist_items('Residential', RESIDENTIAL_CHECKLIST_ITEMS)
    return render_template('residential_form.html', checklist=checklist, inspections=get_residential_inspections(), show_form=True, establishment_data=get_establishment_data())

@app.route('/new_burial_form')
def new_burial_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    inspection_id = request.args.get('id')
    if inspection_id:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM burial_site_inspections WHERE id = ?", (inspection_id,))
        inspection = c.fetchone()
        conn.close()
        if inspection:
            inspection_data = {
                'id': inspection[0],
                'inspection_date': inspection[1],
                'applicant_name': inspection[2],
                'deceased_name': inspection[3],
                'burial_location': inspection[4],
                'site_description': inspection[5],
                'proximity_water_source': inspection[6],
                'proximity_perimeter_boundaries': inspection[7],
                'proximity_road_pathway': inspection[8],
                'proximity_trees': inspection[9],
                'proximity_houses_buildings': inspection[10],
                'proposed_grave_type': inspection[11],
                'general_remarks': inspection[12],
                'inspector_signature': inspection[13],
                'received_by': inspection[14],
                'created_at': inspection[15]
            }
            return render_template('burial_form.html', inspection=inspection_data)
    return render_template('burial_form.html', inspection=None)

@app.route('/new_water_supply_form')
def new_water_supply_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    return render_template('water_supply_form.html', checklist=[], inspections=get_inspections())

@app.route('/new_spirit_licence_form')
def new_spirit_licence_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    # Default inspection data for new form
    inspection = {
        'id': '',
        'establishment_name': '',
        'owner': '',
        'address': '',
        'license_no': '13697',  # Default license number per submit route
        'inspector_name': session.get('inspector', 'Inspector'),
        'inspection_date': datetime.now().strftime('%Y-%m-%d'),
        'inspection_time': '',
        'type_of_establishment': 'Spirit Licence Premises',
        'no_of_employees': '',
        'no_with_fhc': '',
        'no_wo_fhc': '',
        'status': '',
        'purpose_of_visit': '',
        'action': '',
        'result': '',
        'critical_score': 0,
        'overall_score': 0,
        'comments': '',
        'inspector_signature': '',
        'received_by': '',
        'scores': {},
        'created_at': ''
    }
    # Load checklist from database (falls back to hardcoded if empty)
    checklist = get_form_checklist_items('Spirit Licence Premises', SPIRIT_LICENCE_CHECKLIST_ITEMS)
    return render_template('spirit_licence_form.html', checklist=checklist, inspections=get_inspections(), show_form=True, establishment_data=get_establishment_data(), read_only=False, inspection=inspection)

@app.route('/new_swimming_pool_form')
def new_swimming_pool_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    inspection = {
        'id': '',
        'establishment_name': '',
        'address': '',
        'physical_location': '',
        'type_of_establishment': '',
        'inspector_name': '',
        'inspection_date': '',
        'inspection_time': '',
        'result': '',
        'overall_score': 0,
        'critical_score': 0,
        'comments': '',
        'inspector_signature': '',
        'inspector_date': '',
        'manager_signature': '',
        'manager_date': '',
        'scores': {}
    }
    # Load checklist from database (falls back to hardcoded if empty)
    checklist = get_form_checklist_items('Swimming Pool', SWIMMING_POOL_CHECKLIST_ITEMS)
    return render_template('swimming_pool_form.html', checklist=checklist, inspections=get_inspections(), inspection=inspection)

@app.route('/new_small_hotels_form')
def new_small_hotels_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    today = datetime.now().strftime('%Y-%m-%d')
    # Load checklist from database (falls back to hardcoded if empty)
    checklist_items = get_form_checklist_items('Small Hotel', SMALL_HOTELS_CHECKLIST_ITEMS)
    return render_template('small_hotels_form.html', checklist_items=checklist_items, today=today)


@app.route('/submit_institutional', methods=['POST'])
def submit_institutional():
    if 'inspector' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    try:
        print("=== INSTITUTIONAL FORM SUBMISSION DEBUG ===")
        print("All form data received:")
        for key, value in request.form.items():
            print(f"  {key}: '{value}'")
        print("=" * 50)

        # Get form data with proper field names
        establishment_name = request.form.get('establishment_name', '')
        owner_operator = request.form.get('owner_operator', '')
        address = request.form.get('address', '')
        inspector_name = request.form.get('inspector_name', '')

        # Institutional specific fields
        staff_complement = request.form.get('staff_complement', '')
        num_occupants = request.form.get('num_occupants', '')
        institution_type = request.form.get('institution_type', '')

        # Building details
        building_size_ft2 = 'Yes' if request.form.get('building_size_ft2') else ''
        building_size_m2 = 'Yes' if request.form.get('building_size_m2') else ''
        building_size_value = request.form.get('building_size_value', '')
        telephone_no = request.form.get('telephone_no', '')
        num_buildings = request.form.get('num_buildings', '')

        # Date and inspection details
        inspection_date = request.form.get('inspection_date', '')
        inspector_code = request.form.get('inspector_code', '')

        # Scores
        overall_score = float(request.form.get('overall_score', 0))
        critical_score = float(request.form.get('critical_score', 0))

        # Calculate Pass/Fail based on scores
        if overall_score >= 70 and critical_score >= 50:
            result = 'Pass'
        else:
            result = 'Fail'

        # Other fields
        license_no = request.form.get('license_no', '')
        registration_status = request.form.get('registration_status', '')
        purpose_of_visit = request.form.get('purpose_of_visit', '')
        action = request.form.get('action', '')
        comments = request.form.get('comments', '')
        inspector_signature = request.form.get('inspector_signature', '')
        received_by = request.form.get('received_by', '')
        photo_data = request.form.get('photos', '[]')

        print("=== PROCESSED FIELD VALUES ===")
        print(f"Staff Complement: '{staff_complement}'")
        print(f"Occupants: '{num_occupants}'")
        print(f"Institution Type: '{institution_type}'")
        print(f"Building Size: '{building_size_value}' (ft²: {building_size_ft2}, m²: {building_size_m2})")
        print(f"Telephone: '{telephone_no}'")
        print(f"Num Buildings: '{num_buildings}'")
        print(f"Purpose of Visit: '{purpose_of_visit}'")
        print(f"Inspection Date: '{inspection_date}'")
        print(f"Inspector Code: '{inspector_code}'")
        print(f"Result: '{result}' (calculated from scores)")
        print(f"License No: '{license_no}'")
        print(f"Registration Status: '{registration_status}'")
        print(f"Action: '{action}'")
        print(f"Comments: '{comments}'")
        print(f"Inspector Signature: '{inspector_signature}'")
        print(f"Received By: '{received_by}'")
        print(f"Overall Score: {overall_score}")
        print(f"Critical Score: {critical_score}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if columns exist and add them if needed
        cursor.execute("PRAGMA table_info(inspections)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        required_columns = [
            'staff_complement', 'num_occupants', 'institution_type',
            'building_size_ft2', 'building_size_m2', 'building_size_value',
            'telephone_no', 'num_buildings', 'inspector_code',
            'registration_status', 'purpose_of_visit', 'action'
        ]

        for column in required_columns:
            if column not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE inspections ADD COLUMN {column} TEXT')
                    print(f"Added missing column: {column}")
                except sqlite3.OperationalError as e:
                    print(f"Error adding column {column}: {e}")

        # Insert the inspection with ALL the data
        cursor.execute("""
            INSERT INTO inspections (
                establishment_name, owner, address, inspector_name,
                staff_complement, num_occupants, institution_type,
                building_size_ft2, building_size_m2, building_size_value,
                telephone_no, num_buildings, inspection_date, inspector_code,
                overall_score, critical_score, result, license_no,
                registration_status, purpose_of_visit, action, comments,
                inspector_signature, received_by, photo_data, form_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            establishment_name, owner_operator, address, inspector_name,
            staff_complement, num_occupants, institution_type,
            building_size_ft2, building_size_m2, building_size_value,
            telephone_no, num_buildings, inspection_date, inspector_code,
            overall_score, critical_score, result, license_no,
            registration_status, purpose_of_visit, action, comments,
            inspector_signature, received_by, photo_data, 'Institutional Health', datetime.now()
        ))

        inspection_id = cursor.lastrowid
        print(f"Created inspection record with ID: {inspection_id}")

        # Save individual scores - Debug each one
        print("=== SAVING INDIVIDUAL SCORES ===")
        scores_saved = 0
        for i in range(1, 32):  # Items 01-31
            score_key = f'score_{i:02d}'
            score_value = request.form.get(score_key, '0')

            print(f"Processing {score_key}: received '{score_value}'")

            if score_value and score_value != '0':
                cursor.execute(
                    "INSERT INTO inspection_items (inspection_id, item_id, details) VALUES (?, ?, ?)",
                    (inspection_id, f'{i:02d}', score_value)
                )
                scores_saved += 1
                print(f"  → Saved {score_key} = {score_value}")
            else:
                print(f"  → Skipped {score_key} (value was '{score_value}')")

        print(f"Total scores saved: {scores_saved}")

        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': 'Institutional Health inspection submitted successfully!',
            'redirect': '/dashboard'
        })

    except Exception as e:
        print(f"ERROR in submit_institutional: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/fix_institutional_status')
def fix_institutional_status():
    """Run this once to update existing institutional records with Pass/Fail status"""
    if 'admin' not in session and 'inspector' not in session:
        return "Access denied"

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all institutional records
    cursor.execute("""
        SELECT id, overall_score, critical_score 
        FROM inspections 
        WHERE form_type = 'Institutional Health'
    """)
    records = cursor.fetchall()

    updated_count = 0
    for record in records:
        inspection_id, overall_score, critical_score = record
        overall_score = overall_score or 0
        critical_score = critical_score or 0

        # Calculate Pass/Fail
        if overall_score >= 70 and critical_score >= 50:
            result = 'Pass'
        else:
            result = 'Fail'

        # Update the record
        cursor.execute("""
            UPDATE inspections 
            SET result = ? 
            WHERE id = ?
        """, (result, inspection_id))
        updated_count += 1
        print(
            f"Updated inspection {inspection_id}: Overall={overall_score}, Critical={critical_score}, Result={result}")

    conn.commit()
    conn.close()

    return f"Updated {updated_count} institutional inspection records! <a href='/dashboard'>Back to Dashboard</a>"


@app.route('/institutional_details/<int:form_id>')
def institutional_details(form_id):
    inspection = InstitutionalInspection.query.get_or_404(form_id)

    # Parse photos from JSON string to Python list
    photos = []
    if inspection.photos:
        try:
            import json
            photos = json.loads(inspection.photos)
        except:
            photos = []

    return render_template('institutional_details.html',
                           inspection=inspection,
                           photo_data=photos)

@app.route('/institutional/inspection/<int:id>')
def institutional_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Institutional Health'", (id,))
    inspection = cursor.fetchone()

    if not inspection:
        conn.close()
        return "Inspection not found", 404

    inspection_dict = dict(inspection)

    # Recalculate Pass/Fail status based on scores
    overall_score = inspection_dict.get('overall_score', 0) or 0
    critical_score = inspection_dict.get('critical_score', 0) or 0

    if overall_score >= 70 and critical_score >= 50:
        inspection_dict['result'] = 'Pass'
    else:
        inspection_dict['result'] = 'Fail'

    # DEBUG: Print what's in the database
    print("=== DATABASE VALUES ===")
    for key, value in inspection_dict.items():
        if value:  # Only print non-empty values
            print(f"{key}: {value}")

    # Get individual scores from inspection_items table
    cursor.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (id,))
    item_scores = {}
    for row in cursor.fetchall():
        item_key = row[0]
        score_value = float(row[1]) if row[1] and str(row[1]).replace('.', '', 1).isdigit() else 0.0
        item_scores[item_key] = score_value

    # Create the scores dictionary that the template expects
    scores = {}
    for item in INSTITUTIONAL_CHECKLIST_ITEMS:
        item_id = item['id']
        scores[item_id] = item_scores.get(item_id, 0.0)

    inspection_dict['scores'] = scores

    conn.close()

    # Parse photos from JSON string to Python list
    photos = []
    if inspection_dict.get('photo_data'):
        try:
            import json
            photos = json.loads(inspection_dict.get('photo_data', '[]'))
        except:
            photos = []

    return render_template('institutional_inspection_detail.html',
                           inspection=inspection_dict,
                           checklist=INSTITUTIONAL_CHECKLIST_ITEMS,
                           photo_data=photos)

@app.route('/submit_spirit_licence', methods=['POST'])
def submit_spirit_licence():
    if 'inspector' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401
    data = {
        'establishment_name': request.form.get('establishment_name', ''),
        'owner': request.form.get('owner_operator', ''),
        'address': request.form.get('address', ''),
        'license_no': '13697',
        'inspector_name': request.form.get('inspector_name', ''),
        'inspection_date': request.form.get('inspection_date', ''),
        'inspection_time': '',
        'type_of_establishment': request.form.get('type_of_establishment', 'Spirit Licence Premises'),
        'purpose_of_visit': request.form.get('purpose_of_visit', ''),
        'action': '',
        'result': 'Pass' if (sum(int(request.form.get(f"score_{i}", 0)) for i in range(1, 35) if int(request.form.get(f"score_{i}", 0)) > 0) >= 70 and
                             sum(int(request.form.get(f"score_{i}", 0)) for i in [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 33, 34] if int(request.form.get(f"score_{i}", 0)) > 0) >= 59) else 'Fail',
        'comments': '\n'.join([f"{i}: {request.form.get(f'comment_{i}', '')}" for i in range(1, 35)]),
        'inspector_signature': request.form.get('inspector_signature', ''),
        'received_by': request.form.get('received_by', ''),
        'scores': ','.join([request.form.get(f"score_{i}", '0') for i in range(1, 35)]),
        'form_type': 'Spirit Licence Premises',
        'no_of_employees': request.form.get('no_of_employees', ''),
        'no_with_fhc': request.form.get('no_with_fhc', ''),
        'no_wo_fhc': request.form.get('no_wo_fhc', ''),
        'status': request.form.get('status', ''),
        'food_inspected': 0.0,
        'food_condemned': 0.0,
        'inspector_code': '',
        'photo_data': request.form.get('photos', '[]'),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    overall_score = sum(int(request.form.get(f"score_{i}", 0)) for i in range(1, 35) if int(request.form.get(f"score_{i}", 0)) > 0)
    data['overall_score'] = overall_score
    critical_score = sum(int(request.form.get(f"score_{i}", 0)) for i in [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 33, 34] if int(request.form.get(f"score_{i}", 0)) > 0)
    data['critical_score'] = critical_score
    try:
        inspection_id = save_inspection(data)
        conn = get_db_connection()
        c = conn.cursor()
        for item in SPIRIT_LICENCE_CHECKLIST_ITEMS:
            score = request.form.get(f"score_{item['id']}", '0')
            c.execute("INSERT INTO inspection_items (inspection_id, item_id, details) VALUES (?, ?, ?)",
                      (inspection_id, item['id'], score))
        conn.commit()
        conn.close()

        # Check and create alert if score below threshold
        check_and_create_alert(
            inspection_id,
            data['inspector_name'],
            'Spirit Licence Premises',
            data['overall_score']
        )

        return jsonify({'status': 'success', 'message': 'Submit Successfully'})
    except sqlite3.Error as e:
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500


@app.route('/submit/<form_type>', methods=['POST'])
def submit_form(form_type):
    if 'inspector' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 403
    try:
        if form_type == 'inspection':
            data = {
                'establishment_name': request.form.get('establishment_name'),
                'address': request.form.get('address'),
                'owner': request.form.get('owner'),
                'license_no': request.form.get('license_no'),
                'inspector_name': request.form.get('inspector_name'),
                'inspector_code': request.form.get('inspector_code'),
                'inspection_date': request.form.get('inspection_date'),
                'inspection_time': request.form.get('inspection_time'),
                'type_of_establishment': request.form.get('type_of_establishment'),
                'no_of_employees': request.form.get('no_of_employees'),
                'purpose_of_visit': request.form.get('purpose_of_visit'),
                'action': request.form.get('action'),
                'food_inspected': request.form.get('food_inspected'),
                'food_condemned': request.form.get('food_condemned'),
                'critical_score': int(request.form.get('critical_score', 0)),
                'overall_score': int(request.form.get('overall_score', 0)),
                'result': request.form.get('result'),
                'comments': request.form.get('comments'),
                'scores': ','.join([request.form.get(f'score_{item["id"]}', '0') for item in FOOD_CHECKLIST_ITEMS]),
                'inspector_signature': request.form.get('inspector_signature'),
                'received_by': request.form.get('received_by'),
                'form_type': 'Food Establishment',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'photo_data': request.form.get('photos', '[]')  # Form sends 'photos' not 'photo_data'
            }
            inspection_id = save_inspection(data)

            conn = get_db_connection()
            c = conn.cursor()
            for item in FOOD_CHECKLIST_ITEMS:
                score = request.form.get(f'score_{item["id"]}', '0')
                c.execute("INSERT INTO inspection_items (inspection_id, item_id, details) VALUES (?, ?, ?)",
                          (inspection_id, item["id"], score))
            conn.commit()
            conn.close()

            # Check and create alert if score below threshold
            check_and_create_alert(
                inspection_id,
                data['inspector_name'],
                'Food Establishment',
                data['overall_score']
            )

            return jsonify({'success': True, 'message': 'Form submitted', 'inspection_id': inspection_id})
        return jsonify({'success': False, 'error': 'Invalid form type'}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/submit_residential', methods=['POST'])
def submit_residential():
    if 'inspector' not in session:
        return jsonify({'message': 'Unauthorized: Please log in'}), 401

    try:
        # Helper function to safely convert to int
        def safe_int_convert(value, default=0):
            try:
                return int(float(value)) if value else default
            except (ValueError, TypeError):
                return default

        data = {
            'premises_name': request.form['premises_name'],
            'owner': request.form['owner'],
            'address': request.form['address'],
            'inspector_name': request.form['inspector_name'],
            'inspection_date': request.form['inspection_date'],
            'inspector_code': request.form['inspector_code'],
            'treatment_facility': request.form['treatment_facility'],
            'vector': request.form['vector'],
            'result': request.form['result'],
            'onsite_system': request.form['onsite_system'],
            'building_construction_type': request.form.get('building_construction_type', ''),
            'purpose_of_visit': request.form['purpose_of_visit'],
            'action': request.form['action'],
            'no_of_bedrooms': request.form.get('no_of_bedrooms', ''),
            'total_population': request.form.get('total_population', ''),
            'critical_score': safe_int_convert(request.form['critical_score']),
            'overall_score': safe_int_convert(request.form['overall_score']),
            'comments': request.form.get('comments', ''),
            'inspector_signature': request.form['inspector_signature'],
            'received_by': request.form.get('received_by', ''),
            'photo_data': request.form.get('photos', '[]'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        inspection_id = save_residential_inspection(data)

        conn = get_db_connection()
        c = conn.cursor()
        for item in RESIDENTIAL_CHECKLIST_ITEMS:
            score = request.form.get(f'score_{item["id"]}', '0')
            # Also apply safe conversion to checklist scores
            safe_score = safe_int_convert(score, 0)
            c.execute("INSERT INTO residential_checklist_scores (form_id, item_id, score) VALUES (?, ?, ?)",
                      (inspection_id, item["id"], safe_score))
        conn.commit()
        conn.close()

        # Check and create alert if score below threshold
        check_and_create_alert(
            inspection_id,
            data['inspector_name'],
            'Residential',
            data['overall_score']
        )

        return jsonify({'message': 'Submit successfully', 'inspection_id': inspection_id})
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/submit_burial', methods=['POST'])
def submit_burial():
    if 'inspector' not in session:
        return jsonify({'message': 'Unauthorized: Please log in'}), 401

    data = {
        'id': request.form.get('id', ''),
        'inspection_date': request.form.get('inspection_date', ''),
        'applicant_name': request.form.get('applicant_name', ''),
        'deceased_name': request.form.get('deceased_name', ''),
        'burial_location': request.form.get('burial_location', ''),
        'site_description': request.form.get('site_description', ''),
        'proximity_water_source': request.form.get('proximity_water_source', ''),
        'proximity_perimeter_boundaries': request.form.get('proximity_perimeter_boundaries', ''),
        'proximity_road_pathway': request.form.get('proximity_road_pathway', ''),
        'proximity_trees': request.form.get('proximity_trees', ''),
        'proximity_houses_buildings': request.form.get('proximity_houses_buildings', ''),
        'proposed_grave_type': request.form.get('proposed_grave_type', ''),
        'general_remarks': request.form.get('general_remarks', ''),
        'inspector_signature': request.form.get('inspector_signature', ''),
        'received_by': request.form.get('received_by', ''),
        'photo_data': request.form.get('photos', '[]')
    }

    try:
        inspection_id = save_burial_inspection(data)
        return jsonify({'message': 'Submit successfully', 'inspection_id': inspection_id})
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/submit_meat_processing', methods=['POST'])
def submit_meat_processing():
    if 'inspector' not in session:
        return jsonify({'message': 'Unauthorized: Please log in'}), 401

    # Helper function to safely convert to float
    def safe_float_convert(value, default=0.0):
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default

    # Helper function to safely convert to int
    def safe_int_convert(value, default=0):
        try:
            return int(value) if value else default
        except (ValueError, TypeError):
            return default

    # Helper function to convert checkbox to int (1 if checked, 0 otherwise)
    def checkbox_to_int(value):
        return 1 if value == 'on' else 0

    # Process photos if included
    photos_json = request.form.get('photos', '[]')

    data = {
        'establishment_name': request.form.get('establishment_name', ''),
        'owner_operator': request.form.get('owner_operator', ''),
        'address': request.form.get('address', ''),
        'inspector_name': request.form.get('inspector_name', ''),
        'establishment_no': request.form.get('establishment_no', ''),
        'overall_score': safe_float_convert(request.form.get('overall_score', '0')),
        'food_contact_surfaces': safe_int_convert(request.form.get('food_contact_surfaces', '0')),
        'water_samples': safe_int_convert(request.form.get('water_samples', '0')),
        'product_samples': safe_int_convert(request.form.get('product_samples', '0')),
        'types_of_products': request.form.get('types_of_products', ''),
        'staff_fhp': safe_int_convert(request.form.get('staff_fhp', '0')),
        'staff_compliment': safe_int_convert(request.form.get('staff_compliment', '0')),
        'water_public': checkbox_to_int(request.form.get('water_public', '')),
        'water_private': checkbox_to_int(request.form.get('water_private', '')),
        'type_processing': checkbox_to_int(request.form.get('type_processing', '')),
        'type_slaughter': checkbox_to_int(request.form.get('type_slaughter', '')),
        'purpose_of_visit': request.form.get('purpose_of_visit', ''),
        'inspection_date': request.form.get('inspection_date', ''),
        'inspector_code': request.form.get('inspector_code', ''),
        'result': request.form.get('result', ''),
        'telephone_no': request.form.get('telephone_no', ''),
        'registration_status': request.form.get('registration_status', ''),
        'action': request.form.get('action', ''),
        'comments': request.form.get('comments', ''),
        'inspector_signature': request.form.get('inspector_signature', ''),
        'received_by': request.form.get('received_by', ''),
        'photo_data': photos_json  # Save photos as JSON
    }

    try:
        inspection_id = save_meat_processing_inspection(data)

        # Save checklist scores
        conn = get_db_connection()
        c = conn.cursor()
        for item in MEAT_PROCESSING_CHECKLIST_ITEMS:
            score = request.form.get(f'score_{item["id"]:02d}', '0')
            safe_score = safe_float_convert(score, 0.0)
            c.execute("INSERT INTO meat_processing_checklist_scores (form_id, item_id, score) VALUES (?, ?, ?)",
                      (inspection_id, item["id"], safe_score))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Submit successfully', 'inspection_id': inspection_id})
    except Exception as e:
        print(f"Error submitting meat processing inspection: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500


@app.route('/submit_swimming_pools', methods=['POST'])
def submit_swimming_pools():
    if 'inspector' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # Auto-fix database columns if needed
    try:
        cursor.execute("SELECT score_1A FROM inspections LIMIT 1")
    except sqlite3.OperationalError:
        # Columns don't exist, add them
        print("Adding missing swimming pool score columns...")
        for item in SWIMMING_POOL_CHECKLIST_ITEMS:
            try:
                cursor.execute(f'ALTER TABLE inspections ADD COLUMN score_{item["id"]} REAL DEFAULT 0')
                print(f"Added column score_{item['id']}")
            except sqlite3.OperationalError:
                pass  # Column already exists
        conn.commit()

    # Extract form data
    operator = request.form.get('operator')
    date_inspection = request.form.get('date_inspection')
    inspector_id = request.form.get('inspector_id')
    pool_class = request.form.get('pool_class')
    address = request.form.get('address')
    physical_location = request.form.get('physical_location')
    inspector_comments = request.form.get('inspector_comments')
    inspector_signature = request.form.get('inspector_signature')
    inspector_date = request.form.get('inspector_date')
    manager_signature = request.form.get('manager_signature')
    manager_date = request.form.get('manager_date')
    photo_data = request.form.get('photos', '[]')

    # DEBUG: Print what we're receiving
    print("=== DEBUG: Form data received ===")
    for key, value in request.form.items():
        if key.startswith('score_'):
            print(f"{key}: {value}")

    # Collect checklist scores with correct field names
    scores = []
    total_score = 0
    max_possible_score = 0

    # Prepare individual score updates
    score_updates = {}

    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        # The form sends field names like score_1A, score_1B, etc.
        score_key = f"score_{item['id']}"
        score = float(request.form.get(score_key, 0))

        # Store for individual column updates
        score_updates[score_key] = score

        scores.append(str(score))
        total_score += score
        max_possible_score += item['wt']

        print(f"Item {item['id']}: looking for {score_key}, got {score}, weight {item['wt']}")

    # Calculate overall score as percentage - rounded to 1 decimal place
    overall_score = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    overall_score = round(min(overall_score, 100), 1)  # Round to 1 decimal place

    # Calculate critical score (items with weight 5 are critical)
    critical_score = sum(float(request.form.get(f"score_{item['id']}", 0))
                         for item in SWIMMING_POOL_CHECKLIST_ITEMS if item['wt'] == 5)

    result = 'Pass' if overall_score >= 70 else 'Fail'

    print(f"=== SCORING DEBUG ===")
    print(f"Total Score: {total_score}")
    print(f"Max Possible: {max_possible_score}")
    print(f"Overall Score: {overall_score}%")
    print(f"Critical Score: {critical_score}")
    print(f"Result: {result}")

    # Build the INSERT query dynamically to include all score columns
    base_columns = '''establishment_name, owner, address, physical_location,
                     type_of_establishment, inspector_name, inspection_date, form_type, result,
                     created_at, comments, scores, overall_score, critical_score, inspector_signature,
                     received_by, manager_date, photo_data'''

    score_columns = ', '.join([f"score_{item['id']}" for item in SWIMMING_POOL_CHECKLIST_ITEMS])
    all_columns = f"{base_columns}, {score_columns}"

    base_placeholders = '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?'
    score_placeholders = ', '.join(['?' for _ in SWIMMING_POOL_CHECKLIST_ITEMS])
    all_placeholders = f"{base_placeholders}, {score_placeholders}"

    base_values = (
        operator, operator, address, physical_location, pool_class, inspector_id,
        date_inspection, 'Swimming Pool', result, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        inspector_comments, ','.join(scores), overall_score, critical_score,
        inspector_signature, manager_signature, manager_date, photo_data
    )

    score_values = tuple(score_updates[f"score_{item['id']}"] for item in SWIMMING_POOL_CHECKLIST_ITEMS)
    all_values = base_values + score_values

    # Insert inspection into main table with all scores
    try:
        cursor.execute(f'''
            INSERT INTO inspections ({all_columns})
            VALUES ({all_placeholders})
        ''', all_values)

        inspection_id = cursor.lastrowid
        print(f"=== SUCCESS: Inspection {inspection_id} saved with all scores ===")

    except sqlite3.OperationalError as e:
        print(f"Error inserting with score columns: {e}")
        # Fallback to basic insert
        cursor.execute('''
            INSERT INTO inspections (establishment_name, owner, address, physical_location, 
            type_of_establishment, inspector_name, inspection_date, form_type, result, 
            created_at, comments, scores, overall_score, critical_score, inspector_signature, 
            received_by, manager_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', base_values)

        inspection_id = cursor.lastrowid

    # Insert inspection items
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_key = f"score_{item['id']}"
        score = float(request.form.get(score_key, 0))
        cursor.execute('''
            INSERT INTO inspection_items (inspection_id, item_id, details)
            VALUES (?, ?, ?)
        ''', (inspection_id, item['id'], str(score)))

    conn.commit()
    conn.close()

    print(f"=== FINAL SUCCESS: Inspection {inspection_id} completely saved ===")
    return jsonify({'status': 'success', 'message': 'Inspection submitted successfully'})


@app.route('/admin/update_database_schema')
def update_database_schema():
    """Update database schema to support all form types"""
    if 'admin' not in session:
        return "Admin access required"

    conn = get_db_connection()
    cursor = conn.cursor()

    # Add columns that might be missing
    new_columns = [
        'staff_complement', 'num_occupants', 'institution_type',
        'building_size_ft2', 'building_size_m2', 'building_size_value',
        'telephone_no', 'num_buildings', 'inspector_code',
        'registration_status', 'purpose_of_visit', 'action'
    ]

    cursor.execute("PRAGMA table_info(inspections)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    for column in new_columns:
        if column not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE inspections ADD COLUMN {column} TEXT')
                print(f"Added column: {column}")
            except sqlite3.OperationalError:
                pass  # Column might already exist

    conn.commit()
    conn.close()

    return "Database schema updated! <a href='/admin'>Back to Admin Dashboard</a>"


@app.route('/fix_swimming_pool_db')
def fix_swimming_pool_db():
    """Run this once to add missing columns to the inspections table"""
    if 'admin' not in session:
        return "Admin access required"

    conn = get_db_connection()
    cursor = conn.cursor()

    # Add score columns for each checklist item
    columns_added = 0
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        try:
            cursor.execute(f'ALTER TABLE inspections ADD COLUMN score_{item["id"]} REAL DEFAULT 0')
            columns_added += 1
            print(f"Added column score_{item['id']}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Error adding score_{item['id']}: {e}")

    conn.commit()
    conn.close()
    return f"Database updated! Added {columns_added} new columns."


@app.route('/new_institutional_form')
def new_institutional_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))

    # Load checklist from database (falls back to hardcoded if empty)
    checklist = get_form_checklist_items('Institutional', INSTITUTIONAL_CHECKLIST_ITEMS)

    inspection = {
        'id': '',
        'establishment_name': '',
        'owner_operator': '',
        'address': '',
        'inspector_name': session.get('inspector', 'Inspector'),
        'staff_complement': '',
        'occupants': '',
        'institution_type': '',
        'building_size': '',
        'telephone': '',
        'num_buildings': '',
        'critical_score': 0,
        'inspection_day': '',
        'inspection_month': '',
        'inspection_year': '',
        'inspector_code': '',
        'overall_score': 0,
        'compliance_result': '',
        'license_no': '',
        'registration_status': '',
        'purpose_of_visit': '',
        'action': '',
        'comments': '',
        'inspector_signature': '',
        'received_by': '',
        'scores': {}
    }
    return render_template('institutional_form.html', inspection=inspection, checklist=checklist)


@app.route('/submit_small_hotels', methods=['POST'])
def submit_small_hotels():
    if 'inspector' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.form
    conn = get_db_connection()
    c = conn.cursor()

    # Updated critical items list based on your corrected form
    critical_items = [
        '1b', '2a', '2e', '3a', '3d', '3f', '3h', '3i', '4a', '4b', '4c', '4d', '4e',
        '5a', '5b', '5c', '6a', '6b', '8b', '8c', '9a', '9b', '11a', '11c', '12a',
        '13a', '15a', '15b', '19a', '19b'
    ]

    # All possible item IDs from your form
    all_item_ids = [
        '1a', '1b', '1c', '1d', '1e', '1f', '1g', '1h',
        '2a', '2b', '2c', '2d', '2e',
        '3a', '3b', '3c', '3d', '3e', '3f', '3g', '3h', '3i',
        '4a', '4b', '4c', '4d', '4e', '4f', '4g',
        '5a', '5b', '5c', '5d', '5e', '5f',
        '6a', '6b',
        '7a', '7b', '7c', '7d', '7e', '7f', '7g',
        '8a', '8b', '8c',
        '9a', '9b', '9c',
        '10a', '10b', '10c', '10d', '10e',
        '11a', '11b', '11c',
        '12a', '12b', '12c', '12d',
        '13a', '13b',
        '14a', '14b',
        '15a', '15b',
        '16a',
        '17a', '17b',
        '18a',
        '19a', '19b',
        '20a'
    ]

    # Count total items and critical items
    total_critical_items = len(critical_items)  # 31 critical items
    total_items = len(all_item_ids)  # 62 total items

    # Calculate scores - item passes if error = 0 (no error)
    critical_items_passed = 0
    total_items_passed = 0

    for item_id in all_item_ids:
        error_value = int(data.get(f'error_{item_id}', 0) or 0)

        # Item passes if error = 0 (no error found)
        if error_value == 0:
            total_items_passed += 1

            if item_id in critical_items:
                critical_items_passed += 1

    # Calculate percentages
    critical_score = round((critical_items_passed / total_critical_items) * 100)
    overall_score = round((total_items_passed / total_items) * 100)

    # Insert inspection with ALL required fields
    c.execute('''
        INSERT INTO inspections (
            establishment_name, address, physical_location, inspector_name,
            inspection_date, comments, result, overall_score, critical_score,
            inspector_signature, manager_signature, received_by,
            photo_data, created_at, form_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
    ''', (
        data.get('establishment_name', ''),
        data.get('address', ''),
        data.get('physical_location', ''),
        data.get('inspector_name', ''),
        data.get('inspection_date', ''),
        data.get('comments', ''),
        'Pass' if overall_score >= 70 else 'Fail',
        overall_score,
        critical_score,
        data.get('inspector_signature', ''),
        data.get('manager_signature', ''),
        data.get('received_by', ''),
        data.get('photos', '[]'),
        'Small Hotel'
    ))
    inspection_id = c.lastrowid

    # Insert ALL checklist items to preserve form data
    for item_id in all_item_ids:
        c.execute('''
            INSERT INTO inspection_items (inspection_id, item_id, obser, error)
            VALUES (?, ?, ?, ?)
        ''', (
            inspection_id,
            item_id,
            data.get(f'obser_{item_id}', ''),
            data.get(f'error_{item_id}', '0')
        ))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Inspection submitted successfully",
        "inspection_id": inspection_id,
        "scores": {
            "critical": critical_score,
            "overall": overall_score
        }
    })


@app.route('/medical_officer')
def medical_officer():
    if 'medical_officer' not in session:
        return redirect(url_for('login'))
    return render_template('medical_officer.html')


@app.route('/dashboard')
def dashboard():
    # If admin is logged in, redirect to admin dashboard
    if 'admin' in session:
        return redirect(url_for('admin'))

    # If inspector not logged in, redirect to login
    if 'inspector' not in session:
        return redirect(url_for('login'))

    # Get inspector username from session
    username = session.get('inspector')

    # Get inspections with proper Pass/Fail calculation
    inspections = get_inspections_with_status()

    # Pass BOTH username and inspections to template
    return render_template('dashboard.html', username=username, inspections=inspections)


def get_inspections_with_status():
    """Get inspections with calculated Pass/Fail status"""
    conn = get_db_connection()
    c = conn.cursor()

    # Get all inspections and calculate status based on scores
    c.execute("""
        SELECT id, establishment_name, owner, address, license_no, inspector_name,
               inspection_date, inspection_time, type_of_establishment, purpose_of_visit,
               action, result, scores, comments, created_at, form_type, inspector_code,
               no_of_employees, food_inspected, food_condemned, overall_score, critical_score
        FROM inspections
        ORDER BY created_at DESC
    """)

    inspections = []
    for row in c.fetchall():
        inspection_data = {
            'id': row[0],
            'establishment_name': row[1] or '',
            'owner': row[2] or '',
            'address': row[3] or '',
            'license_no': row[4] or '',
            'inspector_name': row[5] or '',
            'inspection_date': row[6] or '',
            'inspection_time': row[7] or '',
            'type_of_establishment': row[8] or '',
            'purpose_of_visit': row[9] or '',
            'action': row[10] or '',
            'result': row[11] or '',
            'scores': row[12] or '',
            'comments': row[13] or '',
            'created_at': row[14] or '',
            'form_type': row[15] or '',
            'inspector_code': row[16] or '',
            'no_of_employees': row[17] or '',
            'food_inspected': row[18] or 0,
            'food_condemned': row[19] or 0,
            'overall_score': row[20] or 0,
            'critical_score': row[21] or 0
        }

        # Calculate Pass/Fail status if not already set
        if not inspection_data['result'] or inspection_data['result'] == 'N/A':
            overall_score = float(inspection_data['overall_score']) if inspection_data['overall_score'] else 0
            critical_score = float(inspection_data['critical_score']) if inspection_data['critical_score'] else 0

            # Different criteria for different form types
            if inspection_data['form_type'] == 'Food Establishment':
                if overall_score >= 70 and critical_score >= 70:
                    inspection_data['result'] = 'Pass'
                else:
                    inspection_data['result'] = 'Fail'
            elif inspection_data['form_type'] == 'Spirit Licence Premises':
                if overall_score >= 70 and critical_score >= 59:
                    inspection_data['result'] = 'Pass'
                else:
                    inspection_data['result'] = 'Fail'
            elif inspection_data['form_type'] == 'Swimming Pool':
                if overall_score >= 70:
                    inspection_data['result'] = 'Pass'
                else:
                    inspection_data['result'] = 'Fail'
            elif inspection_data['form_type'] == 'Small Hotel':
                if overall_score >= 70:
                    inspection_data['result'] = 'Pass'
                else:
                    inspection_data['result'] = 'Fail'
            elif inspection_data['form_type'] == 'Barbershop':
                if overall_score >= 70:
                    inspection_data['result'] = 'Satisfactory'
                else:
                    inspection_data['result'] = 'Unsatisfactory'
            elif inspection_data['form_type'] == 'Institutional Health':
                if overall_score >= 70 and critical_score >= 50:
                    inspection_data['result'] = 'Pass'
                else:
                    inspection_data['result'] = 'Fail'
            else:
                if overall_score >= 70:
                    inspection_data['result'] = 'Pass'
                else:
                    inspection_data['result'] = 'Fail'

        inspections.append(inspection_data)

    # Add meat processing inspections
    c.execute("""
        SELECT id, establishment_name, owner_operator, address, establishment_no, inspector_name,
               inspection_date, '' as inspection_time, '' as type_of_establishment, purpose_of_visit,
               action, result, '' as scores, comments, created_at, 'Meat Processing' as form_type,
               inspector_code, 0 as no_of_employees, 0 as food_inspected, 0 as food_condemned,
               overall_score, 0 as critical_score
        FROM meat_processing_inspections
        ORDER BY created_at DESC
    """)

    for row in c.fetchall():
        inspection_data = {
            'id': row[0],
            'establishment_name': row[1] or '',
            'owner': row[2] or '',
            'address': row[3] or '',
            'license_no': row[4] or '',
            'inspector_name': row[5] or '',
            'inspection_date': row[6] or '',
            'inspection_time': row[7] or '',
            'type_of_establishment': row[8] or '',
            'purpose_of_visit': row[9] or '',
            'action': row[10] or '',
            'result': row[11] or '',
            'scores': row[12] or '',
            'comments': row[13] or '',
            'created_at': row[14] or '',
            'form_type': row[15] or '',
            'inspector_code': row[16] or '',
            'no_of_employees': row[17] or '',
            'food_inspected': row[18] or 0,
            'food_condemned': row[19] or 0,
            'overall_score': row[20] or 0,
            'critical_score': row[21] or 0
        }
        inspections.append(inspection_data)

    # Sort all inspections by created_at in descending order
    inspections.sort(key=lambda x: x['created_at'] or '', reverse=True)

    conn.close()
    return inspections


@app.route('/fix_inspection_results')
def fix_inspection_results():
    """One-time fix to update all inspection results based on scores"""
    if 'admin' not in session and 'inspector' not in session:
        return "Access denied"

    conn = get_db_connection()
    c = conn.cursor()

    # Get all inspections that need status updates
    c.execute("""
        SELECT id, overall_score, critical_score, form_type, result
        FROM inspections 
        WHERE result IS NULL OR result = 'N/A' OR result = ''
    """)

    inspections_to_update = c.fetchall()
    updated_count = 0

    for row in inspections_to_update:
        inspection_id, overall_score, critical_score, form_type, current_result = row
        overall_score = float(overall_score) if overall_score else 0
        critical_score = float(critical_score) if critical_score else 0

        # Calculate new result based on form type
        if form_type == 'Food Establishment':
            new_result = 'Pass' if overall_score >= 70 and critical_score >= 70 else 'Fail'
        elif form_type == 'Spirit Licence Premises':
            new_result = 'Pass' if overall_score >= 70 and critical_score >= 59 else 'Fail'
        elif form_type == 'Swimming Pool':
            new_result = 'Pass' if overall_score >= 70 else 'Fail'
        elif form_type == 'Small Hotel':
            new_result = 'Pass' if overall_score >= 70 else 'Fail'
        elif form_type == 'Barbershop':
            new_result = 'Satisfactory' if overall_score >= 70 else 'Unsatisfactory'
        elif form_type == 'Institutional Health':
            new_result = 'Pass' if overall_score >= 70 and critical_score >= 50 else 'Fail'
        else:
            new_result = 'Pass' if overall_score >= 70 else 'Fail'

        # Update the database
        c.execute("UPDATE inspections SET result = ? WHERE id = ?", (new_result, inspection_id))
        updated_count += 1
        print(
            f"Updated inspection {inspection_id}: {form_type} - Overall: {overall_score}, Critical: {critical_score} → {new_result}")

    conn.commit()
    conn.close()

    return f"Updated {updated_count} inspection results! <a href='/dashboard'>Back to Dashboard</a>"



@app.route('/stats')
def get_stats():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM inspections")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Food Establishment'")
    food = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM residential_inspections")
    residential = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM burial_site_inspections")
    burial = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Spirit Licence Premises'")
    spirit_licence = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Swimming Pool'")
    swimming_pool = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Small Hotel'")
    small_hotels = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Barbershop'")
    barbershop = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Institutional Health'")
    institutional = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM meat_processing_inspections")
    meat_processing = c.fetchone()[0]
    conn.close()
    return jsonify({
        'total': total + residential + burial + meat_processing,  # Include all in total
        'food': food,
        'residential': residential,
        'burial': burial,
        'spirit_licence': spirit_licence,
        'swimming_pool': swimming_pool,
        'small_hotels': small_hotels,
        'barbershop': barbershop,
        'institutional': institutional,
        'meat_processing': meat_processing
    })

@app.route('/search', methods=['GET'])
def search():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '').lower()
    data = get_establishment_data()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, applicant_name, deceased_name FROM burial_site_inspections WHERE LOWER(applicant_name) LIKE ? OR LOWER(deceased_name) LIKE ?", (f'%{query}%', f'%{query}%'))
    burial_records = c.fetchall()
    c.execute("SELECT id, establishment_name, owner, license_no FROM inspections WHERE form_type = 'Barbershop' AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ? OR LOWER(license_no) LIKE ?)", (f'%{query}%', f'%{query}%', f'%{query}%'))
    barbershop_records = c.fetchall()
    conn.close()
    suggestions = []
    for establishment_name, owner, license_no, id in data:
        if query in (establishment_name or '').lower() or query in (owner or '').lower() or query in (license_no or '').lower():
            suggestions.append({'text': f"{establishment_name} (Owner: {owner}, License: {license_no})", 'id': id, 'type': 'food'})
    for id, applicant_name, deceased_name in burial_records:
        if query in (applicant_name or '').lower() or query in (deceased_name or '').lower():
            suggestions.append({'text': f"{deceased_name} (Applicant: {applicant_name})", 'id': id, 'type': 'burial'})
    for id, establishment_name, owner, license_no in barbershop_records:
        if query in (establishment_name or '').lower() or query in (owner or '').lower() or query in (license_no or '').lower():
            suggestions.append({'text': f"{establishment_name} (Owner: {owner}, License: {license_no})", 'id': id, 'type': 'barbershop'})
    return jsonify({'suggestions': suggestions})


@app.route('/search_residential', methods=['GET'])
def search_residential():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    query = request.args.get('term', '').lower()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, premises_name, owner, created_at, result 
        FROM residential_inspections 
        WHERE LOWER(premises_name) LIKE ? OR LOWER(owner) LIKE ? OR LOWER(created_at) LIKE ?
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))
    records = c.fetchall()
    suggestions = [{'id': row[0], 'premises_name': row[1], 'owner': row[2], 'created_at': row[3], 'result': row[4]} for row in records]
    conn.close()
    return jsonify({'suggestions': suggestions})

@app.route('/inspection/<int:id>')
def inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, establishment_name, owner, address, license_no, inspector_name, inspection_date, inspection_time, type_of_establishment, purpose_of_visit, action, result, scores, comments, created_at, form_type, inspector_code, no_of_employees, food_inspected, food_condemned, photo_data, received_by, inspector_signature FROM inspections WHERE id = ?", (id,))
    inspection = c.fetchone()
    conn.close()

    if inspection:
        scores = [int(float(x)) for x in inspection[12].split(',')] if inspection[12] else [0] * 45
        inspection_data = {
            'id': inspection[0],
            'establishment_name': inspection[1] or '',
            'owner': inspection[2] or '',
            'address': inspection[3] or '',
            'license_no': inspection[4] or '',
            'inspector_name': inspection[5] or '',
            'inspection_date': inspection[6] or '',
            'inspection_time': inspection[7] or '',
            'type_of_establishment': inspection[8] or '',
            'purpose_of_visit': inspection[9] or '',
            'action': inspection[10] or '',
            'result': inspection[11] or '',
            'scores': dict(zip(range(1, 46), scores)),
            'comments': inspection[13] or '',
            'inspector_signature': inspection[22] if len(inspection) > 22 else inspection[5] or '',
            'received_by': inspection[21] if len(inspection) > 21 else '',
            'overall_score': sum(score for score in scores if score > 0),
            'critical_score': sum(score for item, score in zip(FOOD_CHECKLIST_ITEMS, scores) if item.get('wt', 0) >= 4 and score > 0),
            'inspector_code': inspection[16] or '',
            'no_of_employees': inspection[17] or '',
            'food_inspected': float(inspection[18]) if inspection[18] else 0.0,
            'food_condemned': float(inspection[19]) if inspection[19] else 0.0,
            'form_type': inspection[15],
            'created_at': inspection[14] or '',
            'photo_data': inspection[20] if len(inspection) > 20 else '[]'
        }

        # Parse photos from JSON string to Python list
        import json
        photos = []
        if inspection_data.get('photo_data'):
            try:
                photos = json.loads(inspection_data.get('photo_data', '[]'))
            except:
                photos = []

        return render_template('inspection_detail.html', inspection=inspection_data, checklist=FOOD_CHECKLIST_ITEMS,
                              photo_data=photos)
    return "Inspection not found", 404

@app.route('/residential/inspection/<int:form_id>')
def residential_inspection(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    details = get_residential_inspection_details(form_id)
    if details:
        premises_name = details['premises_name']
        owner = details['owner']
        address = details['address']
        inspector_name = details['inspector_name']
        inspection_date = details['inspection_date']
        inspector_code = details['inspector_code']
        treatment_facility = details['treatment_facility']
        vector = details['vector']
        result = details['result']
        onsite_system = details['onsite_system']
        building_construction_type = details['building_construction_type']
        purpose_of_visit = details['purpose_of_visit']
        action = details['action']
        no_of_bedrooms = details['no_of_bedrooms']
        total_population = details['total_population']
        critical_score = details['critical_score']
        overall_score = details['overall_score']
        comments = details['comments']
        inspector_signature = details['inspector_signature']
        received_by = details['received_by']
        created_at = details['created_at']
        checklist_scores = details['checklist_scores']
    else:
        premises_name = owner = address = inspector_name = inspection_date = inspector_code = treatment_facility = vector = result = onsite_system = building_construction_type = purpose_of_visit = action = no_of_bedrooms = total_population = comments = inspector_signature = received_by = created_at = 'N/A'
        critical_score = overall_score = 0
        checklist_scores = {item['id']: '0' for item in RESIDENTIAL_CHECKLIST_ITEMS}

    # Parse photos from JSON string to Python list
    import json
    photos = []
    if details and details.get('photo_data'):
        try:
            photos = json.loads(details.get('photo_data', '[]'))
        except:
            photos = []

    return render_template('residential_inspection_details.html',
                          form_id=form_id,
                          premises_name=premises_name,
                          owner=owner,
                          address=address,
                          inspector_name=inspector_name,
                          inspection_date=inspection_date,
                          inspector_code=inspector_code,
                          treatment_facility=treatment_facility,
                          vector=vector,
                          result=result,
                          onsite_system=onsite_system,
                          building_construction_type=building_construction_type,
                          purpose_of_visit=purpose_of_visit,
                          action=action,
                          no_of_bedrooms=no_of_bedrooms,
                          total_population=total_population,
                          critical_score=critical_score,
                          overall_score=overall_score,
                          comments=comments,
                          inspector_signature=inspector_signature,
                          received_by=received_by,
                          created_at=created_at,
                          checklist=RESIDENTIAL_CHECKLIST_ITEMS,
                          checklist_scores=checklist_scores,
                          photo_data=photos)

@app.route('/meat_processing/inspection/<int:form_id>')
def meat_processing_inspection(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    details = get_meat_processing_inspection_details(form_id)
    if details:
        # Parse photos from JSON string to Python list
        import json
        photos = []
        if details.get('photo_data'):
            try:
                photos = json.loads(details.get('photo_data', '[]'))
            except:
                photos = []

        return render_template('meat_processing_inspection_details.html',
                              form_id=form_id,
                              establishment_name=details['establishment_name'],
                              owner_operator=details['owner_operator'],
                              address=details['address'],
                              inspector_name=details['inspector_name'],
                              establishment_no=details['establishment_no'],
                              overall_score=details['overall_score'],
                              food_contact_surfaces=details['food_contact_surfaces'],
                              water_samples=details['water_samples'],
                              product_samples=details['product_samples'],
                              types_of_products=details['types_of_products'],
                              staff_fhp=details['staff_fhp'],
                              staff_compliment=details.get('staff_compliment', 0),
                              water_public=details['water_public'],
                              water_private=details['water_private'],
                              type_processing=details['type_processing'],
                              type_slaughter=details['type_slaughter'],
                              purpose_of_visit=details['purpose_of_visit'],
                              inspection_date=details['inspection_date'],
                              inspector_code=details['inspector_code'],
                              result=details['result'],
                              telephone_no=details['telephone_no'],
                              registration_status=details['registration_status'],
                              action=details['action'],
                              comments=details['comments'],
                              inspector_signature=details['inspector_signature'],
                              received_by=details['received_by'],
                              created_at=details['created_at'],
                              checklist=MEAT_PROCESSING_CHECKLIST_ITEMS,
                              checklist_scores=details['checklist_scores'],
                              photo_data=photos)
    else:
        return "Inspection not found", 404

import logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/burial/inspection/<int:id>')
def burial_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    inspection = get_burial_inspection_details(id)
    if not inspection:
        logging.error(f"No burial inspection found for id: {id}")
        return "Not Found", 404
    inspection_data = {
        'id': inspection['id'],
        'inspection_date': inspection['inspection_date'],
        'applicant_name': inspection['applicant_name'],
        'deceased_name': inspection['deceased_name'],
        'burial_location': inspection['burial_location'],
        'site_description': inspection['site_description'],
        'proximity_water_source': inspection['proximity_water_source'],
        'proximity_perimeter_boundaries': inspection['proximity_perimeter_boundaries'],
        'proximity_road_pathway': inspection['proximity_road_pathway'],
        'proximity_trees': inspection['proximity_trees'],
        'proximity_houses_buildings': inspection['proximity_houses_buildings'],
        'proposed_grave_type': inspection['proposed_grave_type'],
        'general_remarks': inspection['general_remarks'],
        'inspector_signature': inspection['inspector_signature'],
        'received_by': inspection['received_by'],
        'created_at': inspection['created_at'],
        'photo_data': inspection.get('photo_data', '[]')
    }
    logging.debug(f"Rendering burial inspection detail for id: {id}")

    # Parse photos from JSON string to Python list
    import json
    photos = []
    if inspection_data.get('photo_data'):
        try:
            photos = json.loads(inspection_data.get('photo_data', '[]'))
        except:
            photos = []

    return render_template('burial_inspection_detail.html', inspection=inspection_data,
                          photo_data=photos)

# Replace ALL your PDF download functions with these exact form replicas


@app.route('/download_residential_pdf/<int:form_id>')
def download_residential_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    details = get_residential_inspection_details(form_id)
    if not details:
        return jsonify({'error': 'Inspection not found'}), 404

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # === EXACT TITLE MATCHING YOUR DETAILS PAGE ===
    y = height - 60
    p.setFont("Times-Bold", 18)
    p.drawCentredString(width / 2, y, "Residential & Non-Residential Inspection Report")
    y -= 50

    # === ALL DETAILS EXACTLY LIKE YOUR HTML ===
    p.setFont("Times-Bold", 14)
    label_x = 50
    value_x = 200
    line_spacing = 25

    # Premises Details
    p.drawString(label_x, y, "Name of Premises:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(details.get('premises_name', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Owner/Agent/Occupier:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(details.get('owner', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Address and Parish:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(details.get('address', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Inspector Name:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(details.get('inspector_name', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Inspection Date:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(details.get('inspection_date', '')))
    y -= line_spacing

    # Scores section
    y -= 20
    p.setFont("Times-Bold", 16)
    p.drawString(label_x, y, "Inspection Results:")
    y -= 30

    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, f"Critical Score: {details.get('critical_score', 0)}")
    y -= line_spacing

    p.drawString(label_x, y, f"Overall Score: {details.get('overall_score', 0)}")
    y -= line_spacing

    # Result
    result = details.get('result', 'N/A')
    result_color = colors.green if result == 'Pass' else colors.red
    p.setFillColor(result_color)
    p.drawString(label_x, y, f"Result: {result}")
    p.setFillColor(colors.black)
    y -= 40

    # Checklist Table
    if y < 400:  # Need room for table
        p.showPage()
        y = height - 50

    p.setFont("Times-Bold", 16)
    p.drawString(label_x, y, "Inspection Checklist")
    y -= 30

    # Table setup
    table_x = 50
    table_width = width - 100
    header_height = 20
    row_height = 15

    # Table header
    p.setLineWidth(1)
    p.rect(table_x, y - header_height, table_width, header_height)
    p.setFillColor(colors.lightgrey)
    p.rect(table_x, y - header_height, table_width, header_height, fill=1)

    p.setFillColor(colors.black)
    p.setFont("Times-Bold", 12)
    p.drawString(table_x + 10, y - 14, "Item")
    p.drawString(table_x + 60, y - 14, "Description")
    p.drawString(table_x + 400, y - 14, "Weight")
    p.drawString(table_x + 460, y - 14, "Score")

    y -= header_height

    # Checklist items
    checklist_scores = details.get('checklist_scores', {})

    for item in RESIDENTIAL_CHECKLIST_ITEMS:
        if y < 100:  # New page if needed
            p.showPage()
            y = height - 50

        score = checklist_scores.get(item['id'], 0)

        p.setFont("Times-Roman", 10)
        p.rect(table_x, y - row_height, table_width, row_height)

        p.drawString(table_x + 10, y - 10, str(item['id']))

        # Truncate long descriptions
        desc = item['desc'][:45] + "..." if len(item['desc']) > 45 else item['desc']
        p.drawString(table_x + 60, y - 10, desc)

        p.drawString(table_x + 405, y - 10, str(item['wt']))
        p.drawString(table_x + 465, y - 10, str(score))

        y -= row_height

    # Comments section
    if y < 120:
        p.showPage()
        y = height - 50

    y -= 30
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Inspector's Comments:")
    y -= 20

    comments = details.get('comments', 'No comments provided.')
    p.setFont("Times-Roman", 12)
    if len(comments) > 80:
        # Word wrap comments
        words = comments.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) < 65:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        for line in lines[:4]:  # Max 4 lines
            p.drawString(label_x, y, line)
            y -= 15
    else:
        p.drawString(label_x, y, comments)
        y -= 15

    # Signatures
    y -= 30
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Inspector's Signature:")
    p.setFont("Times-Roman", 14)
    p.drawString(label_x + 150, y, str(details.get('inspector_signature', '')))

    p.setFont("Times-Bold", 14)
    p.drawString(350, y, "Received by:")
    p.setFont("Times-Roman", 14)
    p.drawString(450, y, str(details.get('received_by', '')))

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=residential_inspection_{form_id}.pdf'
    return response


@app.route('/download_meat_processing_pdf/<int:form_id>')
def download_meat_processing_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    details = get_meat_processing_inspection_details(form_id)
    if not details:
        return jsonify({'error': 'Inspection not found'}), 404

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    y = height - 60
    p.setFont("Times-Bold", 16)
    p.drawCentredString(width / 2, y, "Ministry of Health")
    y -= 20
    p.setFont("Times-Bold", 14)
    p.drawCentredString(width / 2, y, "Meat Processing Plant and Slaughter Place Inspection Report")
    y -= 50

    # Details section
    p.setFont("Times-Bold", 12)
    label_x = 50
    value_x = 220
    line_spacing = 20

    # Basic Information
    p.drawString(label_x, y, "Name of Establishment:")
    p.setFont("Times-Roman", 12)
    p.drawString(value_x, y, str(details.get('establishment_name', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Owner/Operator:")
    p.setFont("Times-Roman", 12)
    p.drawString(value_x, y, str(details.get('owner_operator', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Address and Parish:")
    p.setFont("Times-Roman", 12)
    p.drawString(value_x, y, str(details.get('address', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Inspector Name:")
    p.setFont("Times-Roman", 12)
    p.drawString(value_x, y, str(details.get('inspector_name', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Inspection Date:")
    p.setFont("Times-Roman", 12)
    p.drawString(value_x, y, str(details.get('inspection_date', '')))
    y -= line_spacing

    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Establishment No.:")
    p.setFont("Times-Roman", 12)
    p.drawString(value_x, y, str(details.get('establishment_no', '')))
    y -= line_spacing

    # Lab Samples Section
    y -= 10
    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Lab Samples Taken:")
    y -= line_spacing

    p.setFont("Times-Roman", 11)
    p.drawString(label_x + 20, y, f"Food Contact Surfaces: {details.get('food_contact_surfaces', 0)}")
    p.drawString(label_x + 220, y, f"Water: {details.get('water_samples', 0)}")
    y -= line_spacing

    p.drawString(label_x + 20, y, f"Product Samples: {details.get('product_samples', 0)}")
    p.drawString(label_x + 220, y, f"Types of Products: {details.get('types_of_products', '')}")
    y -= line_spacing

    p.drawString(label_x + 20, y, f"Staff with FHP: {details.get('staff_fhp', 0)}")
    y -= line_spacing + 10

    # Water Source and Establishment Type
    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Water Source:")
    p.setFont("Times-Roman", 11)
    water_source = []
    if details.get('water_public'):
        water_source.append("Public")
    if details.get('water_private'):
        water_source.append("Private")
    p.drawString(value_x, y, ", ".join(water_source) if water_source else "N/A")
    y -= line_spacing

    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Type of Establishment:")
    p.setFont("Times-Roman", 11)
    est_types = []
    if details.get('type_processing'):
        est_types.append("Processing Plant")
    if details.get('type_slaughter'):
        est_types.append("Slaughter Place")
    p.drawString(value_x, y, ", ".join(est_types) if est_types else "N/A")
    y -= line_spacing + 10

    # Inspection Results
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Inspection Results:")
    y -= line_spacing + 5

    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, f"Overall Score: {details.get('overall_score', 0)}")
    y -= line_spacing

    result = details.get('result', 'N/A')
    result_color = colors.green if result == 'Satisfactory' else colors.red
    p.setFillColor(result_color)
    p.drawString(label_x, y, f"Result: {result}")
    p.setFillColor(colors.black)
    y -= line_spacing

    p.setFont("Times-Roman", 11)
    p.drawString(label_x, y, f"Purpose of Visit: {details.get('purpose_of_visit', 'N/A')}")
    y -= line_spacing
    p.drawString(label_x, y, f"Action: {details.get('action', 'N/A')}")
    y -= line_spacing
    p.drawString(label_x, y, f"Registration Status: {details.get('registration_status', 'N/A')}")
    y -= 40

    # Checklist Table
    if y < 400:
        p.showPage()
        y = height - 50

    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Inspection Checklist")
    y -= 25

    # Table setup
    table_x = 50
    table_width = width - 100
    header_height = 18
    row_height = 14

    # Table header
    p.setLineWidth(1)
    p.rect(table_x, y - header_height, table_width, header_height)
    p.setFillColor(colors.lightgrey)
    p.rect(table_x, y - header_height, table_width, header_height, fill=1)

    p.setFillColor(colors.black)
    p.setFont("Times-Bold", 10)
    p.drawString(table_x + 5, y - 12, "ID")
    p.drawString(table_x + 30, y - 12, "Description")
    p.drawString(table_x + 420, y - 12, "Wt")
    p.drawString(table_x + 455, y - 12, "Score")

    y -= header_height

    # Checklist items
    checklist_scores = details.get('checklist_scores', {})

    for item in MEAT_PROCESSING_CHECKLIST_ITEMS:
        if y < 80:
            p.showPage()
            y = height - 50

        score = checklist_scores.get(item['id'], 0)

        p.setFont("Times-Roman", 9)
        p.rect(table_x, y - row_height, table_width, row_height)

        p.drawString(table_x + 5, y - 10, str(item['id']))

        # Truncate long descriptions
        desc = item['desc'][:52] + "..." if len(item['desc']) > 52 else item['desc']
        p.drawString(table_x + 30, y - 10, desc)

        p.drawString(table_x + 425, y - 10, str(item['wt']))
        p.drawString(table_x + 460, y - 10, str(score))

        y -= row_height

    # Comments section
    if y < 120:
        p.showPage()
        y = height - 50

    y -= 30
    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Inspector's Comments:")
    y -= 18

    comments = details.get('comments', 'No comments provided.')
    p.setFont("Times-Roman", 10)
    if len(comments) > 80:
        # Word wrap comments
        words = comments.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) < 70:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        for line in lines[:4]:
            p.drawString(label_x, y, line)
            y -= 12
    else:
        p.drawString(label_x, y, comments)
        y -= 12

    # Signatures
    y -= 30
    p.setFont("Times-Bold", 12)
    p.drawString(label_x, y, "Inspector's Signature:")
    p.setFont("Times-Roman", 11)
    p.drawString(label_x + 130, y, str(details.get('inspector_signature', '')))

    p.setFont("Times-Bold", 12)
    p.drawString(350, y, "Received by:")
    p.setFont("Times-Roman", 11)
    p.drawString(440, y, str(details.get('received_by', '')))

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=meat_processing_inspection_{form_id}.pdf'
    return response


# Replace your existing download_burial_pdf function with this exact replica
@app.route('/download_burial_pdf/<int:form_id>')
def download_burial_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    inspection = get_burial_inspection_details(form_id)
    if not inspection:
        return jsonify({'error': 'Inspection not found'}), 404

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # === EXACT TITLE MATCHING YOUR DETAILS PAGE ===
    y = height - 60
    p.setFont("Times-Bold", 18)
    p.drawCentredString(width / 2, y, "Burial Site Inspection Report")
    y -= 50

    # === ALL DETAILS EXACTLY LIKE YOUR HTML ===
    p.setFont("Times-Bold", 14)
    label_x = 50
    value_x = 200
    line_spacing = 25

    # Date of Inspection
    p.drawString(label_x, y, "Date of Inspection:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(inspection.get('inspection_date', '')))
    y -= line_spacing

    # Name of Applicant
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Name of Applicant:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(inspection.get('applicant_name', '')))
    y -= line_spacing

    # Name of Deceased
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Name of Deceased:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(inspection.get('deceased_name', '')))
    y -= line_spacing

    # Location of Burial Spot
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Location of Burial Spot:")
    p.setFont("Times-Roman", 14)
    p.drawString(value_x, y, str(inspection.get('burial_location', '')))
    y -= line_spacing

    # Brief description of site
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Brief description of site (e.g. topography etc.):")
    y -= 20
    p.setFont("Times-Roman", 14)

    # Handle multi-line site description
    site_desc = str(inspection.get('site_description', ''))
    if site_desc:
        # Word wrap the description
        words = site_desc.split()
        lines = []
        current_line = ""
        max_width = 65  # characters per line

        for word in words:
            if len(current_line + word) < max_width:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        for line in lines[:3]:  # Max 3 lines
            p.drawString(label_x, y, line)
            y -= 18
    else:
        p.drawString(label_x, y, "")
        y -= 18

    y -= 10

    # === PROXIMITY SECTION EXACTLY LIKE YOUR HTML ===
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Proximity to:")
    y -= 25

    # Bullet points exactly like your HTML
    p.setFont("Times-Roman", 14)
    bullet_x = 80
    proximity_items = [
        f"Water Source/or water ways (≥30m): {inspection.get('proximity_water_source', '')} metres",
        f"Perimeter Boundaries (≥3m): {inspection.get('proximity_perimeter_boundaries', '')} metres",
        f"Road or pathway (≥6m): {inspection.get('proximity_road_pathway', '')} metres",
        f"Trees (≥3m): {inspection.get('proximity_trees', '')} metres",
        f"Houses/Buildings (≥3m): {inspection.get('proximity_houses_buildings', '')} metres"
    ]

    for item in proximity_items:
        # Draw bullet point
        p.drawString(bullet_x - 10, y, "•")
        p.drawString(bullet_x, y, item)
        y -= 20

    y -= 10

    # Proposed type of grave
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Proposed type of grave to be built:")
    p.setFont("Times-Roman", 14)
    p.drawString(label_x + 280, y, str(inspection.get('proposed_grave_type', '')))
    y -= line_spacing

    # General Remarks
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "General Remarks:")
    y -= 20
    p.setFont("Times-Roman", 14)

    remarks = str(inspection.get('general_remarks', '') or 'None')
    if remarks and len(remarks) > 60:
        # Word wrap remarks
        words = remarks.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) < 65:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        for line in lines[:3]:
            p.drawString(label_x, y, line)
            y -= 18
    else:
        p.drawString(label_x, y, remarks)
        y -= 18

    y -= 15

    # === INSTRUCTIONS SECTION EXACTLY LIKE YOUR HTML ===
    p.setFont("Times-Italic", 14)
    p.drawString(label_x, y, "Please be guided by the following instructions:")
    y -= 25

    # Instructions bullet points
    p.setFont("Times-Roman", 14)
    instructions = [
        "No Sepulchre should be constructed,",
        "The depth of the grave should be at least 42 inches or (1.1 meters) from the top of the coffin to the top of the grave,",
        "Any change(s) to the recommended site should be communicated to the Public Health Inspector for approval before construction of grave,",
        "Any other instructions given by the Public Health Inspector."
    ]

    for instruction in instructions:
        # Draw bullet
        p.drawString(bullet_x - 10, y, "•")

        # Handle long instructions with word wrapping
        if len(instruction) > 65:
            words = instruction.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line + word) < 55:  # Shorter for indented text
                    current_line += word + " "
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())

            # First line with bullet
            p.drawString(bullet_x, y, lines[0] if lines else "")
            y -= 18

            # Continuation lines indented
            for line in lines[1:]:
                p.drawString(bullet_x + 10, y, line)
                y -= 18
        else:
            p.drawString(bullet_x, y, instruction)
            y -= 18

        y -= 5  # Extra space between instructions

    # === FAILURE NOTICE EXACTLY LIKE YOUR HTML ===
    y -= 10
    p.setFont("Times-Bold", 14)

    failure_text = "Failure to comply with the above or any other instructions given by the Public Health Inspector constitute a breach and is therefore liable for prosecution."

    # Word wrap the failure notice
    words = failure_text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + word) < 65:
            current_line += word + " "
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())

    for line in lines:
        p.drawString(label_x, y, line)
        y -= 18

    y -= 20

    # === SIGNATURES SECTION EXACTLY LIKE YOUR HTML ===
    if y < 100:  # New page if needed
        p.showPage()
        y = height - 50

    p.setFont("Times-Bold", 14)

    # Inspector's Signature (left side)
    p.drawString(label_x, y, "Inspector's Signature:")
    p.setFont("Times-Roman", 14)
    p.drawString(label_x + 150, y, str(inspection.get('inspector_signature', '')))

    # Received by (right side)
    p.setFont("Times-Bold", 14)
    p.drawString(350, y, "Received by:")
    p.setFont("Times-Roman", 14)
    p.drawString(450, y, str(inspection.get('received_by', '')))

    y -= 30

    # Created At
    p.setFont("Times-Bold", 14)
    p.drawString(label_x, y, "Created At:")
    p.setFont("Times-Roman", 14)
    p.drawString(label_x + 80, y, str(inspection.get('created_at', '')))

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=burial_site_inspection_{form_id}.pdf'
    return response


@app.route('/download_swimming_pool_pdf/<int:form_id>')
def download_swimming_pool_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Swimming Pool'", (form_id,))
    inspection = cursor.fetchone()

    if not inspection:
        conn.close()
        return jsonify({'error': 'Inspection not found'}), 404

    inspection_dict = dict(inspection)

    # Get individual scores
    cursor.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (form_id,))
    item_scores = {row[0]: float(row[1]) if row[1] and str(row[1]).replace('.', '', 1).isdigit() else 0.0
                   for row in cursor.fetchall()}
    conn.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # === EXACT HTML HEADER REPLICA ===
    y = height - 50
    p.setFont("Helvetica-Bold", 26)
    p.setFillColor(colors.Color(0, 155 / 255, 58 / 255))
    p.drawCentredString(width / 2, y, "Swimming Pool Inspection Details")
    y -= 30

    # Score box exactly like HTML
    p.setFont("Helvetica-Bold", 18)
    score_text = f"Score: {inspection_dict.get('overall_score', 0)}%"
    p.drawCentredString(width / 2, y, score_text)
    y -= 50

    # === TOP INFO TABLE - EXACT HTML STRUCTURE ===
    p.setFont("Helvetica", 10)
    p.setLineWidth(1)
    p.setStrokeColor(colors.black)

    # Table borders and structure exactly like HTML
    table_y = y
    row_height = 30

    # Draw table border
    p.rect(50, table_y - 90, width - 100, 90)

    # Row 1
    current_y = table_y - 25
    # Vertical lines for columns
    p.line(150, table_y, 150, table_y - 90)  # After "Operator"
    p.line(300, table_y, 300, table_y - 90)  # After value
    p.line(400, table_y, 400, table_y - 90)  # After "Date"
    p.line(500, table_y, 500, table_y - 90)  # After date value

    # Horizontal lines
    p.line(50, table_y - 30, width - 50, table_y - 30)  # After row 1
    p.line(50, table_y - 60, width - 50, table_y - 60)  # After row 2

    # Content
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, current_y, "Operator")
    p.setFont("Helvetica", 10)
    p.drawString(160, current_y, str(inspection_dict.get('establishment_name', '')))

    p.setFont("Helvetica-Bold", 10)
    p.drawString(310, current_y, "Date Inspection")
    p.setFont("Helvetica", 10)
    p.drawString(410, current_y, str(inspection_dict.get('inspection_date', '')))

    p.setFont("Helvetica-Bold", 10)
    p.drawString(510, current_y, "Inspector's Id")

    # Row 2
    current_y -= 30
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, current_y, "Pool Class")
    p.setFont("Helvetica", 10)
    p.drawString(160, current_y, str(inspection_dict.get('type_of_establishment', '')))

    p.setFont("Helvetica-Bold", 10)
    p.drawString(310, current_y, "Address")
    p.setFont("Helvetica", 10)
    # Address spans multiple columns
    address_text = str(inspection_dict.get('address', ''))
    if len(address_text) > 30:
        address_text = address_text[:27] + "..."
    p.drawString(370, current_y, address_text)

    # Row 3
    current_y -= 30
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, current_y, "Physical Location")
    p.setFont("Helvetica", 10)
    phys_loc = str(inspection_dict.get('physical_location', ''))
    if len(phys_loc) > 50:
        phys_loc = phys_loc[:47] + "..."
    p.drawString(200, current_y, phys_loc)

    y = current_y - 50

    # === CHECKLIST TABLE - EXACT HTML STRUCTURE ===

    # Define swimming pool checklist exactly as in your HTML
    swimming_pool_data = [
        # Category headers and items exactly matching your HTML
        ("1 - Documentation (15%)", "category"),
        ("A", "Written procedures for microbiological monitoring of pool water implemented", "1A", True),
        ("B", "Microbiological results", "1B", False),
        ("C", "Date of last testing within required frequency", "1C", False),
        ("D", "Acceptable monitoring procedures", "1D", True),
        ("E", "Daily log books and records up-to-date", "1E", False),
        ("F", "Written emergency procedures established and implemented", "1F", True),
        ("G", "Personal liability and accident insurance", "1G", True),
        ("H", "Lifeguard/Lifesaver certification", "1H", True),

        ("2 - Physical condition of pool (10%)", "category"),
        ("A", "Defects in pool construction", "2A", False),
        ("B", "Evidence of flaking paint and/or mould growth", "2B", False),
        ("C", "All surfaces of the deck and pool free from obstruction that can cause accident/injury", "2C", True),
        ("D", "Exposed piping: - identified/colour coded", "2D", False),
        ("E", "In good repair", "2E", False),
        ("F", "Suction fittings/inlets: - in good repair", "2F", False),
        ("G", "At least two suction orifices equipped with anti-vortex plates", "2G", True),
        ("H", "Perimeter drains free of debris", "2H", False),
        ("I", "Pool walls and floor clean", "2I", False),
        ("J", "Components of the re-circulating system maintained", "2J", False),

        ("3 - Pool chemistry (20%)", "category"),
        ("A", "Clarity", "3A", True),
        ("B", "Chlorine residual > 0.5 mg/l", "3B", True),
        ("C", "pH value within range of 7.5 and 7.8", "3C", True),
        ("D", "Well supplied and equipped", "3D", False),

        ("4 - Pool chemicals (10%)", "category"),
        ("A", "Pool chemicals - stored safely", "4A", True),
        ("B", "Dispensed automatically or in a safe manner", "4B", False),

        ("5 - Safety (10%)", "category"),
        ("A", "Depth markings clearly visible", "5A", False),
        ("B", "Working emergency phone", "5B", False),

        ("6 - Safety Aids (10%)", "category"),
        ("A", "Reaching poles with hook", "6A", False),
        ("B", "Two throwing aids", "6B", False),
        ("C", "Spine board with cervical collar", "6C", False),
        ("D", "Well equipped first aid kit", "6D", False),

        ("7 - Signs and notices (5%)", "category"),
        ("A", "Caution notices: - pool depth indications", "7A", False),
        ("B", "Public health notices", "7B", False),
        ("C", "Emergency procedures", "7C", False),
        ("D", "Maximum bathing load", "7D", False),
        ("E", "Lifeguard on duty/bathe at your own risk signs", "7E", False),

        ("8 - Lifeguards/Lifesavers (10%)", "category"),
        ("A", "Licensed Lifeguards always on duty during pool opening hours", "8A", False),
        ("B", "If N/A, trained lifesavers readily available", "8B", True),
        ("C", "Number of lifeguard/lifesavers", "8C", False),

        ("9 - Sanitary facilities (10%)", "category"),
        ("A", "Shower, toilet and dressing rooms: - clean and disinfected as required", "9A", True),
        ("B", "Vented", "9B", False),
        ("C", "Well supplied and equipped", "9C", False)
    ]

    # Draw clean table exactly like HTML
    table_start_y = y
    row_height = 20

    # Table column widths exactly matching HTML
    col1_width = 40  # Item
    col2_width = 350  # Details
    col3_width = 70  # Score
    col4_width = 50  # Points
    table_width = col1_width + col2_width + col3_width + col4_width

    # Draw outer table border
    p.setLineWidth(1)
    p.setStrokeColor(colors.black)

    current_y = table_start_y

    for item in swimming_pool_data:
        if current_y < 100:  # New page if needed
            p.showPage()
            current_y = height - 50

        if item[1] == "category":
            # Category header - exact styling from HTML
            p.setFillColor(colors.Color(255 / 255, 210 / 255, 0))  # #ffd200
            p.rect(50, current_y - row_height, table_width, row_height, fill=1)

            p.setFillColor(colors.Color(0, 155 / 255, 58 / 255))  # #009b3a
            p.setFont("Helvetica-Bold", 12)
            p.drawString(60, current_y - 14, item[0].upper())

            # Category border
            p.setStrokeColor(colors.black)
            p.rect(50, current_y - row_height, table_width, row_height)

            current_y -= row_height
            continue

        # Regular item row
        item_letter = item[0]
        description = item[1]
        score_key = item[2]
        is_critical = item[3] if len(item) > 3 else False

        # Get score value
        score = inspection_dict.get(f'score_{score_key}', 0)
        if not score:
            score = item_scores.get(score_key, 0)
        score = float(score) if score else 0

        # Critical item background (light green like HTML)
        if is_critical:
            p.setFillColor(colors.Color(0, 155 / 255, 58 / 255, 0.2))
            p.rect(50, current_y - row_height, table_width, row_height, fill=1)

        # Row border
        p.setFillColor(colors.black)
        p.setStrokeColor(colors.black)
        p.rect(50, current_y - row_height, table_width, row_height)

        # Column dividers
        p.line(50 + col1_width, current_y, 50 + col1_width, current_y - row_height)
        p.line(50 + col1_width + col2_width, current_y, 50 + col1_width + col2_width, current_y - row_height)
        p.line(50 + col1_width + col2_width + col3_width, current_y, 50 + col1_width + col2_width + col3_width,
               current_y - row_height)

        # Content with proper alignment
        p.setFont("Helvetica", 10)

        # Item letter (centered)
        p.drawCentredString(50 + col1_width / 2, current_y - 12, item_letter)

        # Description (left aligned with padding)
        desc_text = description
        if len(desc_text) > 50:
            desc_text = desc_text[:47] + "..."
        p.drawString(55 + col1_width, current_y - 12, desc_text)

        # Score status (Yes/No) - centered
        status = "Yes" if score > 0 else "No"
        status_color = colors.Color(0, 155 / 255, 58 / 255) if score > 0 else colors.Color(211 / 255, 47 / 255,
                                                                                           47 / 255)
        p.setFillColor(status_color)
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(50 + col1_width + col2_width + col3_width / 2, current_y - 12, status)

        # Points (centered)
        p.setFillColor(colors.Color(0, 155 / 255, 58 / 255))
        p.setFont("Helvetica", 9)
        p.drawCentredString(50 + col1_width + col2_width + col3_width + col4_width / 2, current_y - 12, f"({score})")

        current_y -= row_height

    # === SCORES SECTION - EXACT HTML LAYOUT ===
    current_y -= 20

    if current_y < 150:
        p.showPage()
        current_y = height - 50

    # Score boxes side by side exactly like HTML
    critical_score = inspection_dict.get('critical_score', 0)
    overall_score = inspection_dict.get('overall_score', 0)

    # Critical Score box
    p.setLineWidth(2)
    p.setStrokeColor(colors.black)
    p.rect(150, current_y - 60, 120, 50)
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawCentredString(210, current_y - 25, "Critical Score:")
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(210, current_y - 45, f"{critical_score}%")

    # Overall Score box
    p.rect(300, current_y - 60, 120, 50)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(360, current_y - 25, "Overall Score:")
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(360, current_y - 45, f"{overall_score}%")

    current_y -= 80

    # Result box
    result = inspection_dict.get('result', 'Unknown')
    result_color = colors.Color(0.8, 1.0, 0.8) if result == 'Pass' else colors.Color(1.0, 0.8, 0.8)
    p.setFillColor(result_color)
    p.rect(250, current_y - 40, 100, 30, fill=1)
    p.setStrokeColor(colors.black)
    p.rect(250, current_y - 40, 100, 30)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(300, current_y - 30, "Result:")
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(300, current_y - 20, result)

    current_y -= 60

    # === COMMENTS SECTION - EXPANDED FOR FULL VISIBILITY ===
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawString(50, current_y, "Inspector's Comments:")
    current_y -= 20

    # Larger comments box with proper word wrapping
    comments_height = 100
    p.setLineWidth(1)
    p.setStrokeColor(colors.black)
    p.rect(50, current_y - comments_height, width - 100, comments_height)

    # Get comments from multiple possible fields
    comments = (inspection_dict.get('inspector_comments') or
                inspection_dict.get('comments') or
                'No comments provided.')

    p.setFont("Helvetica", 10)

    if comments and comments.strip() and comments != 'No comments provided.':
        # Proper word wrapping for longer comments
        words = str(comments).split()
        lines = []
        current_line = ""
        max_chars_per_line = 85

        for word in words:
            if len(current_line + " " + word) <= max_chars_per_line:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Draw each line with proper spacing
        line_y = current_y - 15
        for i, line in enumerate(lines[:6]):  # Show up to 6 lines
            if line_y > current_y - comments_height + 10:  # Stay within box
                p.drawString(55, line_y, line)
                line_y -= 12
            else:
                break
    else:
        p.drawString(55, current_y - 25, "No comments provided.")

    current_y -= comments_height + 20

    # === SIGNATURES - EXACT HTML TABLE LAYOUT ===
    if current_y < 100:
        p.showPage()
        current_y = height - 50

    # Three column signature layout exactly like HTML
    sig_width = (width - 100) / 3

    # Draw signature table borders
    p.setLineWidth(1)
    p.rect(50, current_y - 60, width - 100, 60)
    p.line(50 + sig_width, current_y, 50 + sig_width, current_y - 60)
    p.line(50 + 2 * sig_width, current_y, 50 + 2 * sig_width, current_y - 60)
    p.line(50, current_y - 30, width - 50, current_y - 30)

    # Headers
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(50 + sig_width / 2, current_y - 15, "Inspector Signature")
    p.drawCentredString(50 + 1.5 * sig_width, current_y - 15, "Manager Signature")
    p.drawCentredString(50 + 2.5 * sig_width, current_y - 15, "Received By")

    # Values
    p.setFont("Helvetica", 9)
    p.drawCentredString(50 + sig_width / 2, current_y - 45, str(inspection_dict.get('inspector_signature', '')))
    p.drawCentredString(50 + 1.5 * sig_width, current_y - 45, str(inspection_dict.get('manager_signature', '')))
    p.drawCentredString(50 + 2.5 * sig_width, current_y - 45, str(inspection_dict.get('received_by', '')))

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=swimming_pool_inspection_{form_id}.pdf'
    return response

@app.route('/download_institutional_pdf/<int:form_id>')
def download_institutional_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT * FROM inspections WHERE id = ? AND form_type = 'Institutional Health'""", (form_id,))
    form_data = c.fetchone()

    if not form_data:
        conn.close()
        return jsonify({'error': 'Inspection not found'}), 404

    # Get individual scores from inspection_items table
    c.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (form_id,))
    checklist_scores = {str(row[0]): float(row[1]) if row[1] and str(row[1]).replace('.', '', 1).isdigit() else 0.0
                        for row in c.fetchall()}
    conn.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # === EXACT TITLE MATCHING YOUR DETAILS PAGE ===
    y = height - 50
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, y, "Ministry of Health")
    y -= 25
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, y, "Institutional Health Inspection Form")
    y -= 40

    # === MAIN INFORMATION SECTION - PROPER 2-COLUMN LAYOUT ===
    p.setLineWidth(1)

    # Draw border around the entire information section
    info_section_height = 120
    p.rect(50, y - info_section_height, width - 100, info_section_height)

    # Column positioning - wider separation
    left_x = 70
    right_x = 350
    field_width = 200
    row_height = 35

    p.setFont("Helvetica", 11)

    # Row 1: Name of Establishment | Owner/Operator
    current_y = y - 25
    p.drawString(left_x, current_y, "Name of Establishment:")
    p.rect(left_x, current_y - 20, field_width, 15)
    p.drawString(left_x + 5, current_y - 12, str(form_data['establishment_name'] or ''))

    p.drawString(right_x, current_y, "Owner/Operator:")
    p.rect(right_x, current_y - 20, field_width - 50, 15)
    p.drawString(right_x + 5, current_y - 12, str(form_data['owner'] or ''))

    # Row 2: Address and Parish | Inspector Name
    current_y -= row_height
    p.drawString(left_x, current_y, "Address and Parish:")
    p.rect(left_x, current_y - 20, field_width, 15)
    p.drawString(left_x + 5, current_y - 12, str(form_data['address'] or ''))

    p.drawString(right_x, current_y, "Inspector Name:")
    p.rect(right_x, current_y - 20, field_width - 50, 15)
    p.drawString(right_x + 5, current_y - 12, str(form_data['inspector_name'] or ''))

    # Row 3: Critical Score | Overall Score
    current_y -= row_height
    p.drawString(left_x, current_y, "Critical Sc.:")
    p.rect(left_x + 80, current_y - 20, 60, 15)
    p.drawString(left_x + 85, current_y - 12, str(form_data['critical_score'] or '0'))

    p.drawString(right_x, current_y, "Overall Sc.:")
    p.rect(right_x + 80, current_y - 20, 60, 15)
    p.drawString(right_x + 85, current_y - 12, str(form_data['overall_score'] or '0'))

    y = y - info_section_height - 10

    # === INSTITUTIONAL DETAILS SECTION ===
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "INSTITUTIONAL DETAILS")
    y -= 25

    # 3-column layout for institutional details
    col1_x, col2_x, col3_x = 50, 230, 410
    detail_y = y

    institutional_details = [
        ("Staff Complement:", form_data['staff_complement'] or 'N/A'),
        ("Building Size:",
         f"{form_data['building_size_value'] or 'N/A'} {'ft²' if form_data['building_size_ft2'] else 'm²' if form_data['building_size_m2'] else ''}"),
        ("No. of Occupants:", form_data['num_occupants'] or 'N/A'),
        ("Telephone No.:", form_data['telephone_no'] or 'N/A'),
        ("Type of Institution:", form_data['institution_type'] or 'N/A'),
        ("No. of Building(s):", form_data['num_buildings'] or 'N/A')
    ]

    p.setFont("Helvetica", 10)
    for i in range(0, len(institutional_details), 3):  # 3 items per row
        row_details = institutional_details[i:i + 3]

        for j, (label, value) in enumerate(row_details):
            x_pos = [col1_x, col2_x, col3_x][j]
            p.drawString(x_pos, detail_y, label)
            p.drawString(x_pos, detail_y - 15, str(value))

        detail_y -= 40

    y = detail_y - 20

    # === INSPECTION AND COMPLIANCE INFO ===
    p.setFont("Helvetica", 11)

    # Left side - Inspection details
    p.drawString(50, y, f"Purpose of Visit: {form_data['purpose_of_visit'] or 'N/A'}")
    p.drawString(50, y - 20, f"Inspection Date: {form_data['inspection_date'] or 'N/A'}")
    p.drawString(50, y - 40, f"Inspector Code: {form_data['inspector_code'] or 'N/A'}")

    # Right side - Compliance details
    p.drawString(320, y, f"License No.: {form_data['license_no'] or 'N/A'}")
    p.drawString(320, y - 20, f"Registration Status: {form_data['registration_status'] or 'N/A'}")
    p.drawString(320, y - 40, f"Action: {form_data['action'] or 'NAI'}")

    y -= 70

    # === PASS/FAIL RESULT ===
    overall_score = float(form_data['overall_score']) if form_data['overall_score'] else 0
    critical_score = float(form_data['critical_score']) if form_data['critical_score'] else 0

    if overall_score >= 70 and critical_score >= 50:
        result_text = f"PASS: Overall Score = {overall_score}, Critical Score = {critical_score}"
        p.setFillColor(colors.green)
    else:
        result_text = f"FAIL: Overall Score = {overall_score} (needs 70+), Critical Score = {critical_score} (needs 50+)"
        p.setFillColor(colors.red)

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, result_text)
    p.setFillColor(colors.black)
    y -= 40

    # === INSPECTION CHECKLIST TABLE ===
    if y < 500:  # Need room for table
        p.showPage()
        y = height - 50

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Inspection Checklist")
    y -= 25

    # Table setup
    table_x = 50
    table_width = width - 100
    header_height = 20
    row_height = 14

    # Table header
    p.setLineWidth(1)
    p.rect(table_x, y - header_height, table_width, header_height)
    p.setFillColor(colors.lightgrey)
    p.rect(table_x, y - header_height, table_width, header_height, fill=1)

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(table_x + 10, y - 14, "Item")
    p.drawString(table_x + 50, y - 14, "Description")
    p.drawString(table_x + 400, y - 14, "Wt")
    p.drawString(table_x + 450, y - 14, "Score")

    y -= header_height

    # Define institutional checklist sections exactly like your form
    institutional_sections = [
        ("BUILDING", [
            {"id": "01", "desc": "Absence of overcrowding", "wt": 5, "critical": True},
            {"id": "02", "desc": "Structural Integrity", "wt": 2, "critical": False},
            {"id": "03", "desc": "Housekeeping", "wt": 2, "critical": False},
            {"id": "04", "desc": "Clean Floor", "wt": 1, "critical": False},
            {"id": "05", "desc": "Clean Walls", "wt": 1, "critical": False},
            {"id": "06", "desc": "Clean Ceiling", "wt": 1, "critical": False},
            {"id": "07", "desc": "Lighting", "wt": 1, "critical": False},
            {"id": "08", "desc": "Ventilation", "wt": 3, "critical": False}
        ]),
        ("WATER SUPPLY", [
            {"id": "09", "desc": "Adequacy", "wt": 5, "critical": True},
            {"id": "10", "desc": "Potability", "wt": 5, "critical": True}
        ]),
        ("EXCRETA DISPOSAL FACILITIES", [
            {"id": "11", "desc": "Sanitary excreta disposal", "wt": 5, "critical": True},
            {"id": "12", "desc": "Adequacy", "wt": 5, "critical": True}
        ]),
        ("FOOD HANDLING FACILITIES", [
            {"id": "13", "desc": "Food Storage", "wt": 5, "critical": True},
            {"id": "14", "desc": "Kitchen", "wt": 5, "critical": True},
            {"id": "15", "desc": "Dining Room", "wt": 5, "critical": True},
            {"id": "16", "desc": "Food handling practices", "wt": 5, "critical": True}
        ]),
        ("SOLID WASTE MANAGEMENT", [
            {"id": "17", "desc": "Storage", "wt": 5, "critical": True},
            {"id": "18", "desc": "Disposal", "wt": 5, "critical": True}
        ]),
        ("PESTS", [
            {"id": "19", "desc": "Absence", "wt": 5, "critical": True},
            {"id": "20", "desc": "Control system in place", "wt": 5, "critical": True}
        ]),
        ("COMPOUND", [
            {"id": "21", "desc": "General Cleanliness", "wt": 2, "critical": False},
            {"id": "22", "desc": "Drainage", "wt": 2, "critical": False},
            {"id": "23", "desc": "Protected from stray animals", "wt": 2, "critical": False},
            {"id": "24", "desc": "Vegetation", "wt": 2, "critical": False}
        ]),
        ("SAFETY MEASURES", [
            {"id": "25", "desc": "Provision for physically challenged", "wt": 2, "critical": False},
            {"id": "26", "desc": "Fire extinguishers", "wt": 5, "critical": True},
            {"id": "27", "desc": "Access to medical care", "wt": 2, "critical": False},
            {"id": "28", "desc": "First Aid available", "wt": 2, "critical": False},
            {"id": "29", "desc": "Emergency exit", "wt": 2, "critical": False},
            {"id": "30", "desc": "Veterinary certification of pets", "wt": 1, "critical": False}
        ]),
        ("REFRIGERATION FOR NON-FOOD", [
            {"id": "31", "desc": "Adequacy", "wt": 2, "critical": False}
        ])
    ]

    p.setFont("Helvetica", 8)

    for section_name, items in institutional_sections:
        # Check for new page
        if y < 80:
            p.showPage()
            y = height - 50
            # Redraw header
            p.setLineWidth(1)
            p.rect(table_x, y - header_height, table_width, header_height)
            p.setFillColor(colors.lightgrey)
            p.rect(table_x, y - header_height, table_width, header_height, fill=1)
            p.setFillColor(colors.black)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(table_x + 10, y - 14, "Item")
            p.drawString(table_x + 50, y - 14, "Description")
            p.drawString(table_x + 400, y - 14, "Wt")
            p.drawString(table_x + 450, y - 14, "Score")
            y -= header_height
            p.setFont("Helvetica", 8)

        # Section header
        p.setFillColor(colors.Color(0.9, 0.9, 0.9))
        p.rect(table_x, y - row_height, table_width, row_height, fill=1)
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 8)
        p.drawString(table_x + 10, y - 10, section_name)
        y -= row_height

        # Section items
        p.setFont("Helvetica", 8)
        for item in items:
            if y < 30:
                p.showPage()
                y = height - 50

            # Critical items get light background
            if item['critical']:
                p.setFillColor(colors.Color(0.95, 0.95, 0.95))
                p.rect(table_x, y - row_height, table_width, row_height, fill=1)

            # Row border
            p.setFillColor(colors.black)
            p.setLineWidth(0.5)
            p.rect(table_x, y - row_height, table_width, row_height)

            # Get score for this item
            score = checklist_scores.get(item['id'], 0)

            # Item content
            p.drawString(table_x + 10, y - 9, item['id'])

            # Truncate description if too long
            desc = item['desc']
            if len(desc) > 45:
                desc = desc[:42] + "..."
            p.drawString(table_x + 50, y - 9, desc)

            p.drawString(table_x + 405, y - 9, str(item['wt']))
            p.drawString(table_x + 455, y - 9, f"{score:.1f}")

            y -= row_height

        y -= 5  # Extra space between sections

    # === COMMENTS SECTION ===
    if y < 120:
        p.showPage()
        y = height - 50

    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Inspector's Comments:")
    y -= 20

    # Comments box
    comments_height = 60
    p.setLineWidth(1)
    p.rect(50, y - comments_height, width - 100, comments_height)

    p.setFont("Helvetica", 9)
    comments = form_data['comments'] or 'N/A'
    if comments and comments != 'N/A':
        # Word wrap comments
        lines = []
        words = comments.split()
        current_line = ""
        for word in words:
            if len(current_line + word) < 70:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        for i, line in enumerate(lines[:4]):  # Max 4 lines
            p.drawString(55, y - 15 - (i * 12), line)
    else:
        p.drawString(55, y - 25, "No comments provided.")

    y -= 80

    # === SIGNATURES SECTION ===
    p.setFont("Helvetica", 10)

    # Inspector signature (left)
    p.drawString(50, y, "Inspector's Signature:")
    p.line(160, y - 2, 280, y - 2)
    p.drawString(165, y, str(form_data['inspector_signature'] or ''))

    # Received by (right)
    p.drawString(350, y, "Rec'd By:")
    p.line(410, y - 2, 530, y - 2)
    p.drawString(415, y, str(form_data['received_by'] or ''))

    # Footer note
    y -= 30
    p.setFont("Helvetica", 8)
    p.drawString(50, y, "EHU (Rev. May 2002)")

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=institutional_health_inspection_{form_id}.pdf'
    return response


@app.route('/download_small_hotels_pdf/<int:form_id>')
def download_small_hotels_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    # Get the inspection data directly from database instead of calling the detail function
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Small Hotel'", (form_id,))
    inspection_row = cursor.fetchone()

    if not inspection_row:
        conn.close()
        return jsonify({'error': 'Inspection not found'}), 404

    inspection_dict = dict(inspection_row)

    # Get individual scores from inspection_items table
    cursor.execute("SELECT item_id, obser, error FROM inspection_items WHERE inspection_id = ?", (form_id,))
    items = cursor.fetchall()

    obser_scores = {}
    error_scores = {}
    for item in items:
        obser_scores[item[0]] = item[1] or '0'
        error_scores[item[0]] = item[2] or '0'

    conn.close()

    # Create the inspection object with all the data your PDF needs
    inspection = {
        'id': form_id,
        'establishment_name': inspection_dict.get('establishment_name', ''),
        'inspector_name': inspection_dict.get('inspector_name', ''),
        'address': inspection_dict.get('address', ''),
        'physical_location': inspection_dict.get('physical_location', ''),
        'inspection_date': inspection_dict.get('inspection_date', ''),
        'critical_score': int(inspection_dict.get('critical_score', 0)),
        'overall_score': int(inspection_dict.get('overall_score', 0)),
        'result': inspection_dict.get('result', 'Unknown'),
        'comments': inspection_dict.get('comments', ''),
        'inspector_signature': inspection_dict.get('inspector_signature', ''),
        'inspector_signature_date': inspection_dict.get('inspector_signature_date', ''),
        'manager_signature': inspection_dict.get('manager_signature', ''),
        'manager_signature_date': inspection_dict.get('manager_signature_date', ''),
        'received_by': inspection_dict.get('received_by', ''),
        'received_by_date': inspection_dict.get('received_by_date', ''),
        'obser': obser_scores,
        'error': error_scores
    }
    if not inspection:
        return jsonify({'error': 'Inspection not found'}), 404

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    def draw_table_header(p, table_x, y, table_width, item_width, details_width, obser_width, error_width,
                          header_height):
        """Helper function to draw table header"""
        p.setLineWidth(1)
        p.setFillColor(colors.Color(0.94, 0.94, 0.94))
        p.rect(table_x, y - header_height, table_width, header_height, fill=1)
        p.setFillColor(colors.black)
        p.rect(table_x, y - header_height, table_width, header_height)

        p.setFont("Helvetica-Bold", 11)
        p.drawCentredString(table_x + item_width / 2, y - 16, "Item")
        p.drawCentredString(table_x + item_width + details_width / 2, y - 16, "Details")
        p.drawCentredString(table_x + item_width + details_width + obser_width / 2, y - 16, "Obser")
        p.drawCentredString(table_x + item_width + details_width + obser_width + error_width / 2, y - 16, "Error")

        # Column separators
        p.line(table_x + item_width, y, table_x + item_width, y - header_height)
        p.line(table_x + item_width + details_width, y, table_x + item_width + details_width, y - header_height)
        p.line(table_x + item_width + details_width + obser_width, y,
               table_x + item_width + details_width + obser_width, y - header_height)

        return y - header_height

    # Start from top of page
    y = height - 40

    # Page number (top right)
    p.setFont("Helvetica", 12)
    p.drawString(width - 100, y, "Page 1 of 5")

    y -= 30

    # Header box
    header_height = 80
    header_width = width - 100
    header_x = 50

    p.setLineWidth(2)
    p.rect(header_x, y - header_height, header_width, header_height)

    # Form number (red)
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(colors.red)
    p.drawString(width - 140, y - 20, "NO. 58402")
    p.setFillColor(colors.black)

    # Centered title
    p.setFont("Helvetica-Bold", 18)
    title_y = y - 35
    p.drawCentredString(width / 2, title_y, "MINISTRY OF HEALTH")
    p.drawCentredString(width / 2, title_y - 20, "Small Hotels Inspection Form - Jamaica")

    y -= header_height + 30

    # Info section
    info_height = 25
    col_width = (width - 100) / 3
    gap = 5

    # Row 1
    row_y = y
    p.setLineWidth(1)
    p.rect(50, row_y - info_height, col_width - gap, info_height)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(55, row_y - 8, "Hotel Name")
    p.setFont("Helvetica", 11)
    hotel_name = str(inspection.get('establishment_name', ''))[:20]
    p.drawString(55, row_y - 20, hotel_name)

    date_x = 50 + col_width
    p.rect(date_x, row_y - info_height, col_width - gap, info_height)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(date_x + 5, row_y - 8, "Date")
    p.setFont("Helvetica", 11)
    p.drawString(date_x + 5, row_y - 20, str(inspection.get('inspection_date', '')))

    inspector_x = 50 + (2 * col_width)
    p.rect(inspector_x, row_y - info_height, col_width - gap, info_height)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(inspector_x + 5, row_y - 8, "Inspector's ID")
    p.setFont("Helvetica", 11)
    p.drawString(inspector_x + 5, row_y - 20, str(inspection.get('inspector_name', '')))

    # Row 2
    row_y -= info_height + 10
    address_width = (2 * col_width) - gap
    p.rect(50, row_y - info_height, address_width, info_height)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(55, row_y - 8, "Address")
    p.setFont("Helvetica", 11)
    address = str(inspection.get('address', ''))[:35]
    p.drawString(55, row_y - 20, address)

    phys_x = 50 + address_width + gap
    phys_width = col_width - gap
    p.rect(phys_x, row_y - info_height, phys_width, info_height)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(phys_x + 5, row_y - 8, "Physical Location")
    p.setFont("Helvetica", 11)
    phys_loc = str(inspection.get('physical_location', ''))[:12]
    p.drawString(phys_x + 5, row_y - 20, phys_loc)

    y = row_y - info_height - 40

    # Table setup
    table_x = 50
    table_width = width - 100
    item_width = int(table_width * 0.08)
    details_width = int(table_width * 0.62)
    obser_width = int(table_width * 0.15)
    error_width = int(table_width * 0.15)
    row_height = 18
    header_height = 25

    # Draw initial table header
    y = draw_table_header(p, table_x, y, table_width, item_width, details_width, obser_width, error_width,
                          header_height)

    # All sections with complete data
    sections_data = [
        ("1 - DOCUMENTATION (8%)", [
            ("A", "Action plan for foodborne illness occurrence", "1a", False),
            ("B", "Food Handlers have valid food handlers permits", "1b", True),
            ("C", "Relevant policy in place to restrict activities of sick employees", "1c", False),
            ("D", "Establishments have a written policy for the proper disposal of waste", "1d", False),
            ("E", "Cleaning schedule for equipment utensil etc available", "1e", False),
            ("F", "Material safety data sheet available for record of hazardous chemicals used", "1f", False),
            ("G", "Record of hazardous chemicals used", "1g", False),
            ("H", "Food suppliers list available", "1h", False),
        ]),
        ("2 - FOOD HANDLERS (5%)", [
            ("A", "Clean appropriate protective garments", "2a", True),
            ("B", "Hands free of jewellery", "2b", False),
            ("C", "Suitable hair restraints", "2c", False),
            ("D", "Nails clean, short and unpolished", "2d", False),
            ("E", "Hands washed as required", "2e", True),
        ]),
        ("3 - FOOD STORAGE (13%)", [
            ("A", "Approved source", "3a", True),
            ("B", "Correct stocking procedures practiced", "3b", False),
            ("C", "Food stored on pallets or shelves off the floor", "3c", False),
            ("D", "No cats, rodents or other animals present in the store", "3d", True),
            ("E", "Products free of infestation", "3e", False),
            ("F", "No pesticides or other hazardous chemicals in food stores", "3f", True),
            ("G", "Satisfactory condition of refrigeration units", "3g", False),
            ("H", "Refrigerated foods < 4°C", "3h", True),
            ("I", "Frozen foods -18°C", "3i", True),
        ]),
        ("4 - FOOD HOLDING AND PREPARATION PRACTICES (8%)", [
            ("A", "Foods thawed according to recommended procedures", "4a", True),
            ("B", "No evidence of cross-contamination during preparation", "4b", True),
            ("C", "No evidence of cross-contamination during holding in refrigerators/coolers", "4c", True),
            ("D", "Foods cooled according to recommended procedures", "4d", True),
            ("E", "Manual dishwashing wash, rinse, sanitize, rinse technique", "4e", True),
            ("F", "Food contact surfaces washed-rinsed-sanitized before & after each use", "4f", False),
            ("G", "Wiping cloths handled properly (sanitizing solution used)", "4g", False),
        ]),
        ("5 - POST PREPARATION (10%)", [
            ("A", "Food protected during transportation", "5a", True),
            ("B", "Dishes identified and labelled", "5b", True),
            ("C", "Food covered or protected from contamination", "5c", True),
            ("D", "Sufficient, appropriate utensils on service line", "5d", False),
            ("E", "Hot holding temperatures > 63°C", "5e", False),
            ("F", "Cold holding temperatures ≤ 5°C", "5f", False),
        ]),
        ("6 - HAND WASHING FACILITIES (3%)", [
            ("A",
             "Hand washing facility installed and maintained for every 40 square meters of floor space or in each principal food area",
             "6a", True),
            ("B", "Equipped with hot and cold water, soap dispenser and hand drying facility", "6b", True),
        ]),
        ("7 - BUILDING (8.5%)", [
            ("A", "Provides adequate space", "7a", False),
            ("B", "Food areas kept clean, free from vermin and unpleasant odours", "7b", False),
            ("C", "Floor, walls and ceiling clean, in good repair", "7c", False),
            ("D", "Mechanical ventilation operable where required", "7d", False),
            ("E", "Lighting adequate for food preparation and cleaning", "7e", False),
            ("F", "General housekeeping satisfactory", "7f", False),
            ("G", "Animals, insect and pest excluded", "7g", False),
        ]),
        ("8 - FOOD CONTACT SURFACES (3%)", [
            ("A", "Made from material which is non-absorbent and non-toxic", "8a", False),
            ("B", "Smooth, cleanable, corrosion resistant", "8b", True),
            ("C", "Proper storage and use of clean utensils", "8c", True),
        ]),
        ("9 - FOOD FLOW (5.5%)", [
            ("A", "Employee traffic pattern avoids food cross-contamination", "9a", True),
            ("B", "Product flow not at risk for cross-contamination", "9b", True),
            (
            "C", "Living quarters, toilets, washrooms, locker separated from areas where food is handled", "9c", False),
        ]),
        ("10 - EQUIPMENT AND UTENSILS SANITIZATION (9.5%)", [
            ("A", "Mechanical dishwashing: Wash-rinse water clean", "10a", False),
            ("B", "Proper water temperature", "10b", False),
            ("C", "Proper timing of cycles", "10c", False),
            ("D", "Sanitizer for low temperature", "10d", False),
            ("E", "Proper handling of hazardous materials", "10e", False),
        ]),
        ("11 - WASTE MANAGEMENT: WASTE CONTAINERS (3%)", [
            ("A", "Appropriate design, convenient placement", "11a", True),
            ("B", "Kept covered when not in continuous use", "11b", False),
            ("C", "Emptied as often as necessary", "11c", True),
        ]),
        ("12 - SOLID WASTE STORAGE AREA (4%)", [
            ("A", "Insect and vermin-proof containers provided where required", "12a", True),
            ("B", "The area around each waste container kept clean", "12b", False),
            ("C", "Effluent from waste bins disposed of in a sanitary manner", "12c", False),
            ("D", "Frequency of garbage removal adequate", "12d", False),
        ]),
        ("13 - DISPOSAL OF SOLID WASTE", [
            ("A", "Garbage, refuse properly disposed of, facilities maintained", "13a", True),
            ("B", "Stored away from living quarters and food areas", "13b", False),
        ]),
        ("14 - HAZARDOUS MATERIALS STORAGE, HANDLING AND DISPOSAL (4%)", [
            ("A", "Hazardous materials stored in properly labelled containers", "14a", False),
            ("B", "Stored away from living quarters and food areas", "14b", True),
        ]),
        ("15 - SANITARY FACILITIES (4%)", [
            ("A", "Approved Sewage Disposal System", "15a", True),
            ("B",
             "Sanitary maintenance of facilities and protection against the entrance of vermin, rodents, dust, and fumes",
             "15b", True),
        ]),
        ("16 - PEST CONTROL (2%)", [
            ("A", "Adequate provision against the entrance of insects, vermin, rodents, dust and fumes", "16a", False),
        ]),
        ("17 - WATER SUPPLY (3%)", [
            ("A", "Approved source(s) sufficient pressure and capacity", "17a", False),
            ("B", "Water quality satisfactory", "17b", False),
        ]),
        ("18 - ICE (1.5%)", [
            ("A", "Satisfactory ice storage conditions", "18a", False),
        ]),
        ("19 - GREY WATER FACILITIES (1%)", [
            ("A", "Traps and vent in good condition", "19a", True),
            ("B", "Floor drains clear and drain freely", "19b", True),
        ]),
        ("20 - MANHOLES (0.5%)", [
            ("A", "Properly constructed with vents and traps where necessary", "20a", False),
        ]),
    ]

    page_num = 1

    for section_name, items in sections_data:
        # Check for new page
        if y < 100:
            p.showPage()
            page_num += 1
            y = height - 50

            # Update page number
            p.setFont("Helvetica", 12)
            p.drawString(width - 100, y, f"Page {page_num} of 5")
            y -= 30

            # Redraw table header
            y = draw_table_header(p, table_x, y, table_width, item_width, details_width, obser_width, error_width,
                                  header_height)

        # Section header
        p.setFillColor(colors.white)
        p.rect(table_x, y - row_height, table_width, row_height, fill=1)
        p.setFillColor(colors.black)
        p.rect(table_x, y - row_height, table_width, row_height)

        p.setFont("Helvetica-Bold", 10)
        p.drawString(table_x + 10, y - 12, section_name)
        y -= row_height

        # Section items
        for item_letter, description, item_id, is_critical in items:
            if y < 30:
                p.showPage()
                page_num += 1
                y = height - 50

                p.setFont("Helvetica", 12)
                p.drawString(width - 100, y, f"Page {page_num} of 5")
                y -= 30

                y = draw_table_header(p, table_x, y, table_width, item_width, details_width, obser_width, error_width,
                                      header_height)

            # Critical item background
            if is_critical:
                p.setFillColor(colors.Color(0.9, 0.9, 0.9))
                p.rect(table_x, y - row_height, table_width, row_height, fill=1)

            p.setFillColor(colors.black)
            p.rect(table_x, y - row_height, table_width, row_height)

            # Column separators
            p.line(table_x + item_width, y, table_x + item_width, y - row_height)
            p.line(table_x + item_width + details_width, y, table_x + item_width + details_width, y - row_height)
            p.line(table_x + item_width + details_width + obser_width, y,
                   table_x + item_width + details_width + obser_width, y - row_height)

            # Content
            p.setFont("Helvetica", 9)
            p.drawCentredString(table_x + item_width / 2, y - 12, item_letter)

            desc = description[:45] + "..." if len(description) > 45 else description
            p.drawString(table_x + item_width + 5, y - 12, desc)

            # Get actual data
            obser_value = str(inspection.get('obser', {}).get(item_id, '0'))
            error_value = str(inspection.get('error', {}).get(item_id, '0'))

            p.drawCentredString(table_x + item_width + details_width + obser_width / 2, y - 12, obser_value)
            p.drawCentredString(table_x + item_width + details_width + obser_width + error_width / 2, y - 12,
                                error_value)

            y -= row_height

        y -= 8  # Space between sections

    # Final page for scores and signatures
    p.showPage()
    y = height - 100

    # Page number
    p.setFont("Helvetica", 12)
    p.drawString(width - 100, y, "Page 5 of 5")
    y -= 50

    # Scores section
    box_width = 180
    box_height = 60
    gap_between_boxes = 40
    total_width = (2 * box_width) + gap_between_boxes
    start_x = (width - total_width) / 2

    # Critical Score
    p.setLineWidth(2)
    p.rect(start_x, y - box_height, box_width, box_height)
    p.setFillColor(colors.Color(0.97, 0.97, 0.97))
    p.rect(start_x, y - box_height, box_width, box_height, fill=1)
    p.setFillColor(colors.black)

    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(start_x + box_width / 2, y - 20, "Critical Score:")
    p.setFont("Helvetica-Bold", 20)
    critical_score = f"{inspection.get('critical_score', 0)}%"
    p.drawCentredString(start_x + box_width / 2, y - 45, critical_score)

    # Overall Score
    overall_x = start_x + box_width + gap_between_boxes
    p.rect(overall_x, y - box_height, box_width, box_height)
    p.setFillColor(colors.Color(0.97, 0.97, 0.97))
    p.rect(overall_x, y - box_height, box_width, box_height, fill=1)
    p.setFillColor(colors.black)

    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(overall_x + box_width / 2, y - 20, "Overall Score:")
    p.setFont("Helvetica-Bold", 20)
    overall_score = f"{inspection.get('overall_score', 0)}%"
    p.drawCentredString(overall_x + box_width / 2, y - 45, overall_score)

    y -= box_height + 40

    # Result
    result = inspection.get('result', 'Unknown')
    result_width = 150
    result_height = 50
    result_x = (width - result_width) / 2

    result_color = colors.green if result == 'Pass' else colors.red

    p.setStrokeColor(result_color)
    p.setLineWidth(2)
    p.rect(result_x, y - result_height, result_width, result_height)

    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(result_color)
    p.drawCentredString(result_x + result_width / 2, y - 20, "RESULT:")
    p.drawCentredString(result_x + result_width / 2, y - 40, result)
    p.setFillColor(colors.black)

    y -= result_height + 40

    # Comments
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Inspector's Comments:")
    y -= 20

    comments_height = 60
    p.setLineWidth(1)
    p.rect(50, y - comments_height, width - 100, comments_height)

    comments = inspection.get('comments', 'No comments provided.')
    if comments:
        p.setFont("Helvetica", 10)
        # Simple word wrap
        words = comments.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= 70:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        comment_y = y - 15
        for line in lines[:3]:  # Max 3 lines
            p.drawString(55, comment_y, line)
            comment_y -= 15

    y -= comments_height + 30

    # Signatures
    sig_width = (width - 100) / 3
    sig_height = 60

    p.setLineWidth(1)
    p.rect(50, y - sig_height, width - 100, sig_height)
    p.line(50 + sig_width, y, 50 + sig_width, y - sig_height)
    p.line(50 + 2 * sig_width, y, 50 + 2 * sig_width, y - sig_height)
    p.line(50, y - 30, width - 50, y - 30)

    # Headers
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(50 + sig_width / 2, y - 15, "Inspector Signature")
    p.drawCentredString(50 + 1.5 * sig_width, y - 15, "Manager Signature")
    p.drawCentredString(50 + 2.5 * sig_width, y - 15, "Received By")

    # Signature values
    p.setFont("Helvetica", 9)
    p.drawCentredString(50 + sig_width / 2, y - 25, str(inspection.get('inspector_signature', '')))
    p.drawCentredString(50 + 1.5 * sig_width, y - 25, str(inspection.get('manager_signature', '')))
    p.drawCentredString(50 + 2.5 * sig_width, y - 25, str(inspection.get('received_by', '')))

    # Date labels and values
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(50 + sig_width / 2, y - 40, "Date")
    p.drawCentredString(50 + 1.5 * sig_width, y - 40, "Date")
    p.drawCentredString(50 + 2.5 * sig_width, y - 40, "Date")

    p.setFont("Helvetica", 8)
    p.drawCentredString(50 + sig_width / 2, y - 52, str(inspection.get('inspector_signature_date', '')))
    p.drawCentredString(50 + 1.5 * sig_width, y - 52, str(inspection.get('manager_signature_date', '')))
    p.drawCentredString(50 + 2.5 * sig_width, y - 52, str(inspection.get('received_by_date', '')))

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=small_hotels_inspection_{form_id}.pdf'
    return response


@app.route('/download_inspection_pdf/<int:form_id>')
def download_inspection_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    inspection = get_inspection_details(form_id)
    if not inspection:
        return jsonify({'error': 'Inspection not found'}), 404

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    def draw_barcode(p, x, y):
        barcode_width = 100
        barcode_height = 30
        p.setFillColor(colors.black)
        for i in range(0, barcode_width, 4):
            p.rect(x + i, y, 2, barcode_height, fill=1)
        p.setFillColor(colors.black)

    def draw_table_header(p, table_x, y, table_width, col_widths, header_height):
        p.setLineWidth(1)
        # Light gray header background to match HTML
        p.setFillColor(colors.Color(0.94, 0.94, 0.94))
        p.rect(table_x, y - header_height, table_width, header_height, fill=1)
        p.setFillColor(colors.black)
        p.rect(table_x, y - header_height, table_width, header_height)

        p.setFont("Helvetica-Bold", 11)
        p.drawCentredString(table_x + col_widths[0] / 2, y - 16, "Item #")
        p.drawCentredString(table_x + col_widths[0] + col_widths[1] / 2, y - 16, "Label")
        p.drawCentredString(table_x + col_widths[0] + col_widths[1] + col_widths[2] / 2, y - 16, "Weight")
        p.drawCentredString(table_x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] / 2, y - 16,
                            "Score")

        x_pos = table_x
        for width_col in col_widths[:-1]:
            x_pos += width_col
            p.line(x_pos, y, x_pos, y - header_height)

        return y - header_height

    # Start from top
    y = height - 40

    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width / 2, y, "Food Establishment Inspection - Completed")
    y -= 50

    # Establishment Details Section
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Establishment Details")
    y -= 30

    # 3-column grid layout
    col_width = (width - 100) / 3
    row_height = 50

    # All establishment details rows
    establishment_rows = [
        [("Name of Establishment:", inspection.get('establishment_name', '')),
         ("Owner/Operator:", inspection.get('owner', '')),
         ("Critical Score:", str(inspection.get('critical_score', '0')))],
        [("Address:", inspection.get('address', '')),
         ("License #:", inspection.get('license_no', '')),
         ("Overall Score:", str(inspection.get('overall_score', '0')))],
        [("Inspector Name:", inspection.get('inspector_name', '')),
         ("Inspector Code:", inspection.get('inspector_code', '')),
         ("Inspection Date:", inspection.get('inspection_date', ''))],
        [("Inspection Time:", inspection.get('inspection_time', '')),
         ("Type of Establishment:", inspection.get('type_of_establishment', '')),
         ("No. of Employees:", str(inspection.get('no_of_employees', '')))],
        [("Purpose of Visit:", inspection.get('purpose_of_visit', '')),
         ("Action:", inspection.get('action', '')),
         ("Result:", inspection.get('result', ''))],
        [("Barcode", "BARCODE"),
         ("Food Inspected (kg):", str(inspection.get('food_inspected', ''))),
         ("Food Condemned (kg):", str(inspection.get('food_condemned', '')))]
    ]

    current_y = y
    for row in establishment_rows:
        col1_x, col2_x, col3_x = 50, 50 + col_width, 50 + (2 * col_width)

        # Column 1
        p.setLineWidth(1)
        p.rect(col1_x, current_y - row_height, col_width - 5, row_height)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(col1_x + 5, current_y - 15, row[0][0])
        p.setFont("Helvetica", 10)

        if row[0][1] == "BARCODE":
            draw_barcode(p, col1_x + 5, current_y - 45)
        else:
            text = str(row[0][1])[:25]
            p.drawString(col1_x + 5, current_y - 35, text)

        # Column 2
        p.rect(col2_x, current_y - row_height, col_width - 5, row_height)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(col2_x + 5, current_y - 15, row[1][0])
        p.setFont("Helvetica", 10)
        text = str(row[1][1])[:25]
        p.drawString(col2_x + 5, current_y - 35, text)

        # Column 3
        p.rect(col3_x, current_y - row_height, col_width - 5, row_height)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(col3_x + 5, current_y - 15, row[2][0])

        if row[2][0] in ["Critical Score:", "Overall Score:"]:
            p.setFont("Helvetica-Bold", 14)
        else:
            p.setFont("Helvetica", 10)

        if row[2][0] == "Result:":
            result_color = colors.green if str(row[2][1]) == 'Satisfactory' else colors.red
            p.setFillColor(result_color)
            p.drawString(col3_x + 5, current_y - 35, str(row[2][1]))
            p.setFillColor(colors.black)
        else:
            text = str(row[2][1])[:25]
            p.drawString(col3_x + 5, current_y - 35, text)

        current_y -= row_height + 5

    # Score message
    critical_score_val = float(inspection.get('critical_score', 0))
    overall_score_val = float(inspection.get('overall_score', 0))
    is_pass = critical_score_val >= 59 and overall_score_val >= 70

    p.setFont("Helvetica-Bold", 12)
    score_color = colors.green if is_pass else colors.red
    p.setFillColor(score_color)

    if is_pass:
        score_message = f"Pass: Critical Score = {critical_score_val}, Total Score = {overall_score_val}"
    else:
        score_message = f"Fail: Critical Score = {critical_score_val} (needs 59+), Total Score = {overall_score_val} (needs 70+)"

    p.drawCentredString(width / 2, current_y - 20, score_message)
    p.setFillColor(colors.black)

    # New page for checklist
    p.showPage()
    y = height - 50

    # Inspection Checklist
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Inspection Checklist")
    y -= 30

    # Table setup
    table_x = 50
    table_width = width - 100
    col_widths = [50, 320, 60, 80]
    header_height = 25
    row_height = 18

    y = draw_table_header(p, table_x, y, table_width, col_widths, header_height)

    scores = inspection.get('scores', {})

    # Use the same FOOD_CHECKLIST_ITEMS that your HTML templates use
    checklist = FOOD_CHECKLIST_ITEMS

    # Group checklist items by categories (matching your HTML logic exactly)
    categories = [
        ("FOOD (1-2)", [item for item in checklist if 1 <= item['id'] <= 2]),
        ("FOOD PROTECTION (3-10)", [item for item in checklist if 3 <= item['id'] <= 10]),
        ("FOOD EQUIPMENT & UTENSILS (11-23)", [item for item in checklist if 11 <= item['id'] <= 23]),
        ("TOILET & HANDWASHING FACILITIES (24-25)", [item for item in checklist if 24 <= item['id'] <= 25]),
        ("SOLID WASTE MANAGEMENT (26-27)", [item for item in checklist if 26 <= item['id'] <= 27]),
        ("INSECT, RODENT, ANIMAL CONTROL (28)", [item for item in checklist if item['id'] == 28]),
        ("PERSONNEL (29-31)", [item for item in checklist if 29 <= item['id'] <= 31]),
        ("LIGHTING (32)", [item for item in checklist if item['id'] == 32]),
        ("VENTILATION (33)", [item for item in checklist if item['id'] == 33]),
        ("DRESSING ROOMS (34)", [item for item in checklist if item['id'] == 34]),
        ("WATER (35)", [item for item in checklist if item['id'] == 35]),
        ("SEWAGE (36)", [item for item in checklist if item['id'] == 36]),
        ("PLUMBING (37-38)", [item for item in checklist if 37 <= item['id'] <= 38]),
        ("FLOORS, WALLS, & CEILINGS (39-40)", [item for item in checklist if 39 <= item['id'] <= 40]),
        ("OTHER OPERATIONS (41-44)", [item for item in checklist if 41 <= item['id'] <= 44]),
    ]

    page_num = 1

    for category_name, items in categories:
        if y < 100:
            p.showPage()
            page_num += 1
            y = height - 50
            y = draw_table_header(p, table_x, y, table_width, col_widths, header_height)

        # Category header - WHITE background (matching HTML exactly)
        p.setFillColor(colors.white)
        p.rect(table_x, y - row_height, table_width, row_height, fill=1)
        p.setFillColor(colors.black)
        p.rect(table_x, y - row_height, table_width, row_height)

        p.setFont("Helvetica-Bold", 10)
        p.drawString(table_x + 10, y - 12, category_name)
        y -= row_height

        # Category items
        for item in items:
            if y < 30:
                p.showPage()
                page_num += 1
                y = height - 50
                y = draw_table_header(p, table_x, y, table_width, col_widths, header_height)

            # Handle both dict and tuple formats from your database
            if isinstance(item, dict):
                item_id = item['id']
                description = item['desc']
                weight = item['wt']
            else:
                item_id, description, weight = item

            score = scores.get(item_id, '0')

            # ONLY apply light gray background for weights 4 and 5 - matching HTML exactly
            # This matches your CSS: tr.important-weight { background: #e6e6e6; }
            weight_float = float(weight)
            if weight_float in [4.0, 5.0]:
                p.setFillColor(colors.Color(0.9, 0.9, 0.9))  # Light gray matching #e6e6e6
                p.rect(table_x, y - row_height, table_width, row_height, fill=1)

            # Always set black fill color before drawing borders and text
            p.setFillColor(colors.black)
            p.rect(table_x, y - row_height, table_width, row_height)

            # Column separators
            x_pos = table_x
            for width_col in col_widths[:-1]:
                x_pos += width_col
                p.line(x_pos, y, x_pos, y - row_height)

            # Content
            p.setFont("Helvetica", 9)
            p.drawCentredString(table_x + col_widths[0] / 2, y - 12, str(item_id))

            # Truncate long descriptions
            desc = str(description)[:45] + "..." if len(str(description)) > 45 else str(description)
            p.drawString(table_x + col_widths[0] + 5, y - 12, desc)

            p.drawCentredString(table_x + col_widths[0] + col_widths[1] + col_widths[2] / 2, y - 12, str(weight))
            p.setFont("Helvetica-Bold", 10)
            p.drawCentredString(table_x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] / 2, y - 12,
                                str(score))

            y -= row_height

        y -= 5  # Small gap between categories

    # New page for records
    p.showPage()
    y = height - 100

    # Records section - matching HTML exactly
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Records:")
    y -= 30

    # Comments area (left side, 2/3 width)
    comments_height = 100
    comments_width = (width - 120) * 2 / 3

    p.setLineWidth(1)
    p.rect(50, y - comments_height, comments_width, comments_height)

    p.setFont("Helvetica-Bold", 10)
    p.drawString(55, y - 15, "Comments:")

    comments = inspection.get('comments', 'No comments provided.')
    if comments:
        p.setFont("Helvetica", 10)
        # Break comments into lines that fit
        words = comments.split()
        lines = []
        current_line = ""
        max_chars_per_line = 55

        for word in words:
            if len(current_line + " " + word) <= max_chars_per_line:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        comment_y = y - 30
        for line in lines[:5]:  # Show up to 5 lines
            p.drawString(55, comment_y, line)
            comment_y -= 12

    # Signature section (right side, 1/3 width)
    sig_x = 60 + comments_width
    sig_width = (width - 120) / 3

    # Inspector's Signature box
    p.setLineWidth(1)
    p.rect(sig_x, y - 50, sig_width, 45)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(sig_x + 5, y - 15, "Inspector's Signature:")
    p.setFont("Helvetica", 10)
    inspector_sig = str(inspection.get('inspector_signature', ''))[:20]
    p.drawString(sig_x + 5, y - 35, inspector_sig)

    # Received By box
    p.rect(sig_x, y - 100, sig_width, 45)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(sig_x + 5, y - 65, "Received By:")
    p.setFont("Helvetica", 10)
    received_by = str(inspection.get('received_by', ''))[:20]
    p.drawString(sig_x + 5, y - 85, received_by)

    y -= 140

    # Footer
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2, y, "Food Establishment Inspection Form")
    p.drawCentredString(width / 2, y - 12, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=food_inspection_{form_id}.pdf'
    return response


@app.route('/spirit_licence/inspection/<int:id>')
def spirit_licence_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # This allows column access by name
    c = conn.cursor()

    c.execute("""SELECT * FROM inspections 
                 WHERE id = ? AND form_type = 'Spirit Licence Premises'""", (id,))
    inspection = c.fetchone()
    conn.close()

    if inspection:
        # Parse scores safely
        scores_str = inspection['scores'] if inspection['scores'] else ''
        if scores_str:
            try:
                scores = [int(float(x)) for x in scores_str.split(',')]
                while len(scores) < 25:
                    scores.append(0)
            except ValueError:
                scores = [0] * 25
        else:
            scores = [0] * 25

        # Helper function to safely get values from Row object
        def safe_get(row, key, default=''):
            try:
                value = row[key]
                return value if value is not None else default
            except (KeyError, IndexError):
                return default

        inspection_data = {
            'id': inspection['id'],
            'establishment_name': safe_get(inspection, 'establishment_name'),
            'owner': safe_get(inspection, 'owner'),
            'address': safe_get(inspection, 'address'),
            'license_no': safe_get(inspection, 'license_no'),
            'inspector_name': safe_get(inspection, 'inspector_name'),
            'inspection_date': safe_get(inspection, 'inspection_date'),
            'inspection_time': safe_get(inspection, 'inspection_time'),
            'type_of_establishment': safe_get(inspection, 'type_of_establishment'),
            'purpose_of_visit': safe_get(inspection, 'purpose_of_visit'),
            'action': safe_get(inspection, 'action'),
            'result': safe_get(inspection, 'result'),
            'scores': {str(i): scores[i-1] for i in range(1, 26)},
            'comments': safe_get(inspection, 'comments'),
            'inspector_signature': safe_get(inspection, 'inspector_signature'),
            'received_by': safe_get(inspection, 'received_by'),
            'overall_score': safe_get(inspection, 'overall_score', 0),
            'critical_score': safe_get(inspection, 'critical_score', 0),
            'form_type': safe_get(inspection, 'form_type'),
            'no_of_employees': safe_get(inspection, 'no_of_employees'),
            'no_with_fhc': safe_get(inspection, 'no_with_fhc', 0),
            'no_wo_fhc': safe_get(inspection, 'no_wo_fhc', 0),
            'status': safe_get(inspection, 'status'),
            'created_at': safe_get(inspection, 'created_at'),
            'photo_data': safe_get(inspection, 'photo_data', '[]')
        }

        # Parse photos from JSON string to Python list
        import json
        photos = []
        if inspection_data.get('photo_data'):
            try:
                photos = json.loads(inspection_data.get('photo_data', '[]'))
            except:
                photos = []

        return render_template('spirit_licence_inspection_detail.html',
                              checklist=[], inspection=inspection_data,
                              photo_data=photos)

    return "Not Found", 404


@app.route('/download_spirit_licence_pdf/<int:form_id>')
def download_spirit_licence_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    # Get inspection details
    inspection = get_spirit_licence_inspection_details(form_id)
    if not inspection:
        return jsonify({'error': 'Inspection not found'}), 404

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    def draw_table_header(p, table_x, y, table_width, col_widths, header_height):
        """Helper function to draw table header"""
        p.setLineWidth(1)
        p.setFillColor(colors.Color(0.96, 0.96, 0.96))
        p.rect(table_x, y - header_height, table_width, header_height, fill=1)
        p.setFillColor(colors.black)
        p.rect(table_x, y - header_height, table_width, header_height)

        p.setFont("Helvetica-Bold", 11)
        p.drawCentredString(table_x + col_widths[0] / 2, y - 16, "Item")
        p.drawCentredString(table_x + col_widths[0] + col_widths[1] / 2, y - 16, "Wt.")
        p.drawCentredString(table_x + col_widths[0] + col_widths[1] + col_widths[2] / 2, y - 16, "Score")
        p.drawCentredString(table_x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] / 2, y - 16,
                            "Inspector's Comments")

        # Column separators
        x_pos = table_x
        for width_col in col_widths[:-1]:
            x_pos += width_col
            p.line(x_pos, y, x_pos, y - header_height)

        return y - header_height

    # Start from top
    y = height - 40

    # Title
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2, y, "Spirit Licence Premises Inspection Details")
    y -= 40

    # Two-column layout for establishment details
    left_col_x = 50
    right_col_x = 300
    col_width = 250
    row_height = 25

    # Left column details
    details_left = [
        ("Name of Establishment:", inspection.get('establishment_name', '')),
        ("Owner/Operator:", inspection.get('owner_operator', '')),
        ("Address of Establishment:", inspection.get('address', '')),
        ("Purpose of Visit:", inspection.get('purpose_of_visit', '')),
    ]

    # Right column details
    details_right = [
        ("Type of Establishment:", inspection.get('type_of_establishment', '')),
        ("Inspector Name:", inspection.get('inspector_name', '')),
        ("Inspection Date:", inspection.get('inspection_date', '')),
        ("Critical Score:", inspection.get('critical_score', '0')),
        ("Overall Score:", inspection.get('overall_score', '0')),
        ("Status:", inspection.get('status', '')),
        ("No. of Employees:", inspection.get('no_of_employees', '')),
        ("No. with FHC:", inspection.get('no_with_fhc', '')),
        ("No. W/O FHC:", inspection.get('no_wo_fhc', '')),
    ]

    # Draw left column
    current_y = y
    for label, value in details_left:
        p.setFont("Helvetica-Bold", 10)
        p.drawString(left_col_x, current_y, label)
        p.setFont("Helvetica", 10)
        p.rect(left_col_x, current_y - 20, col_width, 18)
        p.drawString(left_col_x + 5, current_y - 15, str(value)[:30])
        current_y -= row_height

    # Draw right column
    current_y = y
    for label, value in details_right:
        p.setFont("Helvetica-Bold", 10)
        p.drawString(right_col_x, current_y, label)
        p.setFont("Helvetica", 10)
        p.rect(right_col_x, current_y - 20, col_width, 18)

        # Special formatting for status and scores
        if label == "Status:":
            status_color = colors.green if str(value) == 'Satisfactory' else colors.red
            p.setFillColor(status_color)
            p.drawString(right_col_x + 5, current_y - 15, str(value))
            p.setFillColor(colors.black)
        else:
            p.drawString(right_col_x + 5, current_y - 15, str(value)[:30])
        current_y -= row_height

    # Move to checklist section
    y = current_y - 40

    # Inspection Checklist title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Inspection Checklist")
    y -= 30

    # Table setup
    table_x = 50
    table_width = width - 100
    col_widths = [250, 40, 60, 160]  # Item, Wt, Score, Comments
    header_height = 25
    row_height = 18

    # Draw initial table header
    y = draw_table_header(p, table_x, y, table_width, col_widths, header_height)

    # Get scores and comments
    scores = inspection.get('scores', {})
    parsed_comments = inspection.get('parsed_comments', {})

    # Organize checklist items by categories matching the HTML form structure
    # Based on the HTML form: Building=1,2; Walls=3; Floors=4,5; Service Counter=6,7; Lighting=8;
    # Washing and Sanitization=9,10,11; Water Supply=12,13; Storage=14,15,16;
    # Sanitary=17,18,19,20,21; Solid Waste=22,23,24; Pest Control=25
    categories = [
        ("Building", [1, 2]),
        ("Walls", [3]),
        ("Floors", [4, 5]),
        ("Service Counter", [6, 7]),
        ("Lighting", [8]),
        ("Washing and Sanitization Facilities", [9, 10, 11]),
        ("Water Supply", [12, 13]),
        ("Storage Facilities", [14, 15, 16]),
        ("Sanitary Facilities", [17, 18, 19, 20, 21]),
        ("Solid Waste Management", [22, 23, 24]),
        ("Pest Control", [25]),
    ]

    # Create a lookup for checklist items
    checklist_lookup = {item['id']: item for item in SPIRIT_LICENCE_CHECKLIST_ITEMS}

    page_num = 1

    for category_name, items in categories:
        # Check for new page
        if y < 100:
            p.showPage()
            page_num += 1
            y = height - 50

            # Redraw table header
            y = draw_table_header(p, table_x, y, table_width, col_widths, header_height)

        # Category header (matching your HTML header-row class)
        p.setFillColor(colors.Color(0.94, 0.94, 0.94))
        p.rect(table_x, y - row_height, table_width, row_height, fill=1)
        p.setFillColor(colors.black)
        p.rect(table_x, y - row_height, table_width, row_height)

        p.setFont("Helvetica-Bold", 10)
        p.drawString(table_x + 10, y - 12, category_name)
        y -= row_height

        # Category items
        for item_id in items:
            if y < 30:
                p.showPage()
                page_num += 1
                y = height - 50

                # Redraw header
                y = draw_table_header(p, table_x, y, table_width, col_widths, header_height)

            # Get item data from checklist
            item_data = checklist_lookup.get(item_id)
            if not item_data:
                continue

            description = item_data['description']
            weight = item_data['wt']
            is_critical = weight >= 5  # Critical items have weight 5 or higher

            # Critical item background (matching your HTML .critical class)
            if is_critical:
                p.setFillColor(colors.Color(0.9, 0.9, 0.9))
                p.rect(table_x, y - row_height, table_width, row_height, fill=1)

            p.setFillColor(colors.black)
            p.rect(table_x, y - row_height, table_width, row_height)

            # Column separators
            x_pos = table_x
            for width_col in col_widths[:-1]:
                x_pos += width_col
                p.line(x_pos, y, x_pos, y - row_height)

            # Content
            p.setFont("Helvetica", 9)

            # Item description
            desc = description[:35] + "..." if len(description) > 35 else description
            p.drawString(table_x + 5, y - 12, desc)

            # Weight
            p.drawCentredString(table_x + col_widths[0] + col_widths[1] / 2, y - 12, str(weight))

            # Score (bold)
            score = scores.get(str(item_id), '0')
            p.setFont("Helvetica-Bold", 10)
            p.drawCentredString(table_x + col_widths[0] + col_widths[1] + col_widths[2] / 2, y - 12, str(score))

            # Comment
            p.setFont("Helvetica", 8)
            comment = parsed_comments.get(str(item_id), '')
            comment_text = comment[:25] + "..." if len(comment) > 25 else comment
            p.drawString(table_x + col_widths[0] + col_widths[1] + col_widths[2] + 5, y - 12, comment_text)

            y -= row_height

        y -= 5  # Space between categories

    # Signatures section
    if y < 80:
        p.showPage()
        y = height - 100

    y -= 20

    # Signature table
    sig_table_height = 60
    p.setLineWidth(1)
    p.rect(table_x, y - sig_table_height, table_width, sig_table_height)

    # Horizontal line to separate rows
    p.line(table_x, y - sig_table_height / 2, table_x + table_width, y - sig_table_height / 2)

    # Vertical line to separate columns
    p.line(table_x + table_width / 2, y, table_x + table_width / 2, y - sig_table_height)

    # Inspector's Signature
    p.setFont("Helvetica-Bold", 10)
    p.drawString(table_x + 10, y - 15, "Inspector's Signature:")
    p.setFont("Helvetica", 10)
    inspector_sig = str(inspection.get('inspector_signature', ''))[:25]
    p.drawString(table_x + table_width / 2 + 10, y - 15, inspector_sig)

    # Rec'd By
    p.setFont("Helvetica-Bold", 10)
    p.drawString(table_x + 10, y - 45, "Rec'd By:")
    p.setFont("Helvetica", 10)
    received_by = str(inspection.get('received_by', ''))[:25]
    p.drawString(table_x + table_width / 2 + 10, y - 45, received_by)

    y -= sig_table_height + 20

    # Footer
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2, y, "Spirit Licence Premises Inspection Form")
    p.drawCentredString(width / 2, y - 12, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=spirit_licence_inspection_{form_id}.pdf'
    return response

@app.route('/swimming_pool/inspection/<int:id>')
def swimming_pool_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # This allows access by column name
    cursor = conn.cursor()

    # Select ALL columns including the individual score columns
    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Swimming Pool'", (id,))
    inspection = cursor.fetchone()

    if not inspection:
        conn.close()
        return "Inspection not found", 404

    # Convert to dictionary for easier template access
    inspection_dict = dict(inspection)

    # Fix the overall score - round to 1 decimal place
    if inspection_dict.get('overall_score'):
        inspection_dict['overall_score'] = round(float(inspection_dict['overall_score']), 1)

    # Fix the critical score - round to 1 decimal place
    if inspection_dict.get('critical_score'):
        inspection_dict['critical_score'] = round(float(inspection_dict['critical_score']), 1)

    # Fix manager signature field mapping
    # Check different possible field names for manager signature
    manager_signature = (
            inspection_dict.get('manager_signature') or
            inspection_dict.get('received_by') or
            inspection_dict.get('manager_name') or
            ''
    )
    inspection_dict['manager_signature'] = manager_signature

    # Debug: Print what scores we have
    print(f"=== DEBUG: Swimming Pool Inspection {id} ===")
    print(f"Overall Score: {inspection_dict.get('overall_score')}")
    print(f"Manager Signature: '{manager_signature}'")
    print(f"Received By: '{inspection_dict.get('received_by')}'")

    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_field = f"score_{item['id']}"
        score_value = inspection_dict.get(score_field, 0)
        print(f"{score_field}: {score_value}")

    # Ensure all score fields exist with proper values
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_field = f"score_{item['id']}"
        if score_field not in inspection_dict or inspection_dict[score_field] is None:
            inspection_dict[score_field] = 0.0
        else:
            # Ensure it's a float
            inspection_dict[score_field] = float(inspection_dict[score_field])

    # Also get backup scores from inspection_items table
    cursor.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (id,))
    item_scores = {row[0]: float(row[1]) if row[1] and str(row[1]).replace('.', '', 1).isdigit() else 0.0
                   for row in cursor.fetchall()}

    conn.close()

    # If individual columns don't exist, use item_scores as fallback
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_field = f"score_{item['id']}"
        if inspection_dict[score_field] == 0.0 and item['id'] in item_scores:
            inspection_dict[score_field] = item_scores[item['id']]
            print(f"Using fallback for {score_field}: {item_scores[item['id']]}")

    # Parse photos from JSON string to Python list
    import json
    photos = []
    if inspection_dict.get('photo_data'):
        try:
            photos = json.loads(inspection_dict.get('photo_data', '[]'))
        except:
            photos = []

    return render_template('swimming_pool_inspection_detail.html',
                           inspection=inspection_dict,
                           checklist=SWIMMING_POOL_CHECKLIST_ITEMS,
                           photo_data=photos)

# Debug route for session verification
@app.route('/debug_session')
def debug_session():
    return jsonify(dict(session))

# Placeholder for create_form_header (implement based on your app's needs)
def create_form_header(pdf_canvas, title, form_id, width, height):
    pdf_canvas.setFont("Helvetica-Bold", 14)
    pdf_canvas.drawCentredString(width / 2, height - 50, title)
    pdf_canvas.drawString(50, height - 70, f"Form ID: {form_id}")
    return height - 90

# Placeholder for draw_checkbox (implement based on your app's needs)
def draw_checkbox(pdf_canvas, x, y, checked=False):
    pdf_canvas.rect(x, y, 8, 8)
    if checked:
        pdf_canvas.drawString(x + 2, y, "X")


@app.route('/search_forms', methods=['GET'])
def search_forms():
    if 'inspector' not in session:
        return redirect(url_for('login'))

    from db_config import execute_query

    query = request.args.get('query', '').lower()
    form_type = request.args.get('type', '')
    conn = get_db_connection()
    forms = []

    def calculate_status(overall_score, critical_score, form_type_val):
        """Calculate Pass/Fail status based on scores and form type"""
        overall_score = float(overall_score) if overall_score else 0
        critical_score = float(critical_score) if critical_score else 0

        if form_type_val == 'Food Establishment':
            return 'Pass' if overall_score >= 70 and critical_score >= 59 else 'Fail'
        elif form_type_val == 'Spirit Licence Premises':
            return 'Pass' if overall_score >= 70 and critical_score >= 60 else 'Fail'
        elif form_type_val == 'Swimming Pool':
            return 'Pass' if overall_score >= 70 else 'Fail'
        elif form_type_val == 'Small Hotel':
            return 'Pass' if overall_score >= 70 else 'Fail'
        elif form_type_val == 'Barbershop':
            return 'Satisfactory' if overall_score >= 60 and critical_score >= 60 else 'Unsatisfactory'
        elif form_type_val == 'Institutional Health':
            return 'Pass' if overall_score >= 70 and critical_score >= 70 else 'Fail'
        elif form_type_val == 'Residential':
            return 'Pass' if overall_score >= 70 and critical_score >= 61 else 'Fail'
        elif form_type_val == 'Meat Processing':
            return 'Pass' if overall_score >= 80 else 'Fail'
        else:
            return 'Pass' if overall_score >= 70 else 'Fail'

    if not form_type or form_type == 'all':
        c = execute_query(conn, """
            SELECT id, establishment_name, created_at, result, form_type, overall_score, critical_score
            FROM inspections
            WHERE form_type IN (
                'Food Establishment', 'Residential & Non-Residential', 'Water Supply',
                'Spirit Licence Premises', 'Swimming Pool', 'Small Hotel', 'Barbershop', 'Institutional Health'
            )
            AND (
                LOWER(establishment_name) LIKE ?
                OR LOWER(owner) LIKE ?
                OR LOWER(address) LIKE ?
            )
            UNION
            SELECT id, applicant_name AS establishment_name, created_at, 'Completed' AS result, 'Burial Site' AS form_type, 0 AS overall_score, 0 AS critical_score
            FROM burial_site_inspections
            WHERE LOWER(applicant_name) LIKE ? OR LOWER(deceased_name) LIKE ?
            UNION
            SELECT id, premises_name AS establishment_name, created_at, result, 'Residential' AS form_type, overall_score, critical_score
            FROM residential_inspections
            WHERE LOWER(premises_name) LIKE ? OR LOWER(owner) LIKE ?
            UNION
            SELECT id, establishment_name, created_at, result, 'Meat Processing' AS form_type, overall_score, 0 AS critical_score
            FROM meat_processing_inspections
            WHERE LOWER(establishment_name) LIKE ? OR LOWER(owner_operator) LIKE ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))

        records = c.fetchall()
        for record in records:
            overall_score = record[5] or 0
            critical_score = record[6] or 0
            form_type_val = record[4]
            current_status = record[3]

            # Calculate status if missing or N/A
            if not current_status or current_status == 'N/A':
                if form_type_val == 'Burial Site':
                    status = 'Completed'
                elif form_type_val == 'Residential':
                    status = calculate_status(overall_score, critical_score, 'Residential')
                else:
                    status = calculate_status(overall_score, critical_score, form_type_val)
            else:
                status = current_status

            forms.append({
                'id': record[0],
                'establishment_name': record[1],
                'created_at': record[2],
                'status': status,
                'result': status,  # Add both for compatibility
                'type': record[4]
            })

    else:
        # Handle specific form types
        if form_type == 'food':
            c = execute_query(conn, """
                SELECT id, establishment_name, created_at, result, overall_score, critical_score, owner
                FROM inspections
                WHERE form_type = 'Food Establishment'
                AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ?)
            """, (f'%{query}%', f'%{query}%'))
        elif form_type == 'residential':
            c = execute_query(conn, """
                SELECT id, premises_name, created_at, result, owner, overall_score, critical_score
                FROM residential_inspections
                WHERE (LOWER(premises_name) LIKE ? OR LOWER(owner) LIKE ?)
            """, (f'%{query}%', f'%{query}%'))
        elif form_type == 'burial':
            c = execute_query(conn, """
                SELECT id, applicant_name, deceased_name, created_at
                FROM burial_site_inspections
                WHERE LOWER(applicant_name) LIKE ? OR LOWER(deceased_name) LIKE ?
            """, (f'%{query}%', f'%{query}%'))
        elif form_type == 'spirit_licence':
            c = execute_query(conn, """
                SELECT id, establishment_name, created_at, result, overall_score, critical_score, owner
                FROM inspections
                WHERE form_type = 'Spirit Licence Premises'
                AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ?)
            """, (f'%{query}%', f'%{query}%'))
        elif form_type == 'swimming_pool':
            c = execute_query(conn, """
                SELECT id, establishment_name, created_at, result, overall_score, critical_score, owner
                FROM inspections
                WHERE form_type = 'Swimming Pool'
                AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ? OR LOWER(address) LIKE ?)
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        elif form_type == 'small_hotels':
            c = execute_query(conn, """
                SELECT id, establishment_name, created_at, result, overall_score, critical_score, owner
                FROM inspections
                WHERE form_type = 'Small Hotel'
                AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ? OR LOWER(address) LIKE ?)
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        elif form_type == 'barbershop':
            c = execute_query(conn, """
                SELECT id, establishment_name, created_at, result, overall_score, critical_score, owner
                FROM inspections
                WHERE form_type = 'Barbershop'
                AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ?)
            """, (f'%{query}%', f'%{query}%'))
        elif form_type == 'institutional':
            c = execute_query(conn, """
                SELECT id, establishment_name, created_at, result, overall_score, critical_score, owner
                FROM inspections
                WHERE form_type = 'Institutional Health'
                AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ?)
            """, (f'%{query}%', f'%{query}%'))
        elif form_type == 'meat_processing':
            c = execute_query(conn, """
                SELECT id, establishment_name, inspection_date, result, overall_score
                FROM meat_processing_inspections
                WHERE (LOWER(establishment_name) LIKE ? OR LOWER(owner_operator) LIKE ?)
            """, (f'%{query}%', f'%{query}%'))
        else:
            conn.close()
            return jsonify({'forms': []}), 404

        records = c.fetchall()
        for record in records:
            form_data = {
                'id': record[0],
                'created_at': record[2] if len(record) > 2 else '',
                'type': form_type
            }

            if form_type == 'residential':
                form_data['premises_name'] = record[1]
                form_data['owner'] = record[4] if len(record) > 4 else ''
                overall_score = record[5] if len(record) > 5 else 0
                critical_score = record[6] if len(record) > 6 else 0
                current_result = record[3] if len(record) > 3 else ''

                if not current_result or current_result == 'N/A':
                    form_data['status'] = calculate_status(overall_score, critical_score, 'Residential')
                else:
                    form_data['status'] = current_result
                form_data['result'] = form_data['status']

            elif form_type == 'burial':
                form_data['applicant_name'] = record[1]
                form_data['deceased_name'] = record[2]
                form_data['status'] = 'Completed'
                form_data['result'] = 'Completed'

            elif form_type == 'institutional':
                form_data['establishment_name'] = record[1]
                overall_score = record[4] if len(record) > 4 else 0
                critical_score = record[5] if len(record) > 5 else 0
                current_result = record[3] if len(record) > 3 else ''

                if not current_result or current_result == 'N/A':
                    form_data['status'] = calculate_status(overall_score, critical_score, 'Institutional Health')
                else:
                    form_data['status'] = current_result
                form_data['result'] = form_data['status']

            elif form_type == 'meat_processing':
                form_data['establishment_name'] = record[1]
                form_data['created_at'] = record[2] if len(record) > 2 else ''
                overall_score = record[4] if len(record) > 4 else 0
                current_result = record[3] if len(record) > 3 else ''

                if not current_result or current_result == 'N/A':
                    form_data['status'] = 'Pass' if float(overall_score) >= 80 else 'Fail'
                else:
                    form_data['status'] = current_result
                form_data['result'] = form_data['status']

            else:
                # All other form types
                form_data['establishment_name'] = record[1]
                form_data['owner'] = record[6] if len(record) > 6 else ''  # Add owner field
                overall_score = record[4] if len(record) > 4 else 0
                critical_score = record[5] if len(record) > 5 else 0
                current_result = record[3] if len(record) > 3 else ''

                if not current_result or current_result == 'N/A':
                    if form_type == 'food':
                        form_data['status'] = calculate_status(overall_score, critical_score, 'Food Establishment')
                    elif form_type == 'spirit_licence':
                        form_data['status'] = calculate_status(overall_score, critical_score, 'Spirit Licence Premises')
                    elif form_type == 'swimming_pool':
                        form_data['status'] = calculate_status(overall_score, critical_score, 'Swimming Pool')
                    elif form_type == 'small_hotels':
                        form_data['status'] = calculate_status(overall_score, critical_score, 'Small Hotel')
                    elif form_type == 'barbershop':
                        form_data['status'] = calculate_status(overall_score, critical_score, 'Barbershop')
                    else:
                        form_data['status'] = 'Unknown'
                else:
                    form_data['status'] = current_result
                form_data['result'] = form_data['status']

            forms.append(form_data)

    conn.close()
    return jsonify({'forms': forms})


# Database schema update for barbershop inspections
def update_barbershop_db_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    columns_added = 0
    for item in BARBERSHOP_CHECKLIST_ITEMS:
        try:
            cursor.execute(f'ALTER TABLE inspections ADD COLUMN score_{item["id"]} REAL DEFAULT 0')
            columns_added += 1
            logging.info(f"Added column score_{item['id']}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                logging.error(f"Error adding score_{item['id']}: {e}")
    for column in ['telephone_no', 'inspector_code', 'purpose_of_visit', 'action', 'registration_status']:
        try:
            cursor.execute(f'ALTER TABLE inspections ADD COLUMN {column} TEXT')
            columns_added += 1
            logging.info(f"Added column {column}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                logging.error(f"Error adding {column}: {e}")
    conn.commit()
    conn.close()


    return columns_added

# Route to render new barbershop inspection form
@app.route('/new_barbershop_form')
def new_barbershop_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))

    # Load checklist from database (falls back to hardcoded if empty)
    checklist = get_form_checklist_items('Barbershop', BARBERSHOP_CHECKLIST_ITEMS)

    inspection = {
        'id': '',
        'establishment_name': '',
        'owner': '',
        'address': '',
        'license_no': '',
        'inspector_name': session.get('inspector', 'Inspector'),
        'inspection_date': datetime.now().strftime('%Y-%m-%d'),
        'inspection_time': '',
        'type_of_establishment': 'Barbershop',
        'no_of_employees': '',
        'result': '',
        'overall_score': 0,
        'critical_score': 0,
        'comments': '',
        'inspector_signature': '',
        'received_by': '',
        'scores': {},
        'created_at': '',
        'telephone_no': '',
        'inspector_code': '',
        'purpose_of_visit': '',
        'action': '',
        'registration_status': ''
    }
    return render_template('barbershop_form.html', checklist=checklist, inspections=get_inspections(),
                           show_form=True, establishment_data=get_establishment_data(), read_only=False,
                           inspection=inspection)


# Route to render new meat processing inspection form
@app.route('/new_meat_processing_form')
def new_meat_processing_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))

    # Load checklist from database (falls back to hardcoded if empty)
    checklist = get_form_checklist_items('Meat Processing', MEAT_PROCESSING_CHECKLIST_ITEMS)

    return render_template('meat_processing_form.html', checklist=checklist)


@app.route('/submit_barbershop', methods=['POST'])
def submit_barbershop():
    if 'inspector' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure score columns exist
    try:
        cursor.execute("SELECT score_01 FROM inspections LIMIT 1")
    except sqlite3.OperationalError:
        update_barbershop_db_schema()

    # Extract form data
    data = {
        'establishment_name': request.form.get('establishment_name', ''),
        'owner': request.form.get('owner', ''),
        'address': request.form.get('address', ''),
        'license_no': request.form.get('license_no', ''),
        'inspector_name': request.form.get('inspector_name', ''),
        'inspection_date': request.form.get('inspection_date', ''),
        'inspection_time': request.form.get('inspection_time', ''),
        'type_of_establishment': 'Barbershop',
        'no_of_employees': request.form.get('no_of_employees', ''),
        'telephone_no': request.form.get('telephone_no', ''),
        'inspector_code': request.form.get('inspector_code', ''),
        'purpose_of_visit': request.form.get('purpose_of_visit', ''),
        'action': request.form.get('action', ''),
        'registration_status': request.form.get('registration_status', ''),
        'comments': request.form.get('comments', ''),  # Get comments directly from form
        'inspector_signature': request.form.get('inspector_signature', ''),
        'received_by': request.form.get('received_by', ''),
        'photo_data': request.form.get('photos', '[]'),  # Get photo data from 'photos' field
        'form_type': 'Barbershop',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Calculate scores
    scores = []
    total_score = 0
    critical_score = 0
    max_possible_score = sum(item['wt'] for item in BARBERSHOP_CHECKLIST_ITEMS)
    critical_max_score = sum(item['wt'] for item in BARBERSHOP_CHECKLIST_ITEMS if item['critical'])
    score_updates = {}

    for item in BARBERSHOP_CHECKLIST_ITEMS:
        score_key = f"score_{item['id']}"
        score = float(request.form.get(score_key, 0))
        score_updates[score_key] = score
        scores.append(str(score))
        total_score += score
        if item['critical']:
            critical_score += score

    # Calculate overall score as percentage
    overall_score = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    overall_score = round(min(overall_score, 100), 1)
    data['overall_score'] = overall_score
    data['critical_score'] = critical_score
    data['scores'] = ','.join(scores)  # Store scores as comma-separated string

    # Determine result based on scores
    critical_pass_threshold = critical_max_score * 0.7  # 70% of critical items
    if overall_score >= 70 and critical_score >= critical_pass_threshold:
        data['result'] = 'Satisfactory'
    else:
        data['result'] = 'Unsatisfactory'

    # Build dynamic INSERT query
    base_columns = '''establishment_name, owner, address, license_no, inspector_name,
                     inspection_date, inspection_time, type_of_establishment, no_of_employees,
                     telephone_no, inspector_code, purpose_of_visit, action, registration_status,
                     comments, result, overall_score, critical_score, scores, inspector_signature,
                     received_by, photo_data, form_type, created_at'''

    score_columns = ', '.join([f"score_{item['id']}" for item in BARBERSHOP_CHECKLIST_ITEMS])
    all_columns = f"{base_columns}, {score_columns}"

    base_placeholders = '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?'
    score_placeholders = ', '.join(['?' for _ in BARBERSHOP_CHECKLIST_ITEMS])
    all_placeholders = f"{base_placeholders}, {score_placeholders}"

    base_values = (
        data['establishment_name'], data['owner'], data['address'], data['license_no'],
        data['inspector_name'], data['inspection_date'], data['inspection_time'],
        data['type_of_establishment'], data['no_of_employees'], data['telephone_no'],
        data['inspector_code'], data['purpose_of_visit'], data['action'], data['registration_status'],
        data['comments'], data['result'], data['overall_score'], data['critical_score'],
        data['scores'], data['inspector_signature'], data['received_by'], data['photo_data'],
        data['form_type'], data['created_at']
    )
    score_values = tuple(score_updates[f"score_{item['id']}"] for item in BARBERSHOP_CHECKLIST_ITEMS)
    all_values = base_values + score_values

    try:
        # Insert inspection
        cursor.execute(f'''
            INSERT INTO inspections ({all_columns})
            VALUES ({all_placeholders})
        ''', all_values)
        inspection_id = cursor.lastrowid

        # Insert inspection items
        for item in BARBERSHOP_CHECKLIST_ITEMS:
            score = score_updates[f"score_{item['id']}"]
            cursor.execute('''
                INSERT INTO inspection_items (inspection_id, item_id, details)
                VALUES (?, ?, ?)
            ''', (inspection_id, item['id'], str(score)))

        conn.commit()
        conn.close()

        # Check and create alert if score below threshold
        check_and_create_alert(
            inspection_id,
            data['inspector_name'],
            'Barbershop',
            data['overall_score']
        )

        # Return success with redirect
        return jsonify({
            'status': 'success',
            'message': 'Inspection submitted successfully',
            'redirect': '/dashboard'
        })

    except sqlite3.Error as e:
        conn.close()
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@app.route('/barbershop/inspection/<int:id>')
def barbershop_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Barbershop'", (id,))
    inspection = cursor.fetchone()

    if not inspection:
        conn.close()
        return "Inspection not found", 404

    inspection_dict = dict(inspection)
    inspection_dict['overall_score'] = round(float(inspection_dict['overall_score']), 1) if inspection_dict.get('overall_score') else 0.0
    inspection_dict['critical_score'] = round(float(inspection_dict['critical_score']), 1) if inspection_dict.get('critical_score') else 0.0

    # Ensure all score fields exist
    for item in BARBERSHOP_CHECKLIST_ITEMS:
        score_field = f"score_{item['id']}"
        if score_field not in inspection_dict or inspection_dict[score_field] is None:
            inspection_dict[score_field] = 0.0
        else:
            inspection_dict[score_field] = float(inspection_dict[score_field])

    # Get backup scores from inspection_items
    cursor.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (id,))
    item_scores = {row[0]: float(row[1]) if row[1] and str(row[1]).replace('.', '', 1).isdigit() else 0.0 for row in cursor.fetchall()}

    for item in BARBERSHOP_CHECKLIST_ITEMS:
        score_field = f"score_{item['id']}"
        if inspection_dict[score_field] == 0.0 and item['id'] in item_scores:
            inspection_dict[score_field] = item_scores[item['id']]

    # ADD THIS: Create the scores dictionary that the template expects
    scores = {}
    for item in BARBERSHOP_CHECKLIST_ITEMS:
        item_id = item['id']
        score_field = f"score_{item_id}"
        scores[item_id] = inspection_dict.get(score_field, 0.0)

    # Add the scores dictionary to inspection_dict
    inspection_dict['scores'] = scores

    conn.close()

    # Parse photos from JSON string to Python list
    import json
    photos = []
    if inspection_dict.get('photo_data'):
        try:
            photos = json.loads(inspection_dict.get('photo_data', '[]'))
        except:
            photos = []

    return render_template('barbershop_inspection_detail.html', inspection=inspection_dict, checklist=BARBERSHOP_CHECKLIST_ITEMS,
                          photo_data=photos)

# Replace your download_barbershop_pdf function with this corrected version
@app.route('/download_barbershop_pdf/<int:form_id>')
def download_barbershop_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Barbershop'", (form_id,))
    form_data = c.fetchone()

    if not form_data:
        conn.close()
        return jsonify({'error': 'Inspection not found'}), 404

    c.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (form_id,))
    checklist_scores = {str(row[0]): float(row[1]) if row[1] and row[1].replace('.', '', 1).isdigit() else 0.0 for row
                        in c.fetchall()}
    conn.close()

    # Debug: Print what we have in the database
    print("=== BARBERSHOP PDF DEBUG ===")
    for key in form_data.keys():
        print(f"{key}: {form_data[key]}")
    print("=============================")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # === EXACT FORM HEADER - Bordered Box ===
    y = height - 50

    # Draw main header border (2px thick)
    p.setLineWidth(2)
    header_height = 60
    p.rect(50, y - header_height, width - 100, header_height)

    # Form ID in top right corner (red text)
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.red)
    p.drawString(width - 120, y - 15, f"Form ID: {form_id}")

    # Date in top right corner (below Form ID)
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.black)
    p.drawString(width - 120, y - 30, f"Date: {form_data['inspection_date'] or '2025-08-22'}")

    # Centered title
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, y - 30, "BARBERSHOP & BEAUTY SALON INSPECTION FORM")

    y -= 80

    # === ESTABLISHMENT INFORMATION SECTION - Bordered Box ===
    p.setLineWidth(1)
    info_start_y = y
    info_height = 140

    # Draw border around entire info section
    p.rect(50, y - info_height, width - 100, info_height)

    # Section title
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, y - 20, "ESTABLISHMENT INFORMATION")

    p.setFont("Helvetica", 10)
    y -= 35

    # Left column information - using your original working syntax
    left_x = 70
    right_x = 320

    info_items = [
        ("Establishment Name:", form_data['establishment_name'] or ''),
        ("Address and Parish:", form_data['address'] or ''),
        ("Inspector Name:", form_data['inspector_name'] or ''),  # This might be empty
        ("Inspection Time:", form_data['inspection_time'] or ''),  # This might be empty
        ("No. of Employees:", str(form_data['no_of_employees'] or '')),
        ("Purpose of Visit:", form_data['purpose_of_visit'] or ''),
        ("Registration Status:", form_data['registration_status'] or '')
    ]

    right_items = [
        ("Owner/Operator:", form_data['owner'] or ''),
        ("License No:", form_data['license_no'] or ''),
        ("Inspection Date:", form_data['inspection_date'] or ''),
        ("Telephone No:", form_data['telephone_no'] or ''),
        ("Inspector Code:", form_data['inspector_code'] or ''),
        ("Action:", form_data['action'] or ''),
        ("", "")  # Empty for alignment
    ]

    for i, ((left_label, left_value), (right_label, right_value)) in enumerate(zip(info_items, right_items)):
        current_y = y - (i * 15)

        # Left column
        p.drawString(left_x, current_y, left_label)
        p.line(left_x + 90, current_y - 2, left_x + 220, current_y - 2)
        p.drawString(left_x + 95, current_y, left_value)

        # Right column
        if right_label:  # Skip empty rows
            p.drawString(right_x, current_y, right_label)
            p.line(right_x + 90, current_y - 2, right_x + 220, current_y - 2)
            p.drawString(right_x + 95, current_y, right_value)

    y -= 160

    # === INSPECTION CHECKLIST SECTION ===
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "INSPECTION CHECKLIST")
    y -= 25

    # === PERFECT TABLE STRUCTURE ===
    # Table dimensions to match your visual exactly
    table_x = 50
    table_width = width - 100
    col_widths = [40, 350, 50, 50, 30]  # Item, Description, Weight, Score, Checkbox

    # Table header with thick border
    p.setLineWidth(2)
    header_height = 20
    p.rect(table_x, y - header_height, table_width, header_height)

    # Header background (light gray)
    p.setFillColor(colors.lightgrey)
    p.rect(table_x, y - header_height, table_width, header_height, fill=1)

    # Header text
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 10)

    # Draw column headers with exact positioning
    p.drawCentredString(table_x + 20, y - 15, "Item")
    p.drawCentredString(table_x + 215, y - 15, "Description")
    p.drawCentredString(table_x + 415, y - 15, "Weight")
    p.drawCentredString(table_x + 465, y - 15, "Score")
    p.drawCentredString(table_x + 495, y - 15, "✓")

    # Draw vertical lines for column separators
    p.setLineWidth(1)
    x_pos = table_x
    for width_col in col_widths[:-1]:
        x_pos += width_col
        p.line(x_pos, y, x_pos, y - header_height)

    y -= header_height

    # === ALL 32 CHECKLIST ITEMS ===
    barbershop_items = [
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

    p.setFont("Helvetica", 9)
    row_height = 15

    for i, item in enumerate(barbershop_items):
        current_y = y - (i * row_height)

        # Check if we need a new page
        if current_y < 100:
            p.showPage()
            current_y = height - 50
            y = current_y

            # Redraw table header on new page
            p.setLineWidth(2)
            p.rect(table_x, y - header_height, table_width, header_height)
            p.setFillColor(colors.lightgrey)
            p.rect(table_x, y - header_height, table_width, header_height, fill=1)
            p.setFillColor(colors.black)
            p.setFont("Helvetica-Bold", 10)
            p.drawCentredString(table_x + 20, y - 15, "Item")
            p.drawCentredString(table_x + 215, y - 15, "Description")
            p.drawCentredString(table_x + 415, y - 15, "Weight")
            p.drawCentredString(table_x + 465, y - 15, "Score")
            p.drawCentredString(table_x + 495, y - 15, "✓")
            y -= header_height
            current_y = y - (i * row_height)
            p.setFont("Helvetica", 9)

        # Row background for critical items (light yellow)
        if item['critical']:
            p.setFillColor(colors.Color(1, 1, 0.8))  # Light yellow
            p.rect(table_x, current_y - row_height, table_width, row_height, fill=1)

        # Row border
        p.setFillColor(colors.black)
        p.setLineWidth(1)
        p.rect(table_x, current_y - row_height, table_width, row_height)

        # Draw vertical column lines
        x_pos = table_x
        for width_col in col_widths[:-1]:
            x_pos += width_col
            p.line(x_pos, current_y, x_pos, current_y - row_height)

        # Get score for this item
        score = checklist_scores.get(item['id'], 0)

        # Draw cell content with exact positioning
        p.setFillColor(colors.black)

        # Item number (centered)
        p.drawCentredString(table_x + 20, current_y - 10, item['id'])

        # Description (left aligned with padding)
        desc = item['desc']
        if len(desc) > 50:
            desc = desc[:47] + "..."
        p.drawString(table_x + 45, current_y - 10, desc)

        # Weight (centered)
        p.drawCentredString(table_x + 415, current_y - 10, str(item['wt']))

        # Score (centered)
        p.drawCentredString(table_x + 465, current_y - 10, f"{score:.1f}")

        # Checkbox (centered)
        checkbox_x = table_x + 490
        checkbox_y = current_y - 12
        p.rect(checkbox_x, checkbox_y, 10, 10)
        if score > 0:
            # Draw X in checkbox
            p.line(checkbox_x + 1, checkbox_y + 1, checkbox_x + 9, checkbox_y + 9)
            p.line(checkbox_x + 9, checkbox_y + 1, checkbox_x + 1, checkbox_y + 9)

    # Move to bottom of table
    y = current_y - row_height - 30

    # === COMMENTS SECTION ===
    if y < 150:
        p.showPage()
        y = height - 50

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Inspector's Comments:")
    y -= 20

    # Comments box with border
    comments_height = 60
    p.setLineWidth(1)
    p.rect(50, y - comments_height, width - 100, comments_height)

    # Comments content
    p.setFont("Helvetica", 9)
    comments = form_data['comments'] or ''
    if comments:
        lines = []
        words = comments.split()
        current_line = ""
        for word in words:
            if len(current_line + word) < 80:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())

        for i, line in enumerate(lines[:4]):  # Max 4 lines
            p.drawString(55, y - 15 - (i * 12), line)
    else:
        p.drawString(55, y - 25, "No comments provided.")

    y -= 80

    # === SIGNATURES SECTION ===
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "SIGNATURES")
    y -= 25

    # Draw signature section border
    p.setLineWidth(1)
    p.line(50, y + 10, width - 50, y + 10)

    p.setFont("Helvetica", 10)

    # Inspector signature
    p.drawString(50, y, "Inspector's Signature:")
    p.line(160, y - 2, 300, y - 2)
    p.drawString(165, y, form_data['inspector_signature'] or '')

    # Received by signature
    p.drawString(350, y, "Rec'd By:")
    p.line(410, y - 2, 550, y - 2)
    p.drawString(415, y, form_data['received_by'] or '')

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=barbershop_inspection_{form_id}.pdf'
    return response

@app.route('/fix_all_forms_to_pass_fail')
def fix_all_forms_to_pass_fail():
    """Fix ALL forms to show Pass/Fail instead of Satisfactory/Unsatisfactory"""
    if 'admin' not in session and 'inspector' not in session:
        return "Access denied"

    conn = get_db_connection()
    c = conn.cursor()

    total_updated = 0

    # 1. Fix RESIDENTIAL inspections
    print("=== FIXING RESIDENTIAL INSPECTIONS ===")
    c.execute("""
        SELECT id, overall_score, critical_score, result
        FROM residential_inspections
    """)

    residential_inspections = c.fetchall()
    residential_updated = 0

    for row in residential_inspections:
        inspection_id, overall_score, critical_score, current_result = row
        overall_score = float(overall_score) if overall_score else 0
        critical_score = float(critical_score) if critical_score else 0

        # Residential: Pass if overall >= 70 and critical >= 61
        new_result = 'Pass' if overall_score >= 70 and critical_score >= 61 else 'Fail'

        c.execute("UPDATE residential_inspections SET result = ? WHERE id = ?", (new_result, inspection_id))
        residential_updated += 1
        print(f"Residential {inspection_id}: Overall: {overall_score}, Critical: {critical_score} → {new_result}")

    # 2. Fix MAIN INSPECTIONS (Food, Barbershop, etc.)
    print("=== FIXING MAIN INSPECTIONS ===")
    c.execute("""
        SELECT id, overall_score, critical_score, form_type, result
        FROM inspections
    """)

    main_inspections = c.fetchall()
    main_updated = 0

    for row in main_inspections:
        inspection_id, overall_score, critical_score, form_type, current_result = row
        overall_score = float(overall_score) if overall_score else 0
        critical_score = float(critical_score) if critical_score else 0

        # Calculate new result based on form type (ALL should be Pass/Fail)
        if form_type == 'Food Establishment':
            new_result = 'Pass' if overall_score >= 70 and critical_score >= 59 else 'Fail'
        elif form_type == 'Spirit Licence Premises':
            new_result = 'Pass' if overall_score >= 70 and critical_score >= 60 else 'Fail'
        elif form_type == 'Swimming Pool':
            new_result = 'Pass' if overall_score >= 70 else 'Fail'
        elif form_type == 'Small Hotel':
            new_result = 'Pass' if overall_score >= 70 else 'Fail'
        elif form_type == 'Barbershop':
            # CHANGED: Barbershop now uses Pass/Fail instead of Satisfactory/Unsatisfactory
            new_result = 'Pass' if overall_score >= 60 and critical_score >= 60 else 'Fail'
        elif form_type == 'Institutional Health':
            new_result = 'Pass' if overall_score >= 70 and critical_score >= 70 else 'Fail'
        else:
            new_result = 'Pass' if overall_score >= 70 else 'Fail'

        c.execute("UPDATE inspections SET result = ? WHERE id = ?", (new_result, inspection_id))
        main_updated += 1
        print(f"{form_type} {inspection_id}: Overall: {overall_score}, Critical: {critical_score} → {new_result}")

    total_updated = residential_updated + main_updated

    conn.commit()
    conn.close()

    return f"""
    <h1>✅ Fixed ALL Forms to Pass/Fail!</h1>
    <p><strong>Residential inspections updated:</strong> {residential_updated}</p>
    <p><strong>Main inspections updated:</strong> {main_updated}</p>
    <p><strong>Total records updated:</strong> {total_updated}</p>
    <br>
    <h3>All forms now show:</h3>
    <ul>
        <li>✅ <strong>Pass</strong> - when criteria are met</li>
        <li>❌ <strong>Fail</strong> - when criteria are not met</li>
        <li>🏁 <strong>Completed</strong> - for burial forms only</li>
    </ul>
    <br>
    <a href='/dashboard' style='background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>Back to Dashboard</a>
    """


@app.route('/get_inspections_with_status')
def get_inspections_with_status():
    """Get inspections with calculated Pass/Fail status for dashboard"""
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    # Get all inspections and calculate status based on scores
    c.execute("""
        SELECT id, establishment_name, owner, address, license_no, inspector_name, 
               inspection_date, inspection_time, type_of_establishment, purpose_of_visit, 
               action, result, scores, comments, created_at, form_type, inspector_code, 
               no_of_employees, food_inspected, food_condemned, overall_score, critical_score
        FROM inspections 
        ORDER BY created_at DESC
    """)

    inspections = []
    for row in c.fetchall():
        inspection_data = {
            'id': row[0],
            'establishment_name': row[1] or '',
            'owner': row[2] or '',
            'address': row[3] or '',
            'license_no': row[4] or '',
            'inspector_name': row[5] or '',
            'inspection_date': row[6] or '',
            'inspection_time': row[7] or '',
            'type_of_establishment': row[8] or '',
            'purpose_of_visit': row[9] or '',
            'action': row[10] or '',
            'result': row[11] or '',
            'scores': row[12] or '',
            'comments': row[13] or '',
            'created_at': row[14] or '',
            'form_type': row[15] or '',
            'inspector_code': row[16] or '',
            'no_of_employees': row[17] or '',
            'food_inspected': row[18] or 0,
            'food_condemned': row[19] or 0,
            'overall_score': row[20] or 0,
            'critical_score': row[21] or 0
        }

        # Calculate Pass/Fail status if not already set
        if not inspection_data['result'] or inspection_data['result'] == 'N/A':
            overall_score = float(inspection_data['overall_score']) if inspection_data['overall_score'] else 0
            critical_score = float(inspection_data['critical_score']) if inspection_data['critical_score'] else 0

            # Different criteria for different form types
            if inspection_data['form_type'] == 'Food Establishment':
                inspection_data['result'] = 'Pass' if overall_score >= 70 and critical_score >= 59 else 'Fail'
            elif inspection_data['form_type'] == 'Spirit Licence Premises':
                inspection_data['result'] = 'Pass' if overall_score >= 70 and critical_score >= 60 else 'Fail'
            elif inspection_data['form_type'] == 'Swimming Pool':
                inspection_data['result'] = 'Pass' if overall_score >= 70 else 'Fail'
            elif inspection_data['form_type'] == 'Small Hotel':
                inspection_data['result'] = 'Pass' if overall_score >= 70 else 'Fail'
            elif inspection_data['form_type'] == 'Barbershop':
                inspection_data[
                    'result'] = 'Satisfactory' if overall_score >= 60 and critical_score >= 60 else 'Unsatisfactory'
            elif inspection_data['form_type'] == 'Institutional Health':
                inspection_data['result'] = 'Pass' if overall_score >= 70 and critical_score >= 70 else 'Fail'
            else:
                inspection_data['result'] = 'Pass' if overall_score >= 70 else 'Fail'

        inspections.append(inspection_data)

    conn.close()
    return jsonify({'inspections': inspections})


# Route to fix barbershop database schema
@app.route('/fix_barbershop_db')
def fix_barbershop_db():
    if 'admin' not in session:
        return "Admin access required", 403
    columns_added = update_barbershop_db_schema()
    return f"Database updated! Added {columns_added} new columns."


# Initialize messages table (add this to your init_db function or run separately)
def init_messages_db():
    """Initialize the messages table"""
    from database import get_auto_increment, get_timestamp_default
    from db_config import get_db_type

    conn = get_db_connection()

    if get_db_type() == 'postgresql':
        conn.autocommit = True

    c = conn.cursor()

    auto_inc = get_auto_increment()
    timestamp = get_timestamp_default()

    # Create messages table
    c.execute(f'''CREATE TABLE IF NOT EXISTS messages (
        id {auto_inc},
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp {timestamp},
        is_read INTEGER DEFAULT 0,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (recipient_id) REFERENCES users(id)
    )''')

    if get_db_type() != 'postgresql':
        conn.commit()
    conn.close()
    print("Messages table initialized successfully")


def init_db():
    from database import get_auto_increment, get_timestamp_default
    from db_config import get_db_type

    conn = get_db_connection()

    # Enable autocommit for schema changes (prevents transaction errors on ALTER failures)
    if get_db_type() == 'postgresql':
        conn.autocommit = True

    c = conn.cursor()

    # Get database-specific syntax
    auto_inc = get_auto_increment()
    timestamp = get_timestamp_default()

    # Create tables
    c.execute(f'''CREATE TABLE IF NOT EXISTS users (
        id {auto_inc},
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('inspector', 'admin', 'medical_officer')),
        email TEXT,
        is_flagged INTEGER DEFAULT 0
    )''')
    c.execute(f'''CREATE TABLE IF NOT EXISTS login_history (
        id {auto_inc},
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        email TEXT,
        role TEXT NOT NULL,
        login_time {timestamp},
        ip_address TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute(f'''CREATE TABLE IF NOT EXISTS messages (
        id {auto_inc},
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp {timestamp},
        is_read INTEGER DEFAULT 0,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (recipient_id) REFERENCES users(id)
    )''')

    # Check if email column exists in users table and add it if not
    if get_db_type() == 'postgresql':
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
        columns = [row['column_name'] for row in c.fetchall()]
    else:
        c.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in c.fetchall()]

    if 'email' not in columns:
        try:
            c.execute('ALTER TABLE users ADD COLUMN email TEXT')
            if get_db_type() != 'postgresql':
                conn.commit()
        except Exception:
            pass  # Column might already exist

    # Insert default users
    try:
        if get_db_type() == 'postgresql':
            c.execute('INSERT INTO users (username, password, role, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING',
                      ('admin', 'adminpass', 'admin', 'admin@example.com'))
            c.execute('INSERT INTO users (username, password, role, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING',
                      ('medofficer', 'medpass', 'medical_officer', 'medofficer@example.com'))
            for i in range(1, 7):
                c.execute('INSERT INTO users (username, password, role, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING',
                          (f'inspector{i}', f'pass{i}', 'inspector', f'inspector{i}@example.com'))
            conn.commit()
        else:
            c.execute('INSERT OR IGNORE INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                      ('admin', 'adminpass', 'admin', 'admin@example.com'))
            c.execute('INSERT OR IGNORE INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                      ('medofficer', 'medpass', 'medical_officer', 'medofficer@example.com'))
            for i in range(1, 7):
                c.execute('INSERT OR IGNORE INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                          (f'inspector{i}', f'pass{i}', 'inspector', f'inspector{i}@example.com'))
            conn.commit()
    except Exception as e:
        logging.error(f"Database integrity error: {str(e)}")

    conn.close()


# Replace your existing login_post() function with this updated version

def draw_checkbox(canvas, x, y, checked=False, size=10):
    """Draw a checkbox at the specified position"""
    canvas.rect(x, y, size, size)
    if checked:
        canvas.line(x + 2, y + 2, x + size - 2, y + size - 2)
        canvas.line(x + 2, y + size - 2, x + size - 2, y + 2)


def create_form_header(canvas, form_title, form_id, width, height):
    """Create standard form header"""
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawCentredString(width/2, height-40, form_title)  # Fixed: drawCentredString instead of drawCentredText
    canvas.setFont("Helvetica", 10)
    canvas.drawString(50, height-60, f"Form ID: {form_id}")
    canvas.drawString(width-150, height-60, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    canvas.line(50, height-70, width-50, height-70)
    return height-90


# ============================================================================
# USER LOCATION TRACKING - Get parish coordinates for map display
# ============================================================================

def get_parish_coordinates(parish):
    """Returns approximate center coordinates for each Jamaican parish"""
    parish_locations = {
        'Kingston': {'lat': 18.0179, 'lng': -76.8099},
        'St. Andrew': {'lat': 18.0323, 'lng': -76.7981},
        'St. Thomas': {'lat': 17.9833, 'lng': -76.3500},
        'Portland': {'lat': 18.1089, 'lng': -76.4097},
        'St. Mary': {'lat': 18.3833, 'lng': -76.9333},
        'St. Ann': {'lat': 18.4333, 'lng': -77.2000},
        'Trelawny': {'lat': 18.3833, 'lng': -77.5833},
        'St. James': {'lat': 18.4762, 'lng': -77.9189},
        'Hanover': {'lat': 18.4167, 'lng': -78.1333},
        'Westmoreland': {'lat': 18.2500, 'lng': -78.1333},
        'St. Elizabeth': {'lat': 18.0833, 'lng': -77.7167},
        'Manchester': {'lat': 18.0500, 'lng': -77.5000},
        'Clarendon': {'lat': 18.0000, 'lng': -77.2500},
        'St. Catherine': {'lat': 18.0000, 'lng': -77.0000}
    }
    return parish_locations.get(parish, {'lat': 18.0179, 'lng': -76.8099})  # Default to Kingston


@app.route('/login', methods=['POST'])
def login_post():
    from db_config import execute_query

    username = request.form['username']
    password = request.form['password']
    login_type = request.form['login_type']
    ip_address = request.remote_addr

    conn = get_db_connection()
    c = execute_query(conn, "SELECT id, username, password, role, email, parish FROM users WHERE username = ? AND password = ?",
              (username, password))
    user = c.fetchone()

    if user and (
            (login_type == 'inspector' and user['role'] == 'inspector') or
            (login_type == 'admin' and user['role'] == 'admin') or
            (login_type == 'medical_officer' and user['role'] == 'medical_officer')):

        session['user_id'] = user['id']
        session[login_type] = user['username']  # ✅ FIXED HERE

        # Get REAL GPS coordinates from the login form (captured by browser geolocation)
        latitude = request.form.get('latitude', '')
        longitude = request.form.get('longitude', '')

        # Get user's parish from database
        try:
            parish = user['parish']
        except (KeyError, IndexError):
            parish = None

        # Record login attempt
        execute_query(conn,
            "INSERT INTO login_history (user_id, username, email, role, login_time, ip_address) VALUES (?, ?, ?, ?, ?, ?)",
            (user['id'], user['username'], user['email'], user['role'],
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ip_address))

        # Mark any old sessions for this user as inactive
        execute_query(conn, "UPDATE user_sessions SET is_active = 0, logout_time = ? WHERE username = ? AND is_active = 1",
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['username']))

        # Track new user session with REAL location (only if GPS coordinates were captured)
        if latitude and longitude:
            try:
                lat_float = float(latitude)
                lng_float = float(longitude)
                execute_query(conn,
                    "INSERT INTO user_sessions (username, user_role, login_time, last_activity, location_lat, location_lng, parish, ip_address, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (user['username'], user['role'],
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     lat_float, lng_float,
                     parish, ip_address, 1))
                print(f"✅ User session tracked with GPS: {user['username']} at ({lat_float}, {lng_float})")
            except (ValueError, TypeError) as e:
                print(f"⚠️ Invalid GPS coordinates, session not tracked: {e}")
        else:
            print(f"⚠️ No GPS coordinates provided, user {user['username']} will not appear on map")

        conn.commit()
        conn.close()

        # Log audit event
        log_audit_event(username, 'login', ip_address, f'Successful {login_type} login')

        if login_type == 'inspector':
            return redirect(url_for('dashboard'))
        elif login_type == 'admin':
            return redirect(url_for('admin'))
        else:  # medical_officer
            return redirect(url_for('medical_officer'))

    conn.close()

    # Log failed login attempt
    log_audit_event(username, 'login_failed', ip_address, f'Failed {login_type} login attempt')

    return render_template('login.html', error='Invalid credentials')


@app.route('/parish_leaderboard')
def parish_leaderboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('parish_leaderboard.html')


@app.route('/api/parish_stats')
def get_parish_stats():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    # Get parish statistics
    c.execute("""
        SELECT 
            parish,
            COUNT(*) as total_inspections,
            SUM(CASE WHEN result = 'Pass' OR result = 'Satisfactory' THEN 1 ELSE 0 END) as passes,
            ROUND(
                (SUM(CASE WHEN result = 'Pass' OR result = 'Satisfactory' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 1
            ) as pass_rate
        FROM (
            SELECT parish, result FROM inspections WHERE parish IS NOT NULL
            UNION ALL
            SELECT parish, result FROM residential_inspections WHERE parish IS NOT NULL
        )
        GROUP BY parish
        ORDER BY pass_rate DESC
    """)

    parish_stats = []
    for row in c.fetchall():
        parish_stats.append({
            'parish': row[0],
            'total_inspections': row[1],
            'passes': row[2],
            'failures': row[1] - row[2],
            'pass_rate': row[3]
        })

    conn.close()
    return jsonify(parish_stats)


@app.route('/api/admin/users', methods=['GET'])
def get_users():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    try:
        c = conn.cursor()
        # Get ALL users, not just inspectors
        c.execute('SELECT id, username, email, role, is_flagged FROM users ORDER BY role, username')
        users = []
        for row in c.fetchall():
            users.append({
                'id': row['id'],
                'username': row['username'],
                'email': row['email'] or 'N/A',
                'role': row['role'],
                'is_flagged': bool(row['is_flagged'])
            })
        return jsonify(users)
    except Exception as e:
        print(f"Error in get_users: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        conn.close()
# These are the missing routes needed for your admin dashboard

@app.route('/api/admin/audit_log')
def get_audit_log():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        from database import get_auto_increment, get_timestamp_default
        from db_config import get_db_type

        conn = get_db_connection()
        cursor = conn.cursor()

        auto_inc = get_auto_increment()
        timestamp = get_timestamp_default()

        # Create audit_log table if it doesn't exist
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS audit_log (
                id {auto_inc},
                timestamp {timestamp},
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                ip_address TEXT,
                details TEXT
            )
        ''')

        # Get audit log entries
        cursor.execute('''
            SELECT timestamp, user, action, ip_address, details 
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''')

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'timestamp': row[0],
                'user': row[1],
                'action': row[2],
                'ip_address': row[3],
                'details': row[4]
            })

        # If no audit logs exist, create some sample data from login history
        if not logs:
            cursor.execute('''
                SELECT login_time, username, 'login' as action, ip_address, role 
                FROM login_history 
                ORDER BY login_time DESC 
                LIMIT 50
            ''')
            for row in cursor.fetchall():
                logs.append({
                    'timestamp': row[0],
                    'user': row[1],
                    'action': row[2],
                    'ip_address': row[3],
                    'details': f'{row[4]} login'
                })

        conn.close()
        return jsonify(logs)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/update_database_schema')
def update_schema():
    """Run this once to update your database schema"""
    if 'admin' not in session:
        return "Admin access required"

    try:
        update_database_schema()
        return "✅ Database schema updated successfully! <a href='/admin'>Back to Admin</a>"
    except Exception as e:
        return f"❌ Error updating schema: {str(e)}"


# Add this route to your app.py file after the other admin routes
@app.route('/api/admin/search_inspections', methods=['GET'])
def search_inspections():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    from db_config import execute_query

    query = request.args.get('q', '').strip().lower()

    if len(query) < 2:
        return jsonify([])

    try:
        conn = get_db_connection()

        results = []

        # Search in main inspections table
        cursor = execute_query(conn, """
            SELECT id, establishment_name, owner, license_no, form_type, inspector_name
            FROM inspections
            WHERE LOWER(establishment_name) LIKE ?
               OR LOWER(owner) LIKE ?
               OR LOWER(license_no) LIKE ?
               OR LOWER(inspector_name) LIKE ?
            LIMIT 20
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))

        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'formType': row[4] or 'Food Establishment',
                'name': row[1] or 'N/A',
                'owner': row[2] or 'N/A',
                'license': row[3] or 'N/A',
                'inspector': row[5] or 'N/A'
            })

        # Search in residential inspections
        cursor = execute_query(conn, """
            SELECT id, premises_name, owner, address, inspector_name
            FROM residential_inspections
            WHERE LOWER(premises_name) LIKE ?
               OR LOWER(owner) LIKE ?
               OR LOWER(inspector_name) LIKE ?
            LIMIT 10
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))

        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'formType': 'Residential',
                'name': row[1] or 'N/A',
                'owner': row[2] or 'N/A',
                'address': row[3] or 'N/A',
                'inspector': row[4] or 'N/A'
            })

        # Search in burial inspections
        cursor = execute_query(conn, """
            SELECT id, applicant_name, deceased_name, burial_location
            FROM burial_site_inspections
            WHERE LOWER(applicant_name) LIKE ?
               OR LOWER(deceased_name) LIKE ?
               OR LOWER(burial_location) LIKE ?
            LIMIT 10
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))

        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'formType': 'Burial',
                'applicant': row[1] or 'N/A',
                'deceased': row[2] or 'N/A',
                'location': row[3] or 'N/A',
                'inspector': 'N/A',
                'name': row[1] or 'N/A',
                'owner': row[2] or 'N/A'
            })

        # Search in meat processing inspections
        cursor = execute_query(conn, """
            SELECT id, establishment_name, owner_operator, establishment_no, inspector_name
            FROM meat_processing_inspections
            WHERE LOWER(establishment_name) LIKE ?
               OR LOWER(owner_operator) LIKE ?
               OR LOWER(establishment_no) LIKE ?
               OR LOWER(inspector_name) LIKE ?
            LIMIT 10
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))

        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'formType': 'Meat Processing',
                'name': row[1] or 'N/A',
                'owner': row[2] or 'N/A',
                'license': row[3] or 'N/A',
                'inspector': row[4] or 'N/A'
            })

        conn.close()
        return jsonify(results[:20])  # Limit total results to 20

    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

# Replace the existing backend routes in app.py with these fixed versions

@app.route('/api/inspector/tasks', methods=['GET'])
def get_inspector_tasks():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get tasks assigned to this inspector
        cursor.execute('''
            SELECT id, title, due_date, details, status, created_at
            FROM tasks 
            WHERE assignee_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'title': row[1],
                'due_date': row[2],
                'details': row[3],
                'status': row[4],
                'created_at': row[5]
            })

        conn.close()
        return jsonify({'tasks': tasks})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/inspector/tasks/<int:task_id>/update', methods=['POST'])
def update_task_status(task_id):  # Fixed parameter name to match route
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        new_status = data.get('status')
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update task status (only if assigned to this inspector)
        cursor.execute('''
            UPDATE tasks 
            SET status = ?
            WHERE id = ? AND assignee_id = ?
        ''', (new_status, task_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Task not found or not assigned to you'}), 404

        conn.commit()
        conn.close()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/inspector/tasks/<int:task_id>/respond', methods=['POST'])
def respond_to_task(task_id):
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        response = data.get('response')  # 'accept' or 'decline'
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update task status based on response
        if response == 'accept':
            new_status = 'In Progress'
        elif response == 'decline':
            new_status = 'Declined'
        else:
            conn.close()
            return jsonify({'error': 'Invalid response'}), 400

        cursor.execute('''
            UPDATE tasks 
            SET status = ?
            WHERE id = ? AND assignee_id = ?
        ''', (new_status, task_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Task not found or not assigned to you'}), 404

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'new_status': new_status})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/inspector/tasks/unread_count', methods=['GET'])
def get_unread_task_count():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from db_config import execute_query

        user_id = session.get('user_id')
        conn = get_db_connection()

        # Count unread tasks (status = 'Pending')
        cursor = execute_query(conn, '''
            SELECT COUNT(*)
            FROM tasks
            WHERE assignee_id = ? AND status = 'Pending'
        ''', (user_id,))

        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({'count': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/inspector_performance')
def get_inspector_performance():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        time_frame = request.args.get('time_frame', 'monthly')
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get inspector performance from your existing tables
        cursor.execute('''
            SELECT 
                inspector_name,
                COUNT(*) as completed,
                AVG(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) * 100 as pass_rate,
                '30 min' as avg_time,
                0 as overdue
            FROM (
                SELECT inspector_name, result FROM inspections
                WHERE inspector_name IS NOT NULL AND inspector_name != ''
                UNION ALL
                SELECT inspector_name, result FROM residential_inspections
                WHERE inspector_name IS NOT NULL AND inspector_name != ''
            ) 
            GROUP BY inspector_name
            HAVING inspector_name IS NOT NULL
        ''')

        inspectors = []
        for row in cursor.fetchall():
            inspectors.append({
                'name': row[0] or 'Unknown',
                'completed': row[1],
                'pass_rate': round(row[2], 1) if row[2] else 0,
                'avg_time': row[3],
                'overdue': row[4]
            })

        conn.close()
        return jsonify({'inspectors': inspectors})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/alerts')
def get_alerts():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        alerts = []

        # Check for failed inspections
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT result FROM inspections WHERE result = 'Fail'
                UNION ALL
                SELECT result FROM residential_inspections WHERE result = 'Fail'
            )
        ''')

        failed_count = cursor.fetchone()[0]

        if failed_count > 0:
            alerts.append({
                'title': 'Failed Inspections Alert',
                'description': f'{failed_count} inspections have failed and may need follow-up',
                'severity': 'critical',
                'timestamp': datetime.now().isoformat()
            })

        # Check for recent inspections
        cursor.execute('''
            SELECT COUNT(*) FROM inspections 
            WHERE date(created_at) = date('now')
        ''')

        today_count = cursor.fetchone()[0]

        if today_count > 10:
            alerts.append({
                'title': 'High Activity Alert',
                'description': f'{today_count} inspections completed today',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            })

        # Check for inspectors with high workload today
        cursor.execute('''
            SELECT inspector_name, COUNT(*) as count 
            FROM inspections 
            WHERE date(created_at) = date('now') AND inspector_name IS NOT NULL
            GROUP BY inspector_name 
            HAVING count > 5
        ''')

        for row in cursor.fetchall():
            alerts.append({
                'title': 'High Workload Alert',
                'description': f'Inspector {row[0]} has {row[1]} inspections today',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            })

        conn.close()
        return jsonify(alerts)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/inspection_locations')
def get_inspection_locations():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        filter_type = request.args.get('filter', 'all')
        conn = get_db_connection()
        cursor = conn.cursor()

        locations = []

        # Get locations from your existing data
        cursor.execute('''
            SELECT 
                id, 
                'Food Establishment' as form_type, 
                result as status, 
                created_at as date,
                address,
                establishment_name
            FROM inspections
            WHERE form_type = 'Food Establishment'
            UNION ALL
            SELECT 
                id, 
                'Residential' as form_type, 
                result as status, 
                created_at as date,
                address,
                premises_name
            FROM residential_inspections
            LIMIT 50
        ''')

        # Sample coordinates around Kingston, Jamaica
        base_lat = 18.0179
        base_lng = -76.8099

        for i, row in enumerate(cursor.fetchall()):
            # Generate sample coordinates (you'd replace this with actual geocoding)
            lat_offset = (i % 20 - 10) * 0.01  # Random spread
            lng_offset = (i % 15 - 7) * 0.01

            locations.append({
                'form_id': row[0],
                'form_type': row[1],
                'status': row[2] or 'Unknown',
                'date': row[3],
                'address': row[4],
                'name': row[5],
                'latitude': base_lat + lat_offset,
                'longitude': base_lng + lng_offset
            })

        if filter_type != 'all':
            locations = [loc for loc in locations if loc['status'].lower() == filter_type.lower()]

        conn.close()
        return jsonify(locations)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/reports')
def get_reports():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        metric = request.args.get('metric', 'inspections')
        timeframe = request.args.get('timeframe', 'monthly')

        conn = get_db_connection()
        cursor = conn.cursor()

        if metric == 'inspections':
            cursor.execute('''
                SELECT 
                    form_type as type,
                    COUNT(*) as count,
                    AVG(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) * 100 as pass_rate
                FROM inspections
                WHERE form_type IS NOT NULL
                GROUP BY form_type
                UNION ALL
                SELECT 
                    'Residential' as type,
                    COUNT(*) as count,
                    AVG(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) * 100 as pass_rate
                FROM residential_inspections
            ''')

            data = []
            for row in cursor.fetchall():
                data.append([row[0], row[1], f"{row[2]:.1f}%" if row[2] else "0%"])

            report = {
                'summary': f'Inspection summary for {timeframe} period',
                'headers': ['Type', 'Count', 'Pass Rate'],
                'data': data
            }

        elif metric == 'user_activity':
            cursor.execute('''
                SELECT 
                    role,
                    COUNT(*) as logins
                FROM login_history
                GROUP BY role
            ''')

            data = []
            for row in cursor.fetchall():
                data.append([row[0], row[1]])

            report = {
                'summary': f'User activity summary for {timeframe} period',
                'headers': ['Role', 'Login Count'],
                'data': data
            }

        conn.close()
        return jsonify(report)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/system_health')
def get_system_health():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        # Get actual system metrics from your database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate some real metrics
        cursor.execute('SELECT COUNT(*) FROM inspections')
        total_inspections = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        # Generate health metrics (you can replace with actual monitoring)
        health = {
            'uptime': 99.5,
            'db_response': 45,  # milliseconds
            'error_rate': 0.2,
            'history': []
        }

        # Generate sample history data
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            health['history'].append({
                'timestamp': date.isoformat(),
                'uptime': 99.5 + (i * 0.01),
                'db_response': 45 + (i * 0.5),
                'error_rate': 0.2 + (i * 0.01)
            })

        conn.close()
        return jsonify(health)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Modify the existing tasks route to include notifications
@app.route('/api/admin/tasks', methods=['GET', 'POST'])
def handle_tasks():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        from database import get_auto_increment, get_timestamp_default
        from db_config import get_db_type

        conn = get_db_connection()
        cursor = conn.cursor()

        auto_inc = get_auto_increment()
        timestamp = get_timestamp_default()

        # Create tasks table if it doesn't exist - updated with notification field
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS tasks (
                id {auto_inc},
                title TEXT NOT NULL,
                assignee_id INTEGER,
                assignee_name TEXT,
                due_date TEXT,
                details TEXT,
                status TEXT DEFAULT 'Pending',
                created_at {timestamp},
                is_notified INTEGER DEFAULT 0
            )
        ''')

        if request.method == 'GET':
            cursor.execute('''
                SELECT id, title, assignee_name, due_date, status
                FROM tasks
                ORDER BY created_at DESC
            ''')

            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'id': row[0],
                    'title': row[1],
                    'assignee': row[2] or 'Unassigned',
                    'due_date': row[3],
                    'status': row[4]
                })

            conn.close()
            return jsonify(tasks)

        elif request.method == 'POST':
            data = request.get_json()

            # Handle assignee - can be username or ID
            assignee = data.get('assignee')
            assignee_id = None
            assignee_name = assignee

            # Check if assignee is a username/string or ID
            if assignee and not assignee.isdigit():
                # It's a username, look up the ID
                cursor.execute('SELECT id FROM users WHERE username = ?', (assignee,))
                user = cursor.fetchone()
                assignee_id = user[0] if user else None
                assignee_name = assignee
            elif assignee and assignee.isdigit():
                # It's a user ID
                cursor.execute('SELECT username FROM users WHERE id = ?', (int(assignee),))
                user = cursor.fetchone()
                assignee_name = user[0] if user else 'Unknown'
                assignee_id = int(assignee)

            cursor.execute('''
                INSERT INTO tasks (title, assignee_id, assignee_name, due_date, details, status)
                VALUES (?, ?, ?, ?, ?, 'Pending')
            ''', (data['title'], assignee_id, assignee_name, data['due_date'], data.get('description', '')))

            conn.commit()
            conn.close()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/inspectors')
def get_inspectors():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get inspectors from users table
        cursor.execute('''
            SELECT id, username 
            FROM users 
            WHERE role = 'inspector'
        ''')

        inspectors = []
        for row in cursor.fetchall():
            inspectors.append({
                'id': row[0],
                'name': row[1]
            })

        conn.close()
        return jsonify(inspectors)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/security_metrics')
def get_security_metrics():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user counts for MFA metrics (simulated)
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "inspector"')
        total_users = cursor.fetchone()[0]

        # Simulate MFA adoption (you'd track this in your users table)
        mfa_enabled = int(total_users * 0.7)
        mfa_disabled = total_users - mfa_enabled

        # Get recent login attempts as security events
        cursor.execute('''
            SELECT login_time, username, role, ip_address
            FROM login_history 
            ORDER BY login_time DESC 
            LIMIT 10
        ''')

        events = []
        for i, row in enumerate(cursor.fetchall()):
            events.append({
                'timestamp': row[0],
                'type': 'Login Attempt',
                'user': row[1],
                'details': f'Successful {row[2]} login from {row[3]}',
                'count': i + 1
            })

        metrics = {
            'mfa_enabled': mfa_enabled,
            'mfa_disabled': mfa_disabled,
            'events': events
        }

        conn.close()
        return jsonify(metrics)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/messages/<int:user_id>')
    def get_messages_for_user(user_id):
        """Get messages between current user and specified user"""
        if 'admin' not in session and 'inspector' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            current_user_id = session.get('user_id')
            if not current_user_id:
                return jsonify({'error': 'User not logged in'}), 401

            conn = get_db_connection()
            c = conn.cursor()

            # Get messages between current user and target user
            c.execute('''
                SELECT m.content, m.timestamp, m.sender_id, m.recipient_id,
                       s.username as sender_name, r.username as recipient_name
                FROM messages m
                JOIN users s ON m.sender_id = s.id
                JOIN users r ON m.recipient_id = r.id
                WHERE (m.sender_id = ? AND m.recipient_id = ?) 
                   OR (m.sender_id = ? AND m.recipient_id = ?)
                ORDER BY m.timestamp ASC
            ''', (current_user_id, user_id, user_id, current_user_id))

            messages = []
            for row in c.fetchall():
                messages.append({
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'sender_id': row['sender_id'],
                    'recipient_id': row['recipient_id'],
                    'sender_name': row['sender_name'],
                    'recipient_name': row['recipient_name'],
                    'is_sent': row['sender_id'] == current_user_id
                })

            conn.close()
            return jsonify(messages)

        except Exception as e:
            print(f"Error getting messages: {e}")
            return jsonify({'error': 'Failed to load messages'}), 500



    # 2. Route to send a message
    @app.route('/api/send_message', methods=['POST'])
    def send_message():
        """Send a message to another user"""
        if 'admin' not in session and 'inspector' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            data = request.get_json()
            recipient_id = data.get('recipient_id')
            content = data.get('content', '').strip()

            if not recipient_id or not content:
                return jsonify({'success': False, 'error': 'Missing recipient or content'}), 400

            sender_id = session.get('user_id')

            conn = get_db_connection()
            c = conn.cursor()

            # Insert message
            c.execute('''
                INSERT INTO messages (sender_id, recipient_id, content, timestamp, is_read)
                VALUES (?, ?, ?, ?, 0)
            ''', (sender_id, recipient_id, content, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            return jsonify({'success': True, 'message': 'Message sent successfully'})

        except Exception as e:
            print(f"Error sending message: {e}")
            return jsonify({'success': False, 'error': 'Failed to send message'}), 500

    @app.route('/small_hotels/inspection/<int:id>')
    def small_hotels_inspection_detail(id):
        if 'inspector' not in session and 'admin' not in session:
            return redirect(url_for('login'))

        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Small Hotel'", (id,))
        inspection = cursor.fetchone()

        if not inspection:
            conn.close()
            return "Small Hotels inspection not found", 404

        inspection_dict = dict(inspection)

        # Get individual scores from inspection_items table
        cursor.execute("SELECT item_id, obser, error FROM inspection_items WHERE inspection_id = ?", (id,))
        items = cursor.fetchall()

        obser_scores = {}
        error_scores = {}
        for item in items:
            obser_scores[item[0]] = item[1] or '0'
            error_scores[item[0]] = item[2] or '0'

        inspection_dict['obser'] = obser_scores
        inspection_dict['error'] = error_scores

        conn.close()

        # Parse photos from JSON string to Python list
        import json
        photos = []
        if inspection_dict.get('photo_data'):
            try:
                photos = json.loads(inspection_dict.get('photo_data', '[]'))
            except:
                photos = []

        return render_template('small_hotels_inspection_detail.html',
                               inspection=inspection_dict,
                               checklist=SMALL_HOTELS_CHECKLIST_ITEMS,
                               photo_data=photos)


    # 3. Route to get all users for contact list
    @app.route('/api/users')
    def get_all_users():
        """Get all users for contact list"""
        if 'admin' not in session and 'inspector' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            current_user_id = session.get('user_id')
            conn = get_db_connection()
            c = conn.cursor()

            # Get all users except current user
            c.execute('''
                SELECT id, username, role 
                FROM users 
                WHERE id != ?
                ORDER BY role, username
            ''', (current_user_id,))

            users = []
            for row in c.fetchall():
                # Get unread message count for this user
                c.execute('''
                    SELECT COUNT(*) 
                    FROM messages 
                    WHERE sender_id = ? AND recipient_id = ? AND is_read = 0
                ''', (row['id'], current_user_id))

                unread_count = c.fetchone()[0]

                users.append({
                    'id': row['id'],
                    'username': row['username'],
                    'role': row['role'],
                    'unread_count': unread_count
                })

            conn.close()
            return jsonify(users)

        except Exception as e:
            print(f"Error loading users: {e}")
            return jsonify({'error': 'Failed to load users'}), 500

    # 4. Route to mark messages as read
    @app.route('/api/mark_messages_read/<int:user_id>', methods=['POST'])
    def mark_messages_read(user_id):
        """Mark all messages from a user as read"""
        if 'admin' not in session and 'inspector' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            current_user_id = session.get('user_id')
            conn = get_db_connection()
            c = conn.cursor()

            c.execute('''
                UPDATE messages 
                SET is_read = 1 
                WHERE sender_id = ? AND recipient_id = ? AND is_read = 0
            ''', (user_id, current_user_id))

            conn.commit()
            conn.close()

            return jsonify({'success': True})

        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return jsonify({'success': False, 'error': 'Failed to mark messages as read'}), 500

    # 2. Route to check unread messages
    @app.route('/api/admin/unread_messages')
    def get_unread_messages():
        """Get count of unread messages for admin"""
        if 'admin' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            admin_id = session.get('user_id')
            conn = get_db_connection()
            c = conn.cursor()

            # Get total unread count
            c.execute('''
                SELECT COUNT(*) as total
                FROM messages 
                WHERE recipient_id = ? AND is_read = 0
            ''', (admin_id,))

            result = c.fetchone()
            total_unread = result['total'] if result else 0

            conn.close()

            return jsonify({
                'count': total_unread,
                'by_user': {}
            })

        except Exception as e:
            print(f"Error getting unread messages: {e}")
            return jsonify({'count': 0, 'by_user': {}})

    # Add these missing routes to your app.py file
    # These work with the routes you already have

    @app.route('/api/admin/mark_messages_read/<int:user_id>', methods=['POST'])
    def mark_messages_read(user_id):
        """Mark all messages from a user as read"""
        if 'admin' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            admin_id = session.get('user_id')
            conn = get_db_connection()
            c = conn.cursor()

            c.execute('''
                UPDATE messages 
                SET is_read = 1 
                WHERE sender_id = ? AND recipient_id = ? AND is_read = 0
            ''', (user_id, admin_id))

            conn.commit()
            conn.close()

            return jsonify({'success': True})

        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return jsonify({'success': False, 'error': 'Failed to mark messages as read'}), 500

    @app.route('/debug_session')
    def debug_session():
        """Debug route to check session data"""
        if 'admin' not in session:
            return jsonify({'error': 'Not logged in as admin'})

        return jsonify({
            'user_id': session.get('user_id'),
            'admin': session.get('admin', False),
            'inspector': session.get('inspector', False),
            'medical_officer': session.get('medical_officer', False)
        })

    @app.route('/setup_complete_messaging')
    def setup_complete_messaging():
        """Complete setup for messaging system with sample data"""
        if 'admin' not in session:
            return "Admin access required"

        try:
            from database import get_auto_increment, get_timestamp_default
            from db_config import get_db_type

            conn = get_db_connection()
            c = conn.cursor()

            auto_inc = get_auto_increment()
            timestamp = get_timestamp_default()

            # Create messages table if it doesn't exist
            c.execute(f'''CREATE TABLE IF NOT EXISTS messages (
                id {auto_inc},
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp {timestamp},
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id)
            )''')

            # Check if users table has required columns
            if get_db_type() == 'postgresql':
                c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
                columns = [row['column_name'] for row in c.fetchall()]
            else:
                c.execute("PRAGMA table_info(users)")
                columns = [row[1] for row in c.fetchall()]

            if 'email' not in columns:
                c.execute('ALTER TABLE users ADD COLUMN email TEXT')
                print("Added email column to users table")

            if 'is_flagged' not in columns:
                c.execute('ALTER TABLE users ADD COLUMN is_flagged INTEGER DEFAULT 0')
                print("Added is_flagged column to users table")

            # Update existing users with default emails if they don't have them
            c.execute("UPDATE users SET email = username || '@health.gov.jm' WHERE email IS NULL OR email = ''")

            # Create some sample messages for testing
            c.execute("SELECT COUNT(*) FROM messages")
            message_count = c.fetchone()[0]

            if message_count == 0:
                print("Creating sample messages...")

                # Get admin and inspector IDs
                c.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
                admin_result = c.fetchone()

                c.execute("SELECT id FROM users WHERE role = 'inspector' LIMIT 1")
                inspector_result = c.fetchone()

                if admin_result and inspector_result:
                    admin_id = admin_result[0]
                    inspector_id = inspector_result[0]

                    sample_messages = [
                        (inspector_id, admin_id, "Hello admin, I have a question about the new inspection forms.",
                         datetime.now().isoformat(), 0),
                        (admin_id, inspector_id, "Hi! I'm here to help. What would you like to know?",
                         datetime.now().isoformat(), 1),
                        (inspector_id, admin_id, "How do I handle failed inspections that need follow-up?",
                         datetime.now().isoformat(), 0),
                        (admin_id, inspector_id,
                         "For failed inspections, you should schedule a re-inspection within 30 days and document the corrective actions needed.",
                         datetime.now().isoformat(), 1)
                    ]

                    for message in sample_messages:
                        c.execute('''
                            INSERT INTO messages (sender_id, recipient_id, content, timestamp, is_read)
                            VALUES (?, ?, ?, ?, ?)
                        ''', message)

                    print("Sample messages created!")

            conn.commit()
            conn.close()

            return """
            <h1>✅ Complete Messaging System Setup!</h1>
            <p>The following has been set up:</p>
            <ul>
                <li>✅ Messages table created</li>
                <li>✅ User table updated with email and flagged columns</li>
                <li>✅ Sample messages created for testing</li>
                <li>✅ All required routes are active</li>
            </ul>
            <br>
            <p><strong>Your messaging system is now ready!</strong></p>
            <p>Go back to your <a href='/admin'>Admin Dashboard</a> and click the messaging icon (💬) in the top right.</p>
            <br>
            <h3>How to test:</h3>
            <ol>
                <li>Click the messaging icon (💬) in the top right of your admin dashboard</li>
                <li>You should see a list of all users in the system</li>
                <li>Click on any user to start a conversation</li>
                <li>Type a message and hit send</li>
                <li>The badge will show unread message counts</li>
            </ol>
            <br>
            <a href="/debug_messaging">🔍 Debug Messaging System</a> | 
            <a href="/admin">🏠 Back to Dashboard</a>
            """

        except Exception as e:
            return f"❌ Error setting up messaging: {e}"

    @app.route('/debug_messaging')
    def debug_messaging():
        """Debug messaging system"""
        if 'admin' not in session:
            return "Admin access required"

        conn = get_db_connection()
        c = conn.cursor()

        # Check users
        c.execute("SELECT id, username, email, role, is_flagged FROM users")
        users = c.fetchall()

        # Check messages
        c.execute("""
            SELECT m.id, s.username as sender, r.username as recipient, 
                   m.content, m.timestamp, m.is_read
            FROM messages m
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.recipient_id = r.id
            ORDER BY m.timestamp DESC
            LIMIT 10
        """)
        messages = c.fetchall()

        # Check current session
        current_user_id = session.get('user_id')

        conn.close()

        html = f"""
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .success {{ color: green; font-weight: bold; }}
            .error {{ color: red; font-weight: bold; }}
            .info {{ background: #e7f3ff; padding: 10px; border-left: 4px solid #2196F3; margin: 10px 0; }}
        </style>

        <h1>🔍 Messaging System Debug</h1>

        <div class="info">
            <strong>Current Session:</strong> User ID = {current_user_id}, Admin = {session.get('admin', False)}
        </div>

        <h2>Users in System ({len(users)} total):</h2>
        <table>
            <tr>
                <th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Flagged</th>
            </tr>
        """

        for user in users:
            flagged_status = 'Yes' if user[4] else 'No'
            html += f"""
            <tr>
                <td>{user[0]}</td>
                <td>{user[1]}</td>
                <td>{user[2] or 'N/A'}</td>
                <td>{user[3]}</td>
                <td>{flagged_status}</td>
            </tr>
            """

        html += f"""
        </table>

        <h2>Recent Messages ({len(messages)} shown):</h2>
        <table>
            <tr>
                <th>ID</th><th>From</th><th>To</th><th>Content</th><th>Time</th><th>Read</th>
            </tr>
        """

        for message in messages:
            content_preview = (message[3][:50] + '...') if len(message[3]) > 50 else message[3]
            read_status = 'Yes' if message[5] else 'No'
            html += f"""
            <tr>
                <td>{message[0]}</td>
                <td>{message[1]}</td>
                <td>{message[2]}</td>
                <td>{content_preview}</td>
                <td>{message[4]}</td>
                <td>{read_status}</td>
            </tr>
            """

        html += """
        </table>

        <h2>🧪 Test Actions:</h2>
        <p>
            <a href="/setup_complete_messaging" style="background: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">🔄 Re-run Setup</a>
            <a href="/admin" style="background: #2196F3; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-left: 10px;">🏠 Back to Dashboard</a>
        </p>

        <h2>📝 API Endpoints Status:</h2>
        <ul>
            <li class="success">✅ /api/admin/users - Get users list</li>
            <li class="success">✅ /api/admin/messages/&lt;user_id&gt; - Get messages</li>
            <li class="success">✅ /api/admin/send_message - Send message</li>
            <li class="success">✅ /api/admin/unread_messages - Check unread count</li>
            <li class="success">✅ /api/admin/mark_messages_read/&lt;user_id&gt; - Mark as read</li>
            <li class="success">✅ /debug_session - Check session data</li>
        </ul>
        """

        return html

    # 3. Setup messages table
    @app.route('/setup_messaging')
    def setup_messaging():
        """One-time setup for messaging system"""
        if 'admin' not in session:
            return "Admin access required"

        try:
            from database import get_auto_increment, get_timestamp_default
            from db_config import get_db_type

            conn = get_db_connection()
            c = conn.cursor()

            auto_inc = get_auto_increment()
            timestamp = get_timestamp_default()

            # Create messages table
            c.execute(f'''CREATE TABLE IF NOT EXISTS messages (
                id {auto_inc},
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp {timestamp},
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id)
            )''')

            if get_db_type() != 'postgresql':
                conn.commit()
            conn.close()

            return "✅ Messaging system setup complete! <a href='/admin'>Back to Admin Dashboard</a>"
        except Exception as e:
            return f"❌ Error setting up messaging: {e}"


@app.route('/api/admin/send_message', methods=['POST'])
def send_message():
    """Send a message to a user"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        recipient_id = data.get('recipient_id')
        content = data.get('content', '').strip()

        if not recipient_id or not content:
            return jsonify({'success': False, 'error': 'Missing recipient or content'}), 400

        sender_id = session.get('user_id')

        conn = get_db_connection()
        c = conn.cursor()

        # Insert message
        c.execute('''
            INSERT INTO messages (sender_id, recipient_id, content, timestamp, is_read)
            VALUES (?, ?, ?, ?, 0)
        ''', (sender_id, recipient_id, content, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Message sent successfully'})

    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({'success': False, 'error': 'Failed to send message'}), 500

# Helper function to log audit events (add this to your login routes)
# Also, make sure you have the log_audit_event function (add this if you don't have it):

def log_audit_event(user, action, ip_address=None, details=None):
    """Log an audit event"""
    try:
        from database import get_auto_increment, get_timestamp_default
        from db_config import get_db_type

        conn = get_db_connection()
        cursor = conn.cursor()

        auto_inc = get_auto_increment()
        timestamp = get_timestamp_default()

        # Create table if it doesn't exist
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS audit_log (
                id {auto_inc},
                timestamp {timestamp},
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                ip_address TEXT,
                details TEXT
            )
        ''')

        if get_db_type() == 'postgresql':
            cursor.execute('''
                INSERT INTO audit_log (timestamp, user, action, ip_address, details)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                datetime.now().isoformat(),
                user,
                action,
                ip_address,
                details
            ))
        else:
            cursor.execute('''
                INSERT INTO audit_log (timestamp, user, action, ip_address, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                user,
                action,
                ip_address,
                details
            ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging audit event: {e}")

@app.route('/api/admin/login_history', methods=['GET'])
def get_login_history():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute(
            'SELECT user_id, username, email, role, login_time, ip_address FROM login_history ORDER BY login_time DESC')
        history = [{'user_id': row['user_id'], 'username': row['username'], 'email': row['email'],
                    'role': row['role'], 'login_time': row['login_time'], 'ip_address': row['ip_address']}
                   for row in c.fetchall()]
        return jsonify(history)
    finally:
        conn.close()


# Test route to check if user management is working
@app.route('/test_users')
def test_users():
    """Test route to see all users (remove this after testing)"""
    if 'admin' not in session:
        return "Access denied"

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, email, role, is_flagged FROM users')
    users = c.fetchall()
    conn.close()

    html = "<h1>All Users in Database:</h1><ul>"
    for user in users:
        html += f"<li>ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}, Flagged: {user[4]}</li>"
    html += "</ul>"
    html += '<br><a href="/admin">Back to Admin Dashboard</a>'

    return html

@app.route('/api/admin/users', methods=['POST'])
def add_user():
    """Add a new user to the system"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', '').strip()

        # Validate required fields
        if not all([username, email, password, role]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400

        # Validate role
        if role not in ['inspector', 'admin', 'medical_officer']:
            return jsonify({'success': False, 'error': 'Invalid role'}), 400

        # Validate password length
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400

        conn = get_db_connection()
        try:
            c = conn.cursor()

            # Check if username already exists
            c.execute('SELECT id FROM users WHERE username = ?', (username,))
            if c.fetchone():
                return jsonify({'success': False, 'error': 'Username already exists'}), 400

            # Check if email already exists
            c.execute('SELECT id FROM users WHERE email = ?', (email,))
            if c.fetchone():
                return jsonify({'success': False, 'error': 'Email already exists'}), 400

            # Insert new user
            c.execute('''
                INSERT INTO users (username, email, password, role, is_flagged) 
                VALUES (?, ?, ?, ?, 0)
            ''', (username, email, password, role))

            conn.commit()

            # Log the action
            log_audit_event(session.get('inspector', 'admin'), 'user_created',
                            request.remote_addr, f'Created user: {username} ({role})')

            return jsonify({'success': True, 'message': 'User created successfully'})

        finally:
            conn.close()

    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred'}), 500


# 2. Route to check unread messages
@app.route('/api/admin/unread_messages')
def get_unread_messages():
    """Get count of unread messages for admin"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        admin_id = session.get('user_id')
        conn = get_db_connection()
        c = conn.cursor()

        # Get total unread count
        c.execute('''
            SELECT COUNT(*) as total
            FROM messages 
            WHERE recipient_id = ? AND is_read = 0
        ''', (admin_id,))

        result = c.fetchone()
        total_unread = result['total'] if result else 0

        conn.close()

        return jsonify({
            'count': total_unread,
            'by_user': {}
        })

    except Exception as e:
        print(f"Error getting unread messages: {e}")
        return jsonify({'count': 0, 'by_user': {}})

    # 3. Setup messages table
    @app.route('/setup_messaging')
    def setup_messaging():
        """One-time setup for messaging system"""
        if 'admin' not in session:
            return "Admin access required"

        try:
            from database import get_auto_increment, get_timestamp_default
            from db_config import get_db_type

            conn = get_db_connection()
            c = conn.cursor()

            auto_inc = get_auto_increment()
            timestamp = get_timestamp_default()

            # Create messages table
            c.execute(f'''CREATE TABLE IF NOT EXISTS messages (
                id {auto_inc},
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp {timestamp},
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id)
            )''')

            if get_db_type() != 'postgresql':
                conn.commit()
            conn.close()

            return "✅ Messaging system setup complete! <a href='/admin'>Back to Admin Dashboard</a>"
        except Exception as e:
            return f"❌ Error setting up messaging: {e}"


@app.route('/api/admin/mark_messages_read/<int:user_id>', methods=['POST'])
def mark_messages_read(user_id):
    """Mark all messages from a user as read"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        admin_id = session.get('user_id')
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
            UPDATE messages 
            SET is_read = 1 
            WHERE sender_id = ? AND recipient_id = ? AND is_read = 0
        ''', (user_id, admin_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error marking messages as read: {e}")
        return jsonify({'success': False, 'error': 'Failed to mark messages as read'}), 500


@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        role = data.get('role', '').strip()

        # Validate required fields
        if not all([email, role]):
            return jsonify({'success': False, 'error': 'Email and role are required'}), 400

        # Validate role
        if role not in ['inspector', 'admin', 'medical_officer']:
            return jsonify({'success': False, 'error': 'Invalid role'}), 400

        conn = get_db_connection()
        try:
            c = conn.cursor()

            # Get current user info
            c.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
            current_user = c.fetchone()
            if not current_user:
                return jsonify({'success': False, 'error': 'User not found'}), 404

            # Check if email already exists for another user
            c.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id))
            if c.fetchone():
                return jsonify({'success': False, 'error': 'Email already exists'}), 400

            # Update user
            c.execute('''
                UPDATE users 
                SET email = ?, role = ? 
                WHERE id = ?
            ''', (email, role, user_id))

            conn.commit()

            # Log the action
            log_audit_event(session.get('inspector', 'admin'), 'user_updated',
                            request.remote_addr, f'Updated user: {current_user["username"]} (new role: {role})')

            return jsonify({'success': True, 'message': 'User updated successfully'})

        finally:
            conn.close()

    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred'}), 500


@app.route('/api/admin/users/<int:user_id>/flag', methods=['POST'])
def flag_user(user_id):
    """Flag or unflag a user"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        is_flagged = data.get('is_flagged', False)

        conn = get_db_connection()
        try:
            c = conn.cursor()

            # Get user info
            c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user = c.fetchone()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404

            # Update flag status
            c.execute('UPDATE users SET is_flagged = ? WHERE id = ?', (1 if is_flagged else 0, user_id))
            conn.commit()

            # Log the action
            action = 'user_flagged' if is_flagged else 'user_unflagged'
            log_audit_event(session.get('inspector', 'admin'), action,
                            request.remote_addr, f'{action.replace("_", " ").title()}: {user["username"]}')

            return jsonify(
                {'success': True, 'message': f'User {"flagged" if is_flagged else "unflagged"} successfully'})

        finally:
            conn.close()

    except Exception as e:
        print(f"Error flagging user: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred'}), 500


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user (cannot delete admin users)"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        conn = get_db_connection()
        try:
            c = conn.cursor()

            # Get user info
            c.execute('SELECT username, role FROM users WHERE id = ?', (user_id,))
            user = c.fetchone()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404

            # Prevent deletion of admin users
            if user['role'] == 'admin':
                return jsonify({'success': False, 'error': 'Cannot delete admin users'}), 403

            # Delete user
            c.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()

            # Log the action
            log_audit_event(session.get('inspector', 'admin'), 'user_deleted',
                            request.remote_addr, f'Deleted user: {user["username"]} ({user["role"]})')

            return jsonify({'success': True, 'message': 'User deleted successfully'})

        finally:
            conn.close()

    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': 'Database error occurred'}), 500


# ==================================================
# STEP 1: DATABASE SCHEMA UPDATES
# Add this to your database.py or run directly
# ==================================================

import sqlite3
from datetime import datetime


def init_form_management_db():
    """Initialize form management tables"""
    from database import get_auto_increment, get_timestamp_default
    from db_config import get_db_type

    conn = get_db_connection()

    # Enable autocommit for schema changes (prevents transaction errors on ALTER failures)
    if get_db_type() == 'postgresql':
        conn.autocommit = True

    c = conn.cursor()

    # Get database-specific syntax
    auto_inc = get_auto_increment()
    timestamp = get_timestamp_default()

    # Form Templates Table - Different types of inspection forms
    c.execute(f'''CREATE TABLE IF NOT EXISTS form_templates (
        id {auto_inc},
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        form_type TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        created_date {timestamp},
        version TEXT DEFAULT '1.0',
        created_by TEXT
    )''')

    # Form Items Table - Individual checklist items for each form
    c.execute(f'''CREATE TABLE IF NOT EXISTS form_items (
        id {auto_inc},
        form_template_id INTEGER NOT NULL,
        item_order INTEGER NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        weight INTEGER NOT NULL,
        is_critical INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_date {timestamp},
        FOREIGN KEY (form_template_id) REFERENCES form_templates(id)
    )''')

    # Form Categories Table - For organizing items
    c.execute(f'''CREATE TABLE IF NOT EXISTS form_categories (
        id {auto_inc},
        name TEXT NOT NULL,
        description TEXT,
        display_order INTEGER DEFAULT 0
    )''')

    # Insert default categories
    default_categories = [
        ('FOOD', 'Food related items', 1),
        ('FOOD PROTECTION', 'Food protection items', 2),
        ('EQUIPMENT & UTENSILS', 'Equipment and utensils', 3),
        ('FACILITIES', 'Facility requirements', 4),
        ('PERSONNEL', 'Personnel requirements', 5),
        ('SAFETY', 'Safety requirements', 6),
        ('GENERAL', 'General requirements', 7)
    ]

    for category in default_categories:
        if get_db_type() == 'postgresql':
            c.execute('INSERT INTO form_categories (name, description, display_order) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING', category)
        else:
            c.execute('INSERT OR IGNORE INTO form_categories (name, description, display_order) VALUES (?, ?, ?)', category)

    # Insert existing form templates
    existing_templates = [
        ('Food Establishment Inspection', 'Standard food safety inspection form', 'Food Establishment'),
        ('Residential & Non-Residential Inspection', 'Residential property inspection form', 'Residential'),
        ('Burial Site Inspection', 'Burial site approval inspection', 'Burial'),
        ('Spirit Licence Premises Inspection', 'Spirit licence premises inspection', 'Spirit Licence Premises'),
        ('Swimming Pool Inspection', 'Swimming pool safety inspection', 'Swimming Pool'),
        ('Small Hotels Inspection', 'Small hotels inspection form', 'Small Hotel'),
        ('Barbershop Inspection', 'Barbershop and beauty salon inspection form', 'Barbershop'),
        ('Institutional Inspection', 'Institutional health inspection form', 'Institutional'),
        ('Meat Processing Inspection', 'Meat processing plant and slaughter place inspection', 'Meat Processing')
    ]

    for template in existing_templates:
        if get_db_type() == 'postgresql':
            c.execute('INSERT INTO form_templates (name, description, form_type) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING', template)
        else:
            c.execute('INSERT OR IGNORE INTO form_templates (name, description, form_type) VALUES (?, ?, ?)', template)

    # Only commit if not using autocommit (SQLite)
    if get_db_type() != 'postgresql':
        conn.commit()
    conn.close()


# ==================================================
# STEP 2: FLASK ROUTES TO ADD TO app.py
# Add these routes to your existing app.py
# ==================================================

# Form Management Routes
@app.route('/admin/forms')
def form_management():
    """Main form management page"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    # Get all form templates with item counts
    c.execute('''
        SELECT ft.id, ft.name, ft.description, ft.form_type, ft.active, ft.version,
               COUNT(fi.id) as item_count
        FROM form_templates ft
        LEFT JOIN form_items fi ON ft.id = fi.form_template_id AND fi.active = 1
        GROUP BY ft.id
        ORDER BY ft.name
    ''')

    forms = c.fetchall()
    conn.close()

    return render_template('form_management.html', forms=forms)


@app.route('/admin/forms/edit/<int:form_id>')
def edit_form(form_id):
    """Edit existing form template"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    # Get form template
    c.execute('SELECT * FROM form_templates WHERE id = ?', (form_id,))
    form_template = c.fetchone()

    if not form_template:
        conn.close()
        return redirect(url_for('form_management'))

    # Get form items
    c.execute('''
        SELECT id, item_order, category, description, weight, is_critical
        FROM form_items 
        WHERE form_template_id = ? AND active = 1
        ORDER BY item_order
    ''', (form_id,))
    items = c.fetchall()

    # Get categories
    c.execute('SELECT name FROM form_categories ORDER BY display_order')
    categories = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template('form_editor.html',
                           form_template=form_template,
                           items=items,
                           categories=categories,
                           is_edit=True)


@app.route('/api/inspector/my_inspections')
def get_my_inspections():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    inspector_name = session.get('inspector')
    inspection_type = request.args.get('type', 'all')

    try:
        inspections = get_inspections_by_inspector(inspector_name, inspection_type)

        # Convert to list of dictionaries for JSON response
        inspections_list = []
        for inspection in inspections:
            form_type = inspection[7] if len(inspection) > 7 else ''
            type_of_establishment = inspection[4]

            # Determine the inspection type for the frontend
            inspection_type = form_type if form_type else type_of_establishment
            if not inspection_type:
                inspection_type = 'food'  # default

            inspections_list.append({
                'id': inspection[0],
                'establishment_name': inspection[1],
                'inspector_name': inspection[2],
                'inspection_date': inspection[3],
                'type_of_establishment': type_of_establishment,
                'type': inspection_type,  # Add this for frontend compatibility
                'created_at': inspection[5],
                'result': inspection[6],
                'form_type': form_type
            })

        return jsonify({'inspections': inspections_list})

    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@app.route('/admin/forms/create')
def create_form():
    """Create new form template"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    # Get categories
    c.execute('SELECT name FROM form_categories ORDER BY display_order')
    categories = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template('form_editor.html',
                           form_template=None,
                           items=[],
                           categories=categories,
                           is_edit=False)


@app.route('/admin/forms/save', methods=['POST'])
def save_form():
    """Save form template and items"""
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        form_id = data.get('form_id')
        form_name = data.get('form_name')
        form_description = data.get('form_description')
        form_type = data.get('form_type')
        items = data.get('items', [])

        conn = get_db_connection()
        c = conn.cursor()

        if form_id:  # Update existing form
            c.execute('''
                UPDATE form_templates 
                SET name = ?, description = ?, form_type = ?, version = ?
                WHERE id = ?
            ''', (form_name, form_description, form_type, '1.1', form_id))

            # Deactivate existing items
            c.execute('UPDATE form_items SET active = 0 WHERE form_template_id = ?', (form_id,))

        else:  # Create new form
            c.execute('''
                INSERT INTO form_templates (name, description, form_type, created_by)
                VALUES (?, ?, ?, ?)
            ''', (form_name, form_description, form_type, session.get('user_id', 'admin')))
            form_id = c.lastrowid

        # Insert/update items
        for item in items:
            c.execute('''
                INSERT INTO form_items 
                (form_template_id, item_order, category, description, weight, is_critical)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (form_id, item['order'], item['category'], item['description'],
                  item['weight'], 1 if item.get('critical') else 0))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'form_id': form_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/forms/delete/<int:form_id>', methods=['POST'])
def delete_form(form_id):
    """Delete form template"""
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Soft delete - just mark as inactive
        c.execute('UPDATE form_templates SET active = 0 WHERE id = ?', (form_id,))
        c.execute('UPDATE form_items SET active = 0 WHERE form_template_id = ?', (form_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/forms/clone/<int:form_id>', methods=['POST'])
def clone_form(form_id):
    """Clone existing form template"""
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get original form
        c.execute('SELECT name, description, form_type FROM form_templates WHERE id = ?', (form_id,))
        original = c.fetchone()

        if not original:
            return jsonify({'success': False, 'error': 'Form not found'}), 404

        # Create clone
        clone_name = f"{original[0]} (Copy)"
        c.execute('''
            INSERT INTO form_templates (name, description, form_type, created_by)
            VALUES (?, ?, ?, ?)
        ''', (clone_name, original[1], original[2], session.get('user_id', 'admin')))

        new_form_id = c.lastrowid

        # Clone items
        c.execute('''
            INSERT INTO form_items 
            (form_template_id, item_order, category, description, weight, is_critical)
            SELECT ?, item_order, category, description, weight, is_critical
            FROM form_items WHERE form_template_id = ? AND active = 1
        ''', (new_form_id, form_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'form_id': new_form_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/forms/preview/<int:form_id>')
def preview_form(form_id):
    """Preview form template"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    # Get form template
    c.execute('SELECT * FROM form_templates WHERE id = ?', (form_id,))
    form_template = c.fetchone()

    # Get form items grouped by category
    c.execute('''
        SELECT category, description, weight, is_critical
        FROM form_items 
        WHERE form_template_id = ? AND active = 1
        ORDER BY item_order
    ''', (form_id,))

    items = c.fetchall()

    # Group items by category
    grouped_items = {}
    for item in items:
        category = item[0]
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append({
            'description': item[1],
            'weight': item[2],
            'is_critical': item[3]
        })

    conn.close()

    return render_template('form_preview.html',
                           form_template=form_template,
                           grouped_items=grouped_items)


@app.route('/api/inspection_counts')
def get_inspection_counts():
    """Get inspection counts by type for admin dashboard"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get counts from main inspections table
        c.execute('''
            SELECT form_type, COUNT(*) as count
            FROM inspections
            WHERE form_type IS NOT NULL
            GROUP BY form_type
        ''')
        main_counts = dict(c.fetchall())

        # Get residential inspection counts
        c.execute('SELECT COUNT(*) FROM residential_inspections')
        residential_count = c.fetchone()[0]

        # Get burial inspection counts
        c.execute('SELECT COUNT(*) FROM burial_site_inspections')
        burial_count = c.fetchone()[0]

        # Combine all counts
        counts = {
            'food_establishment': main_counts.get('Food Establishment', 0),
            'small_hotel': main_counts.get('Small Hotel', 0),
            'swimming_pool': main_counts.get('Swimming Pool', 0),
            'institutional_health': main_counts.get('Institutional Health', 0),
            'spirit_licence': main_counts.get('Spirit Licence Premises', 0),
            'barbershop': main_counts.get('Barbershop', 0),
            'residential': residential_count,
            'burial': burial_count
        }

        # Add any custom form types from form_templates
        existing_form_types = [
            'Food Establishment', 'Small Hotel', 'Swimming Pool',
            'Institutional Health', 'Spirit Licence Premises', 'Barbershop'
        ]
        placeholders = ','.join(['?' for _ in existing_form_types])
        c.execute(f'''
            SELECT ft.form_type, COUNT(i.id) as count
            FROM form_templates ft
            LEFT JOIN inspections i ON ft.form_type = i.form_type
            WHERE ft.active = 1 AND ft.form_type NOT IN ({placeholders})
            GROUP BY ft.form_type
        ''', existing_form_types)

        custom_forms = c.fetchall()
        for form_type, count in custom_forms:
            # Convert form type to key format
            key = form_type.lower().replace(' ', '_').replace('-', '_')
            counts[key] = count

        conn.close()
        return jsonify(counts)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forms/active')
def get_active_forms():
    """Get active forms for inspector dashboard"""
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''
        SELECT ft.id, ft.name, ft.description, ft.form_type,
               COUNT(fi.id) as item_count
        FROM form_templates ft
        LEFT JOIN form_items fi ON ft.id = fi.form_template_id AND fi.active = 1
        WHERE ft.active = 1
        GROUP BY ft.id
        ORDER BY ft.name
    ''')

    forms = []
    for row in c.fetchall():
        forms.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'form_type': row[3],
            'item_count': row[4]
        })

    conn.close()
    return jsonify({'forms': forms})


# Add these routes to your app.py to migrate your existing checklists

@app.route('/debug/forms')
def debug_forms():
    """Debug route to check what's in the database"""
    if 'admin' not in session:
        return "Admin access required"

    conn = get_db_connection()
    c = conn.cursor()

    # Check templates
    c.execute('SELECT * FROM form_templates')
    templates = c.fetchall()

    # Check items
    c.execute('SELECT * FROM form_items')
    items = c.fetchall()

    conn.close()

    return f"<h2>Form Templates ({len(templates)}):</h2><pre>{templates}</pre><br><br><h2>Form Items ({len(items)}):</h2><pre>{items}</pre>"


@app.route('/admin/migrate_all_checklists')
def migrate_all_checklists():
    """Migrate all existing checklists to the database"""
    if 'admin' not in session:
        return "Admin access required"

    conn = get_db_connection()
    c = conn.cursor()

    results = []

    # 1. Migrate Food Establishment Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Food Establishment',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            # Check if items already exist
            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                # Define categories for food items
                categories = {
                    1: "FOOD", 2: "FOOD",
                    3: "FOOD PROTECTION", 4: "FOOD PROTECTION", 5: "FOOD PROTECTION",
                    6: "FOOD PROTECTION", 7: "FOOD PROTECTION", 8: "FOOD PROTECTION",
                    9: "FOOD PROTECTION", 10: "FOOD PROTECTION",
                    11: "EQUIPMENT & UTENSILS", 12: "EQUIPMENT & UTENSILS", 13: "EQUIPMENT & UTENSILS",
                    14: "EQUIPMENT & UTENSILS", 15: "EQUIPMENT & UTENSILS", 16: "EQUIPMENT & UTENSILS",
                    17: "EQUIPMENT & UTENSILS", 18: "EQUIPMENT & UTENSILS", 19: "EQUIPMENT & UTENSILS",
                    20: "EQUIPMENT & UTENSILS", 21: "EQUIPMENT & UTENSILS", 22: "EQUIPMENT & UTENSILS",
                    23: "EQUIPMENT & UTENSILS",
                    24: "FACILITIES", 25: "FACILITIES", 26: "FACILITIES", 27: "FACILITIES", 28: "FACILITIES",
                    29: "PERSONNEL", 30: "PERSONNEL", 31: "PERSONNEL", 32: "PERSONNEL",
                    33: "FACILITIES", 34: "FACILITIES", 35: "FACILITIES", 36: "FACILITIES", 37: "FACILITIES",
                    38: "FACILITIES", 39: "FACILITIES", 40: "FACILITIES", 41: "FACILITIES",
                    42: "SAFETY", 43: "GENERAL", 44: "GENERAL", 45: "GENERAL"
                }

                # Insert each item from FOOD_CHECKLIST_ITEMS
                for item in FOOD_CHECKLIST_ITEMS:
                    item_id = item['id']
                    category = categories.get(item_id, "GENERAL")
                    is_critical = 1 if item['wt'] >= 4 else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, item_id, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Food Establishment: Migrated {len(FOOD_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Food Establishment: Already has {existing_count} items")
        else:
            results.append("❌ Food Establishment template not found")
    except Exception as e:
        results.append(f"❌ Food Establishment migration failed: {str(e)}")

    # 2. Migrate Residential Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Residential',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                # Define categories for residential items
                residential_categories = {
                    1: "BUILDING CONDITION", 2: "BUILDING CONDITION", 3: "BUILDING CONDITION",
                    4: "BUILDING CONDITION", 5: "BUILDING CONDITION", 6: "BUILDING CONDITION",
                    7: "BUILDING CONDITION", 8: "BUILDING CONDITION",
                    9: "WATER SUPPLY", 10: "WATER SUPPLY",
                    11: "DRAINAGE", 12: "DRAINAGE",
                    13: "VECTOR CONTROL - MOSQUITOES", 14: "VECTOR CONTROL - MOSQUITOES",
                    15: "VECTOR CONTROL - FLIES", 16: "VECTOR CONTROL - FLIES",
                    17: "VECTOR CONTROL - RODENTS", 18: "VECTOR CONTROL - RODENTS",
                    19: "TOILET FACILITIES", 20: "TOILET FACILITIES", 21: "TOILET FACILITIES", 22: "TOILET FACILITIES",
                    23: "SOLID WASTE", 24: "SOLID WASTE",
                    25: "GENERAL"
                }

                for item in RESIDENTIAL_CHECKLIST_ITEMS:
                    item_id = item['id']
                    category = residential_categories.get(item_id, "GENERAL")
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, item_id, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Residential: Migrated {len(RESIDENTIAL_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Residential: Already has {existing_count} items")
        else:
            results.append("❌ Residential template not found")
    except Exception as e:
        results.append(f"❌ Residential migration failed: {str(e)}")

    # 3. Migrate Spirit Licence Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Spirit Licence Premises',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                # Define categories for spirit licence items
                spirit_categories = {
                    1: "BUILDING CONDITION", 2: "BUILDING CONDITION", 3: "BUILDING CONDITION",
                    4: "BUILDING CONDITION", 5: "BUILDING CONDITION", 6: "BUILDING CONDITION",
                    7: "BUILDING CONDITION", 8: "BUILDING CONDITION", 9: "BUILDING CONDITION",
                    10: "LIGHTING", 11: "LIGHTING",
                    12: "WASHING FACILITIES", 13: "WASHING FACILITIES", 14: "WASHING FACILITIES",
                    15: "WASHING FACILITIES",
                    16: "WATER SUPPLY", 17: "WATER SUPPLY", 18: "WATER SUPPLY",
                    19: "STORAGE", 20: "STORAGE", 21: "STORAGE", 22: "STORAGE",
                    23: "SANITARY FACILITIES", 24: "SANITARY FACILITIES", 25: "SANITARY FACILITIES",
                    26: "SANITARY FACILITIES", 27: "SANITARY FACILITIES", 28: "SANITARY FACILITIES",
                    29: "WASTE MANAGEMENT", 30: "WASTE MANAGEMENT", 31: "WASTE MANAGEMENT", 32: "WASTE MANAGEMENT",
                    33: "PEST CONTROL", 34: "PEST CONTROL"
                }

                for item in SPIRIT_LICENCE_CHECKLIST_ITEMS:
                    item_id = item['id']
                    category = spirit_categories.get(item_id, "GENERAL")
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, item_id, category, item['description'], item['wt'], is_critical))

                results.append(f"✅ Spirit Licence: Migrated {len(SPIRIT_LICENCE_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Spirit Licence: Already has {existing_count} items")
        else:
            results.append("❌ Spirit Licence template not found")
    except Exception as e:
        results.append(f"❌ Spirit Licence migration failed: {str(e)}")

    # 4. Migrate Swimming Pool Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Swimming Pool',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                for i, item in enumerate(SWIMMING_POOL_CHECKLIST_ITEMS):
                    category = item.get('category', 'GENERAL')
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, i + 1, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Swimming Pool: Migrated {len(SWIMMING_POOL_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Swimming Pool: Already has {existing_count} items")
        else:
            results.append("❌ Swimming Pool template not found")
    except Exception as e:
        results.append(f"❌ Swimming Pool migration failed: {str(e)}")

    # 5. Migrate Small Hotels Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Small Hotel',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                for i, item in enumerate(SMALL_HOTELS_CHECKLIST_ITEMS):
                    # Determine category based on item ID pattern
                    item_id = item['id']
                    if item_id.startswith('1'):
                        category = "DOCUMENTATION"
                    elif item_id.startswith('2'):
                        category = "PERSONNEL"
                    elif item_id.startswith('3'):
                        category = "FOOD STORAGE"
                    elif item_id.startswith('4'):
                        category = "FOOD PREPARATION"
                    elif item_id.startswith('5'):
                        category = "WASTE MANAGEMENT"
                    elif item_id.startswith('6'):
                        category = "WASTE MANAGEMENT"
                    elif item_id.startswith('8'):
                        category = "SAFETY"
                    elif item_id.startswith('9'):
                        category = "FOOD SERVICE"
                    elif item_id.startswith('10'):
                        category = "FACILITIES"
                    elif item_id.startswith('12'):
                        category = "EQUIPMENT"
                    elif item_id.startswith('13'):
                        category = "OPERATIONS"
                    elif item_id.startswith('15'):
                        category = "UTILITIES"
                    elif item_id.startswith('16'):
                        category = "UTILITIES"
                    else:
                        category = "GENERAL"

                    is_critical = 1 if item.get('critical', False) else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, i + 1, category, item['description'], 2.5, is_critical))

                results.append(f"✅ Small Hotels: Migrated {len(SMALL_HOTELS_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Small Hotels: Already has {existing_count} items")
        else:
            results.append("❌ Small Hotels template not found")
    except Exception as e:
        results.append(f"❌ Small Hotels migration failed: {str(e)}")

    # 6. Migrate Barbershop Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Barbershop',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                for i, item in enumerate(BARBERSHOP_CHECKLIST_ITEMS):
                    category = item.get('category', 'GENERAL')
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, i + 1, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Barbershop: Migrated {len(BARBERSHOP_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Barbershop: Already has {existing_count} items")
        else:
            results.append("❌ Barbershop template not found")
    except Exception as e:
        results.append(f"❌ Barbershop migration failed: {str(e)}")

    # 7. Migrate Institutional Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Institutional',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                for i, item in enumerate(INSTITUTIONAL_CHECKLIST_ITEMS):
                    category = item.get('category', 'GENERAL')
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, i + 1, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Institutional: Migrated {len(INSTITUTIONAL_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Institutional: Already has {existing_count} items")
        else:
            results.append("❌ Institutional template not found")
    except Exception as e:
        results.append(f"❌ Institutional migration failed: {str(e)}")

    # 8. Migrate Meat Processing Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Meat Processing',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                for i, item in enumerate(MEAT_PROCESSING_CHECKLIST_ITEMS):
                    category = item.get('category', 'GENERAL')
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, i + 1, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Meat Processing: Migrated {len(MEAT_PROCESSING_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Meat Processing: Already has {existing_count} items")
        else:
            results.append("❌ Meat Processing template not found")
    except Exception as e:
        results.append(f"❌ Meat Processing migration failed: {str(e)}")

    conn.commit()
    conn.close()

    # Format results as HTML
    html_results = "<h1>Checklist Migration Results</h1><ul>"
    for result in results:
        html_results += f"<li>{result}</li>"
    html_results += "</ul>"
    html_results += "<br><a href='/admin/forms'>Go to Form Management</a> | <a href='/debug/forms'>Debug Database</a>"

    return html_results


@app.route('/admin/reset_database')
def reset_database():
    """Reset and reinitialize the form management database"""
    if 'admin' not in session:
        return "Admin access required"

    conn = get_db_connection()
    c = conn.cursor()

    # Clear existing data
    c.execute('DELETE FROM form_items')
    c.execute('DELETE FROM form_templates')
    c.execute('DELETE FROM form_categories')

    conn.commit()
    conn.close()

    # Reinitialize
    init_form_management_db()

    return "Database reset complete! <a href='/admin/migrate_all_checklists'>Run migration now</a>"
# ==================================================
# STEP 3: UPDATE EXISTING CHECKLIST LOADING
# Replace your existing checklist variables with dynamic loading
# ==================================================

def get_form_items(form_template_id):
    """Get form items for a specific template"""
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''
        SELECT id, item_order, category, description, weight, is_critical
        FROM form_items 
        WHERE form_template_id = ? AND active = 1
        ORDER BY item_order
    ''', (form_template_id,))

    items = []
    for row in c.fetchall():
        items.append({
            'id': row[0],
            'order': row[1],
            'category': row[2],
            'desc': row[3],
            'description': row[3],  # For compatibility
            'wt': row[4],
            'weight': row[4],  # For compatibility
            'critical': bool(row[5])
        })

    conn.close()
    return items


def get_form_template_by_type(form_type):
    """Get form template by type"""
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('SELECT id FROM form_templates WHERE form_type = ? AND active = 1', (form_type,))
    row = c.fetchone()

    conn.close()
    return row[0] if row else None


@app.route('/new_form')
def new_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))

    # Load checklist from database (falls back to hardcoded if empty)
    checklist = get_form_checklist_items('Food Establishment', FOOD_CHECKLIST_ITEMS)

    # Get last_edited info for this form type
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT last_edited_by, last_edited_date, last_edited_role, version
        FROM form_templates
        WHERE form_type = ? AND active = 1
    ''', ('Food Establishment',))
    form_info = c.fetchone()
    conn.close()

    last_edited_info = None
    if form_info and form_info[0]:  # if last_edited_by exists
        last_edited_info = {
            'editor': form_info[0],
            'date': form_info[1],
            'role': form_info[2] or 'admin',
            'version': form_info[3] or '1.0'
        }

    # Default inspection data for new form (your existing code)
    inspection = {
        'id': '',
        'establishment_name': '',
        'owner': '',
        'address': '',
        'license_no': '',
        'inspector_name': '',
        'inspector_code': '',
        'inspection_date': '',
        'inspection_time': '',
        'type_of_establishment': '',
        'no_of_employees': '',
        'purpose_of_visit': '',
        'action': '',
        'result': '',
        'food_inspected': 0.0,
        'food_condemned': 0.0,
        'critical_score': 0,
        'overall_score': 0,
        'comments': '',
        'inspector_signature': '',
        'received_by': '',
        'scores': {},
        'created_at': ''
    }

    return render_template('inspection_form.html',
                           checklist=checklist,
                           inspections=get_inspections(),
                           show_form=True,
                           establishment_data=get_establishment_data(),
                           read_only=False,
                           inspection=inspection,
                           last_edited_info=last_edited_info)


@app.route('/debug/forms_check')
def debug_forms_check():
    """Debug route to check what's in the database"""
    if 'admin' not in session:
        return "Admin access required"

    conn = get_db_connection()
    c = conn.cursor()

    # Check templates
    c.execute('SELECT * FROM form_templates')
    templates = c.fetchall()

    # Check items
    c.execute('SELECT * FROM form_items')
    items = c.fetchall()

    conn.close()

    return f"<h2>Form Templates ({len(templates)}):</h2><pre>{templates}</pre><br><br><h2>Form Items ({len(items)}):</h2><pre>{items}</pre>"


@app.route('/setup_messaging_complete')
def setup_messaging_complete():
    if 'admin' not in session:
        return "Admin access required"

    init_messages_db()  # This function already exists in your code
    return "✅ Messaging system ready! <a href='/admin'>Back to Admin</a>"


@app.route('/admin/migrate_food_checklist')
def migrate_food_checklist():
    if 'admin' not in session:
        return "Admin access required"

    conn = get_db_connection()
    c = conn.cursor()

    # Get Food Establishment template ID
    c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Food Establishment',))
    result = c.fetchone()

    if not result:
        return "Food Establishment template not found"

    template_id = result[0]

    # Check if items already exist
    c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
    existing_count = c.fetchone()[0]

    if existing_count > 0:
        return f"Items already exist: {existing_count} items found"

    # Insert your 45 FOOD_CHECKLIST_ITEMS
    categories = {
        1: "FOOD", 2: "FOOD",
        3: "FOOD PROTECTION", 4: "FOOD PROTECTION", 5: "FOOD PROTECTION",
        6: "FOOD PROTECTION", 7: "FOOD PROTECTION", 8: "FOOD PROTECTION",
        9: "FOOD PROTECTION", 10: "FOOD PROTECTION",
        11: "EQUIPMENT & UTENSILS", 12: "EQUIPMENT & UTENSILS", 13: "EQUIPMENT & UTENSILS",
        14: "EQUIPMENT & UTENSILS", 15: "EQUIPMENT & UTENSILS", 16: "EQUIPMENT & UTENSILS",
        17: "EQUIPMENT & UTENSILS", 18: "EQUIPMENT & UTENSILS", 19: "EQUIPMENT & UTENSILS",
        20: "EQUIPMENT & UTENSILS", 21: "EQUIPMENT & UTENSILS", 22: "EQUIPMENT & UTENSILS",
        23: "EQUIPMENT & UTENSILS",
        24: "FACILITIES", 25: "FACILITIES", 26: "FACILITIES", 27: "FACILITIES", 28: "FACILITIES",
        29: "PERSONNEL", 30: "PERSONNEL", 31: "PERSONNEL", 32: "PERSONNEL",
        33: "FACILITIES", 34: "FACILITIES", 35: "FACILITIES", 36: "FACILITIES", 37: "FACILITIES",
        38: "FACILITIES", 39: "FACILITIES", 40: "FACILITIES", 41: "FACILITIES",
        42: "SAFETY", 43: "GENERAL", 44: "GENERAL", 45: "GENERAL"
    }

    # Insert each item from your FOOD_CHECKLIST_ITEMS
    for item in FOOD_CHECKLIST_ITEMS:
        item_id = item['id']
        category = categories.get(item_id, "GENERAL")
        is_critical = 1 if item['wt'] >= 4 else 0

        c.execute('''
            INSERT INTO form_items 
            (form_template_id, item_order, category, description, weight, is_critical)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template_id, item_id, category, item['desc'], item['wt'], is_critical))

    conn.commit()
    conn.close()

    return f"Successfully migrated {len(FOOD_CHECKLIST_ITEMS)} items! <a href='/admin/forms'>Check Form Management</a>"


@app.route('/admin/migrate_remaining_fixed')
def migrate_remaining_fixed():
    if 'admin' not in session:
        return "Admin access required"

    conn = get_db_connection()
    c = conn.cursor()
    results = []

    # 1. Migrate Residential (Template ID 2)
    try:
        template_id = 2  # From your debug output
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        if c.fetchone()[0] == 0:
            residential_categories = {
                1: "BUILDING", 2: "BUILDING", 3: "BUILDING", 4: "BUILDING", 5: "BUILDING", 6: "BUILDING", 7: "BUILDING",
                8: "BUILDING",
                9: "WATER SUPPLY", 10: "WATER SUPPLY", 11: "DRAINAGE", 12: "DRAINAGE",
                13: "VECTOR CONTROL", 14: "VECTOR CONTROL", 15: "VECTOR CONTROL", 16: "VECTOR CONTROL",
                17: "VECTOR CONTROL", 18: "VECTOR CONTROL",
                19: "TOILET FACILITIES", 20: "TOILET FACILITIES", 21: "TOILET FACILITIES", 22: "TOILET FACILITIES",
                23: "SOLID WASTE", 24: "SOLID WASTE", 25: "GENERAL"
            }
            for item in RESIDENTIAL_CHECKLIST_ITEMS:
                c.execute('''INSERT INTO form_items (form_template_id, item_order, category, description, weight, is_critical)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (template_id, item['id'], residential_categories.get(item['id'], "GENERAL"),
                           item['desc'], item['wt'], 1 if item['wt'] >= 5 else 0))
            results.append(f"✅ Residential: {len(RESIDENTIAL_CHECKLIST_ITEMS)} items")
        else:
            results.append("⚠️ Residential: Already migrated")
    except Exception as e:
        results.append(f"❌ Residential failed: {str(e)}")

    # 2. Migrate Spirit Licence (Template ID 4)
    try:
        template_id = 4  # From your debug output
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        if c.fetchone()[0] == 0:
            for i, item in enumerate(SPIRIT_LICENCE_CHECKLIST_ITEMS):
                c.execute('''INSERT INTO form_items (form_template_id, item_order, category, description, weight, is_critical)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (template_id, i + 1, "GENERAL", item['description'], item['wt'], 1 if item['wt'] >= 5 else 0))
            results.append(f"✅ Spirit Licence: {len(SPIRIT_LICENCE_CHECKLIST_ITEMS)} items")
        else:
            results.append("⚠️ Spirit Licence: Already migrated")
    except Exception as e:
        results.append(f"❌ Spirit Licence failed: {str(e)}")

    # 3. Migrate Swimming Pool (Template ID 5)
    try:
        template_id = 5  # From your debug output
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        if c.fetchone()[0] == 0:
            for i, item in enumerate(SWIMMING_POOL_CHECKLIST_ITEMS):
                c.execute('''INSERT INTO form_items (form_template_id, item_order, category, description, weight, is_critical)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (template_id, i + 1, item.get('category', 'GENERAL'), item['desc'], item['wt'],
                           1 if item['wt'] >= 5 else 0))
            results.append(f"✅ Swimming Pool: {len(SWIMMING_POOL_CHECKLIST_ITEMS)} items")
        else:
            results.append("⚠️ Swimming Pool: Already migrated")
    except Exception as e:
        results.append(f"❌ Swimming Pool failed: {str(e)}")

    # 4. Migrate Small Hotels (Template ID 6)
    try:
        template_id = 6  # From your debug output
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        if c.fetchone()[0] == 0:
            for i, item in enumerate(SMALL_HOTELS_CHECKLIST_ITEMS):
                c.execute('''INSERT INTO form_items (form_template_id, item_order, category, description, weight, is_critical)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (template_id, i + 1, "GENERAL", item['description'], 2.5,
                           1 if item.get('critical', False) else 0))
            results.append(f"✅ Small Hotels: {len(SMALL_HOTELS_CHECKLIST_ITEMS)} items")
        else:
            results.append("⚠️ Small Hotels: Already migrated")
    except Exception as e:
        results.append(f"❌ Small Hotels failed: {str(e)}")

    conn.commit()
    conn.close()

    return "<h1>Migration Results:</h1><ul>" + "".join(
        [f"<li>{r}</li>" for r in results]) + "</ul><br><a href='/admin/forms'>Check Form Management</a>"


@app.route('/small_hotels/inspection/<int:id>')
def small_hotels_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Small Hotel'", (id,))
    inspection = cursor.fetchone()

    if not inspection:
        conn.close()
        return "Small Hotels inspection not found", 404

    inspection_dict = dict(inspection)

    # Get individual scores from inspection_items table
    cursor.execute("SELECT item_id, obser, error FROM inspection_items WHERE inspection_id = ?", (id,))
    items = cursor.fetchall()

    obser_scores = {}
    error_scores = {}
    for item in items:
        obser_scores[item[0]] = item[1] or '0'
        error_scores[item[0]] = item[2] or '0'

    conn.close()

    # Extract and calculate the scores your template expects
    critical_score = int(inspection_dict.get('critical_score', 0))
    overall_score = int(inspection_dict.get('overall_score', 0))

    # Determine result based on scores
    result = 'Pass' if critical_score >= 70 and overall_score >= 70 else 'Fail'

    # Create inspection object that your template expects
    inspection_obj = {
        'id': id,
        'establishment_name': inspection_dict.get('establishment_name', ''),
        'inspector_name': inspection_dict.get('inspector_name', ''),
        'address': inspection_dict.get('address', ''),
        'physical_location': inspection_dict.get('physical_location', ''),
        'inspection_date': inspection_dict.get('inspection_date', ''),
        'critical_score': critical_score,
        'overall_score': overall_score,
        'result': result,
        'comments': inspection_dict.get('comments', ''),
        'inspector_signature': inspection_dict.get('inspector_signature', ''),
        'inspector_signature_date': inspection_dict.get('inspector_signature_date', ''),
        'manager_signature': inspection_dict.get('manager_signature', ''),
        'manager_signature_date': inspection_dict.get('manager_signature_date', ''),
        'received_by': inspection_dict.get('received_by', ''),
        'received_by_date': inspection_dict.get('received_by_date', ''),
        'obser': obser_scores,
        'error': error_scores
    }

    # Parse photos from JSON string to Python list
    import json
    photos = []
    if inspection_dict.get('photo_data'):
        try:
            photos = json.loads(inspection_dict.get('photo_data', '[]'))
        except:
            photos = []

    return render_template('small_hotels_inspection_detail.html',
                           inspection=inspection_obj,
                           photo_data=photos)

# SIMPLIFIED INSPECTION REPORTS
@app.route('/api/admin/generate_report', methods=['POST'])
def generate_admin_report():
    if 'admin' not in session and 'inspector' not in session:
        return jsonify({'error': 'Unauthorized - Please log in'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        # Support both camelCase and snake_case
        report_type = data.get('report_type') or data.get('reportType', 'basic_summary')
        inspection_type = data.get('inspection_type') or data.get('inspectionType', 'all')
        start_date = data.get('start_date') or data.get('startDate')
        end_date = data.get('end_date') or data.get('endDate')

        print(f"DEBUG: Received data: {data}")
        print(f"DEBUG: Report type: {report_type}, Inspection type: {inspection_type}")
        print(f"DEBUG: Date range: {start_date} to {end_date}")

        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required', 'received': data}), 400

        # Generate basic report based on type
        report_generators = {
            'comprehensive': generate_basic_summary_report,  # Use basic summary for comprehensive
            'basic_summary': generate_basic_summary_report,
            'trend_analysis': generate_trend_analysis_report,
            'failure_breakdown': generate_failure_breakdown_report,
            'inspector_performance': generate_inspector_performance_report,
            'scores_by_type': generate_scores_by_type_report,
            'monthly_trends': generate_monthly_trends_report,
            'establishment_ranking': generate_establishment_ranking_report,
            'parish_analysis': generate_basic_summary_report  # Placeholder for parish analysis
        }

        generator_func = report_generators.get(report_type, generate_basic_summary_report)
        print(f"DEBUG: Using generator function: {generator_func.__name__}")

        report = generator_func(inspection_type, start_date, end_date)
        print(f"DEBUG: Generated report: {report}")

        return jsonify({
            'success': True,
            'report': report,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': report_type,
                'inspection_type': inspection_type,
                'date_range': f"{start_date} to {end_date}"
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_and_create_alert(inspection_id, inspector_name, form_type, score):
    """Check if inspection score is below threshold and create alert if needed"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get global threshold
        c.execute('SELECT threshold_value FROM threshold_settings WHERE chart_type = ? AND enabled = 1', ('global',))
        result = c.fetchone()

        if result:
            threshold_value = result[0]

            # Check if score is below threshold
            if score < threshold_value:
                # Create alert
                c.execute('''
                    INSERT INTO threshold_alerts
                    (inspection_id, inspector_name, form_type, score, threshold_value, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (inspection_id, inspector_name, form_type, score, threshold_value))

                conn.commit()
                print(f"Alert created: Inspection {inspection_id}, Score {score} below threshold {threshold_value}")

        conn.close()
    except Exception as e:
        print(f"Error creating alert: {str(e)}")

@app.route('/api/admin/save_threshold', methods=['POST'])
def save_threshold():
    """Save threshold settings for chart alerts"""
    try:
        data = request.json
        chart_type = data.get('chart_type')
        threshold_value = data.get('threshold_value')
        enabled = data.get('enabled', 1)

        conn = get_db_connection()
        c = conn.cursor()

        # Upsert threshold setting
        c.execute('''
            INSERT INTO threshold_settings (chart_type, inspection_type, threshold_value, enabled, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(chart_type, inspection_type) DO UPDATE SET
                threshold_value = excluded.threshold_value,
                enabled = excluded.enabled,
                updated_at = CURRENT_TIMESTAMP
        ''', (chart_type, chart_type, threshold_value, enabled))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Threshold saved successfully',
            'chart_type': chart_type,
            'threshold_value': threshold_value
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/get_thresholds', methods=['GET'])
def get_thresholds():
    """Get all threshold settings"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
            SELECT chart_type, threshold_value, enabled
            FROM threshold_settings
            WHERE enabled = 1
        ''')

        thresholds = {}
        for row in c.fetchall():
            thresholds[row[0]] = {
                'value': row[1],
                'enabled': row[2] == 1
            }

        conn.close()

        return jsonify({
            'success': True,
            'thresholds': thresholds
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/threshold_alerts', methods=['POST'])
def create_threshold_alert():
    """Create threshold alert when inspection falls below threshold"""
    try:
        data = request.json
        inspection_id = data.get('inspection_id')
        inspector_name = data.get('inspector_name')
        form_type = data.get('form_type')
        score = data.get('score')
        threshold_value = data.get('threshold_value')

        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
            INSERT INTO threshold_alerts
            (inspection_id, inspector_name, form_type, score, threshold_value, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (inspection_id, inspector_name, form_type, score, threshold_value))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Alert created successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/threshold_alerts/acknowledge/<int:alert_id>', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge a threshold alert"""
    try:
        data = request.json
        acknowledged_by = data.get('acknowledged_by', session.get('username', 'admin'))

        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
            UPDATE threshold_alerts
            SET acknowledged = 1,
                acknowledged_by = ?,
                acknowledged_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (acknowledged_by, alert_id))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Alert acknowledged'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/threshold_alerts/list', methods=['GET'])
def list_threshold_alerts():
    """List all threshold alerts"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
            SELECT id, inspection_id, inspector_name, form_type, score, threshold_value,
                   acknowledged, acknowledged_by, acknowledged_at, created_at
            FROM threshold_alerts
            ORDER BY acknowledged ASC, created_at DESC
        ''')

        alerts = []
        for row in c.fetchall():
            alerts.append({
                'id': row[0],
                'inspection_id': row[1],
                'inspector_name': row[2],
                'form_type': row[3],
                'score': row[4],
                'threshold_value': row[5],
                'acknowledged': row[6] == 1,
                'acknowledged_by': row[7],
                'acknowledged_at': row[8],
                'created_at': row[9]
            })

        conn.close()

        return jsonify({
            'success': True,
            'alerts': alerts
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/threshold_alerts/clear_acknowledged', methods=['POST'])
def clear_acknowledged_alerts():
    """Clear all acknowledged alerts"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('DELETE FROM threshold_alerts WHERE acknowledged = 1')

        conn.commit()
        deleted_count = c.rowcount
        conn.close()

        return jsonify({
            'success': True,
            'message': f'{deleted_count} alert(s) cleared'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Enhanced Comprehensive Report Generator Functions
def generate_basic_summary_report(inspection_type, start_date, end_date):
    try:
        print(f"DEBUG: Generating comprehensive report for {inspection_type} from {start_date} to {end_date}")

        conn = get_db_connection()
        c = conn.cursor()

        # 1. OVERALL SUMMARY with Pass/Fail Rates
        if inspection_type == 'all':
            summary_query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN result IN ('Pass', 'Satisfactory') OR overall_score >= 70 THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN result IN ('Fail', 'Unsatisfactory') OR overall_score < 70 THEN 1 ELSE 0 END) as failed,
                    AVG(overall_score) as avg_score,
                    MAX(overall_score) as max_score,
                    MIN(overall_score) as min_score
                FROM inspections
                WHERE DATE(inspection_date) BETWEEN ? AND ?
            """
            params = (start_date, end_date)
        else:
            summary_query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN result IN ('Pass', 'Satisfactory') OR overall_score >= 70 THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN result IN ('Fail', 'Unsatisfactory') OR overall_score < 70 THEN 1 ELSE 0 END) as failed,
                    AVG(overall_score) as avg_score,
                    MAX(overall_score) as max_score,
                    MIN(overall_score) as min_score
                FROM inspections
                WHERE DATE(inspection_date) BETWEEN ? AND ?
                AND form_type = ?
            """
            params = (start_date, end_date, inspection_type)

        c.execute(summary_query, params)
        result = c.fetchone()

        total_inspections = result[0] or 0
        passed_inspections = result[1] or 0
        failed_inspections = result[2] or 0
        avg_score = result[3] or 0
        max_score = result[4] or 0
        min_score = result[5] or 0

        pass_percentage = (passed_inspections / total_inspections * 100) if total_inspections > 0 else 0
        fail_percentage = (failed_inspections / total_inspections * 100) if total_inspections > 0 else 0

        print(f"DEBUG: Found {total_inspections} total inspections")

        # 2. TREND DATA - Daily/Weekly breakdown
        trend_query = """
            SELECT
                DATE(inspection_date) as date,
                COUNT(*) as total,
                SUM(CASE WHEN result IN ('Pass', 'Satisfactory') OR overall_score >= 70 THEN 1 ELSE 0 END) as passed,
                SUM(CASE WHEN result IN ('Fail', 'Unsatisfactory') OR overall_score < 70 THEN 1 ELSE 0 END) as failed,
                AVG(overall_score) as avg_score
            FROM inspections
            WHERE DATE(inspection_date) BETWEEN ? AND ?
            {}
            GROUP BY DATE(inspection_date)
            ORDER BY date
        """.format("AND form_type = ?" if inspection_type != 'all' else "")

        trend_params = params
        c.execute(trend_query, trend_params)
        trend_data = [{
            'date': row[0],
            'total': row[1],
            'passed': row[2],
            'failed': row[3],
            'avg_score': round(row[4], 1) if row[4] else 0,
            'pass_rate': round((row[2] / row[1] * 100) if row[1] > 0 else 0, 1)
        } for row in c.fetchall()]

        # 3. TOP PERFORMING INSPECTORS (Perfect Scores)
        inspector_query = """
            SELECT
                inspector_name,
                COUNT(*) as total_inspections,
                SUM(CASE WHEN overall_score = 100 THEN 1 ELSE 0 END) as perfect_scores,
                SUM(CASE WHEN critical_score = (SELECT MAX(critical_score) FROM inspections WHERE inspector_name = i.inspector_name) THEN 1 ELSE 0 END) as max_critical,
                AVG(overall_score) as avg_overall,
                AVG(critical_score) as avg_critical,
                SUM(CASE WHEN result IN ('Pass', 'Satisfactory') THEN 1 ELSE 0 END) as passes
            FROM inspections i
            WHERE DATE(inspection_date) BETWEEN ? AND ?
            {}
            GROUP BY inspector_name
            HAVING COUNT(*) > 0
            ORDER BY perfect_scores DESC, avg_overall DESC
            LIMIT 10
        """.format("AND form_type = ?" if inspection_type != 'all' else "")

        c.execute(inspector_query, params)
        top_inspectors = [{
            'name': row[0],
            'total_inspections': row[1],
            'perfect_scores': row[2],
            'max_critical_scores': row[3],
            'avg_overall_score': round(row[4], 1) if row[4] else 0,
            'avg_critical_score': round(row[5], 1) if row[5] else 0,
            'pass_count': row[6],
            'pass_rate': round((row[6] / row[1] * 100) if row[1] > 0 else 0, 1)
        } for row in c.fetchall()]

        # 4. MOST FAILED CHECKLIST ITEMS
        # Get all inspection_items with failures
        checklist_query = """
            SELECT
                ii.item_id,
                COUNT(*) as total_checks,
                SUM(CASE WHEN CAST(ii.details AS INTEGER) = 0 THEN 1 ELSE 0 END) as failures,
                i.form_type
            FROM inspection_items ii
            JOIN inspections i ON ii.inspection_id = i.id
            WHERE DATE(i.inspection_date) BETWEEN ? AND ?
            {}
            GROUP BY ii.item_id, i.form_type
            HAVING failures > 0
            ORDER BY failures DESC, total_checks DESC
            LIMIT 20
        """.format("AND i.form_type = ?" if inspection_type != 'all' else "")

        c.execute(checklist_query, params)
        failed_items = [{
            'item_id': row[0],
            'total_checks': row[1],
            'failure_count': row[2],
            'form_type': row[3],
            'failure_rate': round((row[2] / row[1] * 100) if row[1] > 0 else 0, 1)
        } for row in c.fetchall()]

        # 5. ESTABLISHMENT RANKINGS
        establishment_query = """
            SELECT
                establishment_name,
                form_type,
                COUNT(*) as inspection_count,
                AVG(overall_score) as avg_score,
                MAX(overall_score) as best_score,
                MIN(overall_score) as worst_score,
                SUM(CASE WHEN result IN ('Pass', 'Satisfactory') THEN 1 ELSE 0 END) as passes
            FROM inspections
            WHERE DATE(inspection_date) BETWEEN ? AND ?
            AND establishment_name IS NOT NULL
            AND establishment_name != ''
            {}
            GROUP BY establishment_name, form_type
            HAVING COUNT(*) > 0
            ORDER BY avg_score DESC
        """.format("AND form_type = ?" if inspection_type != 'all' else "")

        c.execute(establishment_query, params)
        all_establishments = c.fetchall()

        top_establishments = [{
            'name': row[0],
            'type': row[1],
            'count': row[2],
            'avg_score': round(row[3], 1) if row[3] else 0,
            'best_score': round(row[4], 1) if row[4] else 0,
            'worst_score': round(row[5], 1) if row[5] else 0,
            'pass_count': row[6]
        } for row in all_establishments[:10]]

        failing_establishments = [{
            'name': row[0],
            'type': row[1],
            'count': row[2],
            'avg_score': round(row[3], 1) if row[3] else 0,
            'best_score': round(row[4], 1) if row[4] else 0,
            'worst_score': round(row[5], 1) if row[5] else 0,
            'pass_count': row[6]
        } for row in sorted(all_establishments, key=lambda x: x[3])[:10]]

        conn.close()

        return {
            'title': f'Comprehensive Inspection Report - {inspection_type}',
            'summary': {
                'total_inspections': total_inspections,
                'passed_inspections': passed_inspections,
                'failed_inspections': failed_inspections,
                'pass_percentage': round(pass_percentage, 1),
                'fail_percentage': round(fail_percentage, 1),
                'average_score': round(avg_score, 1),
                'highest_score': round(max_score, 1),
                'lowest_score': round(min_score, 1)
            },
            'trend_data': trend_data,
            'top_inspectors': top_inspectors,
            'common_failures': failed_items,
            'top_establishments': top_establishments,
            'failing_establishments': failing_establishments,
            'date_range': f"{start_date} to {end_date}"
        }
    except Exception as e:
        print(f"DEBUG: Error in generate_basic_summary_report: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': f'Error generating report: {str(e)}'}

def generate_trend_analysis_report(inspection_type, start_date, end_date):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get weekly trend data
        if inspection_type == 'all':
            query = """
                SELECT
                    strftime('%Y-W%W', inspection_date) as week,
                    COUNT(*) as total,
                    SUM(CASE WHEN overall_score < 70 THEN 1 ELSE 0 END) as failed
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND inspection_date IS NOT NULL
                GROUP BY strftime('%Y-W%W', inspection_date)
                ORDER BY week
            """
            params = (start_date, end_date)
        else:
            query = """
                SELECT
                    strftime('%Y-W%W', inspection_date) as week,
                    COUNT(*) as total,
                    SUM(CASE WHEN overall_score < 70 THEN 1 ELSE 0 END) as failed
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND form_type = ?
                AND inspection_date IS NOT NULL
                GROUP BY strftime('%Y-W%W', inspection_date)
                ORDER BY week
            """
            params = (start_date, end_date, inspection_type)

        c.execute(query, params)
        results = c.fetchall()
        conn.close()

        # Process results
        trend_data = []
        for week, total, failed in results:
            failure_rate = (failed / total * 100) if total > 0 else 0
            trend_data.append({
                'week': week,
                'total': total,
                'failed': failed or 0,
                'failure_rate': round(failure_rate, 1)
            })

        # Determine if failures are increasing or decreasing
        if len(trend_data) >= 2:
            recent_avg = sum([d['failure_rate'] for d in trend_data[-3:]]) / min(3, len(trend_data))
            older_avg = sum([d['failure_rate'] for d in trend_data[:3]]) / min(3, len(trend_data))
            trend_direction = "Increasing" if recent_avg > older_avg else "Decreasing"
        else:
            trend_direction = "Insufficient data"

        return {
            'title': f'Trend Analysis Report - {inspection_type}',
            'trend_direction': trend_direction,
            'weekly_data': trend_data,
            'summary': {
                'total_weeks': len(trend_data),
                'avg_weekly_inspections': round(sum([d['total'] for d in trend_data]) / len(trend_data), 1) if trend_data else 0,
                'avg_failure_rate': round(sum([d['failure_rate'] for d in trend_data]) / len(trend_data), 1) if trend_data else 0
            }
        }
    except Exception as e:
        return {'error': f'Error generating trend analysis: {str(e)}'}

def generate_failure_breakdown_report(inspection_type, start_date, end_date):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get total failed inspections count
        if inspection_type == 'all':
            failed_query = """
                SELECT COUNT(*)
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND overall_score < 70
                AND inspection_date IS NOT NULL
            """
            failed_params = (start_date, end_date)
        else:
            failed_query = """
                SELECT COUNT(*)
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND form_type = ?
                AND overall_score < 70
                AND inspection_date IS NOT NULL
            """
            failed_params = (start_date, end_date, inspection_type)

        c.execute(failed_query, failed_params)
        total_failed = c.fetchone()[0] or 0

        # Get failed checklist items (this might need adjustment based on your actual schema)
        # For now, let's get some basic failure analysis from the inspections table
        if inspection_type == 'all':
            items_query = """
                SELECT form_type, COUNT(*) as failure_count
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND overall_score < 70
                AND inspection_date IS NOT NULL
                GROUP BY form_type
                ORDER BY failure_count DESC
                LIMIT 10
            """
            items_params = (start_date, end_date)
        else:
            # For specific inspection type, we'll create mock categories for demonstration
            items_query = """
                SELECT
                    CASE
                        WHEN overall_score < 30 THEN 'Critical Violations'
                        WHEN overall_score < 50 THEN 'Major Violations'
                        ELSE 'Minor Violations'
                    END as category,
                    COUNT(*) as failure_count
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND form_type = ?
                AND overall_score < 70
                AND inspection_date IS NOT NULL
                GROUP BY category
                ORDER BY failure_count DESC
            """
            items_params = (start_date, end_date, inspection_type)

        c.execute(items_query, items_params)
        items_results = c.fetchall()

        conn.close()

        # Format results
        top_failed_items = [{'item': item, 'count': count} for item, count in items_results]

        return {
            'title': f'Failure Breakdown Report - {inspection_type}',
            'total_failed_inspections': total_failed,
            'top_failed_items': top_failed_items,
            'top_failed_categories': top_failed_items[:5],  # Use same data for categories
            'summary': {
                'most_common_failure': top_failed_items[0]['item'] if top_failed_items else 'No failures found',
                'failure_frequency': top_failed_items[0]['count'] if top_failed_items else 0
            }
        }
    except Exception as e:
        return {'error': f'Error generating failure breakdown: {str(e)}'}

def generate_inspector_performance_report(inspection_type, start_date, end_date):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get inspector performance data
        if inspection_type == 'all':
            query = """
                SELECT
                    inspector_name,
                    COUNT(*) as total_inspections,
                    SUM(CASE WHEN overall_score >= 70 THEN 1 ELSE 0 END) as passed_inspections,
                    AVG(CASE WHEN overall_score IS NOT NULL THEN overall_score ELSE 0 END) as avg_score
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND inspection_date IS NOT NULL
                AND inspector_name IS NOT NULL
                GROUP BY inspector_name
                ORDER BY total_inspections DESC
            """
            params = (start_date, end_date)
        else:
            query = """
                SELECT
                    inspector_name,
                    COUNT(*) as total_inspections,
                    SUM(CASE WHEN overall_score >= 70 THEN 1 ELSE 0 END) as passed_inspections,
                    AVG(CASE WHEN overall_score IS NOT NULL THEN overall_score ELSE 0 END) as avg_score
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND form_type = ?
                AND inspection_date IS NOT NULL
                AND inspector_name IS NOT NULL
                GROUP BY inspector_name
                ORDER BY total_inspections DESC
            """
            params = (start_date, end_date, inspection_type)

        c.execute(query, params)
        results = c.fetchall()
        conn.close()

        # Process results
        performance_data = []
        for inspector, total, passed, avg_score in results:
            pass_rate = (passed / total * 100) if total > 0 else 0
            performance_data.append({
                'inspector': inspector or 'Unknown',
                'total_inspections': total,
                'passed_inspections': passed or 0,
                'pass_rate': round(pass_rate, 1),
                'avg_time_days': 1  # Simplified - actual calculation would need more data
            })

        return {
            'title': f'Inspector Performance Report - {inspection_type}',
            'inspector_performance': performance_data,
            'summary': {
                'total_inspectors': len(performance_data),
                'most_active_inspector': performance_data[0]['inspector'] if performance_data else 'None',
                'highest_pass_rate': max([p['pass_rate'] for p in performance_data]) if performance_data else 0
            }
        }
    except Exception as e:
        return {'error': f'Error generating inspector performance: {str(e)}'}

def generate_scores_by_type_report(inspection_type, start_date, end_date):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get scores by form type from all tables
        scores_data = []

        # Regular inspections
        query = """
            SELECT form_type, AVG(overall_score) as avg_score, COUNT(*) as count
            FROM inspections
            WHERE inspection_date BETWEEN ? AND ?
            AND inspection_date IS NOT NULL
            AND overall_score IS NOT NULL
            GROUP BY form_type
        """
        c.execute(query, (start_date, end_date))
        regular_results = c.fetchall()

        for form_type, avg_score, count in regular_results:
            scores_data.append({
                'type': form_type or 'Unknown',
                'avg_score': round(avg_score, 1),
                'count': count,
                'source': 'inspections'
            })

        # Residential inspections
        res_query = """
            SELECT 'Residential' as form_type, AVG(overall_score) as avg_score, COUNT(*) as count
            FROM residential_inspections
            WHERE inspection_date BETWEEN ? AND ?
            AND inspection_date IS NOT NULL
            AND overall_score IS NOT NULL
        """
        c.execute(res_query, (start_date, end_date))
        res_result = c.fetchone()

        if res_result and res_result[2] > 0:
            scores_data.append({
                'type': 'Residential',
                'avg_score': round(res_result[1], 1),
                'count': res_result[2],
                'source': 'residential_inspections'
            })

        # Burial inspections don't have scores, so we'll show count only
        burial_query = """
            SELECT COUNT(*) as count
            FROM burial_site_inspections
            WHERE inspection_date BETWEEN ? AND ?
            AND inspection_date IS NOT NULL
        """
        c.execute(burial_query, (start_date, end_date))
        burial_result = c.fetchone()

        if burial_result and burial_result[0] > 0:
            scores_data.append({
                'type': 'Burial Site',
                'avg_score': 'N/A (No scoring)',
                'count': burial_result[0],
                'source': 'burial_site_inspections'
            })

        conn.close()

        return {
            'title': 'Inspection Scores by Type',
            'scores_by_type': scores_data,
            'summary': {
                'total_types': len(scores_data),
                'highest_avg_type': max(scores_data, key=lambda x: x['avg_score'] if isinstance(x['avg_score'], (int, float)) else 0)['type'] if scores_data else 'None'
            }
        }
    except Exception as e:
        return {'error': f'Error generating scores by type: {str(e)}'}

def generate_monthly_trends_report(inspection_type, start_date, end_date):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get monthly trends from all tables
        monthly_data = []

        # Regular inspections
        if inspection_type == 'all':
            query = """
                SELECT
                    strftime('%Y-%m', inspection_date) as month,
                    COUNT(*) as total,
                    SUM(CASE WHEN overall_score >= 70 THEN 1 ELSE 0 END) as passed
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND inspection_date IS NOT NULL
                GROUP BY strftime('%Y-%m', inspection_date)
                ORDER BY month
            """
            params = (start_date, end_date)
        else:
            query = """
                SELECT
                    strftime('%Y-%m', inspection_date) as month,
                    COUNT(*) as total,
                    SUM(CASE WHEN overall_score >= 70 THEN 1 ELSE 0 END) as passed
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND form_type = ?
                AND inspection_date IS NOT NULL
                GROUP BY strftime('%Y-%m', inspection_date)
                ORDER BY month
            """
            params = (start_date, end_date, inspection_type)

        c.execute(query, params)
        results = c.fetchall()

        for month, total, passed in results:
            pass_rate = (passed / total * 100) if total > 0 else 0
            monthly_data.append({
                'month': month,
                'total': total,
                'passed': passed or 0,
                'failed': total - (passed or 0),
                'pass_rate': round(pass_rate, 1)
            })

        # Add residential data if inspection_type is 'all' or 'Residential'
        if inspection_type == 'all' or inspection_type == 'Residential':
            res_query = """
                SELECT
                    strftime('%Y-%m', inspection_date) as month,
                    COUNT(*) as total,
                    SUM(CASE WHEN overall_score >= 70 THEN 1 ELSE 0 END) as passed
                FROM residential_inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND inspection_date IS NOT NULL
                GROUP BY strftime('%Y-%m', inspection_date)
                ORDER BY month
            """
            c.execute(res_query, (start_date, end_date))
            res_results = c.fetchall()

            # Merge residential data with existing monthly data
            for month, total, passed in res_results:
                existing_month = next((item for item in monthly_data if item['month'] == month), None)
                if existing_month:
                    existing_month['total'] += total
                    existing_month['passed'] += passed or 0
                    existing_month['failed'] = existing_month['total'] - existing_month['passed']
                    existing_month['pass_rate'] = round((existing_month['passed'] / existing_month['total'] * 100), 1)
                else:
                    pass_rate = (passed / total * 100) if total > 0 else 0
                    monthly_data.append({
                        'month': month,
                        'total': total,
                        'passed': passed or 0,
                        'failed': total - (passed or 0),
                        'pass_rate': round(pass_rate, 1)
                    })

        conn.close()

        # Sort by month
        monthly_data.sort(key=lambda x: x['month'])

        return {
            'title': 'Monthly Trends Analysis',
            'monthly_trends': monthly_data,
            'summary': {
                'total_months': len(monthly_data),
                'avg_monthly_inspections': round(sum([m['total'] for m in monthly_data]) / len(monthly_data), 1) if monthly_data else 0,
                'avg_pass_rate': round(sum([m['pass_rate'] for m in monthly_data]) / len(monthly_data), 1) if monthly_data else 0
            }
        }
    except Exception as e:
        return {'error': f'Error generating monthly trends: {str(e)}'}

def generate_establishment_ranking_report(inspection_type, start_date, end_date):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get top performing establishments
        if inspection_type == 'all':
            top_query = """
                SELECT
                    establishment_name,
                    owner,
                    AVG(overall_score) as avg_score,
                    COUNT(*) as inspection_count,
                    form_type
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND inspection_date IS NOT NULL
                AND overall_score IS NOT NULL
                AND establishment_name IS NOT NULL
                GROUP BY establishment_name, owner
                HAVING COUNT(*) >= 1
                ORDER BY avg_score DESC
                LIMIT 10
            """
            params = (start_date, end_date)
        else:
            top_query = """
                SELECT
                    establishment_name,
                    owner,
                    AVG(overall_score) as avg_score,
                    COUNT(*) as inspection_count,
                    form_type
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND form_type = ?
                AND inspection_date IS NOT NULL
                AND overall_score IS NOT NULL
                AND establishment_name IS NOT NULL
                GROUP BY establishment_name, owner
                HAVING COUNT(*) >= 1
                ORDER BY avg_score DESC
                LIMIT 10
            """
            params = (start_date, end_date, inspection_type)

        c.execute(top_query, params)
        top_results = c.fetchall()

        # Get worst performing establishments
        if inspection_type == 'all':
            worst_query = """
                SELECT
                    establishment_name,
                    owner,
                    AVG(overall_score) as avg_score,
                    COUNT(*) as inspection_count,
                    form_type
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND inspection_date IS NOT NULL
                AND overall_score IS NOT NULL
                AND establishment_name IS NOT NULL
                GROUP BY establishment_name, owner
                HAVING COUNT(*) >= 1
                ORDER BY avg_score ASC
                LIMIT 10
            """
            params = (start_date, end_date)
        else:
            worst_query = """
                SELECT
                    establishment_name,
                    owner,
                    AVG(overall_score) as avg_score,
                    COUNT(*) as inspection_count,
                    form_type
                FROM inspections
                WHERE inspection_date BETWEEN ? AND ?
                AND form_type = ?
                AND inspection_date IS NOT NULL
                AND overall_score IS NOT NULL
                AND establishment_name IS NOT NULL
                GROUP BY establishment_name, owner
                HAVING COUNT(*) >= 1
                ORDER BY avg_score ASC
                LIMIT 10
            """
            params = (start_date, end_date, inspection_type)

        c.execute(worst_query, params)
        worst_results = c.fetchall()

        conn.close()

        # Process results
        top_performers = []
        for name, owner, avg_score, count, form_type in top_results:
            top_performers.append({
                'establishment': name or 'Unknown',
                'owner': owner or 'Unknown',
                'avg_score': round(avg_score, 1),
                'inspection_count': count,
                'type': form_type or 'Unknown'
            })

        worst_performers = []
        for name, owner, avg_score, count, form_type in worst_results:
            worst_performers.append({
                'establishment': name or 'Unknown',
                'owner': owner or 'Unknown',
                'avg_score': round(avg_score, 1),
                'inspection_count': count,
                'type': form_type or 'Unknown'
            })

        return {
            'title': 'Establishment Performance Ranking',
            'top_performers': top_performers,
            'worst_performers': worst_performers,
            'summary': {
                'highest_score': top_performers[0]['avg_score'] if top_performers else 0,
                'lowest_score': worst_performers[0]['avg_score'] if worst_performers else 0,
                'total_establishments_analyzed': len(set([e['establishment'] for e in top_performers + worst_performers]))
            }
        }
    except Exception as e:
        return {'error': f'Error generating establishment ranking: {str(e)}'}

# ================== ADVANCED ANALYTICS ENGINE ==================

def generate_comprehensive_multi_dimensional_analysis(inspection_type, start_date, end_date, depth, options):
    """Generate comprehensive multi-dimensional analysis with deep insights"""

    # Core data aggregation
    core_stats = get_advanced_statistical_overview(inspection_type, start_date, end_date)

    analysis = {
        'executiveSummary': core_stats,
        'total_analyzed_records': core_stats['totalInspections'],
        'dataQualityMetrics': assess_data_quality(inspection_type, start_date, end_date),
        'statisticalInsights': generate_statistical_insights(inspection_type, start_date, end_date),
    }

    if options.get('includeChecklistCorrelations'):
        analysis['checklistCorrelations'] = analyze_checklist_item_correlations(inspection_type, start_date, end_date)

    if options.get('includeInspectorBehavioral'):
        analysis['inspectorBehavioralPatterns'] = analyze_inspector_behavioral_patterns(inspection_type, start_date, end_date)

    if options.get('includeTimeSeriesAnalysis'):
        analysis['timeSeriesDecomposition'] = perform_time_series_decomposition(inspection_type, start_date, end_date)

    if options.get('includeRiskScoring'):
        analysis['riskScoringModel'] = generate_risk_scoring_model(inspection_type, start_date, end_date)

    if options.get('includeCompliancePatterns'):
        analysis['compliancePatterns'] = mine_compliance_patterns(inspection_type, start_date, end_date)

    if options.get('includeOutlierDetection'):
        analysis['outlierAnalysis'] = detect_and_analyze_outliers(inspection_type, start_date, end_date)

    if options.get('includeClusterAnalysis'):
        analysis['establishmentClusters'] = perform_establishment_clustering(inspection_type, start_date, end_date)

    if options.get('includeSeasonalityAnalysis'):
        analysis['seasonalityImpact'] = analyze_seasonal_impact_patterns(inspection_type, start_date, end_date)

    if options.get('includeResourceOptimization'):
        analysis['resourceOptimization'] = generate_resource_optimization_insights(inspection_type, start_date, end_date)

    # Generate advanced recommendations based on all analysis
    analysis['strategicRecommendations'] = generate_strategic_recommendations(analysis)
    analysis['actionableTasks'] = generate_actionable_task_recommendations(analysis)

    return analysis

def get_advanced_statistical_overview(inspection_type, start_date, end_date):
    """Enhanced statistical overview with advanced metrics"""
    conn = get_db_connection()
    c = conn.cursor()

    # Multi-source data aggregation
    total_inspections = 0
    all_scores = []
    pass_fail_data = []
    critical_violations = 0
    inspection_durations = []

    # Query main inspections
    query = "SELECT result, overall_score, critical_score, created_at, inspection_time FROM inspections WHERE created_at BETWEEN ? AND ?"
    params = [start_date, end_date]

    if inspection_type != 'all':
        query += " AND form_type = ?"
        params.append(inspection_type)

    c.execute(query, params)
    for row in c.fetchall():
        result, overall_score, critical_score, created_at, inspection_time = row
        total_inspections += 1

        if overall_score:
            all_scores.append(overall_score)

        pass_fail_data.append(1 if result in ['Pass', 'Satisfactory'] else 0)

        if critical_score and critical_score < 50:
            critical_violations += 1

    # Calculate advanced statistical metrics
    import statistics

    if all_scores:
        score_mean = statistics.mean(all_scores)
        score_median = statistics.median(all_scores)
        score_std = statistics.stdev(all_scores) if len(all_scores) > 1 else 0
        score_variance = statistics.variance(all_scores) if len(all_scores) > 1 else 0

        # Quartile analysis
        all_scores.sort()
        q1 = all_scores[len(all_scores)//4] if all_scores else 0
        q3 = all_scores[3*len(all_scores)//4] if all_scores else 0
        iqr = q3 - q1
    else:
        score_mean = score_median = score_std = score_variance = q1 = q3 = iqr = 0

    pass_rate = (sum(pass_fail_data) / len(pass_fail_data) * 100) if pass_fail_data else 0

    # Quality indicators
    data_completeness = (len(all_scores) / total_inspections * 100) if total_inspections > 0 else 0

    conn.close()

    return {
        'totalInspections': total_inspections,
        'passRate': round(pass_rate, 2),
        'averageScore': round(score_mean, 2),
        'medianScore': round(score_median, 2),
        'scoreStandardDeviation': round(score_std, 2),
        'scoreVariance': round(score_variance, 2),
        'firstQuartile': round(q1, 2),
        'thirdQuartile': round(q3, 2),
        'interQuartileRange': round(iqr, 2),
        'criticalViolations': critical_violations,
        'dataCompleteness': round(data_completeness, 2),
        'riskLevel': 'High' if pass_rate < 70 else 'Medium' if pass_rate < 85 else 'Low',
        'performanceGrade': calculate_performance_grade(pass_rate, score_mean),
        'trendIndicator': calculate_trend_indicator(inspection_type, start_date, end_date)
    }

def calculate_performance_grade(pass_rate, avg_score):
    """Calculate overall performance grade"""
    combined_score = (pass_rate + avg_score) / 2
    if combined_score >= 90:
        return 'A+'
    elif combined_score >= 85:
        return 'A'
    elif combined_score >= 80:
        return 'B+'
    elif combined_score >= 75:
        return 'B'
    elif combined_score >= 70:
        return 'C+'
    elif combined_score >= 65:
        return 'C'
    elif combined_score >= 60:
        return 'D'
    else:
        return 'F'

def calculate_trend_indicator(inspection_type, start_date, end_date):
    """Calculate performance trend over time"""
    conn = get_db_connection()
    c = conn.cursor()

    # Get scores by week for trend analysis
    query = """
        SELECT strftime('%W', created_at) as week, AVG(overall_score) as avg_score
        FROM inspections
        WHERE created_at BETWEEN ? AND ? AND overall_score IS NOT NULL
    """
    params = [start_date, end_date]

    if inspection_type != 'all':
        query += " AND form_type = ?"
        params.append(inspection_type)

    query += " GROUP BY week ORDER BY week"

    c.execute(query, params)
    weekly_scores = [row[1] for row in c.fetchall()]

    conn.close()

    if len(weekly_scores) < 2:
        return '➡️ Stable'

    # Simple trend calculation
    first_half = weekly_scores[:len(weekly_scores)//2]
    second_half = weekly_scores[len(weekly_scores)//2:]

    if not first_half or not second_half:
        return '➡️ Stable'

    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)

    improvement = second_avg - first_avg

    if improvement > 5:
        return '📈 Improving'
    elif improvement < -5:
        return '📉 Declining'
    else:
        return '➡️ Stable'

def assess_data_quality(inspection_type, start_date, end_date):
    """Assess the quality and completeness of inspection data"""
    conn = get_db_connection()
    c = conn.cursor()

    # Count total records and missing data
    query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN overall_score IS NULL THEN 1 ELSE 0 END) as missing_scores,
            SUM(CASE WHEN inspector_name IS NULL OR inspector_name = '' THEN 1 ELSE 0 END) as missing_inspector,
            SUM(CASE WHEN establishment_name IS NULL OR establishment_name = '' THEN 1 ELSE 0 END) as missing_establishment
        FROM inspections
        WHERE created_at BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if inspection_type != 'all':
        query += " AND form_type = ?"
        params.append(inspection_type)

    c.execute(query, params)
    row = c.fetchone()

    total, missing_scores, missing_inspector, missing_establishment = row

    if total == 0:
        return {'quality': 'No Data', 'completeness': 0}

    completeness = ((total - missing_scores - missing_inspector - missing_establishment) / (total * 3)) * 100

    quality_grade = 'Excellent' if completeness > 95 else 'Good' if completeness > 85 else 'Fair' if completeness > 70 else 'Poor'

    conn.close()

    return {
        'quality': quality_grade,
        'completeness': round(completeness, 2),
        'totalRecords': total,
        'missingScores': missing_scores,
        'missingInspectors': missing_inspector,
        'missingEstablishments': missing_establishment,
        'recommendations': generate_data_quality_recommendations(completeness, missing_scores, missing_inspector)
    }

def generate_data_quality_recommendations(completeness, missing_scores, missing_inspector):
    """Generate recommendations for improving data quality"""
    recommendations = []

    if completeness < 85:
        recommendations.append("🔧 Implement mandatory field validation in inspection forms")

    if missing_scores > 0:
        recommendations.append("📊 Ensure all inspections include proper scoring")

    if missing_inspector > 0:
        recommendations.append("👤 Improve inspector identification tracking")

    if completeness > 95:
        recommendations.append("✅ Data quality is excellent - maintain current standards")

    return recommendations

def generate_checklist_failure_analysis(inspection_type, start_date, end_date):
    """Analyze which checklist items fail most frequently"""
    conn = get_db_connection()
    c = conn.cursor()

    # Get inspection items with failures
    query = """
        SELECT ii.item_id, ii.details, COUNT(*) as failure_count,
               AVG(CASE WHEN ii.error = 'fail' OR ii.obser = 'fail' THEN 1 ELSE 0 END) as failure_rate
        FROM inspection_items ii
        JOIN inspections i ON ii.inspection_id = i.id
        WHERE i.created_at BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if inspection_type != 'all':
        query += " AND i.form_type = ?"
        params.append(inspection_type)

    query += """
        GROUP BY ii.item_id, ii.details
        HAVING failure_count > 0
        ORDER BY failure_rate DESC, failure_count DESC
        LIMIT 15
    """

    c.execute(query, params)
    items = []

    for row in c.fetchall():
        item_id, details, failure_count, failure_rate = row

        # Determine impact based on failure rate and frequency
        if failure_rate > 0.7:
            impact = 'High'
        elif failure_rate > 0.4:
            impact = 'Medium'
        else:
            impact = 'Low'

        items.append({
            'itemId': item_id,
            'description': details or f"Item {item_id}",
            'failureRate': round(failure_rate * 100, 1),
            'totalFailures': failure_count,
            'impact': impact
        })

    conn.close()
    return items

def generate_inspector_performance(inspection_type, start_date, end_date):
    """Generate inspector performance statistics"""
    conn = get_db_connection()
    c = conn.cursor()

    query = """
        SELECT inspector_name,
               COUNT(*) as total_inspections,
               AVG(overall_score) as avg_score,
               SUM(CASE WHEN result IN ('Pass', 'Satisfactory') THEN 1 ELSE 0 END) as passed,
               SUM(CASE WHEN result IN ('Fail', 'Unsatisfactory') THEN 1 ELSE 0 END) as failed
        FROM inspections
        WHERE created_at BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if inspection_type != 'all':
        query += " AND form_type = ?"
        params.append(inspection_type)

    query += " GROUP BY inspector_name ORDER BY total_inspections DESC"

    c.execute(query, params)
    inspectors = []

    for row in c.fetchall():
        inspector_name, total, avg_score, passed, failed = row
        pass_rate = round((passed / total) * 100, 1) if total > 0 else 0

        inspectors.append({
            'name': inspector_name,
            'totalInspections': total,
            'averageScore': round(avg_score or 0, 1),
            'passRate': pass_rate,
            'efficiency': 'High' if pass_rate > 80 else 'Medium' if pass_rate > 60 else 'Low'
        })

    conn.close()
    return inspectors

def generate_score_analysis(inspection_type, start_date, end_date):
    """Generate detailed score analysis and trends"""
    conn = get_db_connection()
    c = conn.cursor()

    query = """
        SELECT overall_score, critical_score, created_at
        FROM inspections
        WHERE created_at BETWEEN ? AND ? AND overall_score IS NOT NULL
    """
    params = [start_date, end_date]

    if inspection_type != 'all':
        query += " AND form_type = ?"
        params.append(inspection_type)

    query += " ORDER BY created_at"

    c.execute(query, params)
    scores = []
    for row in c.fetchall():
        overall_score, critical_score, created_at = row
        scores.append({
            'overall': overall_score,
            'critical': critical_score or 0,
            'date': created_at
        })

    conn.close()
    return {
        'scores': scores,
        'trends': analyze_score_trends(scores)
    }

def analyze_score_trends(scores):
    """Analyze score trends over time"""
    if len(scores) < 2:
        return {'trend': 'insufficient_data'}

    # Simple trend analysis
    recent_scores = [s['overall'] for s in scores[-10:]]  # Last 10 scores
    older_scores = [s['overall'] for s in scores[:-10]] if len(scores) > 10 else []

    if not older_scores:
        return {'trend': 'stable', 'direction': 'no_change'}

    recent_avg = sum(recent_scores) / len(recent_scores)
    older_avg = sum(older_scores) / len(older_scores)

    improvement = recent_avg - older_avg

    if improvement > 5:
        return {'trend': 'improving', 'direction': 'up', 'improvement': round(improvement, 1)}
    elif improvement < -5:
        return {'trend': 'declining', 'direction': 'down', 'decline': round(abs(improvement), 1)}
    else:
        return {'trend': 'stable', 'direction': 'stable'}

def generate_recommendations(inspection_type, start_date, end_date):
    """Generate actionable recommendations based on data"""
    conn = get_db_connection()
    c = conn.cursor()

    recommendations = []

    # Get failure rate
    query = """
        SELECT
            SUM(CASE WHEN result IN ('Pass', 'Satisfactory') THEN 1 ELSE 0 END) as passed,
            COUNT(*) as total
        FROM inspections
        WHERE created_at BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if inspection_type != 'all':
        query += " AND form_type = ?"
        params.append(inspection_type)

    c.execute(query, params)
    row = c.fetchone()
    passed, total = row if row else (0, 0)

    if total > 0:
        pass_rate = (passed / total) * 100

        if pass_rate < 70:
            recommendations.append("🚨 Critical: Pass rate is below 70%. Consider additional inspector training and stricter initial assessments.")
        elif pass_rate < 85:
            recommendations.append("⚠️ Pass rate could be improved. Review most common failure points and provide targeted guidance.")

    # Get most common failures
    checklist_failures = generate_checklist_failure_analysis(inspection_type, start_date, end_date)
    if checklist_failures and len(checklist_failures) > 0:
        top_failure = checklist_failures[0]
        recommendations.append(f"🎯 Focus on '{top_failure['description']}' - it has a {top_failure['failureRate']}% failure rate.")

    # Add general recommendations
    recommendations.extend([
        "📚 Implement regular inspector training sessions on most failed checklist items.",
        "📊 Set up monthly performance reviews with individual inspectors.",
        "🔄 Create feedback loops between inspectors and management for continuous improvement."
    ])

    conn.close()
    return recommendations[:5]  # Return top 5 recommendations

def generate_geographic_analysis(inspection_type, start_date, end_date):
    """Generate geographic distribution analysis"""
    # This would require location data - for now return basic structure
    return {
        'distribution': 'Geographic analysis requires location data implementation',
        'note': 'Feature available when location tracking is enabled'
    }

@app.route('/api/admin/download_report', methods=['GET'])
def download_report():
    if 'admin' not in session and 'inspector' not in session:
        return jsonify({'error': 'Unauthorized - Please log in'}), 401

    try:
        # Get parameters from query string (support both naming conventions)
        report_type = request.args.get('report_type') or request.args.get('reportType', 'basic_summary')
        inspection_type = request.args.get('inspection_type') or request.args.get('inspectionType', 'all')
        start_date = request.args.get('start_date') or request.args.get('startDate')
        end_date = request.args.get('end_date') or request.args.get('endDate')
        format_type = request.args.get('format', 'pdf')

        # Generate report data using the simplified functions
        report_generators = {
            'basic_summary': generate_basic_summary_report,
            'trend_analysis': generate_trend_analysis_report,
            'failure_breakdown': generate_failure_breakdown_report,
            'inspector_performance': generate_inspector_performance_report,
            'scores_by_type': generate_scores_by_type_report,
            'monthly_trends': generate_monthly_trends_report,
            'establishment_ranking': generate_establishment_ranking_report,
            'comprehensive': generate_basic_summary_report  # Use basic summary for comprehensive
        }

        generator_func = report_generators.get(report_type, generate_basic_summary_report)
        report_data = generator_func(inspection_type, start_date, end_date)

        if format_type == 'pdf':
            return generate_professional_pdf_report(report_data, report_type, inspection_type, start_date, end_date)
        elif format_type == 'csv':
            return generate_csv_download(report_data, report_type, inspection_type, start_date, end_date)
        else:
            return jsonify({'error': 'Unsupported format. Use pdf or csv'}), 400

    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

def generate_professional_pdf_report(report_data, report_type, inspection_type, start_date, end_date):
    """Generate professional PDF report with clean formatting"""
    from io import BytesIO
    from datetime import datetime

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    # Professional styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2C3E50')
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#34495E')
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leading=14
    )

    story = []

    # Header
    story.append(Paragraph("Inspection Management System", title_style))
    story.append(Paragraph(f"{report_data.get('title', 'Inspection Report')}", heading_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", body_style))
    story.append(Paragraph(f"Report Period: {start_date} to {end_date}", body_style))
    story.append(Spacer(1, 20))

    # Add content based on report type
    if report_type == 'basic_summary':
        add_basic_summary_content(story, report_data, styles)
    elif report_type == 'trend_analysis':
        add_trend_analysis_content(story, report_data, styles)
    elif report_type == 'failure_breakdown':
        add_failure_breakdown_content(story, report_data, styles)
    elif report_type == 'inspector_performance':
        add_inspector_performance_content(story, report_data, styles)

    # Footer
    story.append(Spacer(1, 20))
    story.append(Paragraph("Report generated by Inspection Management System",
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9,
                                       alignment=TA_CENTER, textColor=colors.grey)))

    doc.build(story)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f'inspection_report_{report_type}_{start_date}_to_{end_date}.pdf',
                     mimetype='application/pdf')

def add_basic_summary_content(story, report_data, styles):
    """Add basic summary report content to PDF"""
    story.append(Paragraph("Executive Summary", styles['Heading2']))

    summary = report_data.get('summary', {})

    # Create summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Inspections', str(summary.get('total_inspections', 0))],
        ['Passed Inspections', str(summary.get('passed_inspections', 0))],
        ['Failed Inspections', str(summary.get('failed_inspections', 0))],
        ['Pass Rate', f"{summary.get('pass_percentage', 0)}%"],
        ['Fail Rate', f"{summary.get('fail_percentage', 0)}%"],
        ['Average Daily Inspections', str(summary.get('average_daily_inspections', 0))]
    ]

    table = Table(summary_data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(table)

def add_trend_analysis_content(story, report_data, styles):
    """Add trend analysis content to PDF"""
    story.append(Paragraph("Trend Analysis", styles['Heading2']))
    story.append(Paragraph(f"Trend Direction: {report_data.get('trend_direction', 'Unknown')}", styles['Normal']))

    summary = report_data.get('summary', {})
    story.append(Paragraph(f"Average Weekly Inspections: {summary.get('avg_weekly_inspections', 0)}", styles['Normal']))
    story.append(Paragraph(f"Average Failure Rate: {summary.get('avg_failure_rate', 0)}%", styles['Normal']))

    # Weekly data table
    weekly_data = report_data.get('weekly_data', [])
    if weekly_data:
        story.append(Paragraph("Weekly Breakdown", styles['Heading3']))
        table_data = [['Week', 'Total', 'Failed', 'Failure Rate']]
        for week_info in weekly_data[:10]:  # Show first 10 weeks
            table_data.append([
                week_info.get('week', ''),
                str(week_info.get('total', 0)),
                str(week_info.get('failed', 0)),
                f"{week_info.get('failure_rate', 0)}%"
            ])

        table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)

def add_failure_breakdown_content(story, report_data, styles):
    """Add failure breakdown content to PDF"""
    story.append(Paragraph("Failure Analysis", styles['Heading2']))
    story.append(Paragraph(f"Total Failed Inspections: {report_data.get('total_failed_inspections', 0)}", styles['Normal']))

    # Top failed items
    top_failed = report_data.get('top_failed_items', [])
    if top_failed:
        story.append(Paragraph("Most Common Failures", styles['Heading3']))
        table_data = [['Failure Reason', 'Count']]
        for item in top_failed[:8]:  # Show top 8
            table_data.append([item.get('item', ''), str(item.get('count', 0))])

        table = Table(table_data, colWidths=[4*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E67E22')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)

def add_inspector_performance_content(story, report_data, styles):
    """Add inspector performance content to PDF"""
    story.append(Paragraph("Inspector Performance Analysis", styles['Heading2']))

    summary = report_data.get('summary', {})
    story.append(Paragraph(f"Total Inspectors: {summary.get('total_inspectors', 0)}", styles['Normal']))
    story.append(Paragraph(f"Most Active Inspector: {summary.get('most_active_inspector', 'None')}", styles['Normal']))
    story.append(Paragraph(f"Highest Pass Rate: {summary.get('highest_pass_rate', 0)}%", styles['Normal']))

    # Inspector performance table
    performance_data = report_data.get('inspector_performance', [])
    if performance_data:
        table_data = [['Inspector', 'Total', 'Passed', 'Pass Rate', 'Avg Time (Days)']]
        for perf in performance_data[:10]:  # Show top 10
            table_data.append([
                perf.get('inspector', ''),
                str(perf.get('total_inspections', 0)),
                str(perf.get('passed_inspections', 0)),
                f"{perf.get('pass_rate', 0)}%",
                str(perf.get('avg_time_days', 0))
            ])

        table = Table(table_data, colWidths=[1.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9B59B6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)

    # Title
    story.append(Paragraph("📊 Comprehensive Inspection Report", title_style))
    story.append(Spacer(1, 20))

    # Report Info
    story.append(Paragraph(f"<b>Report Period:</b> {start_date} to {end_date}", styles['Normal']))
    story.append(Paragraph(f"<b>Inspection Type:</b> {inspection_type}", styles['Normal']))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph("📈 Executive Summary", styles['Heading2']))
    summary_data = [
        ['Metric', 'Value'],
        ['Total Inspections', str(summary['totalInspections'])],
        ['Pass Rate', f"{summary['passRate']}%"],
        ['Average Score', str(summary['averageScore'])],
        ['Critical Violations', str(summary['criticalViolations'])]
    ]

    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Checklist Failures
    if checklist_failures:
        story.append(Paragraph("❌ Most Failed Checklist Items", styles['Heading2']))

        failure_data = [['Item', 'Failure Rate', 'Total Failures', 'Impact']]
        for item in checklist_failures[:10]:  # Top 10
            failure_data.append([
                item['description'][:50] + '...' if len(item['description']) > 50 else item['description'],
                f"{item['failureRate']}%",
                str(item['totalFailures']),
                item['impact']
            ])

        failure_table = Table(failure_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        failure_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(failure_table)
        story.append(Spacer(1, 20))

    # Recommendations
    if recommendations:
        story.append(Paragraph("💡 Key Recommendations", styles['Heading2']))
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
        story.append(Spacer(1, 20))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="comprehensive_inspection_report_{start_date}_to_{end_date}.pdf"'
    return response

def generate_csv_report(summary, checklist_failures, inspector_stats, inspection_type, start_date, end_date):
    """Generate CSV report data"""
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Write summary data
    writer.writerow(['Comprehensive Inspection Report'])
    writer.writerow(['Report Period', f'{start_date} to {end_date}'])
    writer.writerow(['Inspection Type', inspection_type])
    writer.writerow([])

    # Executive Summary
    writer.writerow(['Executive Summary'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Inspections', summary['totalInspections']])
    writer.writerow(['Pass Rate', f"{summary['passRate']}%"])
    writer.writerow(['Average Score', summary['averageScore']])
    writer.writerow(['Critical Violations', summary['criticalViolations']])
    writer.writerow([])

    # Checklist Failures
    if checklist_failures:
        writer.writerow(['Most Failed Checklist Items'])
        writer.writerow(['Item Description', 'Failure Rate (%)', 'Total Failures', 'Impact'])
        for item in checklist_failures:
            writer.writerow([item['description'], item['failureRate'], item['totalFailures'], item['impact']])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename="inspection_report_{start_date}_to_{end_date}.csv"'
    return response

def generate_csv_download(report_data, report_type, inspection_type, start_date, end_date):
    """Generate CSV file download from report data"""
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['Inspection Management System - Analytics Report'])
    writer.writerow(['Report Type', report_type.replace('_', ' ').title()])
    writer.writerow(['Inspection Type', inspection_type])
    writer.writerow(['Period', f'{start_date} to {end_date}'])
    writer.writerow(['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])

    # Summary Section
    if 'summary' in report_data:
        writer.writerow(['EXECUTIVE SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        summary = report_data['summary']
        writer.writerow(['Total Inspections', summary.get('total_inspections', 0)])
        writer.writerow(['Passed Inspections', summary.get('passed_inspections', 0)])
        writer.writerow(['Failed Inspections', summary.get('failed_inspections', 0)])
        writer.writerow(['Pass Rate', f"{summary.get('pass_percentage', 0)}%"])
        writer.writerow(['Fail Rate', f"{summary.get('fail_percentage', 0)}%"])
        writer.writerow(['Average Score', f"{summary.get('average_score', 0)}%"])
        writer.writerow(['Average Daily Inspections', summary.get('average_daily_inspections', 0)])
        writer.writerow([])

    # Top Inspectors
    if 'top_inspectors' in report_data:
        writer.writerow(['TOP PERFORMING INSPECTORS'])
        writer.writerow(['Inspector Name', 'Total Inspections', 'Average Score'])
        for inspector in report_data['top_inspectors']:
            writer.writerow([inspector.get('name'), inspector.get('count'), f"{inspector.get('avg_score', 0)}%"])
        writer.writerow([])

    # Common Failures
    if 'common_failures' in report_data:
        writer.writerow(['MOST COMMON FAILURES'])
        writer.writerow(['Item', 'Failure Count'])
        for failure in report_data['common_failures']:
            writer.writerow([failure.get('item'), failure.get('count')])
        writer.writerow([])

    # Monthly Trends
    if 'monthly_data' in report_data:
        writer.writerow(['MONTHLY TRENDS'])
        writer.writerow(['Month', 'Total Inspections', 'Passed', 'Failed', 'Pass Rate'])
        for month in report_data['monthly_data']:
            writer.writerow([
                month.get('month'),
                month.get('total', 0),
                month.get('passed', 0),
                month.get('failed', 0),
                f"{month.get('pass_rate', 0)}%"
            ])
        writer.writerow([])

    # Establishment Rankings
    if 'top_establishments' in report_data:
        writer.writerow(['TOP PERFORMING ESTABLISHMENTS'])
        writer.writerow(['Establishment Name', 'Average Score', 'Inspections'])
        for est in report_data['top_establishments']:
            writer.writerow([est.get('name'), f"{est.get('avg_score', 0)}%", est.get('count', 0)])
        writer.writerow([])

    if 'failing_establishments' in report_data:
        writer.writerow(['FAILING ESTABLISHMENTS'])
        writer.writerow(['Establishment Name', 'Average Score', 'Inspections'])
        for est in report_data['failing_establishments']:
            writer.writerow([est.get('name'), f"{est.get('avg_score', 0)}%", est.get('count', 0)])
        writer.writerow([])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="inspection_report_{report_type}_{start_date}_to_{end_date}.csv"'
    return response


# ============================================================================
# FORM BUILDER API - Admin Form Management
# ============================================================================

@app.route('/admin/form_builder')
def form_builder():
    """Admin form builder page"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM form_templates WHERE active = 1 ORDER BY name')
    templates = c.fetchall()
    conn.close()

    return render_template('admin_form_builder.html', templates=templates)


@app.route('/api/admin/forms/templates', methods=['GET'])
def get_form_templates():
    """Get all form templates"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM form_templates WHERE active = 1 ORDER BY name')
    templates = []
    for row in c.fetchall():
        templates.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'form_type': row[3],
            'active': row[4],
            'created_date': row[5],
            'version': row[6]
        })
    conn.close()

    return jsonify({'templates': templates})


@app.route('/api/admin/forms/template/<int:template_id>/items', methods=['GET'])
def get_form_items(template_id):
    """Get all items for a form template"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, form_template_id, item_order, category, description,
               weight, is_critical, active, created_date
        FROM form_items
        WHERE form_template_id = ? AND active = 1
        ORDER BY item_order
    ''', (template_id,))

    items = []
    for row in c.fetchall():
        items.append({
            'id': row[0],
            'form_template_id': row[1],
            'item_order': row[2],
            'category': row[3],
            'description': row[4],
            'weight': row[5],
            'is_critical': row[6],
            'active': row[7],
            'created_date': row[8]
        })
    conn.close()

    return jsonify({'items': items})


@app.route('/api/admin/forms/item', methods=['POST'])
def create_form_item():
    """Create a new form item"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    conn = get_db_connection()
    c = conn.cursor()

    # Get the next item_order number
    c.execute('SELECT MAX(item_order) FROM form_items WHERE form_template_id = ?',
              (data['form_template_id'],))
    max_order = c.fetchone()[0]
    next_order = (max_order + 1) if max_order else 1

    c.execute('''
        INSERT INTO form_items (
            form_template_id, item_order, category, description,
            weight, is_critical, active, created_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['form_template_id'],
        next_order,
        data.get('category', 'GENERAL'),
        data['description'],
        data.get('weight', 1),
        data.get('is_critical', 0),
        1,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))

    item_id = c.lastrowid

    # Track who edited this form
    update_form_editor_tracking(data['form_template_id'], conn)

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'item_id': item_id, 'message': 'Item created successfully'})


@app.route('/api/admin/forms/item/<int:item_id>', methods=['PUT'])
def update_form_item(item_id):
    """Update an existing form item"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    conn = get_db_connection()
    c = conn.cursor()

    # Get template_id for this item
    c.execute('SELECT form_template_id FROM form_items WHERE id = ?', (item_id,))
    result = c.fetchone()
    template_id = result[0] if result else None

    c.execute('''
        UPDATE form_items
        SET category = ?, description = ?, weight = ?, is_critical = ?
        WHERE id = ?
    ''', (
        data.get('category'),
        data.get('description'),
        data.get('weight'),
        data.get('is_critical'),
        item_id
    ))

    # Track who edited this form
    if template_id:
        update_form_editor_tracking(template_id, conn)

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Item updated successfully'})


@app.route('/api/admin/forms/item/<int:item_id>', methods=['DELETE'])
def delete_form_item(item_id):
    """Soft delete a form item (set active = 0)"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    # Get template_id for this item
    c.execute('SELECT form_template_id FROM form_items WHERE id = ?', (item_id,))
    result = c.fetchone()
    template_id = result[0] if result else None

    # Soft delete - keep for old forms
    c.execute('UPDATE form_items SET active = 0 WHERE id = ?', (item_id,))

    # Track who edited this form
    if template_id:
        update_form_editor_tracking(template_id, conn)

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Item deleted successfully'})


@app.route('/api/admin/forms/items/reorder', methods=['POST'])
def reorder_form_items():
    """Reorder form items"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json  # Expected: {'items': [{'id': 1, 'order': 1}, ...]}
    conn = get_db_connection()
    c = conn.cursor()

    for item in data['items']:
        c.execute('UPDATE form_items SET item_order = ? WHERE id = ?',
                  (item['order'], item['id']))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Items reordered successfully'})


def update_form_editor_tracking(template_id, conn):
    """Helper function to track who edited a form and when"""
    c = conn.cursor()

    # Get admin user info from session
    admin_username = session.get('admin', 'Unknown Admin')

    # Get admin's full details from database
    c.execute('SELECT username, role, email FROM users WHERE username = ?', (admin_username,))
    admin = c.fetchone()

    if admin:
        editor_name = admin[0]
        editor_role = admin[1]
    else:
        editor_name = admin_username
        editor_role = 'admin'

    # Update tracking fields
    c.execute('''
        UPDATE form_templates
        SET last_edited_by = ?,
            last_edited_date = ?,
            last_edited_role = ?
        WHERE id = ?
    ''', (editor_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), editor_role, template_id))


@app.route('/api/admin/forms/template/<int:template_id>/version', methods=['POST'])
def increment_template_version(template_id):
    """Increment form template version when changes are saved"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    # Get current version
    c.execute('SELECT version FROM form_templates WHERE id = ?', (template_id,))
    current_version = c.fetchone()[0]

    # Increment version (e.g., '1.0' -> '1.1', '1.9' -> '2.0')
    try:
        major, minor = current_version.split('.')
        minor = int(minor) + 1
        if minor >= 10:
            major = str(int(major) + 1)
            minor = 0
        new_version = f"{major}.{minor}"
    except:
        new_version = '1.1'

    c.execute('UPDATE form_templates SET version = ? WHERE id = ?',
              (new_version, template_id))

    # Track who made this edit
    update_form_editor_tracking(template_id, conn)

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'new_version': new_version})


# ============================================================================
# FORM TEMPLATE INFO API - Get template details including last edited info
# ============================================================================

@app.route('/api/admin/forms/template/<int:template_id>/info', methods=['GET'])
def get_form_template_info(template_id):
    """Get form template information including last edited details"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''
        SELECT id, name, description, form_type, version,
               last_edited_by, last_edited_date, last_edited_role
        FROM form_templates
        WHERE id = ? AND active = 1
    ''', (template_id,))

    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Template not found'}), 404

    return jsonify({
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'form_type': row[3],
        'version': row[4],
        'last_edited_by': row[5],
        'last_edited_date': row[6],
        'last_edited_role': row[7]
    })


# ============================================================================
# FORM FIELDS API - Admin can edit form field labels, types, properties
# ============================================================================

@app.route('/api/admin/forms/template/<int:template_id>/fields', methods=['GET'])
def get_form_fields(template_id):
    """Get all fields for a form template"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''
        SELECT id, field_name, field_label, field_type, field_order,
               required, placeholder, default_value, options, field_group
        FROM form_fields
        WHERE form_template_id = ? AND active = 1
        ORDER BY field_order
    ''', (template_id,))

    fields = []
    for row in c.fetchall():
        fields.append({
            'id': row[0],
            'field_name': row[1],
            'field_label': row[2],
            'field_type': row[3],
            'field_order': row[4],
            'required': row[5],
            'placeholder': row[6],
            'default_value': row[7],
            'options': row[8],
            'field_group': row[9]
        })

    conn.close()
    return jsonify({'fields': fields})


@app.route('/api/admin/forms/field', methods=['POST'])
def create_form_field():
    """Create a new form field"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    conn = get_db_connection()
    c = conn.cursor()

    # Get the next field_order number
    c.execute('SELECT MAX(field_order) FROM form_fields WHERE form_template_id = ?',
              (data['form_template_id'],))
    max_order = c.fetchone()[0]
    next_order = (max_order + 1) if max_order else 1

    c.execute('''
        INSERT INTO form_fields (
            form_template_id, field_name, field_label, field_type, field_order,
            required, placeholder, default_value, options, field_group, active, created_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (
        data['form_template_id'],
        data['field_name'],
        data['field_label'],
        data['field_type'],
        data.get('field_order', next_order),
        data.get('required', 0),
        data.get('placeholder', ''),
        data.get('default_value', ''),
        data.get('options', ''),
        data.get('field_group', 'main'),
        1
    ))

    field_id = c.lastrowid

    # Track who edited this form
    update_form_editor_tracking(data['form_template_id'], conn)

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'field_id': field_id})


@app.route('/api/admin/forms/field/<int:field_id>', methods=['PUT'])
def update_form_field(field_id):
    """Update an existing form field"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    conn = get_db_connection()
    c = conn.cursor()

    # Get template_id for this field
    c.execute('SELECT form_template_id FROM form_fields WHERE id = ?', (field_id,))
    result = c.fetchone()
    template_id = result[0] if result else None

    c.execute('''
        UPDATE form_fields SET
            field_label = ?,
            field_type = ?,
            field_order = ?,
            required = ?,
            placeholder = ?,
            default_value = ?,
            options = ?,
            field_group = ?
        WHERE id = ?
    ''', (
        data['field_label'],
        data['field_type'],
        data['field_order'],
        data.get('required', 0),
        data.get('placeholder', ''),
        data.get('default_value', ''),
        data.get('options', ''),
        data.get('field_group', 'main'),
        field_id
    ))

    # Track who edited this form
    if template_id:
        update_form_editor_tracking(template_id, conn)

    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/admin/forms/field/<int:field_id>', methods=['DELETE'])
def delete_form_field(field_id):
    """Soft delete a form field (set active = 0)"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    # Get template_id for this field
    c.execute('SELECT form_template_id FROM form_fields WHERE id = ?', (field_id,))
    result = c.fetchone()
    template_id = result[0] if result else None

    # Soft delete - preserve for old forms
    c.execute('UPDATE form_fields SET active = 0 WHERE id = ?', (field_id,))

    # Track who edited this form
    if template_id:
        update_form_editor_tracking(template_id, conn)

    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ============================================================================
# ACTIVE USERS API - Show logged-in users on admin map
# ============================================================================

@app.route('/api/admin/active_users_map', methods=['GET'])
def get_active_users_map():
    """Get all currently logged-in users with their locations for the map"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    c = conn.cursor()

    # Get all active sessions with VALID GPS coordinates (logged in within last 24 hours)
    # Only show users who have real location data - no nulls, no fake coordinates
    c.execute('''
        SELECT username, user_role, location_lat, location_lng, parish, login_time, last_activity
        FROM user_sessions
        WHERE is_active = 1
        AND datetime(last_activity) > datetime('now', '-24 hours')
        AND location_lat IS NOT NULL
        AND location_lng IS NOT NULL
        AND location_lat != 0
        AND location_lng != 0
        ORDER BY last_activity DESC
    ''')

    users = []
    for row in c.fetchall():
        users.append({
            'username': row[0],
            'role': row[1],
            'lat': row[2],
            'lng': row[3],
            'parish': row[4],
            'login_time': row[5],
            'last_activity': row[6]
        })

    conn.close()
    print(f"📍 Active Users Map API: Returning {len(users)} users with valid GPS coordinates")
    return jsonify({'users': users, 'count': len(users)})


def auto_migrate_checklists():
    """Automatically migrate checklists if form_items table is empty"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Check if any items exist
        c.execute('SELECT COUNT(*) FROM form_items')
        count = c.fetchone()[0]
        conn.close()

        if count == 0:
            print("⚡ No checklist items found. Running automatic migration...")
            # Call the migration function logic
            with app.test_request_context():
                from flask import session
                session['admin'] = True
                migrate_all_checklists()
            print("✅ Automatic migration completed!")
        else:
            print(f"✓ Found {count} checklist items in database")
    except Exception as e:
        print(f"⚠️  Auto-migration error: {str(e)}")


# Initialize database and migrate checklists on app startup (works with Gunicorn)
init_db()
init_form_management_db()
auto_migrate_checklists()


if __name__ == '__main__':
    app.run(debug=True, port=5002)