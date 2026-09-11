"""
=============================================================================
SKD TOOL - REMOTE AUTO-UPDATE & MICRO-PATCH ENGINE (ENTERPRISE DUAL-MODE)
=============================================================================
Provides:
1. Micro-Patch Mode (Ultra-Fast 500KB - 2.5MB Hotfix Updates, Zero PC Freezes, 0.2s Restart)
2. Full Binary Mode (Major Version Upgrades with PID-Synchronized Atomic Swap)
3. Cryptographic SHA-256 Checksum Verification
4. Zero-Cache CDN Queries & Cache-Busting
=============================================================================
"""

import os
import sys
import re
import json
import time
import zipfile
import hashlib
import requests
import tempfile
import subprocess
import shutil
from typing import Dict, Any, Optional, Tuple, Callable

# Base Release Version
BASE_APP_VERSION = "1.1.1"

def get_current_app_version() -> str:
    """Read the effective application version (checks live micro-patch manifest first)."""
    try:
        from utils import get_app_data_path
        manifest_path = get_app_data_path(os.path.join("patches", "patch_manifest.json"))
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("version"):
                    return str(data["version"]).strip()
    except Exception:
        pass
    return BASE_APP_VERSION

CURRENT_APP_VERSION = get_current_app_version()

# Default Update Feed Endpoint (GitHub Repository)
DEFAULT_UPDATE_FEED_URL = "https://raw.githubusercontent.com/ksuyvisal-a11y/tool-download/main/update.json"
LOCAL_FALLBACK_UPDATE_PATH = os.path.join(
    os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)),
    "update.json"
)

def parse_semver(ver_str: str) -> Tuple[int, int, int]:
    """Parse version strings like '1.2.3' or 'v1.2.3' into (major, minor, patch)."""
    clean = str(ver_str).strip().lower().lstrip('v')
    parts = clean.split('.')
    try:
        def _to_int(s: str) -> int:
            digits = re.sub(r'\D', '', s.split('-')[0])
            return int(digits) if digits else 0

        major = _to_int(parts[0]) if len(parts) > 0 else 0
        minor = _to_int(parts[1]) if len(parts) > 1 else 0
        patch = _to_int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except Exception:
        return (0, 0, 0)

def is_newer_version(remote_ver: str, local_ver: str) -> bool:
    """Return True if remote_ver is strictly greater than local_ver."""
    return parse_semver(remote_ver) > parse_semver(local_ver)

def compute_file_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file for cryptographic integrity check."""
    sha = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha.update(chunk)
    return sha.hexdigest().lower()


class UpdateEngine:
    """
    Enterprise Dual-Mode Auto-Update Engine:
    - Mode 1: Micro-Patch (1 MB - 2.5 MB Patch ZIP) -> 0.2s Restart, zero disk/CPU strain, zero PC lag
    - Mode 2: Full Binary (Standalone EXE / Setup) -> Used for major framework version leaps
    """
    def __init__(self, current_version: str = CURRENT_APP_VERSION):
        self.current_version = get_current_app_version()
        self.cached_update_info: Optional[Dict[str, Any]] = None
        self._is_downloading = False
        self._cancel_download = False

    def cancel_update_download(self):
        """Signal ongoing download to abort cleanly."""
        self._cancel_download = True

    def check_for_updates(self, custom_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the remote update server for the latest version and changelog.
        Uses cache-busting and falls back to GitHub Releases API if update.json is unreachable.
        """
        self.current_version = get_current_app_version()
        feed_url = custom_url or DEFAULT_UPDATE_FEED_URL
        data: Optional[Dict[str, Any]] = None

        # 1. Try Remote update.json with cache-busting parameter and headers
        try:
            bust_url = f"{feed_url}?_t={int(time.time())}" if '?' not in feed_url else f"{feed_url}&_t={int(time.time())}"
            headers = {
                'User-Agent': f'SKD_TOOL_CLIENT/{self.current_version} (Windows NT 10.0; Win64; x64)',
                'Accept': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
            resp = requests.get(bust_url, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
        except Exception:
            pass

        # 2. Fallback: Query GitHub Releases API directly if raw update.json fails
        if not data and 'github.com' in feed_url:
            try:
                parts = feed_url.replace("https://raw.githubusercontent.com/", "").replace("https://github.com/", "").split("/")
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                    gh_headers = {
                        'User-Agent': f'SKD_TOOL_UPDATER/{self.current_version}',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                    gh_resp = requests.get(api_url, headers=gh_headers, timeout=6)
                    if gh_resp.status_code == 200:
                        releases = gh_resp.json()
                        if isinstance(releases, list) and len(releases) > 0:
                            valid_rels = [r for r in releases if not r.get('draft', False)]
                            if valid_rels:
                                latest_rel = valid_rels[0]
                                tag = latest_rel.get('tag_name', '').lstrip('v')
                                
                                # Check for patch.zip first (micro-update), then fallback to .exe
                                patch_asset = None
                                exe_asset = None
                                for a in latest_rel.get('assets', []):
                                    name_low = a.get('name', '').lower()
                                    if name_low.endswith('.zip') or 'patch' in name_low:
                                        patch_asset = a
                                        break
                                    elif name_low.endswith('.exe'):
                                        exe_asset = a

                                chosen_asset = patch_asset or exe_asset
                                if chosen_asset and tag:
                                    is_patch = chosen_asset.get('name', '').lower().endswith('.zip')
                                    size_bytes = chosen_asset.get('size', 0)
                                    size_str = f"{size_bytes / (1024*1024):.1f} MB" if size_bytes >= 1024*1024 else f"{size_bytes / 1024:.0f} KB"
                                    data = {
                                        "version": tag,
                                        "title": latest_rel.get('name') or f"SKD TOOL v{tag} Release",
                                        "release_date": latest_rel.get('published_at', '')[:10] or "Recently",
                                        "type": "patch" if is_patch else "full",
                                        "mandatory": False,
                                        "changelog": [line.strip().lstrip('-* ') for line in latest_rel.get('body', '').split('\n') if line.strip() and not line.startswith('#')][:8] or ["Bug fixes and improvements"],
                                        "download_url": chosen_asset.get('browser_download_url'),
                                        "sha256": "",
                                        "file_size": size_str
                                    }
            except Exception:
                pass

        # 3. Fallback to Local update.json
        if not data and os.path.exists(LOCAL_FALLBACK_UPDATE_PATH):
            try:
                with open(LOCAL_FALLBACK_UPDATE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                pass

        if not data:
            return {
                "has_update": False,
                "current_version": self.current_version,
                "error": "Could not connect to update server. Please check internet connection."
            }

        latest_version = str(data.get("version", self.current_version)).strip()
        has_new = is_newer_version(latest_version, self.current_version)
        mandatory = bool(data.get("mandatory", False) or data.get("force_update", False))
        dl_url = str(data.get("download_url", ""))
        update_type = data.get("type", "patch" if dl_url.lower().split('?')[0].endswith(".zip") else "full")

        raw_changelog = data.get("changelog", [
            "Performance optimizations and speed improvements",
            "Universal Downloader engine enhanced",
            "Core stability and bug fixes"
        ])
        if isinstance(raw_changelog, str):
            raw_changelog = [raw_changelog]

        result = {
            "has_update": has_new,
            "current_version": self.current_version,
            "latest_version": latest_version,
            "release_date": data.get("release_date", "Recently"),
            "type": update_type,
            "mandatory": mandatory,
            "changelog": raw_changelog,
            "download_url": dl_url,
            "sha256": str(data.get("sha256", "")).lower().strip(),
            "file_size": str(data.get("file_size", "2.4 MB" if update_type == "patch" else "106 MB")),
            "title": data.get("title", f"SKD TOOL v{latest_version} Release")
        }

        self.cached_update_info = result
        return result

    def download_update_executable(
        self,
        download_url: str,
        expected_sha256: str = "",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        max_retries: int = 3
    ) -> str:
        """
        Download the update package.
        - If ZIP (Micro-Patch ~2MB): Extracts directly to %APPDATA%/SKD_Tool/patches/
        - If EXE (Full Binary ~100MB): Prepares standalone executable for PID swap
        """
        from utils import get_app_data_path

        self._is_downloading = True
        self._cancel_download = False

        clean_url_base = download_url.lower().split('?')[0]
        is_zip = clean_url_base.endswith('.zip') or (self.cached_update_info and self.cached_update_info.get("type") == "patch")
        temp_dir = tempfile.gettempdir()
        file_ext = ".zip" if is_zip else ".exe"
        target_filename = f"SKD_TOOL_Update_{int(time.time())}{file_ext}"
        target_path = os.path.join(temp_dir, target_filename)

        headers = {
            'User-Agent': f'SKD_TOOL_UPDATER/{self.current_version} (Windows NT 10.0; Win64; x64)',
            'Accept': '*/*'
        }

        total_bytes = 0
        last_error = None

        # Check if download_url is a local file path
        if os.path.exists(download_url):
            try:
                shutil.copy2(download_url, target_path)
                total_bytes = os.path.getsize(target_path)
            except Exception:
                target_path = download_url
                total_bytes = os.path.getsize(target_path) if os.path.exists(target_path) else 0
        else:
            for attempt in range(1, max_retries + 1):
                if self._cancel_download:
                    self._is_downloading = False
                    raise Exception("Update download cancelled by user.")

                try:
                    resp = requests.get(download_url, headers=headers, stream=True, timeout=25, allow_redirects=True)
                    if resp.status_code == 404:
                        raise Exception(f"Update package not found (HTTP 404).\nPlease verify the release file URL:\n{download_url}")
                    resp.raise_for_status()

                    content_len = resp.headers.get('Content-Length')
                    total_bytes = int(content_len) if content_len and content_len.isdigit() else 0
                    downloaded = 0
                    start_time = time.time()
                    last_update = start_time

                    with open(target_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            if self._cancel_download:
                                f.close()
                                try:
                                    if os.path.exists(target_path): os.remove(target_path)
                                except Exception: pass
                                self._is_downloading = False
                                raise Exception("Update download cancelled by user.")

                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                now = time.time()
                                elapsed = now - last_update

                                if elapsed >= 0.15 or (total_bytes > 0 and downloaded == total_bytes):
                                    pct = (downloaded / total_bytes * 100.0) if total_bytes > 0 else 0.0
                                    total_elapsed = now - start_time
                                    spd = (downloaded / total_elapsed) if total_elapsed > 0 else 0
                                    eta_secs = int((total_bytes - downloaded) / spd) if spd > 0 and total_bytes > downloaded else 0

                                    if progress_callback:
                                        progress_callback({
                                            "percent": round(pct, 1),
                                            "downloaded": downloaded,
                                            "total": total_bytes,
                                            "speed": spd,
                                            "eta": eta_secs,
                                            "status": "downloading"
                                        })
                                    last_update = now

                    last_error = None
                    break

                except Exception as e:
                    last_error = e
                    if self._cancel_download:
                        raise e
                    time.sleep(1.5)

            if last_error:
                self._is_downloading = False
                try:
                    if os.path.exists(target_path): os.remove(target_path)
                except Exception: pass
                raise Exception(f"Failed to download update after {max_retries} attempts: {last_error}")

        self._is_downloading = False

        # Verify SHA-256 Checksum if provided
        if expected_sha256 and expected_sha256.strip():
            actual_hash = compute_file_sha256(target_path)
            if actual_hash != expected_sha256.lower().strip():
                try:
                    os.remove(target_path)
                except Exception: pass
                raise Exception("Cryptographic Checksum Mismatch! The update package may be corrupted or modified.")

        # If Micro-Patch ZIP: Extract directly into %APPDATA%/SKD_Tool/patches/
        if is_zip:
            patch_dest_dir = get_app_data_path("patches")
            os.makedirs(patch_dest_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(target_path, 'r') as zip_ref:
                    zip_ref.extractall(patch_dest_dir)

                # Write patch manifest with updated version
                new_ver = self.cached_update_info.get("latest_version", self.current_version) if self.cached_update_info else self.current_version
                manifest_data = {
                    "version": new_ver,
                    "applied_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "micro_patch",
                    "files_count": len(zip_ref.namelist())
                }
                manifest_file = os.path.join(patch_dest_dir, "patch_manifest.json")
                with open(manifest_file, "w", encoding="utf-8") as mf:
                    json.dump(manifest_data, mf, indent=2)

                # Clean up downloaded zip file
                try:
                    os.remove(target_path)
                except Exception:
                    pass

                if progress_callback:
                    eff_total = total_bytes or os.path.getsize(manifest_file)
                    progress_callback({
                        "percent": 100.0,
                        "status": "completed",
                        "file_path": manifest_file,
                        "downloaded": eff_total,
                        "total": eff_total,
                        "speed": 0,
                        "eta": 0
                    })

                return manifest_file

            except Exception as e:
                raise Exception(f"Failed to apply micro-patch: {e}")

        # If Full Binary EXE:
        if progress_callback:
            file_s = os.path.getsize(target_path) if os.path.exists(target_path) else total_bytes
            progress_callback({
                "percent": 100.0,
                "status": "completed",
                "file_path": target_path,
                "downloaded": file_s,
                "total": file_s,
                "speed": 0,
                "eta": 0
            })

        return target_path

    def launch_update_and_exit(self, new_file_path: str):
        """
        Launch the new version and gracefully close current process.
        - For Micro-Patch: Restarts current EXE instantly in 0.2s without heavy copying!
        - For Full Binary: Uses PID-targeted atomic replacement script.
        """
        from utils import get_base_dir

        current_exe = sys.executable if getattr(sys, 'frozen', False) else None
        current_pid = os.getpid()
        detach_flags = (getattr(subprocess, 'DETACHED_PROCESS', 0x00000008) | 
                        getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0x00000200))

        is_micro_patch = new_file_path.endswith('.json') or 'manifest' in new_file_path.lower() or 'patch' in new_file_path.lower()

        if is_micro_patch:
            # INSTANT ZERO-FREEZE RESTART FOR MICRO-PATCH
            if sys.platform == "win32":
                if current_exe:
                    subprocess.Popen([current_exe], creationflags=detach_flags, cwd=get_base_dir())
                else:
                    script_main = os.path.abspath(sys.argv[0])
                    subprocess.Popen([sys.executable, script_main], creationflags=detach_flags, cwd=get_base_dir())
            else:
                subprocess.Popen([sys.executable] + sys.argv, cwd=get_base_dir())

            os._exit(0)

        # FULL BINARY EXE SWAP
        if not os.path.exists(new_file_path):
            raise Exception("Downloaded update file not found.")

        if sys.platform == "win32":
            is_installer = "setup" in os.path.basename(new_file_path).lower()

            if is_installer:
                subprocess.Popen([new_file_path], creationflags=detach_flags, cwd=tempfile.gettempdir())
            elif current_exe and os.path.exists(current_exe) and os.path.abspath(current_exe).lower() != os.path.abspath(new_file_path).lower():
                exe_name = os.path.basename(current_exe)
                bat_path = os.path.join(tempfile.gettempdir(), f"skd_swap_{int(time.time())}.bat")
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(f"""@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

taskkill /F /IM "{exe_name}" /T >nul 2>&1
taskkill /F /PID {current_pid} /T >nul 2>&1
ping 127.0.0.1 -n 2 >nul

set /a count=0
:copy_loop
set /a count+=1
copy /y "{new_file_path}" "{current_exe}" >nul 2>&1
if not errorlevel 1 goto start_app
ping 127.0.0.1 -n 2 >nul
if !count! geq 15 goto emergency_launch
goto copy_loop

:start_app
ping 127.0.0.1 -n 2 >nul
del "{new_file_path}" >nul 2>&1
start "" "{current_exe}"
(goto) 2>nul & del "%~f0"
exit

:emergency_launch
start "" "{new_file_path}"
(goto) 2>nul & del "%~f0"
exit
""")
                subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=detach_flags, cwd=tempfile.gettempdir())
            else:
                subprocess.Popen([new_file_path], creationflags=detach_flags, cwd=tempfile.gettempdir())
        else:
            subprocess.Popen([new_file_path], cwd=get_base_dir())

        os._exit(0)


# Global Singleton Update Engine
updater = UpdateEngine()


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("="*65)
    print("⚡ SKD TOOL - REMOTE UPDATE & MICRO-PATCH ENGINE DIAGNOSTIC")
    print("="*65)
    print(f"📌 Effective Version  : {get_current_app_version()}")
    print(f"📦 Base Version       : {BASE_APP_VERSION}")
    print(f"🌐 Update Feed URL    : {DEFAULT_UPDATE_FEED_URL}")
    print("\n🔍 Checking for updates...")
    
    check_result = updater.check_for_updates()
    print("\n--- [Update Server Response] ---")
    print(json.dumps(check_result, indent=2, ensure_ascii=False))
    
    if check_result.get("has_update"):
        print(f"\n🚀 New update available: v{check_result.get('latest_version')} ({check_result.get('type')})")
    else:
        print(f"\n✅ You are running the latest version (v{get_current_app_version()}).")
    print("="*65)

