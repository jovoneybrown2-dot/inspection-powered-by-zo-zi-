#!/usr/bin/env python3
"""
Script to update all inspection forms with signature pad component
"""
import os
import re

# Forms to update
forms = [
    'residential_form.html',
    'barbershop_form.html',
    'burial_form.html',
    'small_hotels_form.html',
    'institutional_form.html',
    'meat_processing_form.html',
    'swimming_pool_form.html'
]

templates_dir = '/Users/jovoneybrown/PycharmProjects/Python-food_Inspection_2/templates'

# Pattern to find received_by text inputs
pattern = r'<input\s+type="text"\s+name="received_by"[^>]*>'

# Replacement signature pad button
replacement = '''<button type="button" onclick="openSignaturePad()" style="padding:8px 16px; background:#4CAF50; color:white; border:none; border-radius:5px; cursor:pointer;">
                            ✍️ Click to Sign
                        </button>
                        <div id="signaturePreview" style="margin-top:10px; display:none;">
                            <img id="signatureImage" style="border:1px solid #ccc; max-width:250px; background:white;" />
                            <button type="button" onclick="clearSignature()" style="margin-left:10px; padding:4px 8px; background:#dc3545; color:white; border:none; border-radius:3px; cursor:pointer; font-size:12px;">
                                ❌ Clear
                            </button>
                        </div>
                        <input type="hidden" name="received_by" id="receivedBySignature" />'''

# Pattern to find closing body tag
body_pattern = r'(\s*)({% include \'zozi_badge\.html\' %})\s*(</body>)'

# Signature pad include
signature_include = r'\1<!-- Signature Pad -->\n\1{% include \'signature_pad.html\' %}\n\n\1\2\n\3'

for form in forms:
    filepath = os.path.join(templates_dir, form)

    if not os.path.exists(filepath):
        print(f"⚠️  Skipping {form} - file not found")
        continue

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace received_by input with signature pad button
        new_content, count1 = re.subn(pattern, replacement, content)

        # Add signature pad include before zozi_badge if not already there
        if 'signature_pad.html' not in new_content:
            new_content, count2 = re.subn(body_pattern, signature_include, new_content)
        else:
            count2 = 0

        if count1 > 0 or count2 > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Updated {form} ({count1} inputs replaced, include {'added' if count2 > 0 else 'already present'})")
        else:
            print(f"⚠️  No changes needed for {form}")

    except Exception as e:
        print(f"❌ Error processing {form}: {str(e)}")

print("\n🎉 Update complete!")
