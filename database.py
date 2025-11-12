import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Inspections table
    c.execute('''CREATE TABLE IF NOT EXISTS inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  establishment_name TEXT,
                  address TEXT,
                  inspector_name TEXT,
                  inspection_date TEXT,
                  inspection_time TEXT,
                  type_of_establishment TEXT,
                  comments TEXT,
                  inspector_signature TEXT,
                  manager_signature TEXT,
                  manager_date TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  physical_location TEXT,
                  owner TEXT,
                  license_no TEXT,
                  no_of_employees TEXT,
                  purpose_of_visit TEXT,
                  action TEXT,
                  result TEXT,
                  food_inspected TEXT,
                  food_condemned TEXT,
                  critical_score INTEGER,
                  overall_score INTEGER,
                  received_by TEXT,
                  form_type TEXT,
                  scores TEXT,
                  inspector_code TEXT,
                  photo_data TEXT)''')

    # Inspection items table
    c.execute('''CREATE TABLE IF NOT EXISTS inspection_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  inspection_id INTEGER,
                  item_id TEXT,
                  details TEXT,
                  obser TEXT,
                  error TEXT,
                  FOREIGN KEY (inspection_id) REFERENCES inspections(id))''')

    # Burial site inspections table
    c.execute('''CREATE TABLE IF NOT EXISTS burial_site_inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  inspection_date TEXT,
                  applicant_name TEXT,
                  deceased_name TEXT,
                  burial_location TEXT,
                  site_description TEXT,
                  proximity_water_source TEXT,
                  proximity_perimeter_boundaries TEXT,
                  proximity_road_pathway TEXT,
                  proximity_trees TEXT,
                  proximity_houses_buildings TEXT,
                  proposed_grave_type TEXT,
                  general_remarks TEXT,
                  inspector_signature TEXT,
                  received_by TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  photo_data TEXT)''')

    # Residential inspections table
    c.execute('''CREATE TABLE IF NOT EXISTS residential_inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  premises_name TEXT,
                  owner TEXT,
                  address TEXT,
                  inspector_name TEXT,
                  inspection_date TEXT,
                  inspector_code TEXT,
                  treatment_facility TEXT,
                  vector TEXT,
                  result TEXT,
                  onsite_system TEXT,
                  building_construction_type TEXT,
                  purpose_of_visit TEXT,
                  action TEXT,
                  no_of_bedrooms TEXT,
                  total_population TEXT,
                  critical_score INTEGER,
                  overall_score INTEGER,
                  comments TEXT,
                  inspector_signature TEXT,
                  received_by TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  photo_data TEXT)''')

    # Residential checklist scores table
    c.execute('''CREATE TABLE IF NOT EXISTS residential_checklist_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  form_id INTEGER,
                  item_id INTEGER,
                  score INTEGER,
                  FOREIGN KEY (form_id) REFERENCES residential_inspections(id))''')

    # Meat processing inspections table
    c.execute('''CREATE TABLE IF NOT EXISTS meat_processing_inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  establishment_name TEXT,
                  owner_operator TEXT,
                  address TEXT,
                  inspector_name TEXT,
                  establishment_no TEXT,
                  overall_score REAL,
                  food_contact_surfaces INTEGER,
                  water_samples INTEGER,
                  product_samples INTEGER,
                  types_of_products TEXT,
                  staff_fhp INTEGER,
                  water_public INTEGER,
                  water_private INTEGER,
                  type_processing INTEGER,
                  type_slaughter INTEGER,
                  purpose_of_visit TEXT,
                  inspection_date TEXT,
                  inspector_code TEXT,
                  result TEXT,
                  telephone_no TEXT,
                  registration_status TEXT,
                  action TEXT,
                  comments TEXT,
                  inspector_signature TEXT,
                  received_by TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  photo_data TEXT)''')

    # Meat processing checklist scores table
    c.execute('''CREATE TABLE IF NOT EXISTS meat_processing_checklist_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  form_id INTEGER,
                  item_id INTEGER,
                  score REAL,
                  FOREIGN KEY (form_id) REFERENCES meat_processing_inspections(id))''')

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  email TEXT,
                  is_flagged INTEGER DEFAULT 0)''')

    # Insert users
    users = [
        ('inspector1', 'Insp123!secure', 'inspector'),
        ('inspector2', 'Insp456!secure', 'inspector'),
        ('inspector3', 'Insp789!secure', 'inspector'),
        ('inspector4', 'Insp012!secure', 'inspector'),
        ('inspector5', 'Insp345!secure', 'inspector'),
        ('inspector6', 'Insp678!secure', 'inspector'),
        ('admin', 'Admin901!secure', 'admin')
    ]
    c.executemany("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", users)

    # Login history table (required by login route)
    c.execute('''CREATE TABLE IF NOT EXISTS login_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  username TEXT NOT NULL,
                  email TEXT,
                  role TEXT NOT NULL,
                  login_time TEXT NOT NULL,
                  ip_address TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')

    # Contacts table
    c.execute('''CREATE TABLE IF NOT EXISTS contacts
                 (user_id INTEGER,
                  contact_id INTEGER,
                  PRIMARY KEY (user_id, contact_id),
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (contact_id) REFERENCES users(id))''')

    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender_id INTEGER NOT NULL,
                  receiver_id INTEGER NOT NULL,
                  content TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  is_read INTEGER DEFAULT 0,
                  FOREIGN KEY (sender_id) REFERENCES users(id),
                  FOREIGN KEY (receiver_id) REFERENCES users(id))''')

    # Add is_read column if it doesn't exist
    try:
        c.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Set existing messages as read
    c.execute("UPDATE messages SET is_read = 1 WHERE is_read IS NULL")

    conn.commit()
    conn.close()

def save_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute('''INSERT INTO inspections (establishment_name, address, inspector_name, inspection_date, inspection_time,
                 type_of_establishment, no_of_employees, purpose_of_visit, action, result, food_inspected, food_condemned,
                 critical_score, overall_score, comments, inspector_signature, received_by, form_type, scores, created_at,
                 inspector_code, license_no, owner, photo_data)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['establishment_name'], data['address'], data['inspector_name'], data['inspection_date'],
               data['inspection_time'], data['type_of_establishment'], data['no_of_employees'],
               data['purpose_of_visit'], data['action'], data['result'], data['food_inspected'],
               data['food_condemned'], data['critical_score'], data['overall_score'], data['comments'],
               data['inspector_signature'], data['received_by'], data['form_type'], data['scores'],
               data['created_at'], data['inspector_code'], data['license_no'], data['owner'],
               data.get('photo_data', '[]')))
    conn.commit()
    inspection_id = c.lastrowid
    conn.close()
    return inspection_id

def save_burial_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    try:
        if data.get('id'):
            c.execute('''UPDATE burial_site_inspections SET
                         inspection_date = ?, applicant_name = ?, deceased_name = ?, burial_location = ?,
                         site_description = ?, proximity_water_source = ?, proximity_perimeter_boundaries = ?,
                         proximity_road_pathway = ?, proximity_trees = ?, proximity_houses_buildings = ?,
                         proposed_grave_type = ?, general_remarks = ?, inspector_signature = ?,
                         received_by = ?, photo_data = ?, created_at = ?
                         WHERE id = ?''',
                      (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
                       data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
                       data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
                       data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
                       data['received_by'], data.get('photo_data', '[]'),
                       data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                       data['id']))
        else:
            c.execute('''INSERT INTO burial_site_inspections (inspection_date, applicant_name, deceased_name, burial_location,
                        site_description, proximity_water_source, proximity_perimeter_boundaries, proximity_road_pathway,
                        proximity_trees, proximity_houses_buildings, proposed_grave_type, general_remarks,
                        inspector_signature, received_by, photo_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
                       data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
                       data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
                       data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
                       data['received_by'], data.get('photo_data', '[]'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def save_residential_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    try:
        if data.get('id'):
            c.execute("""
                            UPDATE residential_inspections
                            SET premises_name = ?, owner = ?, address = ?, inspector_name = ?,
                                inspection_date = ?, inspector_code = ?, treatment_facility = ?, vector = ?,
                                result = ?, onsite_system = ?, building_construction_type = ?, purpose_of_visit = ?,
                                action = ?, no_of_bedrooms = ?, total_population = ?, critical_score = ?,
                                overall_score = ?, comments = ?, inspector_signature = ?, received_by = ?,
                                created_at = ?, photo_data = ?
                            WHERE id = ?
                        """,
                        (data['premises_name'], data['owner'], data['address'], data['inspector_name'],
                         data['inspection_date'], data['inspector_code'], data['treatment_facility'], data['vector'],
                         data['result'], data['onsite_system'], data['building_construction_type'], data['purpose_of_visit'],
                         data['action'], data.get('no_of_bedrooms', ''), data.get('total_population', ''),
                         data.get('critical_score', 0), data.get('overall_score', 0), data['comments'],
                         data['inspector_signature'], data['received_by'],
                         data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                         data.get('photo_data', '[]'), data['id']))
        else:
            c.execute("""
                INSERT INTO residential_inspections (
                    premises_name, owner, address, inspector_name,
                    inspection_date, inspector_code, treatment_facility, vector, result, onsite_system,
                    building_construction_type, purpose_of_visit, action, no_of_bedrooms, total_population,
                    critical_score, overall_score, comments, inspector_signature, received_by, created_at, photo_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['premises_name'], data['owner'], data['address'], data['inspector_name'],
                data['inspection_date'], data['inspector_code'], data['treatment_facility'], data['vector'],
                data['result'], data['onsite_system'], data['building_construction_type'], data['purpose_of_visit'],
                data['action'], data.get('no_of_bedrooms', ''), data.get('total_population', ''),
                data.get('critical_score', 0), data.get('overall_score', 0), data['comments'],
                data['inspector_signature'], data['received_by'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get('photo_data', '[]')
            ))
            conn.commit()

        inspection_id = c.lastrowid if not data.get('id') else data['id']
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        inspection_id = None
    finally:
        conn.close()
    return inspection_id

def save_meat_processing_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    try:
        if data.get('id'):
            c.execute("""
                UPDATE meat_processing_inspections
                SET establishment_name = ?, owner_operator = ?, address = ?, inspector_name = ?,
                    establishment_no = ?, overall_score = ?, food_contact_surfaces = ?, water_samples = ?,
                    product_samples = ?, types_of_products = ?, staff_fhp = ?, water_public = ?,
                    water_private = ?, type_processing = ?, type_slaughter = ?, purpose_of_visit = ?,
                    inspection_date = ?, inspector_code = ?, result = ?, telephone_no = ?,
                    registration_status = ?, action = ?, comments = ?, inspector_signature = ?,
                    received_by = ?, created_at = ?, photo_data = ?
                WHERE id = ?
            """, (
                data['establishment_name'], data['owner_operator'], data['address'], data['inspector_name'],
                data['establishment_no'], data['overall_score'], data['food_contact_surfaces'], data['water_samples'],
                data['product_samples'], data['types_of_products'], data['staff_fhp'], data['water_public'],
                data['water_private'], data['type_processing'], data['type_slaughter'], data['purpose_of_visit'],
                data['inspection_date'], data['inspector_code'], data['result'], data['telephone_no'],
                data['registration_status'], data['action'], data['comments'], data['inspector_signature'],
                data['received_by'], data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                data.get('photo_data', '[]'), data['id']
            ))
        else:
            c.execute("""
                INSERT INTO meat_processing_inspections (
                    establishment_name, owner_operator, address, inspector_name,
                    establishment_no, overall_score, food_contact_surfaces, water_samples,
                    product_samples, types_of_products, staff_fhp, water_public,
                    water_private, type_processing, type_slaughter, purpose_of_visit,
                    inspection_date, inspector_code, result, telephone_no,
                    registration_status, action, comments, inspector_signature,
                    received_by, created_at, photo_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['establishment_name'], data['owner_operator'], data['address'], data['inspector_name'],
                data['establishment_no'], data['overall_score'], data['food_contact_surfaces'], data['water_samples'],
                data['product_samples'], data['types_of_products'], data['staff_fhp'], data['water_public'],
                data['water_private'], data['type_processing'], data['type_slaughter'], data['purpose_of_visit'],
                data['inspection_date'], data['inspector_code'], data['result'], data['telephone_no'],
                data['registration_status'], data['action'], data['comments'], data['inspector_signature'],
                data['received_by'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get('photo_data', '[]')
            ))
            conn.commit()

        inspection_id = c.lastrowid if not data.get('id') else data['id']
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        inspection_id = None
    finally:
        conn.close()
    return inspection_id

def get_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment, created_at, result FROM inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections

def get_inspections_by_inspector(inspector_name, inspection_type='all'):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    if inspection_type == 'all':
        # Get all inspection types for this inspector
        c.execute("""
            SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment,
                   created_at, result, form_type
            FROM inspections
            WHERE inspector_name = ?
            UNION
            SELECT id, premises_name as establishment_name, inspector_name, inspection_date,
                   'Residential' as type_of_establishment, created_at, result, 'Residential' as form_type
            FROM residential_inspections
            WHERE inspector_name = ?
            UNION
            SELECT id, establishment_name, inspector_name, inspection_date,
                   'Meat Processing' as type_of_establishment, created_at, result, 'Meat Processing' as form_type
            FROM meat_processing_inspections
            WHERE inspector_name = ?
            ORDER BY inspection_date DESC
        """, (inspector_name, inspector_name, inspector_name))
    else:
        # Filter by inspection type
        if inspection_type == 'Residential':
            c.execute("""SELECT id, premises_name as establishment_name, inspector_name, inspection_date,
                         'Residential' as type_of_establishment, created_at, result, 'Residential' as form_type
                         FROM residential_inspections
                         WHERE inspector_name = ? ORDER BY inspection_date DESC""", (inspector_name,))
        elif inspection_type == 'Meat Processing':
            c.execute("""SELECT id, establishment_name, inspector_name, inspection_date,
                         'Meat Processing' as type_of_establishment, created_at, result, 'Meat Processing' as form_type
                         FROM meat_processing_inspections
                         WHERE inspector_name = ? ORDER BY inspection_date DESC""", (inspector_name,))
        else:
            c.execute("""SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment,
                         created_at, result, form_type FROM inspections
                         WHERE inspector_name = ? AND (form_type = ? OR type_of_establishment = ?)
                         ORDER BY inspection_date DESC""", (inspector_name, inspection_type, inspection_type))

    inspections = c.fetchall()
    conn.close()
    return inspections

def get_burial_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, applicant_name, deceased_name, created_at, 'Completed' AS status FROM burial_site_inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections

def get_residential_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, premises_name, inspection_date, result FROM residential_inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections

def get_meat_processing_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, establishment_name, inspection_date, result FROM meat_processing_inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections

def get_inspection_details(inspection_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT * FROM inspections WHERE id = ?", (inspection_id,))
    inspection = c.fetchone()

    if inspection:
        if inspection[24] == 'Food Establishment':
            scores = [int(x) for x in inspection[25].split(',')] if inspection[25] else [0] * 45
            inspection_dict = {
                'id': inspection[0],
                'establishment_name': inspection[1] or '',
                'address': inspection[2] or '',
                'inspector_name': inspection[3] or '',
                'inspection_date': inspection[4] or '',
                'inspection_time': inspection[5] or '',
                'type_of_establishment': inspection[6] or '',
                'comments': inspection[7] or '',
                'inspector_signature': inspection[8] or '',
                'manager_signature': inspection[9] or '',
                'manager_date': inspection[10] or '',
                'created_at': inspection[11] or '',
                'physical_location': inspection[12] or '',
                'owner': inspection[13] or '',
                'license_no': inspection[14] or '',
                'no_of_employees': inspection[15] or '',
                'purpose_of_visit': inspection[16] or '',
                'action': inspection[17] or '',
                'result': inspection[18] or '',
                'food_inspected': inspection[19] or '',
                'food_condemned': inspection[20] or '',
                'critical_score': inspection[21] or 0,
                'overall_score': inspection[22] or 0,
                'received_by': inspection[23] or '',
                'form_type': inspection[24] or '',
                'scores': dict(zip(range(1, 46), scores)),
                'inspector_code': inspection[26] or '',
                'photo_data': inspection[27] if len(inspection) > 27 else '[]'
            }
        else:
            c.execute("SELECT item_id, details, obser, error FROM inspection_items WHERE inspection_id = ?", (inspection_id,))
            items = c.fetchall()
            scores = {int(item[0]): item[1] for item in items if item[1]}
            inspection_dict = {
                'id': inspection[0],
                'establishment_name': inspection[1] or '',
                'address': inspection[2] or '',
                'inspector_name': inspection[3] or '',
                'inspection_date': inspection[4] or '',
                'inspection_time': inspection[5] or '',
                'type_of_establishment': inspection[6] or '',
                'comments': inspection[7] or '',
                'inspector_signature': inspection[8] or '',
                'manager_signature': inspection[9] or '',
                'manager_date': inspection[10] or '',
                'created_at': inspection[11] or '',
                'physical_location': inspection[12] or '',
                'owner': inspection[13] or '',
                'license_no': inspection[14] or '',
                'no_of_employees': inspection[15] or '',
                'purpose_of_visit': inspection[16] or '',
                'action': inspection[17] or '',
                'result': inspection[18] or '',
                'food_inspected': inspection[19] or '',
                'food_condemned': inspection[20] or '',
                'critical_score': inspection[21] or 0,
                'overall_score': inspection[22] or 0,
                'received_by': inspection[23] or '',
                'form_type': inspection[24] or '',
                'scores': scores,
                'inspector_code': inspection[26] or '',
                'photo_data': inspection[27] if len(inspection) > 27 else '[]'
            }
        conn.close()
        return inspection_dict
    conn.close()
    return None

def get_burial_inspection_details(inspection_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT * FROM burial_site_inspections WHERE id = ?", (inspection_id,))
    inspection = c.fetchone()
    conn.close()
    if inspection:
        return {
            'id': inspection[0],
            'inspection_date': inspection[1] or '',
            'applicant_name': inspection[2] or '',
            'deceased_name': inspection[3] or '',
            'burial_location': inspection[4] or '',
            'site_description': inspection[5] or '',
            'proximity_water_source': inspection[6] or '',
            'proximity_perimeter_boundaries': inspection[7] or '',
            'proximity_road_pathway': inspection[8] or '',
            'proximity_trees': inspection[9] or '',
            'proximity_houses_buildings': inspection[10] or '',
            'proposed_grave_type': inspection[11] or '',
            'general_remarks': inspection[12] or '',
            'inspector_signature': inspection[13] or '',
            'received_by': inspection[14] or '',
            'created_at': inspection[15] or '',
            'photo_data': inspection[16] if len(inspection) > 16 else '[]'
        }
    return None

def get_residential_inspection_details(inspection_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT * FROM residential_inspections WHERE id = ?", (inspection_id,))
    inspection = c.fetchone()
    if inspection:
        c.execute("SELECT item_id, score FROM residential_checklist_scores WHERE form_id = ?", (inspection_id,))
        checklist_scores = dict(c.fetchall())
        conn.close()
        return {
            'id': inspection[0],
            'premises_name': inspection[1] or '',
            'owner': inspection[2] or '',
            'address': inspection[3] or '',
            'inspector_name': inspection[4] or '',
            'inspection_date': inspection[5] or '',
            'inspector_code': inspection[6] or '',
            'treatment_facility': inspection[7] or '',
            'vector': inspection[8] or '',
            'result': inspection[9] or '',
            'onsite_system': inspection[10] or '',
            'building_construction_type': inspection[11] or '',
            'purpose_of_visit': inspection[12] or '',
            'action': inspection[13] or '',
            'no_of_bedrooms': inspection[14] or '',
            'total_population': inspection[15] or '',
            'critical_score': inspection[16] or 0,
            'overall_score': inspection[17] or 0,
            'comments': inspection[18] or '',
            'inspector_signature': inspection[19] or '',
            'received_by': inspection[20] or '',
            'created_at': inspection[21] or '',
            'photo_data': inspection[22] if len(inspection) > 22 else '[]',
            'checklist_scores': checklist_scores
        }
    conn.close()
    return None

def get_meat_processing_inspection_details(inspection_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT * FROM meat_processing_inspections WHERE id = ?", (inspection_id,))
    inspection = c.fetchone()
    if inspection:
        c.execute("SELECT item_id, score FROM meat_processing_checklist_scores WHERE form_id = ?", (inspection_id,))
        checklist_scores = dict(c.fetchall())
        conn.close()
        return {
            'id': inspection[0],
            'establishment_name': inspection[1] or '',
            'owner_operator': inspection[2] or '',
            'address': inspection[3] or '',
            'inspector_name': inspection[4] or '',
            'establishment_no': inspection[5] or '',
            'overall_score': inspection[6] or 0.0,
            'food_contact_surfaces': inspection[7] or 0,
            'water_samples': inspection[8] or 0,
            'product_samples': inspection[9] or 0,
            'types_of_products': inspection[10] or '',
            'staff_fhp': inspection[11] or 0,
            'water_public': inspection[12] or 0,
            'water_private': inspection[13] or 0,
            'type_processing': inspection[14] or 0,
            'type_slaughter': inspection[15] or 0,
            'purpose_of_visit': inspection[16] or '',
            'inspection_date': inspection[17] or '',
            'inspector_code': inspection[18] or '',
            'result': inspection[19] or '',
            'telephone_no': inspection[20] or '',
            'registration_status': inspection[21] or '',
            'action': inspection[22] or '',
            'comments': inspection[23] or '',
            'inspector_signature': inspection[24] or '',
            'received_by': inspection[25] or '',
            'created_at': inspection[26] or '',
            'photo_data': inspection[27] if len(inspection) > 27 else '[]',
            'checklist_scores': checklist_scores
        }
    conn.close()
    return None


def get_small_hotels_inspection_details(form_id):
    conn = sqlite3.connect('inspections.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Small Hotel'", (form_id,))
    inspection = cursor.fetchone()

    if not inspection:
        conn.close()
        return None

    inspection_dict = dict(inspection)

    # Get individual scores
    cursor.execute("SELECT item_id, obser, error FROM inspection_items WHERE inspection_id = ?", (form_id,))
    items = cursor.fetchall()

    obser_scores = {}
    error_scores = {}
    for item in items:
        obser_scores[item[0]] = item[1] or '0'
        error_scores[item[0]] = item[2] or '0'

    inspection_dict['obser'] = obser_scores
    inspection_dict['error'] = error_scores

    conn.close()
    return inspection_dict


def get_spirit_licence_inspection_details(form_id):
    conn = sqlite3.connect('inspections.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Spirit Licence Premises'", (form_id,))
    inspection = cursor.fetchone()

    if not inspection:
        conn.close()
        return None

    inspection_dict = dict(inspection)

    # Parse scores from the scores string
    scores_str = inspection_dict.get('scores', '')
    if scores_str:
        score_list = scores_str.split(',')
        scores = {}
        for i, score in enumerate(score_list, 1):
            scores[str(i)] = score
        inspection_dict['scores'] = scores
    else:
        inspection_dict['scores'] = {}

    # Parse comments into a dictionary for easier access
    comments_str = inspection_dict.get('comments', '')
    parsed_comments = {}
    if comments_str:
        comment_lines = comments_str.split('\n')
        for line in comment_lines:
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2 and parts[0].strip().isdigit():
                    parsed_comments[parts[0].strip()] = parts[1].strip()
    inspection_dict['parsed_comments'] = parsed_comments

    conn.close()
    return inspection_dict

def update_database_schema():
    """Update database schema to handle all form types properly"""
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Add missing columns with error handling
    columns_to_add = [
        ('no_with_fhc', 'INTEGER DEFAULT 0'),
        ('no_wo_fhc', 'INTEGER DEFAULT 0'),
        ('status', 'TEXT'),
        ('manager_signature', 'TEXT'),
        ('manager_date', 'TEXT'),
        ('parish', 'TEXT'),
        ('physical_location', 'TEXT')
    ]

    for column_name, column_def in columns_to_add:
        try:
            c.execute(f"ALTER TABLE inspections ADD COLUMN {column_name} {column_def}")
            print(f"Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Error adding {column_name}: {e}")
            # Column already exists, continue

    # Add missing columns for residential_inspections
    try:
        c.execute("ALTER TABLE residential_inspections ADD COLUMN parish TEXT")
    except sqlite3.OperationalError:
        pass

    # Add missing swimming pool score columns
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        try:
            c.execute(f'ALTER TABLE inspections ADD COLUMN score_{item["id"]} REAL DEFAULT 0')
        except sqlite3.OperationalError:
            pass

    # Create indexes for better performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_inspections_form_type ON inspections(form_type)",
        "CREATE INDEX IF NOT EXISTS idx_inspections_date ON inspections(inspection_date)",
        "CREATE INDEX IF NOT EXISTS idx_inspections_inspector ON inspections(inspector_name)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_login_history_user ON login_history(user_id)"
    ]

    for index in indexes:
        try:
            c.execute(index)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()