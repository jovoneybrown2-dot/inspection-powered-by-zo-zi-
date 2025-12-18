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

def create_pwa_icon(input_path, output_path, size, corner_radius_percent=8):
    """
    Create a PWA icon with slightly rounded corners (square with soft edges)

    Args:
        input_path: Path to input image (inspec.JPG)
        output_path: Path to save output icon
        size: Size in pixels (e.g., 192, 512)
        corner_radius_percent: Percentage of size to use for corner radius (default 8% for slight curve)
    """
    print(f"Creating {size}x{size} icon...")

    # Open the original image
    img = Image.open(input_path)

    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Get original dimensions
    width, height = img.size

    # Focus ONLY on the square icon content (remove circular magnifying glass frame)
    # Crop very tight to show just the square with icons inside
    # The actual square content is roughly from 28% to 72% of the image
    crop_margin_horizontal = int(width * 0.28)   # 28% from left/right - removes circular frame
    crop_margin_vertical = int(height * 0.25)     # 25% from top - removes top of circular frame
    crop_margin_bottom = int(height * 0.38)       # 38% from bottom - removes magnifying glass handle

    crop_box = (
        crop_margin_horizontal,              # left
        crop_margin_vertical,                # top
        width - crop_margin_horizontal,      # right
        height - crop_margin_bottom          # bottom
    )

    # Crop to the square icon portion
    img_cropped = img.crop(crop_box)

    # Make it square (in case crop wasn't perfectly square)
    crop_width = crop_box[2] - crop_box[0]
    crop_height = crop_box[3] - crop_box[1]
    square_size = min(crop_width, crop_height)

    # Center crop to square
    if crop_width > crop_height:
        diff = crop_width - crop_height
        img_cropped = img_cropped.crop((diff // 2, 0, crop_width - diff // 2, crop_height))
    elif crop_height > crop_width:
        diff = crop_height - crop_width
        img_cropped = img_cropped.crop((0, diff // 2, crop_width, crop_height - diff // 2))

    # Resize to target size with high-quality resampling
    img_resized = img_cropped.resize((size, size), Image.Resampling.LANCZOS)

    # Calculate corner radius (8% = slight curve, not too rounded)
    corner_radius = int(size * (corner_radius_percent / 100))

    # Create rounded mask with slight curves
    mask = create_rounded_rectangle_mask((size, size), corner_radius)

    # Create output image with dark background (matching the icon style)
    output = Image.new('RGBA', (size, size), (26, 26, 46, 255))  # Dark blue-gray background

    # Apply the mask to create slightly rounded corners
    output.paste(img_resized, (0, 0), img_resized)
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

    # Create square icons with slightly curved edges (for display)
    print("\n📦 Creating display icons (square with slightly curved edges):")
    for size, filename in icon_sizes:
        output_path = os.path.join(static_dir, filename)
        create_rounded_rectangle_mask_icon(input_image, output_path, size, corner_radius_percent=8)

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
    create_rounded_rectangle_mask_icon(input_image, apple_icon_path, 180, corner_radius_percent=8)

    # Create favicon sizes
    print("\n🌐 Creating Favicons:")
    favicon_sizes = [
        (16, 'favicon-16x16.png'),
        (32, 'favicon-32x32.png'),
    ]

    for size, filename in favicon_sizes:
        output_path = os.path.join(static_dir, filename)
        create_rounded_rectangle_mask_icon(input_image, output_path, size, corner_radius_percent=8)

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
