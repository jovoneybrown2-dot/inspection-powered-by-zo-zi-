#!/usr/bin/env python3
"""
Create PWA icons from the custom Inspec logo
"""
from PIL import Image
import os

# Open the source image
source_image = 'static/inspec.jpg'
img = Image.open(source_image)

# Convert to RGBA if needed
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Create white background
def create_icon_with_background(img, size):
    """Create icon with white background"""
    # Create white background
    background = Image.new('RGBA', (size, size), (255, 255, 255, 255))

    # Calculate scaling to fit within size while maintaining aspect ratio
    img_width, img_height = img.size
    aspect = img_width / img_height

    if aspect > 1:
        # Wider than tall
        new_width = int(size * 0.9)  # 90% of size with padding
        new_height = int(new_width / aspect)
    else:
        # Taller than wide
        new_height = int(size * 0.9)
        new_width = int(new_height * aspect)

    # Resize image
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Center the image on the background
    offset = ((size - new_width) // 2, (size - new_height) // 2)
    background.paste(resized, offset, resized)

    return background

# Create 192x192 icon
icon_192 = create_icon_with_background(img, 192)
icon_192.save('static/icon-192.png', 'PNG')
print('✓ Created static/icon-192.png')

# Create 512x512 icon
icon_512 = create_icon_with_background(img, 512)
icon_512.save('static/icon-512.png', 'PNG')
print('✓ Created static/icon-512.png')

print('\nPWA icons created successfully!')
