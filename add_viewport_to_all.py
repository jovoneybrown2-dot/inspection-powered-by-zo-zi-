#!/usr/bin/env python3
"""
Add viewport meta tag to all HTML files that are missing it
This ensures proper responsive scaling on tablets, iPads, and mobile devices
"""
import os
import re

def add_viewport_to_html(filepath):
    """Add viewport meta tag to HTML file if missing"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if viewport already exists
    if 'viewport' in content.lower():
        return False  # Already has viewport

    # Find the <head> tag
    head_pattern = r'(<head[^>]*>)'
    match = re.search(head_pattern, content, re.IGNORECASE)

    if not match:
        print(f"  ⚠️  No <head> tag found in {filepath}")
        return False

    # Insert viewport after <head>
    head_tag = match.group(1)
    viewport_tags = '''
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">'''

    new_content = content.replace(
        head_tag,
        head_tag + viewport_tags,
        1  # Only replace first occurrence
    )

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True  # Successfully added

def main():
    templates_dir = 'templates'

    print("=" * 70)
    print("ADDING VIEWPORT META TAGS TO ALL HTML FILES")
    print("=" * 70)
    print(f"\nScanning: {templates_dir}/\n")

    html_files = [f for f in os.listdir(templates_dir) if f.endswith('.html')]

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for filename in sorted(html_files):
        filepath = os.path.join(templates_dir, filename)

        try:
            if add_viewport_to_html(filepath):
                print(f"✅ {filename:50} ADDED")
                updated_count += 1
            else:
                print(f"⏭️  {filename:50} SKIPPED (already has viewport)")
                skipped_count += 1
        except Exception as e:
            print(f"❌ {filename:50} ERROR: {e}")
            error_count += 1

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files scanned:  {len(html_files)}")
    print(f"✅ Updated:           {updated_count}")
    print(f"⏭️  Skipped:           {skipped_count}")
    print(f"❌ Errors:            {error_count}")
    print("=" * 70)

    if updated_count > 0:
        print(f"\n🎉 Successfully added viewport tags to {updated_count} files!")
        print("📱 Your app is now fully responsive for tablets and mobile devices!")
    else:
        print("\n✓ All files already have viewport tags!")

if __name__ == '__main__':
    main()
