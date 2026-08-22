import os
import shutil
from PIL import Image, ImageDraw

BRAIN_DIR = r"C:\Users\M\.gemini\antigravity-ide\brain\85c13d51-741d-46a7-9832-da8a9ad280aa"
ASSETS_DIR = r"d:\Sal\tool download\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

# Find generated files in brain dir
cloud_files = [f for f in os.listdir(BRAIN_DIR) if f.startswith("cloud_glow_3d") and f.endswith(".jpg")]
play_files = [f for f in os.listdir(BRAIN_DIR) if f.startswith("play_cube_glow_3d") and f.endswith(".jpg")]
thumb_files = [f for f in os.listdir(BRAIN_DIR) if f.startswith("default_thumbnail") and f.endswith(".jpg")]

# Process Cloud Glow
if cloud_files:
    src_cloud = os.path.join(BRAIN_DIR, cloud_files[-1])
    img = Image.open(src_cloud).convert("RGBA")
    # Resize to 240x240
    img = img.resize((240, 240), Image.Resampling.LANCZOS)
    out_cloud = os.path.join(ASSETS_DIR, "cloud_glow.png")
    img.save(out_cloud, "PNG")
    print(f"[OK] Saved: {out_cloud}")

# Process Play Cube Glow
if play_files:
    src_play = os.path.join(BRAIN_DIR, play_files[-1])
    img = Image.open(src_play).convert("RGBA")
    # Resize to 140x140
    img = img.resize((140, 140), Image.Resampling.LANCZOS)
    out_play = os.path.join(ASSETS_DIR, "play_cube.png")
    img.save(out_play, "PNG")
    print(f"[OK] Saved: {out_play}")

# Process Default Thumbnail
if thumb_files:
    src_thumb = os.path.join(BRAIN_DIR, thumb_files[-1])
    img = Image.open(src_thumb).convert("RGBA")
    # Create 16:9 thumbnail with rounded corners and overlay play button
    tw, th = 200, 115
    img = img.resize((tw, th), Image.Resampling.LANCZOS)
    
    # Draw play button in center
    draw = ImageDraw.Draw(img)
    cx, cy = tw // 2, th // 2
    r = 20
    # Semi-transparent dark circle
    overlay = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, 160), outline=(255, 255, 255, 200), width=2)
    # White triangle
    tri_s = 9
    ov_draw.polygon([
        (cx - int(tri_s * 0.7), cy - tri_s),
        (cx - int(tri_s * 0.7), cy + tri_s),
        (cx + tri_s, cy)
    ], fill=(255, 255, 255, 240))
    
    img = Image.alpha_composite(img, overlay)
    out_thumb = os.path.join(ASSETS_DIR, "default_thumb.png")
    img.save(out_thumb, "PNG")
    print(f"[OK] Saved: {out_thumb}")
