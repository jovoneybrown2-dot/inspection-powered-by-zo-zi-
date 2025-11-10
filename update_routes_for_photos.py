#!/usr/bin/env python3
"""
Update all routes and database functions to pass photo_data
"""

# Routes that need photo_data added - format: (line_num_approx, route_name, param_to_add)
ROUTES_TO_UPDATE = [
    # (1072, 'institutional_inspection_detail', 'photo_data'),
    # (2003, 'inspection_detail', 'photo_data'),  # food
    # (2038, 'residential_inspection_details', 'photo_data'),  # DONE
    # (2071, 'meat_processing_inspection_details', 'photo_data'),  # DONE
    # (2135, 'burial_inspection_detail', 'photo_data'),
    # (4493, 'spirit_licence_inspection_detail', 'photo_data'),
    # (4843, 'swimming_pool_inspection_detail', 'photo_data'),
    # (5346, 'barbershop_inspection_detail', 'photo_data'),
    # (6928, 'small_hotels_inspection_detail', 'photo_data'),
]

# Database get functions that need photo_data added
DB_FUNCTIONS_TO_UPDATE = [
    'get_inspection_details',  # food
    'get_burial_inspection_details',
    'get_small_hotels_inspection_details',
    'get_spirit_licence_inspection_details',
]

print("=" * 70)
print("Route and Database Update Guide for Photo Support")
print("=" * 70)
print("\n✓ Templates Updated: ALL detail pages now have photo sidebars")
print("✓ Database Functions Updated:")
print("  - save_inspection() - includes photo_data")
print("  - save_meat_processing_inspection() - includes photo_data")
print("  - save_residential_inspection() - includes photo_data")
print("  - get_meat_processing_inspection_details() - returns photo_data")
print("  - get_residential_inspection_details() - returns photo_data")
print("\n✓ Routes Updated:")
print("  - meat_processing_inspection() - passes photo_data")
print("  - residential_inspection() - passes photo_data")

print("\n" + "=" * 70)
print("Manual Updates Needed:")
print("=" * 70)

print("\n📝 Database Functions (database.py):")
print("   Add this line to each get function return dict:")
print("   'photo_data': inspection[N] if len(inspection) > N else '[]',")
print("\n   Functions to update:")
for func in DB_FUNCTIONS_TO_UPDATE:
    print(f"   - {func}")

print("\n📝 App Routes (app.py):")
print("   Add this parameter to each render_template call:")
print("   photo_data=details.get('photo_data', '[]')")
print("   OR")
print("   photo_data=inspection.get('photo_data', '[]')")
print("\n   Routes to update:")
routes = [
    "institutional_inspection() - line ~1072",
    "inspection_detail() / food inspection - line ~2003",
    "burial_inspection_detail() - line ~2135",
    "spirit_licence_inspection() - line ~4493",
    "swimming_pool_inspection() - line ~4843",
    "barbershop_inspection() - line ~5346",
    "small_hotels_inspection() - line ~6928",
]
for route in routes:
    print(f"   - {route}")

print("\n" + "=" * 70)
print("How to Test:")
print("=" * 70)
print("1. python app.py")
print("2. Login as inspector")
print("3. Fill out any form and add photos")
print("4. Submit and view the details page")
print("5. Photos should appear in the sidebar!")
print("=" * 70)
