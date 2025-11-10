#!/usr/bin/env python3
"""
Add missing JavaScript for photo display to all detail templates
"""
import os

# JavaScript code to add
PHOTO_JAVASCRIPT = '''
    <script>
        // Display photos in sidebar
        function displayPhotos() {
            const photoData = {{ photo_data|tojson|safe }};
            const container = document.getElementById('photosSidebarContainer');

            if (!photoData || photoData === '[]' || photoData.length === 0) {
                container.innerHTML = '<div class="no-photos">No photos attached to this inspection.</div>';
                return;
            }

            let photos = [];
            try {
                photos = typeof photoData === 'string' ? JSON.parse(photoData) : photoData;
            } catch (e) {
                console.error('Error parsing photo data:', e);
                container.innerHTML = '<div class="no-photos">Error loading photos.</div>';
                return;
            }

            if (!Array.isArray(photos) || photos.length === 0) {
                container.innerHTML = '<div class="no-photos">No photos attached to this inspection.</div>';
                return;
            }

            container.innerHTML = photos.map((photo, index) => `
                <div class="photo-item">
                    <div class="photo-item-number">📷 ${photo.number || 'Photo ' + (index + 1)}</div>
                    <img src="${photo.data}" alt="${photo.number}" onclick="viewPhotoFullSize('${photo.data}')">
                    ${photo.comment ? `<div class="photo-item-comment">${photo.comment}</div>` : ''}
                </div>
            `).join('');
        }

        function viewPhotoFullSize(dataUrl) {
            window.open(dataUrl, '_blank');
        }

        // Display photos on page load
        document.addEventListener('DOMContentLoaded', displayPhotos);
    </script>
'''

# Templates that need the JavaScript
TEMPLATES_TO_FIX = [
    'burial_inspection_detail.html',
    'inspection_detail.html',
    'institutional_inspection_detail.html',
    'residential_inspection_details.html',
    'small_hotels_inspection_detail.html',
    'spirit_licence_inspection_detail.html',
    'swimming_pool_inspection_detail.html'
]

def add_photo_javascript(template_path):
    """Add photo JavaScript to a template before the closing body tag"""
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if JavaScript already exists
    if 'displayPhotos' in content:
        print(f"  ✓ {os.path.basename(template_path)} already has photo JavaScript")
        return False

    # Find the position to insert (before closing body tag and after zozi_badge if present)
    if "{% include 'zozi_badge.html' %}" in content:
        # Insert before zozi_badge
        content = content.replace(
            "{% include 'zozi_badge.html' %}",
            f"{PHOTO_JAVASCRIPT}\n\n    {{% include 'zozi_badge.html' %}}"
        )
    elif '</body>' in content:
        # Insert before </body>
        content = content.replace('</body>', f"{PHOTO_JAVASCRIPT}\n</body>")
    else:
        print(f"  ✗ Could not find insertion point in {os.path.basename(template_path)}")
        return False

    # Write back
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ Added photo JavaScript to {os.path.basename(template_path)}")
    return True

def main():
    print("=" * 70)
    print("Adding Photo JavaScript to Detail Templates")
    print("=" * 70)

    templates_dir = 'templates'
    fixed_count = 0

    for template_name in TEMPLATES_TO_FIX:
        template_path = os.path.join(templates_dir, template_name)
        if os.path.exists(template_path):
            if add_photo_javascript(template_path):
                fixed_count += 1
        else:
            print(f"  ✗ Template not found: {template_name}")

    print("\n" + "=" * 70)
    print(f"✅ Complete! Fixed {fixed_count} templates")
    print("=" * 70)
    print("\nNow submit a NEW barbershop inspection with photos to test!")

if __name__ == '__main__':
    main()
