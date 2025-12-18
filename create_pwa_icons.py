#!/usr/bin/env python3
"""
Create PWA icons from the Inspec logo
Generates properly sized icons with rounded corners for iOS and Android
"""

from PIL import Image, ImageDraw, ImageFilter
import os

def create_rounded_rectangle_mask(size, radius):
    """Create a rounded rectangle mask"""
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)

    # Draw rounded rectangle
    draw.rounded_rectangle(
        [(0, 0), size],
        radius=radius,
        fill=255
    )

    return mask

def create_pwa_icon(input_path, output_path, size, corner_radius_percent=20):
    """
    Create a PWA icon with rounded corners

    Args:
        input_path: Path to input image (inspec.JPG)
        output_path: Path to save output icon
        size: Size in pixels (e.g., 192, 512)
        corner_radius_percent: Percentage of size to use for corner radius (default 20%)
    """
    print(f"Creating {size}x{size} icon...")

    # Open the original image
    img = Image.open(input_path)

    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Find the main icon content (crop out excess dark space)
    # We'll focus on the center rounded square portion
    width, height = img.size

    # Calculate crop box to focus on the rounded square icon
    # The actual icon appears to be roughly centered with some padding
    crop_margin = int(width * 0.15)  # 15% margin from edges
    crop_box = (
        crop_margin,           # left
        crop_margin,           # top
        width - crop_margin,   # right
        height - crop_margin   # bottom
    )

    # Crop to focus on main icon
    img_cropped = img.crop(crop_box)

    # Resize to target size with high-quality resampling
    img_resized = img_cropped.resize((size, size), Image.Resampling.LANCZOS)

    # Calculate corner radius
    corner_radius = int(size * (corner_radius_percent / 100))

    # Create rounded mask
    mask = create_rounded_rectangle_mask((size, size), corner_radius)

    # Create output image with transparency
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    # Apply the mask to create rounded corners
    output.paste(img_resized, (0, 0))
    output.putalpha(mask)

    # Save the icon
    output.save(output_path, 'PNG', optimize=True)
    print(f"✅ Saved: {output_path}")

    return output

def create_square_icon(input_path, output_path, size):
    """
    Create a square icon without rounded corners (for maskable icons)
    iOS and Android will apply their own masks
    """
    print(f"Creating {size}x{size} square icon (maskable)...")

    # Open the original image
    img = Image.open(input_path)

    # Convert to RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Crop to focus on main content
    width, height = img.size
    crop_margin = int(width * 0.15)
    crop_box = (crop_margin, crop_margin, width - crop_margin, height - crop_margin)
    img_cropped = img.crop(crop_box)

    # Resize to target size
    img_resized = img_cropped.resize((size, size), Image.Resampling.LANCZOS)

    # Add some padding for safe area (20% padding)
    padded_size = size
    padding = int(size * 0.1)  # 10% padding on each side

    # Create a new image with padding
    output = Image.new('RGBA', (padded_size, padded_size), (0, 0, 0, 0))

    # Calculate position to center the icon with padding
    paste_size = size - (padding * 2)
    img_with_padding = img_resized.resize((paste_size, paste_size), Image.Resampling.LANCZOS)

    # Paste centered
    output.paste(img_with_padding, (padding, padding), img_with_padding)

    # Save
    output.save(output_path, 'PNG', optimize=True)
    print(f"✅ Saved: {output_path}")

    return output

def main():
    """Generate all required PWA icons"""

    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(script_dir, 'static')
    input_image = os.path.join(static_dir, 'inspec.JPG')

    # Check if input exists
    if not os.path.exists(input_image):
        print(f"❌ Error: {input_image} not found!")
        return

    print("🎨 Creating PWA icons from Inspec logo...")
    print(f"📁 Input: {input_image}")
    print(f"📁 Output: {static_dir}/\n")

    # Standard PWA icon sizes
    icon_sizes = [
        (72, 'icon-72.png'),
        (96, 'icon-96.png'),
        (128, 'icon-128.png'),
        (144, 'icon-144.png'),
        (152, 'icon-152.png'),
        (192, 'icon-192.png'),
        (384, 'icon-384.png'),
        (512, 'icon-512.png'),
    ]

    # Create rounded corner icons (for display)
    print("\n📦 Creating display icons (with rounded corners):")
    for size, filename in icon_sizes:
        output_path = os.path.join(static_dir, filename)
        create_rounded_rectangle_mask_icon(input_image, output_path, size, corner_radius_percent=22)

    # Create maskable icons (square with safe area padding)
    print("\n📦 Creating maskable icons (for adaptive icons):")
    maskable_sizes = [
        (192, 'icon-192-maskable.png'),
        (512, 'icon-512-maskable.png'),
    ]

    for size, filename in maskable_sizes:
        output_path = os.path.join(static_dir, filename)
        create_square_icon(input_image, output_path, size)

    # Create apple-touch-icon (180x180 for iOS)
    print("\n🍎 Creating Apple Touch Icon:")
    apple_icon_path = os.path.join(static_dir, 'apple-touch-icon.png')
    create_rounded_rectangle_mask_icon(input_image, apple_icon_path, 180, corner_radius_percent=22)

    # Create favicon sizes
    print("\n🌐 Creating Favicons:")
    favicon_sizes = [
        (16, 'favicon-16x16.png'),
        (32, 'favicon-32x32.png'),
    ]

    for size, filename in favicon_sizes:
        output_path = os.path.join(static_dir, filename)
        create_rounded_rectangle_mask_icon(input_image, output_path, size, corner_radius_percent=20)

    print("\n✅ All icons created successfully!")
    print("\nNext steps:")
    print("1. Update manifest.json with new icon sizes")
    print("2. Add apple-touch-icon meta tag to HTML")
    print("3. Test on iOS and Android devices")

def create_rounded_rectangle_mask_icon(input_path, output_path, size, corner_radius_percent):
    """Helper function that combines the logic"""
    return create_pwa_icon(input_path, output_path, size, corner_radius_percent)

if __name__ == '__main__':
    main()
