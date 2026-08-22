"""
=============================================================================
SKD TOOL - REMOTE AUTO-UPDATE & VERSION MANAGEMENT ENGINE (ENTERPRISE)
=============================================================================
Provides remote version checking, cryptographic checksum verification,
mandatory/optional update policies, changelog inspection, and live in-app update installation.
"""

import os
import sys
import json
import time
import hashlib
import requests
import tempfile
import subprocess
from typing import Dict, Any, Optional, Tuple, Callable

# Current Software Release Version
CURRENT_APP_VERSION = "1.1.0"

# Default Update Feed Endpoint (Your GitHub Repository)
DEFAULT_UPDATE_FEED_URL = "https://raw.githubusercontent.com/ksuyvisal-a11y/tool-download/main/update.json"
LOCAL_FALLBACK_UPDATE_PATH = os.path.join(
    os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)),
    "update.json"
)

def parse_semver(ver_str: str) -> Tuple[int, int, int]:
    """Parse version strings like '1.2.3' or 'v1.2.3' into (major, minor, patch)."""
    clean = ver_str.strip().lower().lstrip('v')
    parts = clean.split('.')
    try:
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2].split('-')[0]) if len(parts) > 2 else 0
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
    def __init__(self, current_version: str = CURRENT_APP_VERSION):
        self.current_version = current_version
        self.cached_update_info: Optional[Dict[str, Any]] = None
        self._is_downloading = False

    def check_for_updates(self, custom_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the remote update server for the latest version and changelog.
        Returns update details dict.
        """
        feed_url = custom_url or DEFAULT_UPDATE_FEED_URL
        data: Optional[Dict[str, Any]] = None

        # 1. Try Remote HTTP/HTTPS Endpoint
        try:
            headers = {
                'User-Agent': f'SKD_TOOL_CLIENT/{self.current_version} (Windows NT 10.0; Win64; x64)',
                'Accept': 'application/json'
            }
            resp = requests.get(feed_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
        except Exception:
            pass

        # 2. Fallback to Local/Peer update.json if remote server is unreachable
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
                "error": "Could not connect to update server."
            }

        latest_version = data.get("version", self.current_version)
        has_new = is_newer_version(latest_version, self.current_version)
        mandatory = bool(data.get("mandatory", False) or data.get("force_update", False))

        result = {
            "has_update": has_new,
            "current_version": self.current_version,
            "latest_version": latest_version,
            "release_date": data.get("release_date", "Recently"),
            "mandatory": mandatory,
            "changelog": data.get("changelog", [
                "Performance optimizations and speed improvements",
                "New user interface enhancements",
                "Core stability and bug fixes"
            ]),
            "download_url": data.get("download_url", ""),
            "sha256": data.get("sha256", "").lower(),
            "file_size": data.get("file_size", "Unknown"),
            "title": data.get("title", f"SKD TOOL v{latest_version} Release")
        }

        self.cached_update_info = result
        return result

    def download_update_executable(
        self,
        download_url: str,
        expected_sha256: str = "",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> str:
        """
        Download the new release executable with live progress reporting and SHA-256 verification.
        Returns the path to the downloaded update executable.
        """
        self._is_downloading = True
        
        # Determine destination temporary file
        temp_dir = tempfile.gettempdir()
        file_ext = ".exe"
        target_filename = f"SKD_TOOL_Update_{int(time.time())}{file_ext}"
        target_path = os.path.join(temp_dir, target_filename)

        # Check if download_url is a local file path
        if os.path.exists(download_url):
            import shutil
            shutil.copy(download_url, target_path)
            if progress_callback:
                progress_callback({"percent": 100.0, "status": "completed", "file_path": target_path})
            return target_path

        # Stream download over HTTP/HTTPS
        headers = {
            'User-Agent': f'SKD_TOOL_UPDATER/{self.current_version}'
        }
        try:
            resp = requests.get(download_url, headers=headers, stream=True, timeout=25)
            if resp.status_code == 404:
                raise Exception(f"File not found on server (404 Not Found).\nPlease make sure you have uploaded SKD_TOOL.exe to your download URL:\n{download_url}")
            resp.raise_for_status()
        except requests.exceptions.RequestException as req_err:
            raise Exception(f"Failed to connect to update server: {req_err}")

        total_bytes = int(resp.headers.get('Content-Length', 0))
        downloaded = 0
        start_time = time.time()
        last_update = start_time

        with open(target_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    elapsed = now - last_update

                    if elapsed >= 0.2 or downloaded == total_bytes:
                        pct = (downloaded / total_bytes * 100.0) if total_bytes > 0 else 0.0
                        spd = (downloaded / (now - start_time)) if (now - start_time) > 0 else 0
                        if progress_callback:
                            progress_callback({
                                "percent": round(pct, 1),
                                "downloaded": downloaded,
                                "total": total_bytes,
                                "speed": spd,
                                "status": "downloading"
                            })
                        last_update = now

        self._is_downloading = False

        # Verify SHA-256 Checksum if provided
        if expected_sha256:
            actual_hash = compute_file_sha256(target_path)
            if actual_hash != expected_sha256.lower().strip():
                try: os.remove(target_path)
                except Exception: pass
                raise Exception("Cryptographic Checksum Mismatch! The update package may be corrupted.")

        if progress_callback:
            progress_callback({"percent": 100.0, "status": "completed", "file_path": target_path})

        return target_path

    def launch_update_and_exit(self, new_exe_path: str):
        """
        Launch the new version and gracefully close current process.
        """
        if not os.path.exists(new_exe_path):
            raise Exception("Downloaded update file not found.")

        # Launch the new process detached
        if sys.platform == "win32":
            subprocess.Popen([new_exe_path], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            subprocess.Popen([new_exe_path])

        # Terminate current process
        sys.exit(0)


# Global Singleton Update Engine
updater = UpdateEngine()
