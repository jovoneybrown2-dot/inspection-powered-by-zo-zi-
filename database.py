import sqlite3
from datetime import datetime
from db_config import get_db_connection, get_db_type, release_db_connection

def get_auto_increment():
    """Return the correct auto-increment syntax for the current database"""
    return 'SERIAL PRIMARY KEY' if get_db_type() == 'postgresql' else 'INTEGER PRIMARY KEY AUTOINCREMENT'

def get_timestamp_default():
    """Return the correct timestamp default for the current database"""
    return 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP' if get_db_type() == 'postgresql' else 'TEXT DEFAULT CURRENT_TIMESTAMP'

def get_insert_ignore():
    """Return the correct INSERT IGNORE syntax for the current database"""
    return 'ON CONFLICT DO NOTHING' if get_db_type() == 'postgresql' else 'OR IGNORE'

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # For PostgreSQL, we need to commit after each schema change
    # to avoid transaction errors with ALTER TABLE
    def safe_commit():
        """Commit changes safely for both database types"""
        try:
            conn.commit()
        except Exception as e:
            print(f"⚠️  Commit warning: {e}")
            pass

    # Get database-specific syntax
    auto_inc = get_auto_increment()
    timestamp = get_timestamp_default()
    insert_ignore = get_insert_ignore()

    # Inspections table
    c.execute(f'''CREATE TABLE IF NOT EXISTS inspections
                 (id {auto_inc},
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
                  created_at {timestamp},
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
    c.execute(f'''CREATE TABLE IF NOT EXISTS inspection_items
                 (id {auto_inc},
                  inspection_id INTEGER,
                  item_id TEXT,
                  details TEXT,
                  obser TEXT,
                  error TEXT,
                  FOREIGN KEY (inspection_id) REFERENCES inspections(id))''')

    # Burial site inspections table
    c.execute(f'''CREATE TABLE IF NOT EXISTS burial_site_inspections
                 (id {auto_inc},
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
                  created_at {timestamp},
                  photo_data TEXT)''')

    # Residential inspections table
    c.execute(f'''CREATE TABLE IF NOT EXISTS residential_inspections
                 (id {auto_inc},
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
                  created_at {timestamp},
                  photo_data TEXT)''')

    # Residential checklist scores table
    c.execute(f'''CREATE TABLE IF NOT EXISTS residential_checklist_scores
                 (id {auto_inc},
                  form_id INTEGER,
                  item_id INTEGER,
                  score INTEGER,
                  FOREIGN KEY (form_id) REFERENCES residential_inspections(id))''')

    # Meat processing inspections table
    c.execute(f'''CREATE TABLE IF NOT EXISTS meat_processing_inspections
                 (id {auto_inc},
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
                  staff_compliment INTEGER,
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
                  created_at {timestamp},
                  photo_data TEXT)''')

    # Migration: Add staff_compliment column if it doesn't exist
    try:
        c.execute("ALTER TABLE meat_processing_inspections ADD COLUMN staff_compliment INTEGER")
        safe_commit()
        print("✓ Added staff_compliment column to meat_processing_inspections table")
    except Exception:
        # Column already exists (catches both SQLite and PostgreSQL errors)
        pass

    # Meat processing checklist scores table
    c.execute(f'''CREATE TABLE IF NOT EXISTS meat_processing_checklist_scores
                 (id {auto_inc},
                  form_id INTEGER,
                  item_id INTEGER,
                  score REAL,
                  FOREIGN KEY (form_id) REFERENCES meat_processing_inspections(id))''')

    # Threshold settings table (for alert system)
    c.execute(f'''CREATE TABLE IF NOT EXISTS threshold_settings
                 (chart_type TEXT NOT NULL,
                  inspection_type TEXT NOT NULL,
                  threshold_value REAL NOT NULL,
                  enabled INTEGER DEFAULT 1,
                  updated_at {timestamp},
                  PRIMARY KEY (chart_type, inspection_type))''')

    # Threshold alerts table (for low score notifications)
    c.execute(f'''CREATE TABLE IF NOT EXISTS threshold_alerts
                 (id {auto_inc},
                  inspection_id INTEGER NOT NULL,
                  inspector_name TEXT NOT NULL,
                  form_type TEXT NOT NULL,
                  score REAL NOT NULL,
                  threshold_value REAL NOT NULL,
                  created_at {timestamp})''')

    # Users table
    c.execute(f'''CREATE TABLE IF NOT EXISTS users
                 (id {auto_inc},
                  username TEXT NOT NULL UNIQUE,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  email TEXT,
                  parish TEXT,
                  first_login INTEGER DEFAULT 1,
                  is_flagged INTEGER DEFAULT 0)''')

    # Migration: Add parish column if it doesn't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN parish TEXT")
        safe_commit()
        print("✓ Added parish column to users table")
    except Exception:  # Catches both SQLite and PostgreSQL errors
        # Column already exists
        pass

    # Migration: Add first_login column if it doesn't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN first_login INTEGER DEFAULT 1")
        safe_commit()
        print("✓ Added first_login column to users table")
    except Exception as e:  # Catches both SQLite and PostgreSQL errors
        # Column already exists or other error
        if "duplicate column" not in str(e).lower() and "already exists" not in str(e).lower():
            print(f"⚠️  Warning: Could not add first_login column: {e}")

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
    if get_db_type() == 'postgresql':
        c.executemany(f"INSERT INTO users (username, password, role) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING", users)
    else:
        c.executemany("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", users)

    # Login history table (required by login route)
    c.execute(f'''CREATE TABLE IF NOT EXISTS login_history
                 (id {auto_inc},
                  user_id INTEGER NOT NULL,
                  username TEXT NOT NULL,
                  email TEXT,
                  role TEXT NOT NULL,
                  login_time TEXT NOT NULL,
                  ip_address TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')

    # Contacts table
    c.execute(f'''CREATE TABLE IF NOT EXISTS contacts
                 (user_id INTEGER,
                  contact_id INTEGER,
                  PRIMARY KEY (user_id, contact_id),
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (contact_id) REFERENCES users(id))''')

    # Messages table
    c.execute(f'''CREATE TABLE IF NOT EXISTS messages
                 (id {auto_inc},
                  sender_id INTEGER NOT NULL,
                  receiver_id INTEGER NOT NULL,
                  content TEXT NOT NULL,
                  timestamp {timestamp},
                  is_read INTEGER DEFAULT 0,
                  FOREIGN KEY (sender_id) REFERENCES users(id),
                  FOREIGN KEY (receiver_id) REFERENCES users(id))''')

    # Add is_read column if it doesn't exist
    try:
        c.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
        safe_commit()
    except Exception:  # Catches both SQLite and PostgreSQL errors
        pass  # Column already exists

    # Set existing messages as read
    c.execute("UPDATE messages SET is_read = 1 WHERE is_read IS NULL")
    safe_commit()

    # User sessions table for tracking active logins
    c.execute(f'''CREATE TABLE IF NOT EXISTS user_sessions
                 (id {auto_inc},
                  username TEXT NOT NULL,
                  user_role VARCHAR(50),
                  login_time TEXT NOT NULL,
                  logout_time TEXT,
                  last_activity TEXT,
                  location_lat REAL,
                  location_lng REAL,
                  parish TEXT,
                  ip_address TEXT,
                  is_active INTEGER DEFAULT 1)''')

    # Form templates table for dynamic form management
    c.execute(f'''CREATE TABLE IF NOT EXISTS form_templates
                 (id {auto_inc},
                  name TEXT NOT NULL UNIQUE,
                  description TEXT,
                  form_type TEXT NOT NULL,
                  active INTEGER DEFAULT 1,
                  created_date {timestamp},
                  version TEXT DEFAULT '1.0',
                  created_by TEXT,
                  last_edited_by TEXT,
                  last_edited_date TEXT,
                  last_edited_role TEXT)''')

    # Form items table for checklist items
    c.execute(f'''CREATE TABLE IF NOT EXISTS form_items
                 (id {auto_inc},
                  form_template_id INTEGER NOT NULL,
                  item_order INTEGER NOT NULL,
                  category TEXT NOT NULL,
                  description TEXT NOT NULL,
                  weight INTEGER NOT NULL,
                  is_critical INTEGER DEFAULT 0,
                  active INTEGER DEFAULT 1,
                  created_date {timestamp},
                  FOREIGN KEY (form_template_id) REFERENCES form_templates(id))''')

    # Migration: Add item_id column to form_items if it doesn't exist
    try:
        c.execute("ALTER TABLE form_items ADD COLUMN item_id TEXT")
        safe_commit()
        print("✓ Added item_id column to form_items table")
    except Exception:
        # Column already exists (catches both SQLite and PostgreSQL errors)
        pass

    # Form categories table
    c.execute(f'''CREATE TABLE IF NOT EXISTS form_categories
                 (id {auto_inc},
                  name TEXT NOT NULL,
                  description TEXT,
                  display_order INTEGER DEFAULT 0)''')

    # Form fields table for dynamic form fields
    c.execute(f'''CREATE TABLE IF NOT EXISTS form_fields
                 (id {auto_inc},
                  form_template_id INTEGER NOT NULL,
                  field_name TEXT NOT NULL,
                  field_label TEXT NOT NULL,
                  field_type TEXT NOT NULL DEFAULT 'text',
                  field_order INTEGER NOT NULL DEFAULT 0,
                  required INTEGER DEFAULT 0,
                  placeholder TEXT,
                  default_value TEXT,
                  options TEXT,
                  field_group TEXT DEFAULT 'main',
                  active INTEGER DEFAULT 1,
                  created_date {timestamp},
                  FOREIGN KEY (form_template_id) REFERENCES form_templates(id))''')

    # Seed default form templates
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

    # Final commit for all schema changes
    safe_commit()
    release_db_connection(conn)

def save_inspection(data):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    try:
        c = conn.cursor()
        query = f'''INSERT INTO inspections (establishment_name, address, inspector_name, inspection_date, inspection_time,
                     type_of_establishment, no_of_employees, purpose_of_visit, action, result, food_inspected, food_condemned,
                     critical_score, overall_score, comments, inspector_signature, received_by, form_type, scores, created_at,
                     inspector_code, license_no, owner, photo_data)
                     VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})'''
        c.execute(query,
                  (data['establishment_name'], data['address'], data['inspector_name'], data['inspection_date'],
                   data['inspection_time'], data['type_of_establishment'], data['no_of_employees'],
                   data['purpose_of_visit'], data['action'], data['result'], data['food_inspected'],
                   data['food_condemned'], data['critical_score'], data['overall_score'], data['comments'],
                   data['inspector_signature'], data['received_by'], data['form_type'], data['scores'],
                   data['created_at'], data['inspector_code'], data['license_no'], data['owner'],
                   data.get('photo_data', '[]')))
        conn.commit()
        if get_db_type() == 'postgresql':
            c.execute('SELECT lastval()')
            inspection_id = c.fetchone()[0]
        else:
            inspection_id = c.lastrowid
        return inspection_id
    except Exception as e:
        conn.rollback()
        print(f"Error saving inspection: {e}")
        raise
    finally:
        release_db_connection(conn)

def save_burial_inspection(data):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if data.get('id'):
            c.execute(f'''UPDATE burial_site_inspections SET
                         inspection_date = {ph}, applicant_name = {ph}, deceased_name = {ph}, burial_location = {ph},
                         site_description = {ph}, proximity_water_source = {ph}, proximity_perimeter_boundaries = {ph},
                         proximity_road_pathway = {ph}, proximity_trees = {ph}, proximity_houses_buildings = {ph},
                         proposed_grave_type = {ph}, general_remarks = {ph}, inspector_signature = {ph},
                         received_by = {ph}, photo_data = {ph}, created_at = {ph}
                         WHERE id = {ph}''',
                      (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
                       data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
                       data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
                       data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
                       data['received_by'], data.get('photo_data', '[]'),
                       data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                       data['id']))
        else:
            c.execute(f'''INSERT INTO burial_site_inspections (inspection_date, applicant_name, deceased_name, burial_location,
                        site_description, proximity_water_source, proximity_perimeter_boundaries, proximity_road_pathway,
                        proximity_trees, proximity_houses_buildings, proposed_grave_type, general_remarks,
                        inspector_signature, received_by, photo_data, created_at)
                        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})''',
                      (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
                       data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
                       data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
                       data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
                       data['received_by'], data.get('photo_data', '[]'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        release_db_connection(conn)

def save_residential_inspection(data):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if data.get('id'):
            c.execute(f"""
                            UPDATE residential_inspections
                            SET premises_name = {ph}, owner = {ph}, address = {ph}, inspector_name = {ph},
                                inspection_date = {ph}, inspector_code = {ph}, treatment_facility = {ph}, vector = {ph},
                                result = {ph}, onsite_system = {ph}, building_construction_type = {ph}, purpose_of_visit = {ph},
                                action = {ph}, no_of_bedrooms = {ph}, total_population = {ph}, critical_score = {ph},
                                overall_score = {ph}, comments = {ph}, inspector_signature = {ph}, received_by = {ph},
                                created_at = {ph}, photo_data = {ph}
                            WHERE id = {ph}
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
            c.execute(f"""
                INSERT INTO residential_inspections (
                    premises_name, owner, address, inspector_name,
                    inspection_date, inspector_code, treatment_facility, vector, result, onsite_system,
                    building_construction_type, purpose_of_visit, action, no_of_bedrooms, total_population,
                    critical_score, overall_score, comments, inspector_signature, received_by, created_at, photo_data
                )
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
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

        if data.get('id'):
            inspection_id = data['id']
        elif get_db_type() == 'postgresql':
            c.execute('SELECT lastval()')
            inspection_id = c.fetchone()[0]
        else:
            inspection_id = c.lastrowid
        return inspection_id
    except Exception as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        release_db_connection(conn)

def save_meat_processing_inspection(data):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if data.get('id'):
            c.execute(f"""
                UPDATE meat_processing_inspections
                SET establishment_name = {ph}, owner_operator = {ph}, address = {ph}, inspector_name = {ph},
                    establishment_no = {ph}, overall_score = {ph}, food_contact_surfaces = {ph}, water_samples = {ph},
                    product_samples = {ph}, types_of_products = {ph}, staff_fhp = {ph}, staff_compliment = {ph}, water_public = {ph},
                    water_private = {ph}, type_processing = {ph}, type_slaughter = {ph}, purpose_of_visit = {ph},
                    inspection_date = {ph}, inspector_code = {ph}, result = {ph}, telephone_no = {ph},
                    registration_status = {ph}, action = {ph}, comments = {ph}, inspector_signature = {ph},
                    received_by = {ph}, created_at = {ph}, photo_data = {ph}
                WHERE id = {ph}
            """, (
                data['establishment_name'], data['owner_operator'], data['address'], data['inspector_name'],
                data['establishment_no'], data['overall_score'], data['food_contact_surfaces'], data['water_samples'],
                data['product_samples'], data['types_of_products'], data['staff_fhp'], data.get('staff_compliment', 0), data['water_public'],
                data['water_private'], data['type_processing'], data['type_slaughter'], data['purpose_of_visit'],
                data['inspection_date'], data['inspector_code'], data['result'], data['telephone_no'],
                data['registration_status'], data['action'], data['comments'], data['inspector_signature'],
                data['received_by'], data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                data.get('photo_data', '[]'), data['id']
            ))
        else:
            c.execute(f"""
                INSERT INTO meat_processing_inspections (
                    establishment_name, owner_operator, address, inspector_name,
                    establishment_no, overall_score, food_contact_surfaces, water_samples,
                    product_samples, types_of_products, staff_fhp, staff_compliment, water_public,
                    water_private, type_processing, type_slaughter, purpose_of_visit,
                    inspection_date, inspector_code, result, telephone_no,
                    registration_status, action, comments, inspector_signature,
                    received_by, created_at, photo_data
                )
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """, (
                data['establishment_name'], data['owner_operator'], data['address'], data['inspector_name'],
                data['establishment_no'], data['overall_score'], data['food_contact_surfaces'], data['water_samples'],
                data['product_samples'], data['types_of_products'], data['staff_fhp'], data.get('staff_compliment', 0), data['water_public'],
                data['water_private'], data['type_processing'], data['type_slaughter'], data['purpose_of_visit'],
                data['inspection_date'], data['inspector_code'], data['result'], data['telephone_no'],
                data['registration_status'], data['action'], data['comments'], data['inspector_signature'],
                data['received_by'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get('photo_data', '[]')
            ))
        conn.commit()

        if data.get('id'):
            inspection_id = data['id']
        elif get_db_type() == 'postgresql':
            c.execute('SELECT lastval()')
            inspection_id = c.fetchone()[0]
        else:
            inspection_id = c.lastrowid
        return inspection_id
    except Exception as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        release_db_connection(conn)

def get_inspections():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment, created_at, result FROM inspections")
        inspections = c.fetchall()
        return inspections
    finally:
        release_db_connection(conn)

def get_inspections_by_inspector(inspector_name, inspection_type='all'):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    c = conn.cursor()

    if inspection_type == 'all':
        # Get all inspection types for this inspector
        c.execute(f"""
            SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment,
                   created_at, result, form_type
            FROM inspections
            WHERE inspector_name = {ph}
            UNION
            SELECT id, premises_name as establishment_name, inspector_name, inspection_date,
                   'Residential' as type_of_establishment, created_at, result, 'Residential' as form_type
            FROM residential_inspections
            WHERE inspector_name = {ph}
            UNION
            SELECT id, establishment_name, inspector_name, inspection_date,
                   'Meat Processing' as type_of_establishment, created_at, result, 'Meat Processing' as form_type
            FROM meat_processing_inspections
            WHERE inspector_name = {ph}
            UNION
            SELECT id, deceased_name as establishment_name, inspector_name, inspection_date,
                   'Burial' as type_of_establishment, created_at, 'Completed' as result, 'Burial' as form_type
            FROM burial_site_inspections
            WHERE inspector_name = {ph}
            ORDER BY created_at DESC
        """, (inspector_name, inspector_name, inspector_name, inspector_name))
    else:
        # Filter by inspection type
        if inspection_type == 'Residential':
            c.execute(f"""SELECT id, premises_name as establishment_name, inspector_name, inspection_date,
                         'Residential' as type_of_establishment, created_at, result, 'Residential' as form_type
                         FROM residential_inspections
                         WHERE inspector_name = {ph} ORDER BY inspection_date DESC""", (inspector_name,))
        elif inspection_type == 'Meat Processing':
            c.execute(f"""SELECT id, establishment_name, inspector_name, inspection_date,
                         'Meat Processing' as type_of_establishment, created_at, result, 'Meat Processing' as form_type
                         FROM meat_processing_inspections
                         WHERE inspector_name = {ph} ORDER BY inspection_date DESC""", (inspector_name,))
        elif inspection_type == 'Burial':
            c.execute(f"""SELECT id, deceased_name as establishment_name, inspector_name, inspection_date,
                         'Burial' as type_of_establishment, created_at, 'Completed' as result, 'Burial' as form_type
                         FROM burial_site_inspections
                         WHERE inspector_name = {ph} ORDER BY inspection_date DESC""", (inspector_name,))
        else:
            c.execute(f"""SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment,
                         created_at, result, form_type FROM inspections
                         WHERE inspector_name = {ph} AND (form_type = {ph} OR type_of_establishment = {ph})
                         ORDER BY inspection_date DESC""", (inspector_name, inspection_type, inspection_type))

    inspections = c.fetchall()
    release_db_connection(conn)
    return inspections

def get_burial_inspections():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT id, applicant_name, deceased_name, created_at, 'Completed' AS status FROM burial_site_inspections")
        inspections = c.fetchall()
        return inspections
    finally:
        release_db_connection(conn)

def get_residential_inspections():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT id, premises_name, inspection_date, result FROM residential_inspections")
        inspections = c.fetchall()
        return inspections
    finally:
        release_db_connection(conn)

def get_meat_processing_inspections():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT id, establishment_name, inspection_date, result FROM meat_processing_inspections")
        inspections = c.fetchall()
        return inspections
    finally:
        release_db_connection(conn)

def get_inspection_details(inspection_id):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute(f"SELECT * FROM inspections WHERE id = {ph}", (inspection_id,))
        inspection = c.fetchone()

        if not inspection:
            return None

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
            c.execute(f"SELECT item_id, details, obser, error FROM inspection_items WHERE inspection_id = {ph}", (inspection_id,))
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
            return inspection_dict
    finally:
        release_db_connection(conn)

def get_burial_inspection_details(inspection_id):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute(f"SELECT * FROM burial_site_inspections WHERE id = {ph}", (inspection_id,))
        inspection = c.fetchone()
        if not inspection:
            return None
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
    finally:
        release_db_connection(conn)

def get_residential_inspection_details(inspection_id):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"SELECT * FROM residential_inspections WHERE id = {ph}", (inspection_id,))
    inspection = c.fetchone()
    if inspection:
        c.execute(f"SELECT item_id, score FROM residential_checklist_scores WHERE form_id = {ph}", (inspection_id,))
        checklist_scores = dict(c.fetchall())
        release_db_connection(conn)
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
    release_db_connection(conn)
    return None

def get_meat_processing_inspection_details(inspection_id):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"SELECT * FROM meat_processing_inspections WHERE id = {ph}", (inspection_id,))
    inspection = c.fetchone()
    if inspection:
        c.execute(f"SELECT item_id, score FROM meat_processing_checklist_scores WHERE form_id = {ph}", (inspection_id,))
        # Convert integer keys to zero-padded string keys to match template expectations
        checklist_scores = {str(item_id).zfill(2): score for item_id, score in c.fetchall()}
        release_db_connection(conn)
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
            'staff_compliment': inspection[12] if len(inspection) > 12 else 0,
            'water_public': inspection[13] if len(inspection) > 13 else 0,
            'water_private': inspection[14] if len(inspection) > 14 else 0,
            'type_processing': inspection[15] if len(inspection) > 15 else 0,
            'type_slaughter': inspection[16] if len(inspection) > 16 else 0,
            'purpose_of_visit': inspection[17] if len(inspection) > 17 else '',
            'inspection_date': inspection[18] if len(inspection) > 18 else '',
            'inspector_code': inspection[19] if len(inspection) > 19 else '',
            'result': inspection[20] if len(inspection) > 20 else '',
            'telephone_no': inspection[21] if len(inspection) > 21 else '',
            'registration_status': inspection[22] if len(inspection) > 22 else '',
            'action': inspection[23] if len(inspection) > 23 else '',
            'comments': inspection[24] if len(inspection) > 24 else '',
            'inspector_signature': inspection[25] if len(inspection) > 25 else '',
            'received_by': inspection[26] if len(inspection) > 26 else '',
            'created_at': inspection[27] if len(inspection) > 27 else '',
            'photo_data': inspection[28] if len(inspection) > 28 else '[]',
            'checklist_scores': checklist_scores
        }
    release_db_connection(conn)
    return None


def get_small_hotels_inspection_details(form_id):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM inspections WHERE id = {ph} AND form_type = 'Small Hotel'", (form_id,))
    inspection = cursor.fetchone()

    if not inspection:
        release_db_connection(conn)
        return None

    inspection_dict = dict(inspection)

    # Get individual scores
    cursor.execute(f"SELECT item_id, obser, error FROM inspection_items WHERE inspection_id = {ph}", (form_id,))
    items = cursor.fetchall()

    obser_scores = {}
    error_scores = {}
    for item in items:
        obser_scores[item[0]] = item[1] or '0'
        error_scores[item[0]] = item[2] or '0'

    inspection_dict['obser'] = obser_scores
    inspection_dict['error'] = error_scores

    release_db_connection(conn)
    return inspection_dict


def get_spirit_licence_inspection_details(form_id):
    from db_config import get_placeholder
    ph = get_placeholder()
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM inspections WHERE id = {ph} AND form_type = 'Spirit Licence Premises'", (form_id,))
    inspection = cursor.fetchone()

    if not inspection:
        release_db_connection(conn)
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

    release_db_connection(conn)
    return inspection_dict

def update_database_schema():
    """Update database schema to handle all form types properly"""
    conn = get_db_connection()
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
    except Exception:  # Catches both SQLite and PostgreSQL errors
        pass

    # Add signature date columns to inspections table
    signature_date_columns = [
        'inspector_signature_date',
        'manager_signature_date',
        'received_by_date'
    ]
    for column in signature_date_columns:
        try:
            c.execute(f"ALTER TABLE inspections ADD COLUMN {column} TEXT")
            print(f"✓ Added {column} column to inspections table")
        except Exception:  # Catches both SQLite and PostgreSQL errors
            pass

    # Add missing swimming pool score columns
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        try:
            c.execute(f'ALTER TABLE inspections ADD COLUMN score_{item["id"]} REAL DEFAULT 0')
        except Exception:  # Catches both SQLite and PostgreSQL errors
            pass

    # Create indexes for better performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_inspections_form_type ON inspections(form_type)",
        "CREATE INDEX IF NOT EXISTS idx_inspections_date ON inspections(inspection_date)",
        "CREATE INDEX IF NOT EXISTS idx_inspections_inspector ON inspections(inspector_name)",
        "CREATE INDEX IF NOT EXISTS idx_inspections_created_at ON inspections(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_inspections_result ON inspections(result)",
        "CREATE INDEX IF NOT EXISTS idx_residential_result ON residential_inspections(result)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_login_history_user ON login_history(user_id)"
    ]

    for index in indexes:
        try:
            c.execute(index)
        except Exception:  # Catches both SQLite and PostgreSQL errors
            pass

    conn.commit()
    release_db_connection(conn)

if __name__ == "__main__":
    init_db()