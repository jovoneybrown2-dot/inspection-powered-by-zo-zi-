#!/usr/bin/env python3
"""
Migration script to populate form_fields table with standard form fields
This allows admins to edit field labels, placeholders, and properties
"""

import sqlite3
from datetime import datetime

def migrate_form_fields():
    """Migrate common form fields to database for all form types"""
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Check if migration already done
    c.execute("SELECT COUNT(*) FROM form_fields")
    if c.fetchone()[0] > 0:
        print("⚠️  Migration already completed. form_fields table has data.")
        response = input("Do you want to clear and re-migrate? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            conn.close()
            return
        c.execute("DELETE FROM form_fields")
        print("✓ Cleared existing form_fields")

    # Common fields used across most forms
    common_fields = [
        {
            'field_name': 'establishment_name',
            'field_label': 'Establishment Name',
            'field_type': 'text',
            'field_order': 1,
            'required': 1,
            'placeholder': 'Enter establishment name',
            'field_group': 'establishment_info'
        },
        {
            'field_name': 'owner',
            'field_label': 'Owner/Operator',
            'field_type': 'text',
            'field_order': 2,
            'required': 1,
            'placeholder': 'Enter owner or operator name',
            'field_group': 'establishment_info'
        },
        {
            'field_name': 'address',
            'field_label': 'Address',
            'field_type': 'textarea',
            'field_order': 3,
            'required': 1,
            'placeholder': 'Enter full address',
            'field_group': 'establishment_info'
        },
        {
            'field_name': 'license_no',
            'field_label': 'License Number',
            'field_type': 'text',
            'field_order': 4,
            'required': 0,
            'placeholder': 'Enter license number',
            'field_group': 'establishment_info'
        },
        {
            'field_name': 'telephone_no',
            'field_label': 'Telephone',
            'field_type': 'tel',
            'field_order': 5,
            'required': 0,
            'placeholder': 'Enter telephone number',
            'field_group': 'establishment_info'
        },
        {
            'field_name': 'parish',
            'field_label': 'Parish',
            'field_type': 'select',
            'field_order': 6,
            'required': 1,
            'options': 'Kingston,St. Andrew,St. Catherine,Clarendon,Manchester,St. Elizabeth,Westmoreland,Hanover,St. James,Trelawny,St. Ann,St. Mary,Portland,St. Thomas',
            'field_group': 'establishment_info'
        },
        {
            'field_name': 'inspection_date',
            'field_label': 'Inspection Date',
            'field_type': 'date',
            'field_order': 10,
            'required': 1,
            'field_group': 'inspection_details'
        },
        {
            'field_name': 'inspection_time',
            'field_label': 'Inspection Time',
            'field_type': 'time',
            'field_order': 11,
            'required': 0,
            'field_group': 'inspection_details'
        },
        {
            'field_name': 'inspector_name',
            'field_label': 'Inspector Name',
            'field_type': 'text',
            'field_order': 12,
            'required': 1,
            'placeholder': 'Inspector name',
            'field_group': 'inspection_details'
        },
        {
            'field_name': 'inspector_code',
            'field_label': 'Inspector Code',
            'field_type': 'text',
            'field_order': 13,
            'required': 0,
            'placeholder': 'Enter inspector code',
            'field_group': 'inspection_details'
        },
        {
            'field_name': 'purpose_of_visit',
            'field_label': 'Purpose of Visit',
            'field_type': 'select',
            'field_order': 14,
            'required': 0,
            'options': 'Routine Inspection,Follow-up,Complaint Investigation,License Renewal,Other',
            'field_group': 'inspection_details'
        },
        {
            'field_name': 'comments',
            'field_label': 'Comments/Recommendations',
            'field_type': 'textarea',
            'field_order': 20,
            'required': 0,
            'placeholder': 'Enter any comments or recommendations',
            'field_group': 'results'
        },
        {
            'field_name': 'action',
            'field_label': 'Action Required',
            'field_type': 'textarea',
            'field_order': 21,
            'required': 0,
            'placeholder': 'Describe actions required',
            'field_group': 'results'
        }
    ]

    # Form-specific fields for different form types
    form_specific_fields = {
        # Institutional forms
        494: [
            {
                'field_name': 'staff_complement',
                'field_label': 'Staff Complement',
                'field_type': 'number',
                'field_order': 7,
                'required': 0,
                'placeholder': 'Number of staff',
                'field_group': 'establishment_info'
            },
            {
                'field_name': 'num_occupants',
                'field_label': 'Number of Occupants',
                'field_type': 'number',
                'field_order': 8,
                'required': 0,
                'placeholder': 'Number of occupants',
                'field_group': 'establishment_info'
            },
            {
                'field_name': 'institution_type',
                'field_label': 'Institution Type',
                'field_type': 'text',
                'field_order': 9,
                'required': 0,
                'placeholder': 'Type of institution',
                'field_group': 'establishment_info'
            }
        ],
        # Barbershop forms
        493: [
            {
                'field_name': 'no_of_employees',
                'field_label': 'Number of Employees',
                'field_type': 'number',
                'field_order': 7,
                'required': 0,
                'placeholder': 'Number of employees',
                'field_group': 'establishment_info'
            },
            {
                'field_name': 'type_of_establishment',
                'field_label': 'Type of Establishment',
                'field_type': 'text',
                'field_order': 8,
                'required': 0,
                'default_value': 'Barbershop',
                'field_group': 'establishment_info'
            }
        ]
    }

    total_fields = 0

    # Get all form template IDs
    c.execute('SELECT id, form_type FROM form_templates WHERE active = 1')
    templates = c.fetchall()

    for template_id, form_type in templates:
        print(f"\n📝 Migrating fields for {form_type}...")

        # Add common fields for this template
        for field in common_fields:
            c.execute('''
                INSERT INTO form_fields (
                    form_template_id, field_name, field_label, field_type,
                    field_order, required, placeholder, default_value, options,
                    field_group, active, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template_id,
                field['field_name'],
                field['field_label'],
                field['field_type'],
                field['field_order'],
                field['required'],
                field.get('placeholder', ''),
                field.get('default_value', ''),
                field.get('options', ''),
                field['field_group'],
                1,  # active
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            total_fields += 1

        # Add form-specific fields if they exist
        if template_id in form_specific_fields:
            for field in form_specific_fields[template_id]:
                c.execute('''
                    INSERT INTO form_fields (
                        form_template_id, field_name, field_label, field_type,
                        field_order, required, placeholder, default_value, options,
                        field_group, active, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    template_id,
                    field['field_name'],
                    field['field_label'],
                    field['field_type'],
                    field['field_order'],
                    field['required'],
                    field.get('placeholder', ''),
                    field.get('default_value', ''),
                    field.get('options', ''),
                    field['field_group'],
                    1,  # active
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                total_fields += 1

        field_count = len(common_fields) + len(form_specific_fields.get(template_id, []))
        print(f"   ✓ Migrated {field_count} fields")

    conn.commit()

    # Verify migration
    print(f"\n✅ Migration complete! Total fields migrated: {total_fields}")
    print("\nVerification:")
    c.execute('''
        SELECT ft.name, COUNT(ff.id) as field_count
        FROM form_templates ft
        LEFT JOIN form_fields ff ON ft.id = ff.form_template_id
        WHERE ft.active = 1
        GROUP BY ft.name
        ORDER BY ft.id
    ''')

    for row in c.fetchall():
        print(f"   • {row[0]}: {row[1]} fields")

    conn.close()
    print("\n🎉 Form fields migration successful! Admins can now edit form fields.")

if __name__ == '__main__':
    print("=" * 60)
    print("FORM FIELDS MIGRATION")
    print("=" * 60)
    print("\nThis will migrate form fields to the database.")
    print("This allows admins to edit field labels and properties.")
    print()

    try:
        migrate_form_fields()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
