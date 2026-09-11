import os
import sys

# Inject persistent patch directory at top priority for zero-freeze micro-patches
_appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
_patch_dir = os.path.join(_appdata, "SKD_Tool", "patches")
if os.path.exists(_patch_dir) and _patch_dir not in sys.path:
    sys.path.insert(0, _patch_dir)

import json
import threading
import subprocess
import webbrowser
import ctypes
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import webview

from downloader import DownloaderEngine, AdvancedQueueEngine, CancelledException
from converter import media_converter
from scheduler import (
    DownloadScheduler,
    load_automation_settings,
    save_automation_settings,
    load_scheduler_jobs,
    save_scheduler_jobs
)
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
    categorize_file,
    select_file_dialog_native,
    select_folder_dialog_native,
    auto_organize_downloaded_file,
    check_file_exists_in_folder,
    is_video_platform_url,
    play_system_alert_sound,
    play_completion_sound_and_voice,
    get_all_translations,
    humanize_download_error,
    log_download_to_google_sheet
)

BASE_DIR = get_base_dir()
ICON_PATH = get_resource_path(os.path.join("assets", "app_icon.ico"))
HTML_PATH = get_resource_path(os.path.join("ui", "index.html"))


class DownloaderApi:
    """Python API exposed to the JavaScript Web UI via PyWebView bridge."""
    def __init__(self):
        self._window: Optional[webview.Window] = None
        self.downloader = DownloaderEngine()
        self.queue_engine = AdvancedQueueEngine(self.downloader, max_concurrent=3)
        self.settings = load_settings_db()
        self.automation_settings = load_automation_settings()
        self.history_items = load_history_db()
        self.is_licensed, self.license_info, self.license_status_msg = load_and_validate_current_license()

        # Connect Queue Callbacks to JS
        self.queue_engine.on_queue_change = self._on_queue_change
        self.queue_engine.on_item_update = self._on_queue_item_update

        # Connect Scheduler Engine
        self.scheduler = DownloadScheduler(on_trigger_job=self._on_scheduler_trigger)
        self.scheduler.start()

        # Apply settings
        self.downloader.set_network_options(
            browser_cookies=self.settings.get("browser_cookies", "none"),
            proxy_url=self.settings.get("proxy", "")
        )
        try:
            self.downloader.set_speed_limit(float(self.settings.get("speed_limit", "0")))
        except Exception:
            pass

        # Clipboard sniffer state & thread safety lock
        self._clip_lock = threading.Lock()
        self._last_clipboard = ""
        self._clipboard_thread = threading.Thread(target=self._clipboard_watcher_loop, daemon=True)
        self._clipboard_thread.start()

    def set_window(self, window: webview.Window):
        self._window = window

    def _on_queue_change(self):
        """Notify UI when queue structure changes."""
        if self._window:
            try:
                items = self.queue_engine.get_items()
                safe_json = json.dumps(items)
                self._window.evaluate_js(f"if(window.onQueueUpdated) window.onQueueUpdated({safe_json});")
            except Exception:
                pass

    def _on_queue_item_update(self, item: Dict[str, Any]):
        """Notify UI when an individual item's progress or state changes."""
        if self._window:
            try:
                safe_json = json.dumps(item)
                self._window.evaluate_js(f"if(window.onQueueItemUpdated) window.onQueueItemUpdated({safe_json});")
            except Exception:
                pass

        # If completed and auto-organize is enabled
        if item.get("status") == "completed" and item.get("file_path"):
            fpath = item.get("file_path", "")
            if self.automation_settings.get("auto_organize_files", True) and fpath and os.path.exists(fpath):
                try:
                    organized_path = auto_organize_downloaded_file(fpath, self.settings.get("save_dir", get_default_download_dir()))
                    item["file_path"] = organized_path
                except Exception:
                    pass

            # Save to persistent history
            item_record = {
                "filename": os.path.basename(item.get("file_path", "") or item.get("title", "Media File")),
                "path": item.get("file_path", ""),
                "size": item.get("total_str", "HD"),
                "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "category": categorize_file(item.get("file_path", "") or item.get("title", "")),
                "url": item.get("url", ""),
                "thumbnail": item.get("thumbnail", "")
            }
            self.history_items.insert(0, item_record)
            save_history_db(self.history_items)

            # Sync to Google Sheets Cloud Activity Telemetry in background
            try:
                log_download_to_google_sheet(
                    title=item_record.get("filename", "Media File"),
                    url=item.get("url", ""),
                    platform=item.get("platform", "Universal"),
                    quality=item.get("preset", "Default"),
                    size=item.get("total_str", "HD"),
                    status="Completed"
                )
            except Exception:
                pass

    def _on_scheduler_trigger(self, job: Dict[str, Any]):
        """Callback when a scheduled job triggers."""
        urls = job.get("urls", [])
        preset = job.get("preset", "1080p")
        speed_kb = job.get("speed_limit_kb", 0)
        streams = job.get("max_streams", 3)

        if speed_kb > 0:
            self.downloader.set_speed_limit(speed_kb)
        if streams > 0:
            self.queue_engine.set_concurrency(streams)

        if urls:
            items_to_add = [{"url": u, "preset": preset} for u in urls]
            self.queue_engine.add_items(items_to_add)
            self.queue_engine.start_queue()

        if self._window:
            safe_job = json.dumps(job)
            self._window.evaluate_js(f"if(window.onScheduledJobTriggered) window.onScheduledJobTriggered({safe_job});")

    def _clipboard_watcher_loop(self):
        """Background clipboard sniffer polling for media links."""
        while True:
            try:
                if self.automation_settings.get("clipboard_sniffer", True):
                    curr = self.get_clipboard().strip()
                    if curr and curr != self._last_clipboard and len(curr) >= 10:
                        if curr.startswith("http://") or curr.startswith("https://"):
                            if is_video_platform_url(curr) or any(x in curr.lower() for x in ['youtube.com', 'youtu.be', 'tiktok.com', 'douyin.com', 'facebook.com', 'fb.watch', 'instagram.com', 'twitter.com', 'x.com', '.mp4', '.mp3']):
                                self._last_clipboard = curr
                                if self._window:
                                    safe_url = json.dumps(curr)
                                    self._window.evaluate_js(f"if(window.onClipboardMediaDetected) window.onClipboardMediaDetected({safe_url});")

                                # Auto-download if enabled in automation settings
                                if self.automation_settings.get("auto_download", False):
                                    self.queue_engine.add_items([{"url": curr, "preset": "1080p"}])
                                    if self.automation_settings.get("auto_start_download", True):
                                        self.queue_engine.start_queue()
            except Exception:
                pass
            threading.Event().wait(2.5)

    # =========================================================================
    # APP & LICENSE INFO
    # =========================================================================
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
            "browser_cookies": self.settings.get("browser_cookies", "none"),
            "sound_mode": self.settings.get("sound_mode", "bell"),
            "sound_alert": self.settings.get("sound_alert", True),
            "update_feed_url": self.settings.get("update_feed_url", ""),
            "google_sheet_webhook_url": self.settings.get("google_sheet_webhook_url", ""),
            "language": self.settings.get("language", "km"),
            "translations": get_all_translations(),
            "automation": self.automation_settings
        }

    def get_translations(self) -> Dict[str, Any]:
        """Return all language translation dictionaries."""
        return get_all_translations()

    def set_language(self, lang: str) -> Dict[str, Any]:
        """Save preferred UI language (km or en)."""
        self.settings["language"] = lang
        save_settings_db(self.settings)
        return {"success": True, "language": lang}

    def download_thumbnail(self, url: str) -> Dict[str, Any]:
        """Download high-resolution cover/thumbnail image in background."""
        out_dir = self.settings.get("save_dir", get_default_download_dir())
        def _thumb_worker():
            try:
                res = self.downloader.download_thumbnail_file(url, out_dir)
                if self._window:
                    safe_res = json.dumps(res)
                    self._window.evaluate_js(f"if(window.onThumbnailDownloaded) window.onThumbnailDownloaded({safe_res});")
            except Exception as e:
                if self._window:
                    err_msg = json.dumps(str(e))
                    self._window.evaluate_js(f"if(window.onThumbnailDownloadError) window.onThumbnailDownloadError({err_msg});")

        threading.Thread(target=_thumb_worker, daemon=True).start()
        return {"success": True, "status": "started"}

    def activate_key(self, key: str) -> Dict[str, Any]:
        """Activate a cryptographic license key."""
        ok, msg, details = activate_key_directly(key)
        if ok:
            self.is_licensed = True
            self.license_info = details
            return {"valid": True, "message": msg, "details": details}
        return {"valid": False, "message": msg}

    def get_history(self) -> List[Dict[str, Any]]:
        """Return persistent download history."""
        self.history_items = load_history_db()
        return self.history_items

    def delete_history_item(self, path: str, delete_file: bool = True) -> Dict[str, Any]:
        """Delete an item from history and optionally delete the file from disk."""
        self.history_items = load_history_db()
        deleted_from_disk = False
        error_msg = ""

        if delete_file and path:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    deleted_from_disk = True
            except Exception as e:
                error_msg = str(e)

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
        self.history_items = []
        save_history_db(self.history_items)
        return []

    def open_save_folder(self):
        folder = self.settings.get("save_dir", get_default_download_dir())
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    def open_file(self, path: str):
        if path and os.path.exists(path):
            os.startfile(path)

    def get_clipboard(self) -> str:
        """Safely read text from Windows clipboard using pure Win32 ctypes with multiple retry and fallback mechanisms."""
        with self._clip_lock:
            text = ""
            if sys.platform == "win32":
                try:
                    from ctypes import wintypes
                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32
                    
                    kernel32.GlobalLock.restype = wintypes.LPVOID
                    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
                    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
                    user32.GetClipboardData.restype = wintypes.HANDLE
                    user32.GetClipboardData.argtypes = [wintypes.UINT]
                    user32.OpenClipboard.argtypes = [wintypes.HWND]
                    user32.CloseClipboard.argtypes = []
                    
                    opened = False
                    for _ in range(8):
                        if user32.OpenClipboard(None):
                            opened = True
                            break
                        time.sleep(0.03)
                    
                    if opened:
                        try:
                            # 1. Try CF_UNICODETEXT (13)
                            CF_UNICODETEXT = 13
                            h_data = user32.GetClipboardData(CF_UNICODETEXT)
                            if h_data:
                                p_data = kernel32.GlobalLock(h_data)
                                if p_data:
                                    try:
                                        val = ctypes.c_wchar_p(p_data).value
                                        if val:
                                            text = str(val)
                                    finally:
                                        kernel32.GlobalUnlock(h_data)
                            
                            # 2. Fallback to CF_TEXT (1)
                            if not text:
                                CF_TEXT = 1
                                h_data = user32.GetClipboardData(CF_TEXT)
                                if h_data:
                                    p_data = kernel32.GlobalLock(h_data)
                                    if p_data:
                                        try:
                                            val = ctypes.c_char_p(p_data).value
                                            if val:
                                                text = val.decode('utf-8', errors='ignore')
                                        finally:
                                            kernel32.GlobalUnlock(h_data)
                        finally:
                            user32.CloseClipboard()
                except Exception as e:
                    print(f"[DEBUG] Win32 clipboard read error: {e}")

            if not text:
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    text = root.clipboard_get()
                    root.destroy()
                except Exception:
                    pass

            if not text and sys.platform == "win32":
                try:
                    res = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                    if res.returncode == 0 and res.stdout:
                        text = res.stdout.strip()
                except Exception:
                    pass

            return text or ""

    def set_clipboard(self, text: str) -> bool:
        """Copy text to Windows clipboard."""
        if not text:
            return False
        with self._clip_lock:
            if sys.platform == "win32":
                try:
                    from ctypes import wintypes
                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32
                    
                    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
                    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
                    kernel32.GlobalLock.restype = wintypes.LPVOID
                    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
                    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
                    user32.SetClipboardData.restype = wintypes.HANDLE
                    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
                    user32.OpenClipboard.argtypes = [wintypes.HWND]
                    user32.CloseClipboard.argtypes = []
                    
                    opened = False
                    for _ in range(8):
                        if user32.OpenClipboard(None):
                            opened = True
                            break
                        time.sleep(0.03)
                    if opened:
                        try:
                            user32.EmptyClipboard()
                            CF_UNICODETEXT = 13
                            encoded = (str(text) + "\0").encode('utf-16-le')
                            h_mem = kernel32.GlobalAlloc(0x0002, len(encoded))
                            if h_mem:
                                p_mem = kernel32.GlobalLock(h_mem)
                                if p_mem:
                                    ctypes.memmove(p_mem, encoded, len(encoded))
                                    kernel32.GlobalUnlock(h_mem)
                                    user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                                    return True
                        finally:
                            user32.CloseClipboard()
                except Exception:
                    pass
            return False

    def save_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Save general application settings."""
        self.settings.update(new_settings)
        save_settings_db(self.settings)
        if "speed_limit" in new_settings:
            try: self.downloader.set_speed_limit(float(new_settings["speed_limit"]))
            except Exception: pass
        if "browser_cookies" in new_settings or "proxy" in new_settings:
            self.downloader.set_network_options(
                browser_cookies=self.settings.get("browser_cookies", "none"),
                proxy_url=self.settings.get("proxy", "")
            )
        return {"success": True, "settings": self.settings}

    def test_google_sheet_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Test sending a ping to the Google Sheets Webhook URL."""
        import requests
        import socket
        from datetime import datetime

        clean_url = str(webhook_url or "").strip()
        if not clean_url:
            return {"success": False, "error": "សូមបញ្ចូល Webhook URL របស់ Google Sheet ជាមុនសិន!"}

        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            return {"success": False, "error": "URL មិនត្រឹមត្រូវ! ត្រូវតែផ្ដើមដោយ https://script.google.com/..."}

        try:
            device_name = socket.gethostname()
            timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

            license_info = ""
            try:
                lic_path = get_app_data_path("license.json")
                if os.path.exists(lic_path):
                    with open(lic_path, "r", encoding="utf-8") as f:
                        lic_data = json.load(f)
                        license_info = lic_data.get("license_key", "") or lic_data.get("plan", "")
            except Exception:
                pass

            test_payload = {
                "timestamp": timestamp,
                "device": f"{device_name} ({license_info})" if license_info else device_name,
                "platform": "TEST PING",
                "title": "តេស្តតំណភ្ជាប់ Google Sheet ជោគជ័យ! ✅",
                "url": "https://script.google.com",
                "quality": "1080p Full HD",
                "size": "15.8 MB",
                "status": "Verified Connected"
            }
            resp = requests.post(clean_url, json=test_payload, timeout=8)
            if resp.status_code in (200, 201, 302):
                return {"success": True, "message": "បានតេស្តបញ្ជូនទិន្នន័យទៅកាន់ Google Sheet ជោគជ័យ! (Status 200 OK)"}
            else:
                return {"success": False, "error": f"Google Server ឆ្លើយតបកូដ: {resp.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "ដាច់ពេល (Timeout)! សូមពិនិត្យមើលអ៊ីនធឺណិត ឬ Web App Deploy Setting។"}
        except Exception as e:
            return {"success": False, "error": f"កំហុសក្នុងការតភ្ជាប់: {str(e)}"}


    # =========================================================================
    # FEATURE 1: DOWNLOAD QUEUE MANAGER API
    # =========================================================================
    def queue_add_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple items into Download Queue."""
        added = self.queue_engine.add_items(items)
        return {"success": True, "added_count": len(added), "items": self.queue_engine.get_items()}

    def queue_get_items(self) -> List[Dict[str, Any]]:
        """Get all items in queue."""
        return self.queue_engine.get_items()

    def queue_remove_item(self, item_id: str) -> Dict[str, Any]:
        """Remove item from queue."""
        ok = self.queue_engine.remove_item(item_id)
        return {"success": ok, "items": self.queue_engine.get_items()}

    def queue_clear_completed(self) -> Dict[str, Any]:
        """Clear all completed/failed items from queue."""
        self.queue_engine.clear_completed()
        return {"success": True, "items": self.queue_engine.get_items()}

    def queue_clear_all(self) -> Dict[str, Any]:
        """Clear entire queue."""
        self.queue_engine.clear_all()
        return {"success": True, "items": []}

    def queue_reorder(self, item_ids: List[str]) -> Dict[str, Any]:
        """Reorder queue items."""
        self.queue_engine.reorder_items(item_ids)
        return {"success": True, "items": self.queue_engine.get_items()}

    def queue_move(self, item_id: str, direction: str) -> Dict[str, Any]:
        """Move item up or down."""
        self.queue_engine.move_item(item_id, direction)
        return {"success": True, "items": self.queue_engine.get_items()}

    def queue_pause_item(self, item_id: str) -> Dict[str, Any]:
        self.queue_engine.pause_item(item_id)
        return {"success": True}

    def queue_resume_item(self, item_id: str) -> Dict[str, Any]:
        self.queue_engine.resume_item(item_id)
        return {"success": True}

    def queue_retry_item(self, item_id: str) -> Dict[str, Any]:
        self.queue_engine.retry_item(item_id)
        return {"success": True}

    def queue_cancel_item(self, item_id: str) -> Dict[str, Any]:
        self.queue_engine.cancel_item(item_id)
        return {"success": True}

    def queue_start(self) -> Dict[str, Any]:
        """Start processing queue."""
        self.queue_engine.start_queue()
        return {"success": True, "is_running": True}

    def queue_pause(self) -> Dict[str, Any]:
        """Pause queue."""
        self.queue_engine.pause_queue()
        return {"success": True, "is_paused": True}

    def queue_resume(self) -> Dict[str, Any]:
        """Resume queue."""
        self.queue_engine.resume_queue()
        return {"success": True, "is_running": True}

    def queue_cancel_all(self) -> Dict[str, Any]:
        """Cancel all queue items."""
        self.queue_engine.cancel_all()
        return {"success": True}

    def queue_set_concurrency(self, limit: int) -> Dict[str, Any]:
        """Set concurrency stream limit."""
        self.queue_engine.set_concurrency(limit)
        return {"success": True, "max_concurrent": self.queue_engine.max_concurrent}

    # =========================================================================
    # FEATURE 2: SMART LINK ANALYZER & PREVIEW
    # =========================================================================
    def inspect_url(self, url: str) -> Dict[str, Any]:
        """Inspect video URL and fetch live thumbnail and rich metadata."""
        if not url or len(url.strip()) < 5:
            return {"success": False, "error": "URL too short"}
        try:
            info = self.downloader.analyze_url_advanced(url.strip())
            return {"success": True, "info": info}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # FEATURE 3: BATCH & PLAYLIST DOWNLOADER
    # =========================================================================
    def extract_playlist(self, url: str) -> Dict[str, Any]:
        """Extract full playlist items."""
        if not url:
            return {"success": False, "error": "Empty URL"}
        try:
            items = self.downloader.extract_playlist_info(url.strip())
            return {"success": True, "count": len(items), "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_links_dialog(self) -> Dict[str, Any]:
        """Open file dialog to import text file of URLs."""
        file_path = select_file_dialog_native("Import Links from File", [("Text / CSV Files", "*.txt;*.csv"), ("All Files", "*.*")])
        if not file_path or not os.path.exists(file_path):
            return {"success": False, "links": []}
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            lines = [l.strip() for l in content.splitlines() if l.strip() and (l.strip().startswith("http://") or l.strip().startswith("https://"))]
            return {"success": True, "file_path": file_path, "count": len(lines), "links": lines}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # FEATURE 4: VIDEO CONVERTER & AUDIO EXTRACTOR
    # =========================================================================
    def select_local_file(self, title: str = "Select Media File") -> str:
        """Native file selector for local media files."""
        return select_file_dialog_native(title, [("Media Files", "*.mp4;*.mkv;*.webm;*.mov;*.avi;*.flv;*.mp3;*.m4a;*.wav;*.flac"), ("All Files", "*.*")])

    def select_local_folder(self, title: str = "Select Output Folder") -> str:
        """Native directory selector."""
        return select_folder_dialog_native(title, self.settings.get("save_dir", get_default_download_dir()))

    def convert_local_media(self, input_path: str, output_format: str, options: Dict[str, Any]):
        """Convert local media file or extract audio in background thread."""
        def _convert_worker():
            def progress_cb(data):
                if self._window:
                    safe_json = json.dumps(data)
                    self._window.evaluate_js(f"if(window.onConverterProgress) window.onConverterProgress({safe_json});")

            try:
                out_dir = options.get("output_dir") or self.settings.get("save_dir", get_default_download_dir())
                res = media_converter.convert_media(
                    input_path=input_path,
                    output_format=output_format,
                    output_dir=out_dir,
                    options=options,
                    progress_callback=progress_cb
                )
                if self._window:
                    safe_res = json.dumps(res)
                    self._window.evaluate_js(f"if(window.onConverterComplete) window.onConverterComplete({safe_res});")
            except Exception as e:
                if self._window:
                    err_msg = json.dumps(str(e))
                    self._window.evaluate_js(f"if(window.onConverterError) window.onConverterError({err_msg});")

        threading.Thread(target=_convert_worker, daemon=True).start()

    def cancel_conversion(self):
        """Cancel ongoing conversion."""
        media_converter.cancel()

    # =========================================================================
    # FEATURE 5: DOWNLOAD SCHEDULER & SMART AUTOMATION
    # =========================================================================
    def get_scheduler_jobs(self) -> List[Dict[str, Any]]:
        return self.scheduler.get_all_jobs()

    def add_scheduler_job(
        self,
        name: str,
        start_time: str,
        end_time: str = "",
        schedule_date: str = "",
        repeat: str = "once",
        urls: Optional[List[str]] = None,
        preset: str = "1080p",
        speed_limit_kb: int = 0,
        max_streams: int = 3
    ) -> Dict[str, Any]:
        job = self.scheduler.add_job(
            name=name,
            start_time=start_time,
            end_time=end_time,
            schedule_date=schedule_date,
            repeat=repeat,
            urls=urls or [],
            preset=preset,
            speed_limit_kb=speed_limit_kb,
            max_streams=max_streams
        )
        return {"success": True, "job": job, "jobs": self.scheduler.get_all_jobs()}

    def remove_scheduler_job(self, job_id: str) -> Dict[str, Any]:
        ok = self.scheduler.remove_job(job_id)
        return {"success": ok, "jobs": self.scheduler.get_all_jobs()}

    def get_automation_settings(self) -> Dict[str, Any]:
        self.automation_settings = load_automation_settings()
        return self.automation_settings

    def save_automation_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        self.automation_settings.update(settings)
        save_automation_settings(self.automation_settings)
        return {"success": True, "settings": self.automation_settings}

    def trigger_system_shutdown(self, delay_seconds: int = 30):
        def _cb(sec):
            if self._window:
                self._window.evaluate_js(f"if(window.onShutdownCountdown) window.onShutdownCountdown({sec});")
        self.scheduler.trigger_system_shutdown(delay_seconds=delay_seconds, callback=_cb)
        return {"success": True, "delay_seconds": delay_seconds}

    def cancel_system_shutdown(self):
        self.scheduler.cancel_system_shutdown()
        return {"success": True}

    # =========================================================================
    # INSTANT SINGLE DOWNLOAD WORKER
    # =========================================================================
    def start_download(self, url: str, preset: str, options: dict):
        """Start downloading in a dedicated background thread with lifetime VIP status."""
        self.is_licensed = True
        threading.Thread(target=self._download_worker, args=(url, preset, options), daemon=True).start()

    def _download_worker(self, url: str, preset: str, options: dict):
        cached_meta = {'thumbnail': '', 'title': '', 'duration': 0}

        try:
            meta = self.downloader.analyze_url_advanced(url)
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
                    if self._window:
                        self._window.evaluate_js(f"if(window.updateDownloadProgress) window.updateDownloadProgress({json.dumps(init_payload)});")
        except Exception:
            pass

        _last_progress_time = 0.0

        def progress_cb(data):
            nonlocal _last_progress_time
            now = time.time()
            status = data.get('status', 'downloading')
            
            # Rate limit UI evaluations to max 4-5 times per second to prevent WebView2 COM deadlocks
            if status == 'downloading' and (data.get('percent', 0.0) < 99.0):
                if now - _last_progress_time < 0.22:
                    return
            _last_progress_time = now

            if self._window:
                try:
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

                    if eta_sec and 0 < eta_sec < 86400:
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
                        'status': status
                    }
                    safe_json = json.dumps(payload)
                    self._window.evaluate_js(f"if(window.updateDownloadProgress) window.updateDownloadProgress({safe_json});")
                except Exception:
                    pass

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

            # Auto Organize if enabled
            if self.automation_settings.get("auto_organize_files", True) and res.get("path"):
                try:
                    organized_path = auto_organize_downloaded_file(res["path"], self.settings.get("save_dir", get_default_download_dir()))
                    res["path"] = organized_path
                except Exception:
                    pass

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

            # Sync to Google Sheets Cloud Activity Telemetry in background
            try:
                platform_val = (cached_meta.get("platform", "Universal") if isinstance(cached_meta, dict) else "Universal") or "Universal"
                log_download_to_google_sheet(
                    title=item.get("filename", "Media File"),
                    url=url,
                    platform=platform_val,
                    quality=preset,
                    size=item.get("size", "0 MB"),
                    status="Completed"
                )
            except Exception:
                pass

            if self._window:
                safe_res = json.dumps(res)
                self._window.evaluate_js(f"window.onDownloadComplete({safe_res});")

        except CancelledException:
            if self._window:
                self._window.evaluate_js("if(window.onDownloadCancelled) window.onDownloadCancelled();")
        except Exception as e:
            if self.downloader.is_cancelled() or "cancelled" in str(e).lower() or isinstance(e, CancelledException):
                if self._window:
                    self._window.evaluate_js("if(window.onDownloadCancelled) window.onDownloadCancelled();")
            else:
                if self._window:
                    user_lang = self.settings.get("language", "km")
                    friendly_msg = humanize_download_error(str(e), lang=user_lang)
                    err_msg = json.dumps(friendly_msg)
                    self._window.evaluate_js(f"if(window.onDownloadError) window.onDownloadError({err_msg});")

    def toggle_pause(self):
        if getattr(self.downloader, '_is_paused', False):
            self.downloader.resume()
            new_state = False
        else:
            self.downloader.pause()
            new_state = True
        if self._window:
            safe_state = json.dumps(new_state)
            self._window.evaluate_js(f"if(window.onDownloadPauseStateChanged) window.onDownloadPauseStateChanged({safe_state});")
        return {"paused": new_state}

    def cancel_download(self):
        self.downloader.cancel()
        if self._window:
            self._window.evaluate_js("if(window.onDownloadCancelled) window.onDownloadCancelled();")
        return {"cancelled": True}

    def play_sound_alert(self, mode: str = ""):
        """Play native Windows completion alert sound and voice announcement."""
        snd_mode = mode or self.settings.get("sound_mode", "both")
        play_completion_sound_and_voice(sound_mode=snd_mode)
        return {"success": True}

    def check_for_updates(self) -> Dict[str, Any]:
        from updater import updater
        custom_feed = self.settings.get("update_feed_url", "")
        return updater.check_for_updates(custom_feed if custom_feed else None)

    def start_download_update(self, download_url: str, expected_sha256: str = ""):
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

    def cancel_download_update(self):
        from updater import updater
        updater.cancel_update_download()
        return {"success": True}

    def install_update_and_restart(self, new_exe_path: str):
        from updater import updater
        def _launch_worker():
            time.sleep(0.3)
            updater.launch_update_and_exit(new_exe_path)
        threading.Thread(target=_launch_worker, daemon=True).start()
        return {"success": True}


def main():
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
    
    if not os.path.exists(HTML_PATH):
        print(f"[ERROR] UI file not found at: {HTML_PATH}")
        sys.exit(1)

    window = webview.create_window(
        title="SKD TOOL - Ultimate Media Downloader & Converter",
        url=HTML_PATH,
        js_api=api,
        width=1280,
        height=880,
        min_size=(1120, 760),
        background_color="#060913",
        text_select=True
    )
    api.set_window(window)
    
    webview.start(debug=False)


if __name__ == "__main__":
    main()
