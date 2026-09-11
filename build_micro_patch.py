"""
=============================================================================
SKD TOOL - 1-CLICK MICRO-PATCH GENERATOR (~800 KB ULTRA-FAST UPDATE)
=============================================================================
Packages updated python modules and UI files into dist/patch.zip and updates update.json.
"""

import os
import sys
import json
import zipfile
import hashlib
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def compute_sha256(file_path: str) -> str:
    sha = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha.update(chunk)
    return sha.hexdigest().lower()

def format_bytes(size: float) -> str:
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.2f} MB"

def create_micro_patch():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    update_json_path = os.path.join(base_dir, "update.json")
    if os.path.exists(update_json_path):
        with open(update_json_path, 'r', encoding='utf-8') as f:
            update_data = json.load(f)
    else:
        update_data = {"version": "1.1.1"}

    ver = update_data.get("version", "1.1.1")
    print(f"📦 Packaging Micro-Patch for SKD TOOL v{ver}...")

    patch_zip_path = os.path.join(dist_dir, "patch.zip")
    if os.path.exists(patch_zip_path):
        try:
            os.remove(patch_zip_path)
        except Exception:
            pass

    # Core Python files to include in micro-patch
    python_files = [
        "downloader.py",
        "app.py",
        "utils.py",
        "updater.py",
        "converter.py",
        "scheduler.py",
        "i18n.py",
        "licensing.py",
        "security_guard.py"
    ]

    # Directories to include (UI, assets)
    include_dirs = ["ui", "assets"]

    with zipfile.ZipFile(patch_zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        # Add python scripts
        for pf in python_files:
            full_p = os.path.join(base_dir, pf)
            if os.path.exists(full_p):
                zipf.write(full_p, arcname=pf)
                print(f"  + Added: {pf}")

        # Add UI and assets
        for d in include_dirs:
            full_d = os.path.join(base_dir, d)
            if os.path.exists(full_d):
                for root, _, files in os.walk(full_d):
                    for file in files:
                        if file.endswith(('.pyc', '.tmp', '.log')):
                            continue
                        f_path = os.path.join(root, file)
                        rel_path = os.path.relpath(f_path, base_dir)
                        zipf.write(f_path, arcname=rel_path)
                        print(f"  + Added: {rel_path}")

    patch_size = os.path.getsize(patch_zip_path)
    patch_size_str = format_bytes(patch_size)
    patch_hash = compute_sha256(patch_zip_path)

    print("\n" + "="*60)
    print(f"✅ Micro-Patch Created Successfully!")
    print(f"📍 Location : {patch_zip_path}")
    print(f"📊 Size     : {patch_size_str} (Super Lightweight!)")
    print(f"🔑 SHA-256  : {patch_hash}")
    print("="*60)

    # Update update.json metadata
    update_data["type"] = "patch"
    update_data["file_size"] = patch_size_str
    update_data["sha256"] = patch_hash
    update_data["download_url"] = f"https://github.com/ksuyvisal-gmail-com/tool-download/releases/download/{ver}/patch.zip"

    with open(update_json_path, 'w', encoding='utf-8') as f:
        json.dump(update_data, f, indent=2, ensure_ascii=False)

    dist_update_json = os.path.join(dist_dir, "update.json")
    with open(dist_update_json, 'w', encoding='utf-8') as f:
        json.dump(update_data, f, indent=2, ensure_ascii=False)

    print(f"📝 Updated update.json with Micro-Patch metadata.")
    print("\n👉 Upload 'dist/patch.zip' and 'update.json' to your GitHub Release.")

if __name__ == "__main__":
    create_micro_patch()
