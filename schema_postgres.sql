
-- WRHA Inspection Management System - PostgreSQL Schema
-- Generated for deployment package
-- Version: 1.0.0

-- Enable UUID extension for unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Inspections table (main inspection records)
CREATE TABLE IF NOT EXISTS inspections (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    photo_data TEXT
);

-- Inspection items table (checklist items for each inspection)
CREATE TABLE IF NOT EXISTS inspection_items (
    id SERIAL PRIMARY KEY,
    inspection_id INTEGER,
    item_id TEXT,
    details TEXT,
    obser TEXT,
    error TEXT,
    FOREIGN KEY (inspection_id) REFERENCES inspections(id) ON DELETE CASCADE
);

-- Burial site inspections table
CREATE TABLE IF NOT EXISTS burial_site_inspections (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    photo_data TEXT
);

-- Residential inspections table
CREATE TABLE IF NOT EXISTS residential_inspections (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    photo_data TEXT,
    parish TEXT
);

-- Residential checklist scores table
CREATE TABLE IF NOT EXISTS residential_checklist_scores (
    id SERIAL PRIMARY KEY,
    form_id INTEGER,
    item_id INTEGER,
    score INTEGER,
    FOREIGN KEY (form_id) REFERENCES residential_inspections(id) ON DELETE CASCADE
);

-- Meat processing inspections table
CREATE TABLE IF NOT EXISTS meat_processing_inspections (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    photo_data TEXT
);

-- Meat processing checklist scores table
CREATE TABLE IF NOT EXISTS meat_processing_checklist_scores (
    id SERIAL PRIMARY KEY,
    form_id INTEGER,
    item_id INTEGER,
    score REAL,
    FOREIGN KEY (form_id) REFERENCES meat_processing_inspections(id) ON DELETE CASCADE
);

-- Threshold settings table (for alert system)
CREATE TABLE IF NOT EXISTS threshold_settings (
    chart_type TEXT NOT NULL,
    inspection_type TEXT NOT NULL,
    threshold_value REAL NOT NULL,
    enabled INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chart_type, inspection_type)
);

-- Threshold alerts table (for low score notifications)
CREATE TABLE IF NOT EXISTS threshold_alerts (
    id SERIAL PRIMARY KEY,
    inspection_id INTEGER NOT NULL,
    inspector_name TEXT NOT NULL,
    form_type TEXT NOT NULL,
    score REAL NOT NULL,
    threshold_value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT,
    parish TEXT,
    first_login INTEGER DEFAULT 1,
    is_flagged INTEGER DEFAULT 0
);

-- Login history table
CREATE TABLE IF NOT EXISTS login_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL,
    login_time TEXT NOT NULL,
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
    user_id INTEGER,
    contact_id INTEGER,
    PRIMARY KEY (user_id, contact_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read INTEGER DEFAULT 0,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    user_role TEXT,
    login_time TEXT NOT NULL,
    logout_time TEXT,
    last_activity TEXT,
    location_lat REAL,
    location_lng REAL,
    parish TEXT,
    ip_address TEXT,
    is_active INTEGER DEFAULT 1
);

-- Form templates table
CREATE TABLE IF NOT EXISTS form_templates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    form_type TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version TEXT DEFAULT '1.0',
    created_by TEXT,
    last_edited_by TEXT,
    last_edited_date TEXT,
    last_edited_role TEXT
);

-- Form items table
CREATE TABLE IF NOT EXISTS form_items (
    id SERIAL PRIMARY KEY,
    form_template_id INTEGER NOT NULL,
    item_order INTEGER NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    weight INTEGER NOT NULL,
    is_critical INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    item_id TEXT,
    FOREIGN KEY (form_template_id) REFERENCES form_templates(id) ON DELETE CASCADE
);

-- Form categories table
CREATE TABLE IF NOT EXISTS form_categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0
);

-- Form fields table
CREATE TABLE IF NOT EXISTS form_fields (
    id SERIAL PRIMARY KEY,
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
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (form_template_id) REFERENCES form_templates(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_inspections_form_type ON inspections(form_type);
CREATE INDEX IF NOT EXISTS idx_inspections_date ON inspections(inspection_date);
CREATE INDEX IF NOT EXISTS idx_inspections_inspector ON inspections(inspector_name);
CREATE INDEX IF NOT EXISTS idx_inspections_created_at ON inspections(created_at);
CREATE INDEX IF NOT EXISTS idx_inspections_result ON inspections(result);
CREATE INDEX IF NOT EXISTS idx_residential_result ON residential_inspections(result);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_login_history_user ON login_history(user_id);

-- Insert default users
INSERT INTO users (username, password, role) VALUES
    ('inspector1', 'Insp123!secure', 'inspector'),
    ('inspector2', 'Insp456!secure', 'inspector'),
    ('inspector3', 'Insp789!secure', 'inspector'),
    ('inspector4', 'Insp012!secure', 'inspector'),
    ('inspector5', 'Insp345!secure', 'inspector'),
    ('inspector6', 'Insp678!secure', 'inspector'),
    ('admin', 'Admin901!secure', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insert default form templates
INSERT INTO form_templates (name, description, form_type) VALUES
    ('Food Establishment Inspection', 'Standard food safety inspection form', 'Food Establishment'),
    ('Residential & Non-Residential Inspection', 'Residential property inspection form', 'Residential'),
    ('Burial Site Inspection', 'Burial site approval inspection', 'Burial'),
    ('Spirit Licence Premises Inspection', 'Spirit licence premises inspection', 'Spirit Licence Premises'),
    ('Swimming Pool Inspection', 'Swimming pool safety inspection', 'Swimming Pool'),
    ('Small Hotels Inspection', 'Small hotels inspection form', 'Small Hotel'),
    ('Barbershop Inspection', 'Barbershop and beauty salon inspection form', 'Barbershop'),
    ('Institutional Inspection', 'Institutional health inspection form', 'Institutional'),
    ('Meat Processing Inspection', 'Meat processing plant and slaughter place inspection', 'Meat Processing')
ON CONFLICT (name) DO NOTHING;

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_version (version) VALUES ('1.0.0') ON CONFLICT DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL schema initialized successfully!';
    RAISE NOTICE 'Database: WRHA Inspection Management System v1.0.0';
END $$;
