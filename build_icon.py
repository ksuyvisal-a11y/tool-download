import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

PNG_CANDIDATES = [
    os.path.join(ASSETS_DIR, "skd_logo_clean.png"),
    os.path.join(ASSETS_DIR, "skd_logo.png")
]

ICO_PATH = os.path.join(ASSETS_DIR, "app_icon.ico")

def generate_ico():
    source_png = None
    for p in PNG_CANDIDATES:
        if os.path.exists(p):
            source_png = p
            break
            
    if not source_png:
        print("❌ No source PNG found in assets directory!")
        return False
        
    try:
        img = Image.open(source_png)
        # Convert RGBA
        img = img.convert("RGBA")
        
        # Create square icon with transparent padding if needed
        w, h = img.size
        max_dim = max(w, h)
        square_img = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
        offset_x = (max_dim - w) // 2
        offset_y = (max_dim - h) // 2
        square_img.paste(img, (offset_x, offset_y), img)
        
        icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        square_img.save(ICO_PATH, format="ICO", sizes=icon_sizes)
        print(f"[OK] Generated Windows Icon at: {ICO_PATH}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to generate .ico: {e}")
        return False

if __name__ == "__main__":
    generate_ico()
