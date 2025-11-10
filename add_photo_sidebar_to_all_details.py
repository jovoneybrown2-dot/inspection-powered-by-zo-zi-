#!/usr/bin/env python3
"""
Automated script to add photo sidebar to all detail page templates
"""
import os
import re

# Photo sidebar CSS to insert
PHOTO_SIDEBAR_CSS = '''        .main-content-wrapper {
            display: flex;
            gap: 20px;
            width: 100%;
            max-width: 1600px;
        }
        .photos-sidebar {
            width: 350px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-height: 90vh;
            overflow-y: auto;
            position: sticky;
            top: 20px;
        }
        .photos-sidebar h3 {
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .photo-item {
            margin-bottom: 20px;
            padding: 10px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .photo-item img {
            width: 100%;
            border-radius: 4px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .photo-item img:hover {
            transform: scale(1.02);
        }
        .photo-item-number {
            font-weight: bold;
            color: #4CAF50;
            margin-bottom: 5px;
        }
        .photo-item-comment {
            font-size: 13px;
            color: #666;
            margin-top: 8px;
        }
        .no-photos {
            text-align: center;
            color: #999;
            padding: 20px;
            font-style: italic;
        }
        @media print {
            .photos-sidebar {
                display: block !important;
                page-break-before: always;
                position: relative;
            }
        }'''

# Photo loading JavaScript
PHOTO_JS = '''
        // Load and display photos
        function loadPhotos() {
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

        // Load photos when page loads
        document.addEventListener('DOMContentLoaded', loadPhotos);'''

# Photo sidebar HTML
PHOTO_SIDEBAR_HTML = '''    <div class="main-content-wrapper">
        <!-- Photos Sidebar -->
        <div class="photos-sidebar">
            <h3>📷 Inspection Photos</h3>
            <div id="photosSidebarContainer">
                <div class="no-photos">No photos attached to this inspection.</div>
            </div>
        </div>

        <!-- Main Form Container -->
        '''

# Files to update (excluding meat_processing and residential which are already done)
DETAIL_PAGES = [
    'small_hotels_inspection_detail.html',
    'details.html',  # food establishment
    'inspection_detail.html',  # food establishment alternate
    'burial_inspection_detail.html',
    'barbershop_inspection_detail.html',
    'institutional_inspection_detail.html',
    'spirit_licence_inspection_detail.html',
    'swimming_pool_inspection_detail.html'
]

def update_detail_page(filepath):
    """Add photo sidebar to a detail page template"""
    if not os.path.exists(filepath):
        print(f"  ⚠ File not found: {filepath}")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    # Check if already updated
    if 'photos-sidebar' in content:
        print(f"  ✓ Already has photo sidebar")
        return True

    # 1. Update body CSS to add gap
    content = re.sub(
        r'(body\s*\{[^}]*?)display:\s*flex;([^}]*?justify-content:\s*center;[^}]*?align-items:\s*flex-start;)',
        r'\1display: flex;\n            gap: 20px;\2',
        content, flags=re.DOTALL
    )

    # 2. Add photo sidebar CSS before closing </style>
    if '</style>' in content:
        content = content.replace('    </style>', PHOTO_SIDEBAR_CSS + '\n    </style>')

    # 3. Update body structure - replace <div class="form-container"> with wrapper
    content = re.sub(
        r'<body>\s*<div class="form-container">',
        PHOTO_SIDEBAR_HTML + '<div class="form-container">',
        content
    )

    # 4. Close the wrappers before </body>
    # Find the last </div> before </body> and add closing divs
    content = re.sub(
        r'(</div>\s*<script>)',
        r'</div>\n        <!-- End Form Container -->\n    </div>\n    <!-- End Main Content Wrapper -->\n\n    <script>',
        content
    )

    # 5. Add photo loading JavaScript before </script>
    # Find the last </script> before {% include or </body>
    content = re.sub(
        r'(</script>\s*(?:{%\s*include|</body>))',
        PHOTO_JS + '\n    </script>\n    ' + r'\1',
        content
    )

    # Write updated content
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"  ✓ Updated successfully")
    return True

def main():
    print("=" * 70)
    print("Adding Photo Sidebars to All Detail Pages")
    print("=" * 70)

    templates_dir = 'templates'
    updated = 0
    skipped = 0

    for filename in DETAIL_PAGES:
        filepath = os.path.join(templates_dir, filename)
        print(f"\n{filename}:")

        if update_detail_page(filepath):
            updated += 1
        else:
            skipped += 1

    print("\n" + "=" * 70)
    print(f"Complete! Updated: {updated}, Skipped: {skipped}")
    print("=" * 70)
    print("\nNext step: Update routes in app.py to pass photo_data parameter")

if __name__ == "__main__":
    main()
