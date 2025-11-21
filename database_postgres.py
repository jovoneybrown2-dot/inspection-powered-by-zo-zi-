import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv
from db_config import get_db_connection

load_dotenv()

# Alias for compatibility with existing code
def get_connection():
    """Get PostgreSQL database connection - uses db_config for proper Render support"""
    return get_db_connection()

def init_db():
    """Initialize database - schema should already be created via schema_postgres.sql"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"PostgreSQL database connected successfully. Users: {count}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

def save_inspection(data):
    """Save inspection to database"""
    conn = get_connection()
    cursor = conn.cursor()

    # Convert empty strings to None for PostgreSQL compatibility
    inspection_time = data.get('inspection_time') or None
    no_of_employees = data.get('no_of_employees') or None
    critical_score = data.get('critical_score') or None
    overall_score = data.get('overall_score') or None

    cursor.execute('''INSERT INTO inspections (establishment_name, address, inspector_name, inspection_date, inspection_time,
                 type_of_establishment, no_of_employees, purpose_of_visit, action, result, food_inspected, food_condemned,
                 critical_score, overall_score, comments, inspector_signature, received_by, form_type, scores, created_at,
                 inspector_code, license_no, owner)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                 RETURNING id''',
              (data['establishment_name'], data['address'], data['inspector_name'], data['inspection_date'],
               inspection_time, data['type_of_establishment'], no_of_employees,
               data['purpose_of_visit'], data['action'], data['result'], data['food_inspected'],
               data['food_condemned'], critical_score, overall_score, data['comments'],
               data['inspector_signature'], data['received_by'], data['form_type'], data['scores'],
               data['created_at'], data['inspector_code'], data['license_no'], data['owner']))

    inspection_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return inspection_id

def save_burial_inspection(data):
    """Save burial site inspection"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if data.get('id'):
            cursor.execute('''UPDATE burial_site_inspections SET
                         inspection_date = %s, applicant_name = %s, deceased_name = %s, burial_location = %s,
                         site_description = %s, proximity_water_source = %s, proximity_perimeter_boundaries = %s,
                         proximity_road_pathway = %s, proximity_trees = %s, proximity_houses_buildings = %s,
                         proposed_grave_type = %s, general_remarks = %s, inspector_signature = %s,
                         received_by = %s, created_at = %s
                         WHERE id = %s''',
                      (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
                       data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
                       data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
                       data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
                       data['received_by'], data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                       data['id']))
        else:
            cursor.execute('''INSERT INTO burial_site_inspections (inspection_date, applicant_name, deceased_name, burial_location,
                        site_description, proximity_water_source, proximity_perimeter_boundaries, proximity_road_pathway,
                        proximity_trees, proximity_houses_buildings, proposed_grave_type, general_remarks,
                        inspector_signature, received_by, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                      (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
                       data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
                       data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
                       data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
                       data['received_by'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def save_residential_inspection(data):
    """Save residential inspection"""
    conn = get_connection()
    cursor = conn.cursor()
    inspection_id = None
    try:
        if data.get('id'):
            cursor.execute("""
                            UPDATE residential_inspections
                            SET premises_name = %s, owner = %s, address = %s, inspector_name = %s,
                                inspection_date = %s, inspector_code = %s, treatment_facility = %s, vector = %s,
                                result = %s, onsite_system = %s, building_construction_type = %s, purpose_of_visit = %s,
                                action = %s, no_of_bedrooms = %s, total_population = %s, critical_score = %s,
                                overall_score = %s, comments = %s, inspector_signature = %s, received_by = %s,
                                created_at = %s
                            WHERE id = %s
                        """,
                        (data['premises_name'], data['owner'], data['address'], data['inspector_name'],
                         data['inspection_date'], data['inspector_code'], data['treatment_facility'], data['vector'],
                         data['result'], data['onsite_system'], data['building_construction_type'], data['purpose_of_visit'],
                         data['action'], data.get('no_of_bedrooms', ''), data.get('total_population', ''),
                         data.get('critical_score', 0), data.get('overall_score', 0), data['comments'],
                         data['inspector_signature'], data['received_by'],
                         data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')), data['id']))
            inspection_id = data['id']
        else:
            cursor.execute("""
                INSERT INTO residential_inspections (
                    premises_name, owner, address, inspector_name,
                    inspection_date, inspector_code, treatment_facility, vector, result, onsite_system,
                    building_construction_type, purpose_of_visit, action, no_of_bedrooms, total_population,
                    critical_score, overall_score, comments, inspector_signature, received_by, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['premises_name'], data['owner'], data['address'], data['inspector_name'],
                data['inspection_date'], data['inspector_code'], data['treatment_facility'], data['vector'],
                data['result'], data['onsite_system'], data['building_construction_type'], data['purpose_of_visit'],
                data['action'], data.get('no_of_bedrooms', ''), data.get('total_population', ''),
                data.get('critical_score', 0), data.get('overall_score', 0), data['comments'],
                data['inspector_signature'], data['received_by'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            inspection_id = cursor.fetchone()[0]
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return inspection_id

def get_inspections():
    """Get all inspections"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment, created_at, result FROM inspections ORDER BY created_at DESC")
    inspections = cursor.fetchall()
    cursor.close()
    conn.close()
    return inspections

def get_inspections_by_inspector(inspector_name, inspection_type='all'):
    """Get inspections by inspector name - safely handles missing tables"""
    conn = get_connection()
    cursor = conn.cursor()
    all_inspections = []

    if inspection_type == 'all':
        # Try to get from each table individually to handle missing tables gracefully

        # Regular inspections
        try:
            cursor.execute("""
                SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment,
                       created_at, result, form_type
                FROM inspections
                WHERE inspector_name = %s
                ORDER BY created_at DESC
            """, (inspector_name,))
            all_inspections.extend(cursor.fetchall())
        except Exception as e:
            print(f"Error fetching regular inspections: {e}")

        # Residential inspections
        try:
            cursor.execute("""
                SELECT id, premises_name as establishment_name, inspector_name, inspection_date,
                       'Residential' as type_of_establishment, created_at, result, 'Residential' as form_type
                FROM residential_inspections
                WHERE inspector_name = %s
                ORDER BY created_at DESC
            """, (inspector_name,))
            all_inspections.extend(cursor.fetchall())
        except Exception as e:
            print(f"Error fetching residential inspections: {e}")

        # Meat processing inspections
        try:
            cursor.execute("""
                SELECT id, establishment_name, inspector_name, inspection_date,
                       'Meat Processing' as type_of_establishment, created_at, result, 'Meat Processing' as form_type
                FROM meat_processing_inspections
                WHERE inspector_name = %s
                ORDER BY created_at DESC
            """, (inspector_name,))
            all_inspections.extend(cursor.fetchall())
        except Exception as e:
            print(f"Error fetching meat processing inspections: {e}")

        # Burial site inspections
        try:
            cursor.execute("""
                SELECT id, deceased_name as establishment_name, '' as inspector_name, inspection_date,
                       'Burial' as type_of_establishment, created_at, 'Completed' as result, 'Burial' as form_type
                FROM burial_site_inspections
                WHERE inspection_date IS NOT NULL
                ORDER BY created_at DESC
            """)
            all_inspections.extend(cursor.fetchall())
        except Exception as e:
            print(f"Error fetching burial inspections: {e}")

        # Sort all inspections by created_at (index 5)
        all_inspections.sort(key=lambda x: x[5] if x[5] else '', reverse=True)

    else:
        # Filter by inspection type
        try:
            if inspection_type == 'Residential':
                cursor.execute("""
                    SELECT id, premises_name as establishment_name, inspector_name, inspection_date,
                           'Residential' as type_of_establishment, created_at, result, 'Residential' as form_type
                    FROM residential_inspections
                    WHERE inspector_name = %s ORDER BY inspection_date DESC
                """, (inspector_name,))
            elif inspection_type == 'Meat Processing':
                cursor.execute("""
                    SELECT id, establishment_name, inspector_name, inspection_date,
                           'Meat Processing' as type_of_establishment, created_at, result, 'Meat Processing' as form_type
                    FROM meat_processing_inspections
                    WHERE inspector_name = %s ORDER BY inspection_date DESC
                """, (inspector_name,))
            elif inspection_type == 'Burial':
                cursor.execute("""
                    SELECT id, deceased_name as establishment_name, '' as inspector_name, inspection_date,
                           'Burial' as type_of_establishment, created_at, 'Completed' as result, 'Burial' as form_type
                    FROM burial_site_inspections
                    ORDER BY inspection_date DESC
                """)
            else:
                cursor.execute("""
                    SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment,
                           created_at, result, form_type FROM inspections
                    WHERE inspector_name = %s AND (form_type = %s OR type_of_establishment = %s)
                    ORDER BY inspection_date DESC
                """, (inspector_name, inspection_type, inspection_type))

            all_inspections = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching {inspection_type} inspections: {e}")

    cursor.close()
    conn.close()
    return all_inspections

def get_burial_inspections():
    """Get all burial inspections - safely handles missing table"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, applicant_name, deceased_name, created_at, 'Completed' AS status FROM burial_site_inspections ORDER BY created_at DESC")
        inspections = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching burial inspections: {e}")
        inspections = []
    cursor.close()
    conn.close()
    return inspections

def get_residential_inspections():
    """Get all residential inspections"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, premises_name, inspection_date, result FROM residential_inspections ORDER BY created_at DESC")
    inspections = cursor.fetchall()
    cursor.close()
    conn.close()
    return inspections

def get_inspection_details(inspection_id):
    """Get detailed inspection information"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inspections WHERE id = %s", (inspection_id,))
    inspection = cursor.fetchone()

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
                'inspector_code': inspection[26] or ''
            }
        else:
            cursor.execute("SELECT item_id, details, obser, error FROM inspection_items WHERE inspection_id = %s", (inspection_id,))
            items = cursor.fetchall()
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
                'inspector_code': inspection[26] or ''
            }
        cursor.close()
        conn.close()
        return inspection_dict
    cursor.close()
    conn.close()
    return None

def get_burial_inspection_details(inspection_id):
    """Get burial inspection details"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM burial_site_inspections WHERE id = %s", (inspection_id,))
    inspection = cursor.fetchone()
    cursor.close()
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
            'created_at': inspection[15] or ''
        }
    return None

def get_residential_inspection_details(inspection_id):
    """Get residential inspection details"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM residential_inspections WHERE id = %s", (inspection_id,))
    inspection = cursor.fetchone()
    if inspection:
        cursor.execute("SELECT item_id, score FROM residential_checklist_scores WHERE form_id = %s", (inspection_id,))
        checklist_scores = dict(cursor.fetchall())
        cursor.close()
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
            'checklist_scores': checklist_scores
        }
    cursor.close()
    conn.close()
    return None

def get_small_hotels_inspection_details(form_id):
    """Get small hotels inspection details"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM inspections WHERE id = %s AND form_type = 'Small Hotel'", (form_id,))
    inspection = cursor.fetchone()

    if not inspection:
        cursor.close()
        conn.close()
        return None

    inspection_dict = dict(inspection)

    # Get individual scores
    cursor.execute("SELECT item_id, obser, error FROM inspection_items WHERE inspection_id = %s", (form_id,))
    items = cursor.fetchall()

    obser_scores = {}
    error_scores = {}
    for item in items:
        obser_scores[item['item_id']] = item['obser'] or '0'
        error_scores[item['item_id']] = item['error'] or '0'

    inspection_dict['obser'] = obser_scores
    inspection_dict['error'] = error_scores

    cursor.close()
    conn.close()
    return inspection_dict

def get_spirit_licence_inspection_details(form_id):
    """Get spirit licence inspection details"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM inspections WHERE id = %s AND form_type = 'Spirit Licence Premises'", (form_id,))
    inspection = cursor.fetchone()

    if not inspection:
        cursor.close()
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

    cursor.close()
    conn.close()
    return inspection_dict

def save_meat_processing_inspection(data):
    """Save meat processing inspection"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if data.get('id'):
            cursor.execute("""
                UPDATE meat_processing_inspections
                SET establishment_name = %s, owner_operator = %s, address = %s, inspector_name = %s,
                    establishment_no = %s, overall_score = %s, critical_score = %s, food_contact_surfaces = %s, water_samples = %s,
                    product_samples = %s, types_of_products = %s, staff_fhp = %s, staff_compliment = %s, water_public = %s,
                    water_private = %s, type_processing = %s, type_slaughter = %s, purpose_of_visit = %s,
                    inspection_date = %s, inspector_code = %s, result = %s, telephone_no = %s,
                    registration_status = %s, action = %s, comments = %s, inspector_signature = %s,
                    received_by = %s, created_at = %s, photo_data = %s
                WHERE id = %s
            """, (
                data['establishment_name'], data['owner_operator'], data['address'], data['inspector_name'],
                data['establishment_no'], data['overall_score'], data.get('critical_score', 0), data['food_contact_surfaces'], data['water_samples'],
                data['product_samples'], data['types_of_products'], data['staff_fhp'], data.get('staff_compliment', 0), data['water_public'],
                data['water_private'], data['type_processing'], data['type_slaughter'], data['purpose_of_visit'],
                data['inspection_date'], data['inspector_code'], data['result'], data['telephone_no'],
                data['registration_status'], data['action'], data['comments'], data['inspector_signature'],
                data['received_by'], data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                data.get('photo_data', '[]'), data['id']
            ))
            inspection_id = data['id']
        else:
            cursor.execute("""
                INSERT INTO meat_processing_inspections (
                    establishment_name, owner_operator, address, inspector_name,
                    establishment_no, overall_score, critical_score, food_contact_surfaces, water_samples,
                    product_samples, types_of_products, staff_fhp, staff_compliment, water_public,
                    water_private, type_processing, type_slaughter, purpose_of_visit,
                    inspection_date, inspector_code, result, telephone_no,
                    registration_status, action, comments, inspector_signature,
                    received_by, created_at, photo_data
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['establishment_name'], data['owner_operator'], data['address'], data['inspector_name'],
                data['establishment_no'], data['overall_score'], data.get('critical_score', 0), data['food_contact_surfaces'], data['water_samples'],
                data['product_samples'], data['types_of_products'], data['staff_fhp'], data.get('staff_compliment', 0), data['water_public'],
                data['water_private'], data['type_processing'], data['type_slaughter'], data['purpose_of_visit'],
                data['inspection_date'], data['inspector_code'], data['result'], data['telephone_no'],
                data['registration_status'], data['action'], data['comments'], data['inspector_signature'],
                data['received_by'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get('photo_data', '[]')
            ))
            inspection_id = cursor.fetchone()[0]

        conn.commit()

        # Save checklist scores if provided
        if 'checklist_scores' in data:
            for item_id, score in data['checklist_scores'].items():
                try:
                    item_id_int = int(item_id)
                    cursor.execute("""
                        INSERT INTO meat_processing_checklist_scores (form_id, item_id, score)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (form_id, item_id) DO UPDATE SET score = EXCLUDED.score
                    """, (inspection_id, item_id_int, score))
                except ValueError:
                    continue
            conn.commit()

        cursor.close()
        conn.close()
        return inspection_id
    except Exception as e:
        print(f"Error saving meat processing inspection: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        raise

def get_meat_processing_inspections():
    """Get all meat processing inspections"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, establishment_name, inspection_date, result FROM meat_processing_inspections ORDER BY created_at DESC")
    inspections = cursor.fetchall()
    cursor.close()
    conn.close()
    return inspections

def get_meat_processing_inspection_details(inspection_id):
    """Get meat processing inspection details"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meat_processing_inspections WHERE id = %s", (inspection_id,))
    inspection = cursor.fetchone()
    if inspection:
        cursor.execute("SELECT item_id, score FROM meat_processing_checklist_scores WHERE form_id = %s", (inspection_id,))
        # Convert integer keys to zero-padded string keys to match template expectations
        checklist_scores = {str(item_id).zfill(2): score for item_id, score in cursor.fetchall()}
        cursor.close()
        conn.close()
        return {
            'id': inspection[0],
            'establishment_name': inspection[1] or '',
            'owner_operator': inspection[2] or '',
            'address': inspection[3] or '',
            'inspector_name': inspection[4] or '',
            'establishment_no': inspection[5] or '',
            'overall_score': inspection[6] or 0.0,
            'critical_score': inspection[7] if len(inspection) > 7 else 0.0,
            'food_contact_surfaces': inspection[8] if len(inspection) > 8 else 0,
            'water_samples': inspection[9] if len(inspection) > 9 else 0,
            'product_samples': inspection[10] if len(inspection) > 10 else 0,
            'types_of_products': inspection[11] if len(inspection) > 11 else '',
            'staff_fhp': inspection[12] if len(inspection) > 12 else 0,
            'staff_compliment': inspection[13] if len(inspection) > 13 else 0,
            'water_public': inspection[14] if len(inspection) > 14 else 0,
            'water_private': inspection[15] if len(inspection) > 15 else 0,
            'type_processing': inspection[16] if len(inspection) > 16 else 0,
            'type_slaughter': inspection[17] if len(inspection) > 17 else 0,
            'purpose_of_visit': inspection[18] if len(inspection) > 18 else '',
            'inspection_date': inspection[19] if len(inspection) > 19 else '',
            'inspector_code': inspection[20] if len(inspection) > 20 else '',
            'result': inspection[21] if len(inspection) > 21 else '',
            'telephone_no': inspection[22] if len(inspection) > 22 else '',
            'registration_status': inspection[23] if len(inspection) > 23 else '',
            'action': inspection[24] if len(inspection) > 24 else '',
            'comments': inspection[25] if len(inspection) > 25 else '',
            'inspector_signature': inspection[26] if len(inspection) > 26 else '',
            'received_by': inspection[27] if len(inspection) > 27 else '',
            'created_at': inspection[28] if len(inspection) > 28 else '',
            'photo_data': inspection[29] if len(inspection) > 29 else '[]',
            'checklist_scores': checklist_scores
        }
    cursor.close()
    conn.close()
    return None

def update_database_schema():
    """Update database schema - not needed for PostgreSQL as schema is created via SQL file"""
    print("PostgreSQL schema should be created via schema_postgres.sql file")
    pass

if __name__ == "__main__":
    init_db()
