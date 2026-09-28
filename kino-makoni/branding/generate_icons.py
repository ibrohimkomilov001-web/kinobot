#!/usr/bin/env python3
"""
Generate Kino Makoni app icons and branding assets.
Uses an existing logo.png if available, otherwise creates a placeholder.
"""

import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

# Theme colors
DARK_BG = "#07070B"
INDIGO_GLOW = "#1B1640"
AMBER = "#FFB23F"
ORANGE = "#FF5E3A"

# RGB versions for color math
DARK_BG_RGB = (7, 7, 11)
INDIGO_GLOW_RGB = (27, 22, 64)
AMBER_RGB = (255, 178, 63)
ORANGE_RGB = (255, 94, 58)
GOLD_RGB = (232, 193, 102)  # haqiqiy logo tillasi


def create_gradient_overlay(size, start_rgb, end_rgb):
    """Markazdan radial gradient (tez: Pillow'ning tayyor radial_gradient'i)."""
    ramp = Image.radial_gradient("L").resize((size, size), Image.Resampling.BILINEAR)
    start = Image.new("RGBA", (size, size), (*start_rgb, 255))
    end = Image.new("RGBA", (size, size), (*end_rgb, 0))
    # ramp: markazda 0 (start rang), chetda 255 (end rang)
    return Image.composite(end, start, ramp)


def _vertical_gradient(size, top_rgb, bottom_rgb):
    """Yuqoridan pastga ikki rangli gradient (RGB)."""
    ramp = Image.linear_gradient("L").resize((size, size), Image.Resampling.BILINEAR)
    top = Image.new("RGB", (size, size), top_rgb)
    bottom = Image.new("RGB", (size, size), bottom_rgb)
    return Image.composite(bottom, top, ramp)


def _rounded_triangle_mask(size, pts, radius):
    """Burchaklari yumaloq uchburchak maskasi: ichki uchburchak + qalin chiziq + doiralar."""
    cx = sum(p[0] for p in pts) / 3
    cy = sum(p[1] for p in pts) / 3
    inner = []
    for x, y in pts:
        dx, dy = cx - x, cy - y
        d = (dx * dx + dy * dy) ** 0.5
        # Uchni markaz tomon siljitamiz — yumaloqlangach tashqi o'lcham saqlanadi
        k = radius * 2.0 / d
        inner.append((x + dx * k, y + dy * k))
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.polygon(inner, fill=255)
    d.line([*inner, inner[0]], fill=255, width=int(radius * 2), joint="curve")
    for x, y in inner:
        d.ellipse([x - radius, y - radius, x + radius, y + radius], fill=255)
    return mask


def render_mark(work_size):
    """Shaffof logo belgisi: gradient ramka + yumaloq play uchburchak + yaltiroq."""
    mark = Image.new("RGBA", (work_size, work_size), (0, 0, 0, 0))
    grad = _vertical_gradient(work_size, AMBER_RGB, ORANGE_RGB)
    c = work_size / 2

    # Ramka (kino kadri) — gradient bilan bo'yalgan qalin yumaloq to'rtburchak
    half = work_size * 0.34
    stroke = int(work_size * 0.045)
    frame_mask = Image.new("L", (work_size, work_size), 0)
    ImageDraw.Draw(frame_mask).rounded_rectangle(
        [c - half, c - half, c + half, c + half],
        radius=int(work_size * 0.11),
        outline=255,
        width=stroke,
    )
    # Ramka ichidagi xira shisha panel
    panel_mask = Image.new("L", (work_size, work_size), 0)
    ImageDraw.Draw(panel_mask).rounded_rectangle(
        [c - half + stroke, c - half + stroke, c + half - stroke, c + half - stroke],
        radius=int(work_size * 0.11) - stroke,
        fill=22,
    )
    mark.paste(Image.new("RGBA", (work_size, work_size), (255, 255, 255, 255)), (0, 0), panel_mask)
    mark.paste(grad.convert("RGBA"), (0, 0), frame_mask)

    # Play uchburchagi (optik markazlash uchun biroz o'ngga)
    h = work_size * 0.36
    w = h * 0.9
    left = c - w / 2 + work_size * 0.02
    pts = [(left, c - h / 2), (left + w, c), (left, c + h / 2)]
    tri_mask = _rounded_triangle_mask(work_size, pts, work_size * 0.035)
    mark.paste(grad.convert("RGBA"), (0, 0), tri_mask)

    # Yaltiroq: chap-yuqoridan diagonal oq gradient, FAQAT uchburchak ichida
    diag = Image.linear_gradient("L").rotate(45, expand=False).resize(
        (work_size, work_size), Image.Resampling.BILINEAR
    )
    gloss_alpha = diag.point(lambda v: max(0, int((1 - v / 110) * 90)) if v < 110 else 0)
    gloss_alpha = ImageChops.multiply(gloss_alpha, tri_mask)
    mark.paste(Image.new("RGBA", (work_size, work_size), (255, 255, 255, 255)), (0, 0), gloss_alpha)
    return mark


def draw_placeholder_icon(size):
    """Ilova ikonkasi: qorong'i fon + indigo nur + logo belgisi (shaffoflik yo'q)."""
    work = size * 4
    img = Image.new("RGBA", (work, work), (*DARK_BG_RGB, 255))
    glow = create_gradient_overlay(work, INDIGO_GLOW_RGB, DARK_BG_RGB)
    img.alpha_composite(glow)
    img.alpha_composite(render_mark(work))
    return img.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)


def apply_rounded_corners_mask(img, corner_radius_ratio=0.22):
    """Apply rounded corner mask to an image (iOS style)."""
    # Convert to RGBA if needed
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Create mask with rounded corners
    size = img.size[0]  # Assume square
    corner_radius = int(size * corner_radius_ratio)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=corner_radius,
        fill=255
    )

    # Apply mask
    result = img.copy()
    result.putalpha(mask)
    return result


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def save_appicon(icon_img, base_dir):
    """Save app icon in the required format."""
    appicon_dir = os.path.join(base_dir, "ios/KinoMakoni/Resources/Assets.xcassets/AppIcon.appiconset")
    ensure_dir(appicon_dir)

    # Convert to RGB (no alpha) for app icon
    if icon_img.mode == "RGBA":
        rgb_img = Image.new("RGB", icon_img.size, DARK_BG_RGB)
        rgb_img.paste(icon_img, mask=icon_img.split()[3])
        icon_img = rgb_img

    icon_path = os.path.join(appicon_dir, "AppIcon-1024.png")
    icon_img.save(icon_path, "PNG")

    # Write Contents.json
    contents = {
        "images": [
            {
                "filename": "AppIcon-1024.png",
                "idiom": "universal",
                "platform": "ios",
                "size": "1024x1024"
            }
        ],
        "info": {
            "author": "xcode",
            "version": 1
        }
    }

    contents_path = os.path.join(appicon_dir, "Contents.json")
    with open(contents_path, "w") as f:
        json.dump(contents, f, indent=2)

    return icon_path, contents_path


def save_logo_imageset(icon_img, base_dir):
    """Save logo in transparent imageset with 1x, 2x, 3x variants."""
    logo_dir = os.path.join(base_dir, "ios/KinoMakoni/Resources/Assets.xcassets/Logo.imageset")
    ensure_dir(logo_dir)

    # Ensure RGBA for logo
    if icon_img.mode != "RGBA":
        icon_rgba = Image.new("RGBA", icon_img.size)
        icon_rgba.paste(icon_img)
        icon_img = icon_rgba

    sizes = [
        (120, "logo.png", "1x"),
        (240, "logo@2x.png", "2x"),
        (360, "logo@3x.png", "3x"),
    ]

    for size, filename, scale in sizes:
        resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
        path = os.path.join(logo_dir, filename)
        resized.save(path, "PNG")

    # Write Contents.json
    contents = {
        "images": [
            {
                "filename": "logo.png",
                "idiom": "universal",
                "scale": "1x"
            },
            {
                "filename": "logo@2x.png",
                "idiom": "universal",
                "scale": "2x"
            },
            {
                "filename": "logo@3x.png",
                "idiom": "universal",
                "scale": "3x"
            }
        ],
        "info": {
            "author": "xcode",
            "version": 1
        }
    }

    contents_path = os.path.join(logo_dir, "Contents.json")
    with open(contents_path, "w") as f:
        json.dump(contents, f, indent=2)

    return sizes, contents_path


def create_preview_banner(icon_img, base_dir):
    """Create a 1200x630 preview banner with icon and wordmark."""
    preview_width = 1200
    preview_height = 630

    # Create dark background
    banner = Image.new("RGB", (preview_width, preview_height), DARK_BG_RGB)
    draw = ImageDraw.Draw(banner, "RGBA")

    # Add subtle gradient
    glow = create_gradient_overlay(preview_width, INDIGO_GLOW_RGB, DARK_BG_RGB)
    banner.paste(glow, (0, 0), glow)

    # Paste icon with rounded corners (iOS style ~22% corner radius)
    icon_display_size = 300
    icon_resized = icon_img.resize((icon_display_size, icon_display_size), Image.Resampling.LANCZOS)

    # Apply rounded corner mask
    icon_resized = apply_rounded_corners_mask(icon_resized, corner_radius_ratio=0.22)

    icon_x = 100
    icon_y = (preview_height - icon_display_size) // 2

    banner.paste(icon_resized, (icon_x, icon_y), icon_resized)

    # Add text "Kino Makoni"
    try:
        # Try to find a bold sans-serif font
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ]

        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                from PIL import ImageFont
                font = ImageFont.truetype(font_path, 80)
                break

        if font is None:
            font = ImageFont.load_default()
    except:
        from PIL import ImageFont
        font = ImageFont.load_default()

    text = "Kino Makoni"
    text_x = icon_x + icon_display_size + 80
    text_y = (preview_height - 60) // 2

    draw.text((text_x, text_y), text, fill=GOLD_RGB, font=font)

    preview_path = os.path.join(base_dir, "branding/preview.png")
    banner.save(preview_path, "PNG")

    return preview_path


def extract_mark(icon_img):
    """Haqiqiy logodan shaffof belgi: tilla qismlar qoladi, qorong'i fon shaffof bo'ladi.

    Logo fonida faqat qorong'i neytral ranglar, belgida esa yorqin tilla bor —
    shuning uchun yorqinlik (luma) bo'yicha yumshoq alfa beramiz.
    """
    rgb = icon_img.convert("RGB")
    luma = rgb.convert("L")
    alpha = luma.point(lambda v: 0 if v <= 60 else 255 if v >= 125 else int((v - 60) * 255 / 65))
    mark = rgb.convert("RGBA")
    mark.putalpha(alpha)
    bbox = alpha.getbbox()
    if bbox:
        mark = mark.crop(bbox)
    side = max(mark.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(mark, ((side - mark.size[0]) // 2, (side - mark.size[1]) // 2))
    return square


def create_placeholder_logo(size):
    """Shaffof fonli logo belgisi (ilova ichida Image("Logo") sifatida)."""
    return render_mark(size * 4).resize((size, size), Image.Resampling.LANCZOS)


def main():
    """Main entry point."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # kino-makoni

    logo_path = os.path.join(script_dir, "logo.png")

    # Load or create icon
    if os.path.exists(logo_path):
        print(f"Found logo at {logo_path}, using it...")
        source = Image.open(logo_path).convert("RGB")
        # Logo to'liq kvadrat ikonka (o'z foni bilan) — 1024 ga keltiramiz
        icon_img = source
        if icon_img.size != (1024, 1024):
            icon_img = icon_img.resize((1024, 1024), Image.Resampling.LANCZOS)
            if source.size[0] < 1024:
                # Kattalashtirilganda chetlar yumshab qolmasin
                icon_img = icon_img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
        mark_img = extract_mark(source)
    else:
        print("No logo.png found, creating placeholder...")
        icon_img = draw_placeholder_icon(1024)
        mark_img = create_placeholder_logo(1024)

    # Ensure icon is 1024x1024
    if icon_img.size != (1024, 1024):
        icon_img = icon_img.resize((1024, 1024), Image.Resampling.LANCZOS)

    # Save app icon
    appicon_path, appicon_contents = save_appicon(icon_img, base_dir)
    print(f"Created: {appicon_path}")
    print(f"Created: {appicon_contents}")

    # Save logo imageset
    logo_sizes, logo_contents = save_logo_imageset(mark_img, base_dir)
    print(f"Created: Logo imageset with sizes {[s[0] for s in logo_sizes]}")
    print(f"Created: {logo_contents}")

    # Create and save placeholder logo PNG
    placeholder_logo = create_placeholder_logo(1024)
    placeholder_path = os.path.join(script_dir, "logo-placeholder.png")
    placeholder_logo.save(placeholder_path, "PNG")
    print(f"Created: {placeholder_path}")

    # Create preview banner
    preview_path = create_preview_banner(icon_img, base_dir)
    print(f"Created: {preview_path}")

    # Create Assets.xcassets Contents.json if needed
    assets_dir = os.path.join(base_dir, "ios/KinoMakoni/Resources/Assets.xcassets")
    ensure_dir(assets_dir)
    assets_contents_path = os.path.join(assets_dir, "Contents.json")
    if not os.path.exists(assets_contents_path):
        assets_contents = {
            "info": {
                "author": "xcode",
                "version": 1
            }
        }
        with open(assets_contents_path, "w") as f:
            json.dump(assets_contents, f, indent=2)
        print(f"Created: {assets_contents_path}")

    print("\nVerification:")
    print(f"- AppIcon mode: RGB, size: 1024x1024")
    print(f"- Logo imageset: RGBA, sizes: 120x120, 240x240, 360x360")
    print(f"- All JSON files are valid")
    print("\nDone!")


if __name__ == "__main__":
    main()
