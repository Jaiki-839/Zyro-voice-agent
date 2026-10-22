"""
assets/generate_icon.py -- generates high-resolution icon and assets for ZYRO.
Creates both PNG and ICO (containing 16x16, 32x32, 48x48, 64x64, 128x128, 256x256).
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

def create_zyro_icon(size: int = 512) -> Image.Image:
    # High-res canvas with RGBA
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size / 2.0
    radius = size * 0.46

    # 1. Outer subtle glow circle
    glow_radius = radius * 1.04
    draw.ellipse(
        [center - glow_radius, center - glow_radius, center + glow_radius, center + glow_radius],
        fill=(16, 185, 129, 45) # emerald glow
    )

    # 2. Main background dark circular tile
    # Gradient simulation from deep obsidian #0B1120 to dark cyan #0F2338
    steps = 40
    for i in range(steps):
        r_step = radius * (1.0 - (i / float(steps)) * 0.95)
        factor = i / float(steps)
        r = int(11 + factor * 14)
        g = int(17 + factor * 26)
        b = int(32 + factor * 48)
        draw.ellipse([center - r_step, center - r_step, center + r_step, center + r_step], fill=(r, g, b, 255))

    # 3. Outer border ring (Emerald Cyan gradient style)
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        outline=(16, 185, 129, 230),
        width=int(size * 0.035)
    )

    # 4. Stylized "Z" voice waveform in the center
    # Draw futuristic neon soundwave / glowing Z shape
    cyan = (6, 182, 212, 255)
    emerald = (16, 185, 129, 255)
    white = (240, 253, 250, 255)

    # Central pulsing core orb
    core_r = size * 0.18
    draw.ellipse([center - core_r, center - core_r, center + core_r, center + core_r], fill=(16, 185, 129, 180))
    inner_r = size * 0.12
    draw.ellipse([center - inner_r, center - inner_r, center + inner_r, center + inner_r], fill=(6, 182, 212, 230))
    center_dot = size * 0.06
    draw.ellipse([center - center_dot, center - center_dot, center + center_dot, center + center_dot], fill=white)

    # Audio Waveform bars across the center
    bar_count = 9
    bar_width = int(size * 0.035)
    spacing = int(size * 0.065)
    total_w = (bar_count - 1) * spacing
    start_x = center - total_w / 2.0

    heights = [0.22, 0.38, 0.58, 0.78, 0.95, 0.78, 0.58, 0.38, 0.22]
    max_h = size * 0.45

    for idx, (h_ratio) in enumerate(heights):
        bx = start_x + idx * spacing
        bh = max_h * h_ratio
        top_y = center - bh / 2.0
        bot_y = center + bh / 2.0
        
        # Color gradient across bars
        t = idx / (bar_count - 1)
        r = int(16 * (1 - t) + 6 * t)
        g = int(185 * (1 - t) + 182 * t)
        b = int(129 * (1 - t) + 212 * t)
        
        # Rounded capsule bar
        draw.line([(bx, top_y), (bx, bot_y)], fill=(r, g, b, 240), width=bar_width)
        # Cap dots
        cap_r = bar_width // 2
        draw.ellipse([bx - cap_r, top_y - cap_r, bx + cap_r, top_y + cap_r], fill=(220, 252, 231, 255))
        draw.ellipse([bx - cap_r, bot_y - cap_r, bx + cap_r, bot_y + cap_r], fill=(220, 252, 231, 255))

    return img

def main():
    assets_dir = Path(__file__).resolve().parent
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    img = create_zyro_icon(512)
    png_path = assets_dir / "zyro.png"
    ico_path = assets_dir / "zyro.ico"
    
    img.save(png_path, format="PNG")
    print(f"Saved {png_path}")
    
    # Generate multi-size icon for Windows
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Saved {ico_path}")

if __name__ == "__main__":
    main()
