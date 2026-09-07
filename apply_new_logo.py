import os
import shutil
from PIL import Image

SRC_IMAGE = r"C:\Users\M\.gemini\antigravity-ide\brain\85c13d51-741d-46a7-9832-da8a9ad280aa\.user_uploaded\media_1787190864446.png"

TOOL_ASSETS = r"d:\Sal\tool download\assets"
WEB_ASSETS = r"d:\Sal\Website\Website\assets"

os.makedirs(TOOL_ASSETS, exist_ok=True)
os.makedirs(WEB_ASSETS, exist_ok=True)

def process_and_deploy_logo():
    if not os.path.exists(SRC_IMAGE):
        print(f"[ERROR] Source image not found at {SRC_IMAGE}")
        return False
        
    img = Image.open(SRC_IMAGE).convert("RGBA")
    
    # 1. Crop to bounding box of non-transparent content
    bbox = img.getbbox()
    if bbox:
        img_cropped = img.crop(bbox)
    else:
        img_cropped = img
        
    cw, ch = img_cropped.size
    print(f"[INFO] Cropped logo content dimensions: {cw}x{ch}")
    
    # 2. Create Square Master Image (Transparent)
    max_side = max(cw, ch)
    # Add 8% padding
    pad = int(max_side * 0.08)
    square_side = max_side + (pad * 2)
    
    master_square = Image.new("RGBA", (square_side, square_side), (0, 0, 0, 0))
    paste_x = (square_side - cw) // 2
    paste_y = (square_side - ch) // 2
    master_square.paste(img_cropped, (paste_x, paste_y), img_cropped)
    
    # 3. Save Clean PNGs for Tool Download
    clean_png_path = os.path.join(TOOL_ASSETS, "skd_logo_clean.png")
    master_square.save(clean_png_path, "PNG")
    print(f"[OK] Saved: {clean_png_path}")
    
    logo_png_path = os.path.join(TOOL_ASSETS, "skd_logo.png")
    master_square.save(logo_png_path, "PNG")
    print(f"[OK] Saved: {logo_png_path}")
    
    # 4. Generate Multi-Resolution Windows ICO
    ico_path = os.path.join(TOOL_ASSETS, "app_icon.ico")
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    master_square.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"[OK] Generated Windows ICO: {ico_path}")
    
    # 5. Save Clean Web Logo
    web_logo_path = os.path.join(WEB_ASSETS, "app_logo.png")
    master_square.save(web_logo_path, "PNG")
    print(f"[OK] Saved: {web_logo_path}")
    
    # 6. Generate PWA Icons with Obsidian Glow Background
    for size, name in [(512, "icon-512.png"), (192, "icon-192.png"), (64, "favicon-64.png")]:
        pwa_bg = Image.new("RGBA", (size, size), (11, 16, 28, 255))
        
        # Resize master logo
        logo_res_size = int(size * 0.82)
        resized_logo = master_square.resize((logo_res_size, logo_res_size), Image.Resampling.LANCZOS)
        
        pos_x = (size - logo_res_size) // 2
        pos_y = (size - logo_res_size) // 2
        pwa_bg.paste(resized_logo, (pos_x, pos_y), resized_logo)
        
        out_pwa = os.path.join(WEB_ASSETS, name)
        pwa_bg.save(out_pwa, "PNG")
        print(f"[OK] Saved PWA Icon ({size}x{size}): {out_pwa}")
        
    return True

if __name__ == "__main__":
    process_and_deploy_logo()
