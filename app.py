import os
import sys
import json
import threading
import subprocess
import webbrowser
from datetime import datetime
from typing import Dict, Any, List, Optional
import webview

from downloader import DownloaderEngine, BatchQueueEngine, CancelledException
from security_guard import perform_startup_security_check
from licensing import (
    get_machine_hwid,
    load_and_validate_current_license,
    activate_key_directly,
    revoke_license
)
from utils import (
    get_default_download_dir,
    get_base_dir,
    get_resource_path,
    get_app_data_path,
    load_history_db,
    save_history_db,
    load_settings_db,
    save_settings_db,
    format_bytes,
    categorize_file
)

BASE_DIR = get_base_dir()
ICON_PATH = get_resource_path(os.path.join("assets", "app_icon.ico"))
HTML_PATH = get_resource_path(os.path.join("ui", "index.html"))


class DownloaderApi:
    """Python API exposed to the JavaScript Web UI via PyWebView bridge."""
    def __init__(self):
        self._window: Optional[webview.Window] = None
        self.downloader = DownloaderEngine()
        self.queue_engine = BatchQueueEngine(self.downloader)
        self.settings = load_settings_db()
        self.history_items = load_history_db()
        self.is_licensed, self.license_info, self.license_status_msg = load_and_validate_current_license()

        # Apply settings
        self.downloader.set_network_options(
            browser_cookies=self.settings.get("browser_cookies", "none"),
            proxy_url=self.settings.get("proxy", "")
        )
        try:
            self.downloader.set_speed_limit(float(self.settings.get("speed_limit", "0")))
        except Exception:
            pass

    def set_window(self, window: webview.Window):
        self._window = window

    def get_app_info(self) -> Dict[str, Any]:
        """Return app metadata, HWID, license info for UI initialization."""
        self.is_licensed, self.license_info, self.license_status_msg = load_and_validate_current_license()
        rem_days = self.license_info.get("remaining_days_str", "28 Days Remaining" if self.is_licensed else "Not Activated")
        from updater import CURRENT_APP_VERSION
        return {
            "app_version": CURRENT_APP_VERSION,
            "hwid": get_machine_hwid(),
            "is_licensed": self.is_licensed,
            "license_remaining": rem_days,
            "license_key": self.license_info.get("key", ""),
            "license_plan": self.license_info.get("plan", "PRO VIP"),
            "license_expiry": self.license_info.get("expiry_date", ""),
            "save_dir": self.settings.get("save_dir", get_default_download_dir()),
            "speed_limit": self.settings.get("speed_limit", "0"),
            "browser_cookies": self.settings.get("browser_cookies", "none")
        }

    def get_history(self) -> List[Dict[str, Any]]:
        """Return persistent download history."""
        self.history_items = load_history_db()
        return self.history_items

    def delete_history_item(self, path: str, delete_file: bool = True) -> Dict[str, Any]:
        """Delete an item from history and optionally delete the file from disk."""
        self.history_items = load_history_db()
        deleted_from_disk = False
        error_msg = ""

        # Safely remove file from disk if requested
        if delete_file and path:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    deleted_from_disk = True
            except Exception as e:
                error_msg = str(e)

        # Remove from persistent history database (match normalized paths)
        norm_target = os.path.normpath(path) if path else ""
        self.history_items = [
            it for it in self.history_items
            if os.path.normpath(it.get("path", "")) != norm_target
        ]
        save_history_db(self.history_items)

        return {
            "success": True,
            "deleted_file": deleted_from_disk,
            "error": error_msg,
            "history": self.history_items
        }

    def clear_all_history(self) -> List[Dict[str, Any]]:
        """Clear all download history."""
        self.history_items = []
        save_history_db(self.history_items)
        return []

    def open_save_folder(self):
        """Open default save directory in Windows Explorer."""
        folder = self.settings.get("save_dir", get_default_download_dir())
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    def open_file(self, path: str):
        """Open a downloaded file with default OS application."""
        if path and os.path.exists(path):
            os.startfile(path)

    def get_clipboard(self) -> str:
        """Get text from system clipboard."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            txt = root.clipboard_get()
            root.destroy()
            return str(txt)
        except Exception:
            return ""

    def activate_key(self, key: str) -> Dict[str, Any]:
        """Activate a cryptographic license key."""
        ok, msg, details = activate_key_directly(key)
        if ok:
            self.is_licensed = True
            self.license_info = details
            return {"valid": True, "message": msg, "details": details}
        return {"valid": False, "message": msg}

    def inspect_url(self, url: str) -> Dict[str, Any]:
        """Inspect video URL and fetch live thumbnail and metadata."""
        if not url or len(url.strip()) < 5:
            return {"success": False}
        try:
            info = self.downloader.fetch_url_info(url.strip())
            return {"success": True, "info": info}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def start_download(self, url: str, preset: str, options: dict):
        """Start downloading in a dedicated background thread."""
        if not self.is_licensed:
            self.is_licensed, self.license_info, _ = load_and_validate_current_license()
            if not self.is_licensed:
                if self._window:
                    self._window.evaluate_js("alert('Please activate your license first!');")
                return

        threading.Thread(target=self._download_worker, args=(url, preset, options), daemon=True).start()

    def _download_worker(self, url: str, preset: str, options: dict):
        cached_meta = {'thumbnail': '', 'title': '', 'duration': 0}

        # 1. Instantly fetch live cover thumbnail & title
        try:
            meta = self.downloader.fetch_url_info(url)
            if meta:
                cached_meta['thumbnail'] = meta.get('thumbnail', '')
                cached_meta['title'] = meta.get('title', '')
                cached_meta['duration'] = meta.get('duration', 0)
                if self._window and cached_meta['thumbnail']:
                    dur_sec = cached_meta['duration']
                    dur_str = f"{int(dur_sec//60):02d}:{int(dur_sec%60):02d}" if dur_sec > 0 else "00:00"
                    init_payload = {
                        'percent': 5.0,
                        'percent_str': "5.0%",
                        'speed_str': "Connecting to Stream Server...",
                        'eta_str': "Calculating...",
                        'downloaded_str': "0 B",
                        'total_str': "Calculating...",
                        'title': cached_meta['title'] or "Downloading Media...",
                        'thumbnail': cached_meta['thumbnail'],
                        'duration_str': dur_str,
                        'status': 'downloading'
                    }
                    self._window.evaluate_js(f"window.updateDownloadProgress({json.dumps(init_payload)});")
        except Exception:
            pass

        def progress_cb(data):
            if self._window:
                spd_bytes = data.get('speed', 0) or 0
                eta_sec = data.get('eta', 0) or 0
                dl_bytes = data.get('downloaded_bytes', 0) or 0
                tot_bytes = data.get('total_bytes', 0) or 0
                pct = data.get('percent', 0.0) or 0.0

                if spd_bytes >= 1024 * 1024:
                    speed_str = f"{spd_bytes / (1024 * 1024):.2f} MB/s"
                elif spd_bytes >= 1024:
                    speed_str = f"{spd_bytes / 1024:.1f} KB/s"
                else:
                    speed_str = f"{spd_bytes} B/s"

                if eta_sec and eta_sec > 0 and eta_sec < 86400:
                    mins = int(eta_sec // 60)
                    secs = int(eta_sec % 60)
                    eta_str = f"{mins:02d}:{secs:02d}"
                else:
                    eta_str = "--:--"

                thumb = data.get('thumbnail') or cached_meta['thumbnail']
                vid_title = data.get('title') or data.get('filename') or cached_meta['title'] or 'Downloading Media...'
                dur_sec = data.get('duration') or cached_meta['duration']
                dur_str = f"{int(dur_sec//60):02d}:{int(dur_sec%60):02d}" if dur_sec > 0 else eta_str

                payload = {
                    'percent': round(pct, 1),
                    'percent_str': f"{pct:.1f}%",
                    'speed_str': speed_str,
                    'eta_str': eta_str,
                    'downloaded_str': format_bytes(dl_bytes),
                    'total_str': format_bytes(tot_bytes) if tot_bytes > 0 else "Calculating...",
                    'title': vid_title,
                    'thumbnail': thumb,
                    'duration_str': dur_str,
                    'status': data.get('status', 'downloading')
                }
                safe_json = json.dumps(payload)
                self._window.evaluate_js(f"window.updateDownloadProgress({safe_json});")

        try:
            self.downloader.reset_cancel()
            res = self.downloader.download(
                url=url,
                output_dir=self.settings.get("save_dir", get_default_download_dir()),
                quality=preset,
                progress_callback=progress_cb,
                download_subs=options.get("subtitles", False),
                bitrate=options.get("bitrate", "320k"),
                trim_start=options.get("trim_start", ""),
                trim_end=options.get("trim_end", "")
            )

            # Record to history with cover thumbnail
            item = {
                "filename": res.get("filename", "Media File"),
                "path": res.get("path", ""),
                "size": format_bytes(res.get("size", 0)),
                "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "category": categorize_file(res.get("filename", "")),
                "url": url,
                "thumbnail": res.get("thumbnail", "") or cached_meta['thumbnail']
            }
            self.history_items.insert(0, item)
            save_history_db(self.history_items)

            if self._window:
                safe_res = json.dumps(res)
                self._window.evaluate_js(f"window.onDownloadComplete({safe_res});")

        except CancelledException:
            if self._window:
                self._window.evaluate_js("window.onDownloadCancelled();")
        except Exception as e:
            if self._window:
                err_msg = json.dumps(str(e))
                self._window.evaluate_js(f"window.onDownloadError({err_msg});")

    def toggle_pause(self):
        """Pause or resume download."""
        if getattr(self.downloader, '_is_paused', False):
            self.downloader.resume()
        else:
            self.downloader.pause()

    def cancel_download(self):
        """Cancel current download."""
        self.downloader.cancel()

    def check_for_updates(self) -> Dict[str, Any]:
        """Check remote server for software updates."""
        from updater import updater
        custom_feed = self.settings.get("update_feed_url", "")
        return updater.check_for_updates(custom_feed if custom_feed else None)

    def start_download_update(self, download_url: str, expected_sha256: str = ""):
        """Download new version update in background thread with live progress."""
        from updater import updater
        
        def _update_worker():
            def progress_cb(data):
                if self._window:
                    safe_json = json.dumps(data)
                    self._window.evaluate_js(f"window.onUpdateDownloadProgress({safe_json});")

            try:
                target_path = updater.download_update_executable(
                    download_url=download_url,
                    expected_sha256=expected_sha256,
                    progress_callback=progress_cb
                )
                if self._window:
                    res = json.dumps({"success": True, "file_path": target_path})
                    self._window.evaluate_js(f"window.onUpdateDownloadComplete({res});")
            except Exception as e:
                if self._window:
                    err = json.dumps(str(e))
                    self._window.evaluate_js(f"window.onUpdateDownloadError({err});")

        threading.Thread(target=_update_worker, daemon=True).start()

    def install_update_and_restart(self, new_exe_path: str):
        """Execute the downloaded update executable and terminate current process."""
        from updater import updater
        updater.launch_update_and_exit(new_exe_path)


def main():
    # 1. Perform Zero-Trust Enterprise Security & Anti-Tamper Check
    sec_ok, sec_msg = perform_startup_security_check()
    if not sec_ok:
        print(f"[SECURITY ALERT]: {sec_msg}")
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"⚠️ Security Protection Violation:\n\n{sec_msg}", "SKD CyberGuard", 0x10)
        except Exception:
            pass
        sys.exit(1)

    api = DownloaderApi()
    
    # Check if UI HTML exists
    if not os.path.exists(HTML_PATH):
        print(f"[ERROR] UI file not found at: {HTML_PATH}")
        sys.exit(1)

    window = webview.create_window(
        title="SKD TOOL - Ultimate Media Downloader",
        url=HTML_PATH,
        js_api=api,
        width=1260,
        height=860,
        min_size=(1100, 750),
        background_color="#060913",
        text_select=False
    )
    api.set_window(window)
    
    # Start PyWebView native window with security lockdown
    webview.start(debug=False)


if __name__ == "__main__":
    main()
