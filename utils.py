import os
import sys
import re
import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# =========================================================================
# 1. TRANSLATION & LOCALIZATION (i18n) DICTIONARY (CLEAN TYPOGRAPHY)
# =========================================================================
TRANSLATIONS = {
    "en": {
        "app_title": "Python Downloader Pro - Studio Edition",
        "app_subtitle": "PRO ULTRA v4.0",
        "nav_downloader": "Downloader",
        "nav_playlist": "Playlist Extractor",
        "nav_queue": "Batch Queue",
        "nav_analytics": "Analytics & Speed",
        "nav_history": "History Log",
        "nav_settings": "Settings",
        "engine_ready": "● Engine Ready",
        "engine_busy": "● Processing...",
        
        # Downloader Tab
        "hero_title": "Media & File Downloader",
        "hero_sub": "Paste video, audio, or direct URL below for ultra-fast multi-threaded download.",
        "placeholder_url": "Paste link here (YouTube, TikTok, Facebook, Instagram, Twitter/X, MP4, MP3, ZIP...)",
        "btn_paste": "Paste",
        "btn_inspect": "Inspect",
        "format_mode": "Type:",
        "fmt_mode_video": "Video (HD/4K)",
        "fmt_mode_audio": "Audio (MP3)",
        "fmt_mode_lossless": "Audio (M4A/WAV)",
        "fmt_mode_direct": "Direct File",
        "quality_label": "Resolution / Quality:",
        "btn_show_adv": "Studio Options (Subtitles, Trim, Bitrate) ▼",
        "btn_hide_adv": "Hide Studio Options ▲",
        "adv_subs": "Download Subtitles (.srt)",
        "adv_bitrate": "MP3 Bitrate:",
        "adv_trim": "Trim (Start - End):",
        "adv_embed_thumb": "Embed Thumbnail",
        "status_ready": "READY",
        "status_inspecting": "INSPECTING URL...",
        "status_downloading": "DOWNLOADING...",
        "status_paused": "PAUSED",
        "status_cancelled": "CANCELLED",
        "status_completed": "DOWNLOAD COMPLETED (100%)",
        "status_failed": "DOWNLOAD FAILED",
        "metric_speed": "Speed",
        "metric_eta": "ETA",
        "btn_start": "START DOWNLOAD",
        "btn_pause": "PAUSE",
        "btn_resume": "RESUME",
        "btn_stop": "STOP",
        "btn_folder": "OPEN FOLDER",
        "clipboard_detected": "Copied link detected: Click to download now!",
        
        # Playlist Tab
        "playlist_title": "Playlist & Channel Extractor",
        "playlist_sub": "Extract all videos from a playlist and download selectively or all at once.",
        "btn_extract_playlist": "Extract Playlist",
        "btn_select_all": "Select All",
        "btn_unselect_all": "Deselect All",
        "btn_download_selected": "Download Selected",
        "playlist_empty": "No playlist loaded yet. Enter a playlist link and click 'Extract Playlist'.",
        
        # Queue Tab
        "queue_title": "Batch Queue Downloader",
        "queue_sub": "Enter URLs (one per line) or import from a text file to download sequentially.",
        "btn_add_queue": "Add to Queue",
        "btn_import_txt": "Import .txt",
        "btn_start_queue": "Start Queue",
        "btn_clear_queue": "Clear Queue",
        "queue_empty": "Queue is currently empty",
        
        # Analytics Tab
        "ana_title": "Analytics & Live Speedometer",
        "ana_sub": "Real-time download performance, storage usage, and category statistics.",
        "ana_total_files": "Total Downloads",
        "ana_total_data": "Data Downloaded",
        "ana_success_rate": "Success Rate",
        "ana_speed_graph": "Live Transfer Speed (Real-time Graph)",
        "ana_category_breakdown": "Category Breakdown",
        "ana_no_data": "No download analytics available yet",
        
        # History Tab
        "history_title": "Download History Log",
        "history_sub": "Search, play media, open folders, and verify file integrity.",
        "btn_export_csv": "Export CSV",
        "btn_export_json": "Export JSON",
        "btn_clear_history": "Clear History",
        "search_placeholder": "Search filename...",
        "history_empty": "No download history found",
        "btn_play_preview": "Play / Open",
        "btn_verify_hash": "Hash Check",
        "btn_delete_item": "Delete",
        
        # Settings Tab
        "settings_title": "App Settings & Preferences",
        "settings_sub": "Configure language, theme, output directory, proxy, and browser cookies.",
        "set_language": "Language (ភាសា):",
        "set_theme": "App Theme:",
        "set_out_folder": "Default Output Folder:",
        "set_browse": "Browse...",
        "set_speed_limit": "Speed Limit (KB/s, 0 = Unlimited):",
        "set_browser_cookies": "Extract Cookies from Browser:",
        "set_proxy": "Network Proxy (e.g. http://127.0.0.1:8080):",
        "set_auto_categorize": "Auto-Categorize Files into Subfolders (Videos, Music, Software, etc.)",
        "set_auto_open": "Auto-open Folder when download completes",
        "set_auto_clear": "Auto-clear URL input after starting download",
        "set_sound_alert": "Play Sound Alert when download finishes",
        "set_clipboard_monitor": "Enable Smart Clipboard Link Sniffer",
        "btn_save_settings": "Save Settings",
        
        # Common / Dialogs
        "msg_success": "Success",
        "msg_warning": "Warning",
        "msg_error": "Error",
        "msg_please_enter_url": "Please enter a valid URL first!",
        "msg_download_done": "Download Completed Successfully!",
        "msg_export_done": "Export completed successfully:",
        "msg_confirm_delete": "Are you sure you want to remove this item?",
    },
    "km": {
        "app_title": "Python Downloader Pro - កំណែទំនើប",
        "app_subtitle": "PRO ULTRA v4.0",
        "nav_downloader": "ទាញយក (Main)",
        "nav_playlist": "Playlist វីដេអូ",
        "nav_queue": "តម្រង់ជួរ (Queue)",
        "nav_analytics": "ស្ថិតិ & Speed",
        "nav_history": "ប្រវត្តិទាញយក",
        "nav_settings": "ការកំណត់",
        "engine_ready": "● ម៉ាស៊ីនរួចរាល់",
        "engine_busy": "● កំពុងដំណើរការ...",
        
        # Downloader Tab
        "hero_title": "កម្មវិធីទាញយក Video & File",
        "hero_sub": "បញ្ចូល Link វីដេអូ, បទភ្លេង ឬ File ទូទៅដើម្បីទាញយកយ៉ាងរហ័សទាន់ចិត្ត។",
        "placeholder_url": "Paste Link ទីនេះ (YouTube, TikTok, Facebook, Instagram, Twitter, MP4, MP3, ZIP...)",
        "btn_paste": "បិទភ្ជាប់",
        "btn_inspect": "ពិនិត្យមើល",
        "format_mode": "ប្រភេទ:",
        "fmt_mode_video": "វីដេអូ (HD/4K)",
        "fmt_mode_audio": "ចម្រៀង (MP3)",
        "fmt_mode_lossless": "សម្លេង (M4A/WAV)",
        "fmt_mode_direct": "Direct File",
        "quality_label": "កម្រិត Resolution / Quality:",
        "btn_show_adv": "ជម្រើសបន្ថែម Studio (Subtitles, កាត់ត, Bitrate) ▼",
        "btn_hide_adv": "បិទជម្រើសបន្ថែម ▲",
        "adv_subs": "ទាញយកអក្សររត់ (.srt)",
        "adv_bitrate": "កម្រិត MP3 Bitrate:",
        "adv_trim": "កាត់តវីដេអូ (Start - End):",
        "adv_embed_thumb": "បង្កប់រូបភាព Thumbnail",
        "status_ready": "ស្ថានភាព៖ រួចរាល់",
        "status_inspecting": "កំពុងពិនិត្យមើល Link...",
        "status_downloading": "កំពុងទាញយកទិន្នន័យ...",
        "status_paused": "បានផ្អាកបណ្តោះអាសន្ន",
        "status_cancelled": "បានបញ្ឈប់ការទាញយក",
        "status_completed": "ទាញយកបានជោគជ័យ ១០០%",
        "status_failed": "ការទាញយកបានបរាជ័យ",
        "metric_speed": "ល្បឿន",
        "metric_eta": "សល់ពេល",
        "btn_start": "ចាប់ផ្តើមទាញយក",
        "btn_pause": "ផ្អាក",
        "btn_resume": "បន្ត",
        "btn_stop": "បញ្ឈប់",
        "btn_folder": "បើក Folder",
        "clipboard_detected": "បានរកឃើញ Link ក្នុង Clipboard: ចុចទីនេះដើម្បីទាញយក!",
        
        # Playlist Tab
        "playlist_title": "ប្រព័ន្ធទាញយក Playlist វីដេអូ",
        "playlist_sub": "ទាញយកបញ្ជីវីដេអូទាំងអស់ក្នុង Playlist និងជ្រើសរើសវីដេអូនីមួយៗបានយ៉ាងងាយស្រួល។",
        "btn_extract_playlist": "ទាញយកបញ្ជី Playlist",
        "btn_select_all": "ជ្រើសទាំងអស់",
        "btn_unselect_all": "ដោះជ្រើសរើស",
        "btn_download_selected": "ទាញយកដែលបានជ្រើស",
        "playlist_empty": "មិនទាន់មាន Playlist ឡើយ។ សូមបញ្ចូល Link Playlist រួចចុច 'ទាញយកបញ្ជី Playlist'។",
        
        # Queue Tab
        "queue_title": "ប្រព័ន្ធទាញយកជាជួរ (Batch Queue)",
        "queue_sub": "បញ្ចូល Link ច្រើនក្នុងពេលតែមួយ (១ បន្ទាត់ម្តង) ឬ Import ពី file .txt ដើម្បីទាញយកបន្តបន្ទាប់គ្នា។",
        "btn_add_queue": "បន្ថែមទៅ Queue",
        "btn_import_txt": "នាំចូល .txt",
        "btn_start_queue": "ចាប់ផ្តើម Queue",
        "btn_clear_queue": "សម្អាត Queue",
        "queue_empty": "មិនទាន់មាន Link ក្នុង Queue ឡើយ",
        
        # Analytics Tab
        "ana_title": "ផ្ទាំងស្ថិតិ & កម្រិតល្បឿន (Analytics)",
        "ana_sub": "តាមដានល្បឿនទាញយកជាក់ស្តែង ទំហំទិន្នន័យសរុប និងការវិភាគប្រភេទ File។",
        "ana_total_files": "File សរុប",
        "ana_total_data": "ទំហំទិន្នន័យសរុប",
        "ana_success_rate": "អត្រាជោគជ័យ",
        "ana_speed_graph": "ក្រាហ្វិកល្បឿនជាក់ស្តែង (Real-time Speed Graph)",
        "ana_category_breakdown": "ការបែងចែកតាមប្រភេទ File",
        "ana_no_data": "មិនទាន់មានទិន្នន័យស្ថិតិនៅឡើយទេ",
        
        # History Tab
        "history_title": "ប្រវត្តិទាញយក (History Log)",
        "history_sub": "ស្វែងរក, ចាក់ស្តាប់/មើល File, បើកមើល Folder និងពិនិត្យមើល Hash សុវត្ថិភាព។",
        "btn_export_csv": "នាំចេញ CSV",
        "btn_export_json": "នាំចេញ JSON",
        "btn_clear_history": "លុបប្រវត្តិ",
        "search_placeholder": "ស្វែងរកឈ្មោះ File...",
        "history_empty": "រកមិនឃើញប្រវត្តិទាញយកឡើយ",
        "btn_play_preview": "បើក/ចាក់មើល",
        "btn_verify_hash": "ពិនិត្យ Hash",
        "btn_delete_item": "លុប",
        
        # Settings Tab
        "settings_title": "ការកំណត់កម្មវិធី (Settings)",
        "settings_sub": "កំណត់ភាសា, រចនាបថ Theme, ទីតាំង Folder, Proxy និង Browser Cookies។",
        "set_language": "ភាសា (Language):",
        "set_theme": "រចនាបថ Theme:",
        "set_out_folder": "ទីតាំងផ្ទុក File (Output Folder):",
        "set_browse": "រើស Folder...",
        "set_speed_limit": "កំណត់កម្រិតល្បឿន (KB/s, 0 = មិនកំណត់):",
        "set_browser_cookies": "ប្រើប្រាស់ Cookies ពី Browser:",
        "set_proxy": "កំណត់ Network Proxy (ឧទាហរណ៍: http://127.0.0.1:8080):",
        "set_auto_categorize": "រៀបចំ File ស្វ័យប្រវត្តិតាម Folder (Videos, Music, Software...)",
        "set_auto_open": "បើក Folder ដោយស្វ័យប្រវត្តិនៅពេលទាញយករួច",
        "set_auto_clear": "លុប Link ស្វ័យប្រវត្តិបន្ទាប់ពីចាប់ផ្តើមទាញយក",
        "set_sound_alert": "បន្លឺសម្លេងជូនដំណឹងនៅពេលទាញយករួចរាល់",
        "set_clipboard_monitor": "បើកមុខងារចាប់ Link ស្វ័យប្រវត្តិ (Clipboard Sniffer)",
        "btn_save_settings": "រក្សាទុកការកំណត់",
        
        # Common / Dialogs
        "msg_success": "ជោគជ័យ",
        "msg_warning": "ការព្រមាន",
        "msg_error": "កំហុស",
        "msg_please_enter_url": "សូមបញ្ចូល Link ជាមុនសិន!",
        "msg_download_done": "ការទាញយកបានបញ្ចប់ដោយជោគជ័យ!",
        "msg_export_done": "បាន Export រួចរាល់៖",
        "msg_confirm_delete": "តើអ្នកប្រាកដជាចង់លុបទិន្នន័យនេះដែរឬទេ?",
    }
}

def t(key: str, lang: str = "km") -> str:
    """Translate key to specified language with fallback."""
    dictionary = TRANSLATIONS.get(lang, TRANSLATIONS["km"])
    return dictionary.get(key, TRANSLATIONS["en"].get(key, key))


# =========================================================================
# 2. PLATFORM IDENTIFIER & COLOR BADGES
# =========================================================================
def detect_platform(url: str) -> Dict[str, str]:
    """Detect platform from URL and return name, badge text, and color."""
    if not url:
        return {"name": "Web Media", "icon": "[ Web Media Link ]", "color": "#38BDF8", "bg": "#0C213B"}
    
    url_lower = url.lower()
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return {"name": "YouTube", "icon": "[ YouTube Video ]", "color": "#EF4444", "bg": "#3B0707"}
    elif 'tiktok.com' in url_lower:
        return {"name": "TikTok", "icon": "[ TikTok Video ]", "color": "#06B6D4", "bg": "#083344"}
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return {"name": "Facebook", "icon": "[ Facebook Video ]", "color": "#3B82F6", "bg": "#172554"}
    elif 'instagram.com' in url_lower:
        return {"name": "Instagram", "icon": "[ Instagram Media ]", "color": "#EC4899", "bg": "#4A0429"}
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return {"name": "X / Twitter", "icon": "[ X / Twitter ]", "color": "#94A3B8", "bg": "#0F172A"}
    elif 'soundcloud.com' in url_lower:
        return {"name": "SoundCloud", "icon": "[ SoundCloud Audio ]", "color": "#F97316", "bg": "#431407"}
    elif 'vimeo.com' in url_lower:
        return {"name": "Vimeo", "icon": "[ Vimeo Video ]", "color": "#06B6D4", "bg": "#083344"}
    elif 'bilibili.com' in url_lower:
        return {"name": "Bilibili", "icon": "[ Bilibili Video ]", "color": "#FB7299", "bg": "#4A044E"}
    elif 'twitch.tv' in url_lower:
        return {"name": "Twitch", "icon": "[ Twitch Stream ]", "color": "#A855F7", "bg": "#3B0764"}
    elif any(url_lower.endswith(ext) or ext + '?' in url_lower for ext in ['.zip', '.rar', '.7z', '.exe', '.pdf', '.iso', '.msi', '.mp4', '.mp3']):
        return {"name": "Direct File", "icon": "[ Direct File Link ]", "color": "#10B981", "bg": "#022C22"}
    else:
        return {"name": "Web Media", "icon": "[ Web Media Link ]", "color": "#38BDF8", "bg": "#0C213B"}


# =========================================================================
# 3. DIRECTORY & PERSISTENT STORAGE HELPERS
# =========================================================================
def get_default_download_dir() -> str:
    """Returns default Downloads directory for the user."""
    if os.name == 'nt':
        import winreg
        try:
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
                if os.path.exists(location):
                    return location
        except Exception:
            pass
    home = Path.home()
    downloads_path = home / "Downloads"
    if downloads_path.exists():
        return str(downloads_path)
    return str(home)

def get_base_dir() -> str:
    """Get root directory of the application (executable dir when frozen, script dir otherwise)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, compatible with PyInstaller bundle (_MEIPASS) and source mode."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundle_path):
            return bundle_path
    
    # Check relative to base_dir
    local_path = os.path.join(get_base_dir(), relative_path)
    if os.path.exists(local_path):
        return local_path
        
    # Check relative to __file__
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
    if os.path.exists(script_path):
        return script_path
        
    return local_path

def get_app_data_path(filename: str) -> str:
    """
    Get writable path for persistent user files (settings, licenses, history).
    Priority 1: Portable local directory next to .exe or script (if writable).
    Priority 2: %APPDATA%/SKD_Tool (if Program Files or read-only directory).
    """
    base_dir = get_base_dir()
    candidate = os.path.join(base_dir, filename)
    if os.path.exists(candidate):
        return candidate

    # Test if base_dir is writable
    try:
        test_file = os.path.join(base_dir, f".write_test_{os.getpid()}.tmp")
        with open(test_file, 'w') as f:
            f.write("1")
        if os.path.exists(test_file):
            os.remove(test_file)
        return candidate
    except Exception:
        pass

    # Fallback to APPDATA for Windows or home directory for cross-platform
    app_data_root = os.environ.get("APPDATA", os.path.expanduser("~"))
    skd_dir = os.path.join(app_data_root, "SKD_Tool")
    try:
        os.makedirs(skd_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(skd_dir, filename)

def load_history_db() -> List[Dict[str, Any]]:
    """Load persistent history from download_history.json."""
    path = get_app_data_path("download_history.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history_db(history_items: List[Dict[str, Any]]):
    """Save history to download_history.json."""
    path = get_app_data_path("download_history.json")
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(history_items, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def load_settings_db() -> Dict[str, Any]:
    """Load persistent settings from settings.json."""
    path = get_app_data_path("app_settings.json")
    default_settings = {
        "language": "km",
        "appearance_mode": "Dark",
        "save_dir": get_default_download_dir(),
        "speed_limit": "0",
        "browser_cookies": "none",
        "proxy": "",
        "auto_categorize": True,
        "auto_open_folder": True,
        "auto_clear_url": False,
        "sound_alert": True,
        "clipboard_monitor": True,
        "quality_preset": "1080p Full HD",
        "audio_bitrate": "320k"
    }
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                default_settings.update(data)
                return default_settings
        except Exception:
            return default_settings
    return default_settings

def save_settings_db(settings_data: Dict[str, Any]):
    """Save settings to settings.json."""
    path = get_app_data_path("app_settings.json")
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# =========================================================================
# 4. FORMATTING & STRING UTILS
# =========================================================================
def format_bytes(size: float) -> str:
    """Format bytes to human readable format (KB, MB, GB)."""
    if size is None or size < 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def format_speed(bytes_per_sec: float) -> str:
    """Format speed in bytes/sec to readable format."""
    if not bytes_per_sec or bytes_per_sec <= 0:
        return "0 KB/s"
    return f"{format_bytes(bytes_per_sec)}/s"

def format_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds is None or seconds < 0:
        return "--:--"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def is_video_platform_url(url: str) -> bool:
    """Check if the URL belongs to a video/audio platform supported by yt-dlp."""
    if not url:
        return False
    video_domains = [
        'youtube.com', 'youtu.be', 'tiktok.com', 'facebook.com', 'fb.watch',
        'instagram.com', 'twitter.com', 'x.com', 'vimeo.com', 'dailymotion.com',
        'soundcloud.com', 'reddit.com', 'twitch.tv', 'bilibili.com', 'pinterest.com'
    ]
    url_lower = url.lower()
    return any(domain in url_lower for domain in video_domains)

def is_playlist_url(url: str) -> bool:
    """Check if the URL points to a playlist or album."""
    if not url:
        return False
    url_lower = url.lower()
    return 'list=' in url_lower or 'playlist' in url_lower or 'album' in url_lower or 'sets' in url_lower

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent invalid characters on Windows and other OS."""
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    filename = filename.strip('. ')
    return filename or 'downloaded_file'

def categorize_file(filename: str) -> str:
    """Categorize file into Videos, Music, Documents, Software, Images, Archives, Others."""
    ext = os.path.splitext(filename)[1].lower()
    
    video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.wmv', '.m4v', '.ts']
    music_exts = ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma', '.opus']
    doc_exts = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.txt', '.csv', '.epub', '.md']
    app_exts = ['.exe', '.msi', '.apk', '.dmg', '.iso', '.bat', '.sh', '.bin']
    img_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.psd', '.ico']
    archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz']

    if ext in video_exts:
        return "Videos"
    elif ext in music_exts:
        return "Music"
    elif ext in doc_exts:
        return "Documents"
    elif ext in app_exts:
        return "Software"
    elif ext in img_exts:
        return "Images"
    elif ext in archive_exts:
        return "Archives"
    return "Others"

def get_category_path(base_dir: str, filename: str) -> str:
    """Get path with category subfolder."""
    category = categorize_file(filename)
    category_dir = os.path.join(base_dir, category)
    os.makedirs(category_dir, exist_ok=True)
    return category_dir

def is_executable_file(filename: str) -> bool:
    """Check if file extension poses security risk (.exe, .bat, .msi, .scr, .cmd)."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ['.exe', '.bat', '.msi', '.scr', '.cmd', '.vbs', '.ps1']

def calculate_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """Calculate SHA256 or MD5 hash of a file."""
    if not os.path.exists(filepath):
        return "N/A"
    hasher = hashlib.sha256() if algorithm == 'sha256' else hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return "Error"

def export_history_csv(history_items: List[Dict[str, Any]], filepath: str) -> bool:
    """Export download history to CSV file."""
    try:
        keys = ['filename', 'path', 'size', 'time', 'status', 'category', 'url', 'platform']
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(history_items)
        return True
    except Exception:
        return False

def export_history_json(history_items: List[Dict[str, Any]], filepath: str) -> bool:
    """Export download history to JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_items, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False
