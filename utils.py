import os
import sys
import re
import csv
import json
import shutil
import hashlib
import threading
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# =========================================================================
# 1. TRANSLATION & LOCALIZATION (i18n) INTEGRATION
# =========================================================================
from i18n import TRANSLATIONS, t, get_all_translations


# =========================================================================
# 2. PLATFORM IDENTIFIER & COLOR BADGES
# =========================================================================
def detect_platform(url: str) -> Dict[str, str]:
    """Detect platform from URL and return name, badge text, and color."""
    if not url:
        return {"name": "Web Media", "icon": "[ Web Media Link ]", "color": "#38BDF8", "bg": "#0C213B"}
    
    url_lower = url.lower()
    if '.m3u8' in url_lower:
        return {"name": "M3U8 HLS Stream", "icon": "[ M3U8 HLS Stream ]", "color": "#10B981", "bg": "#022C22"}
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        if '/shorts/' in url_lower:
            return {"name": "YouTube Shorts", "icon": "[ YouTube Shorts ]", "color": "#EF4444", "bg": "#3B0707"}
        return {"name": "YouTube", "icon": "[ YouTube Video ]", "color": "#EF4444", "bg": "#3B0707"}
    elif 'douyin.com' in url_lower:
        return {"name": "Douyin (抖音)", "icon": "[ Douyin Video ]", "color": "#00F2FE", "bg": "#082F49"}
    elif 'tiktok.com' in url_lower:
        if '/shortdrama/' in url_lower:
            return {"name": "TikTok Short Drama", "icon": "[ TikTok Short Drama ]", "color": "#06B6D4", "bg": "#083344"}
        elif '/photo/' in url_lower:
            return {"name": "TikTok Photos", "icon": "[ TikTok Photos ]", "color": "#06B6D4", "bg": "#083344"}
        elif '/foryou' in url_lower or '/explore' in url_lower or '/following' in url_lower:
            return {"name": "TikTok Feed", "icon": "[ TikTok Home Feed ]", "color": "#F59E0B", "bg": "#451A03"}
        return {"name": "TikTok", "icon": "[ TikTok Video ]", "color": "#06B6D4", "bg": "#083344"}
    elif 'kuaishou.com' in url_lower or 'kwai.com' in url_lower:
        return {"name": "Kuaishou (快手)", "icon": "[ Kuaishou Video ]", "color": "#FF7700", "bg": "#431407"}
    elif 'xiaohongshu.com' in url_lower or 'xhslink.com' in url_lower:
        return {"name": "Xiaohongshu (小红书)", "icon": "[ RED / 小红书 ]", "color": "#FF2442", "bg": "#450A0A"}
    elif 'weibo.com' in url_lower or 'weibo.cn' in url_lower:
        return {"name": "Weibo (微博)", "icon": "[ Weibo Video ]", "color": "#E6162D", "bg": "#450A0A"}
    elif 'iqiyi.com' in url_lower or 'iq.com' in url_lower:
        return {"name": "iQIYI (爱奇艺)", "icon": "[ iQIYI Drama ]", "color": "#00C300", "bg": "#052E16"}
    elif 'wetv.vip' in url_lower or 'v.qq.com' in url_lower:
        return {"name": "WeTV / Tencent", "icon": "[ WeTV / Tencent ]", "color": "#0099FF", "bg": "#082F49"}
    elif 'youku.com' in url_lower:
        return {"name": "Youku (优酷)", "icon": "[ Youku Drama ]", "color": "#00B2FF", "bg": "#082F49"}
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower or 'fb.gg' in url_lower or 'fb.me' in url_lower:
        if '/reel/' in url_lower or '/share/r/' in url_lower:
            return {"name": "Facebook Reel", "icon": "[ Facebook Reel ]", "color": "#3B82F6", "bg": "#172554"}
        return {"name": "Facebook", "icon": "[ Facebook Video ]", "color": "#3B82F6", "bg": "#172554"}
    elif 'instagram.com' in url_lower:
        if '/reel/' in url_lower or '/reels/' in url_lower:
            return {"name": "Instagram Reel", "icon": "[ Instagram Reel ]", "color": "#EC4899", "bg": "#4A0429"}
        return {"name": "Instagram", "icon": "[ Instagram Media ]", "color": "#EC4899", "bg": "#4A0429"}
    elif 'threads.net' in url_lower:
        return {"name": "Threads", "icon": "[ Threads Media ]", "color": "#E2E8F0", "bg": "#0F172A"}
    elif 'capcut.com' in url_lower:
        return {"name": "CapCut", "icon": "[ CapCut Template ]", "color": "#00D2D3", "bg": "#083344"}
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return {"name": "X / Twitter", "icon": "[ X / Twitter ]", "color": "#94A3B8", "bg": "#0F172A"}
    elif 'pinterest.com' in url_lower or 'pin.it' in url_lower or 'pinterest.' in url_lower:
        return {"name": "Pinterest", "icon": "[ Pinterest Pin ]", "color": "#E60023", "bg": "#450A0A"}
    elif 'reddit.com' in url_lower or 'redd.it' in url_lower:
        return {"name": "Reddit", "icon": "[ Reddit Video ]", "color": "#FF4500", "bg": "#431407"}
    elif 'soundcloud.com' in url_lower:
        return {"name": "SoundCloud", "icon": "[ SoundCloud Audio ]", "color": "#F97316", "bg": "#431407"}
    elif 'vimeo.com' in url_lower:
        return {"name": "Vimeo", "icon": "[ Vimeo Video ]", "color": "#06B6D4", "bg": "#083344"}
    elif 'bilibili.com' in url_lower or 'bilibili.tv' in url_lower:
        return {"name": "Bilibili (哔哩哔哩)", "icon": "[ Bilibili Video ]", "color": "#FB7299", "bg": "#4A044E"}
    elif 'twitch.tv' in url_lower:
        return {"name": "Twitch", "icon": "[ Twitch Stream ]", "color": "#A855F7", "bg": "#3B0764"}
    elif 'drive.google.com' in url_lower:
        return {"name": "Google Drive", "icon": "[ Google Drive ]", "color": "#34A853", "bg": "#064E3B"}
    elif 'dropbox.com' in url_lower:
        return {"name": "Dropbox", "icon": "[ Dropbox ]", "color": "#0061FF", "bg": "#1E3A8A"}
    elif 'mediafire.com' in url_lower:
        return {"name": "MediaFire", "icon": "[ MediaFire ]", "color": "#0070F3", "bg": "#0C213B"}
    elif any(url_lower.endswith(ext) or ext + '?' in url_lower for ext in ['.zip', '.rar', '.7z', '.exe', '.pdf', '.iso', '.msi', '.mp4', '.mkv', '.webm', '.mov', '.avi', '.mp3', '.m4a', '.wav']):
        return {"name": "Direct File", "icon": "[ Direct File Link ]", "color": "#10B981", "bg": "#022C22"}
    else:
        return {"name": "Web Media / Drama", "icon": "[ Universal Stream ]", "color": "#38BDF8", "bg": "#0C213B"}


# =========================================================================
# 3. DIRECTORY & PERSISTENT STORAGE HELPERS
# =========================================================================
def get_best_available_drive_folder(subfolder: str = "Downloads") -> str:
    """Find drive with maximum available disk space if C: drive is full."""
    best_path = ""
    max_free = 0
    import string
    available_drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    for d in available_drives:
        try:
            usage = shutil.disk_usage(d)
            if usage.free > max_free:
                max_free = usage.free
                best_path = os.path.join(d, subfolder)
        except Exception:
            continue
    if best_path:
        try:
            os.makedirs(best_path, exist_ok=True)
            return best_path
        except Exception:
            pass
    return os.path.join(os.path.expanduser("~"), subfolder)

def get_default_download_dir() -> str:
    """Returns default Downloads directory with low disk space auto-protection."""
    default_dir = ""
    if os.name == 'nt':
        import winreg
        try:
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
                if os.path.exists(location):
                    default_dir = location
        except Exception:
            pass
    if not default_dir:
        home = Path.home()
        downloads_path = home / "Downloads"
        default_dir = str(downloads_path) if downloads_path.exists() else str(home)

    # Check if default drive has critically low space (< 1.5 GB)
    try:
        drive_root = os.path.splitdrive(default_dir)[0] + "\\"
        free_bytes = shutil.disk_usage(drive_root).free
        if free_bytes < 1.5 * 1024 * 1024 * 1024:  # less than 1.5 GB
            return get_best_available_drive_folder("Downloads")
    except Exception:
        pass

    return default_dir

def get_base_dir() -> str:
    """Get root directory of the application (executable dir when frozen, script dir otherwise)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource.
    Priority order:
    1. Workspace / Base executable folder (in dev mode)
    2. Live Micro-Patch in %APPDATA%/SKD_Tool/patches/ (for frozen app)
    3. PyInstaller bundle (_MEIPASS)
    """
    # 0. In dev mode (not frozen), workspace source files ALWAYS take highest priority!
    if not getattr(sys, 'frozen', False):
        local_path = os.path.join(get_base_dir(), relative_path)
        if os.path.exists(local_path):
            return local_path
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
        if os.path.exists(script_path):
            return script_path

    # 1. Micro-Patch override (for frozen executable)
    patch_path = os.path.join(get_app_data_path("patches"), relative_path)
    if os.path.exists(patch_path):
        return patch_path

    # 2. PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundle_path):
            return bundle_path
    
    # 3. Check relative to base_dir
    local_path = os.path.join(get_base_dir(), relative_path)
    if os.path.exists(local_path):
        return local_path
        
    # 4. Check relative to __file__
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
    if os.path.exists(script_path):
        return script_path
        
    return local_path

def get_app_data_path(filename: str = "") -> str:
    """
    Get clean persistent path in %APPDATA%/SKD_Tool for settings, history, and databases.
    Prevents polluting user Desktop or download folder with messy json/database files.
    Automatically migrates any legacy files from base_dir to APPDATA and cleans up Desktop.
    """
    app_data_root = os.environ.get("APPDATA", os.path.expanduser("~"))
    skd_dir = os.path.join(app_data_root, "SKD_Tool")
    try:
        os.makedirs(skd_dir, exist_ok=True)
    except Exception:
        pass

    if not filename:
        return skd_dir

    target_path = os.path.join(skd_dir, filename)

    # Clean Desktop / Portable Migration:
    # If file previously existed on Desktop or next to .exe, migrate it to %APPDATA%/SKD_Tool
    # so history and settings are preserved, and remove the file from Desktop to keep it spotless!
    try:
        base_dir = get_base_dir()
        old_file = os.path.join(base_dir, filename)
        if os.path.exists(old_file) and os.path.abspath(old_file).lower() != os.path.abspath(target_path).lower():
            if not os.path.exists(target_path):
                import shutil
                shutil.copy2(old_file, target_path)
            # Remove legacy file from Desktop/folder to keep it clean
            try:
                os.remove(old_file)
            except Exception:
                pass
    except Exception:
        pass

    return target_path

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

DEFAULT_TELEGRAM_BOT_TOKEN = "8562796575:AAF2Pa3T-xySa5TkSFpSdwUAE__9V15mXpE"
DEFAULT_TELEGRAM_CHAT_ID = "5096452919"

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
        "audio_bitrate": "320k",
        "telegram_bot_token": DEFAULT_TELEGRAM_BOT_TOKEN,
        "telegram_chat_id": DEFAULT_TELEGRAM_CHAT_ID,
        "telegram_telemetry_enabled": True,
        "telegram_notify_on_start": False
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
    """Check if the URL belongs to a video/audio platform supported by yt-dlp or dedicated extractors."""
    if not url:
        return False
    video_domains = [
        'youtube.com', 'youtu.be', 'tiktok.com', 'douyin.com', 'facebook.com', 'fb.watch', 'fb.gg', 'fb.me',
        'instagram.com', 'twitter.com', 'x.com', 'threads.net', 'capcut.com', 'vimeo.com', 'dailymotion.com',
        'soundcloud.com', 'reddit.com', 'redd.it', 'twitch.tv', 'bilibili.com', 'bilibili.tv',
        'pinterest.com', 'pin.it', 'pinterest.', 'kuaishou.com', 'kwai.com', 'xiaohongshu.com',
        'xhslink.com', 'weibo.com', 'weibo.cn', 'iqiyi.com', 'iq.com', 'wetv.vip', 'v.qq.com',
        'youku.com', 'terabox.com', 'teraboxapp.com', '.m3u8'
    ]
    url_lower = url.lower()
    return any(domain in url_lower for domain in video_domains)

def transform_cloud_url(url: str) -> str:
    """Transform cloud storage links (Google Drive, Dropbox, MediaFire, Terabox) into direct download streams."""
    if not url:
        return url
    u = url.strip()
    u_lower = u.lower()
    
    # 1. Google Drive direct link converter
    if 'drive.google.com' in u_lower:
        m = re.search(r'/file/d/([a-zA-Z0-9_-]+)', u)
        if not m:
            m = re.search(r'id=([a-zA-Z0-9_-]+)', u)
        if m:
            file_id = m.group(1)
            return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t"

    # 2. Dropbox direct link converter
    if 'dropbox.com' in u_lower:
        if 'dl=0' in u:
            return u.replace('dl=0', 'dl=1')
        elif '?' not in u:
            return f"{u}?dl=1"
        elif 'dl=1' not in u:
            return f"{u}&dl=1"

    # 3. Mediafire direct link scraping/converter
    if 'mediafire.com' in u_lower and not u_lower.endswith('.mp4') and not u_lower.endswith('.zip') and not u_lower.endswith('.rar'):
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
            resp = requests.get(u, headers=headers, timeout=6)
            if resp.status_code == 200:
                m = re.search(r'href="(https?://download\d+\.mediafire\.com/[^"]+)"', resp.text)
                if m:
                    return m.group(1)
                m2 = re.search(r'aria-label="Download file"\s+href="([^"]+)"', resp.text)
                if m2:
                    return m2.group(1)
        except Exception:
            pass

    return u

def humanize_download_error(err_str: str, lang: str = "km") -> str:
    """Convert technical error strings into user-friendly explanations in Khmer and English."""
    err_low = str(err_str).lower()
    
    if "tiktok.com/foryou" in err_low or "/foryou" in err_low or "tiktok feed" in err_low or "feed 'for you'" in err_low:
        if lang == "km":
            return "តំណភ្ជាប់នេះជាទំព័រដើម Feed 'For You' របស់ TikTok (មិនមែនជា Link វីដេអូឡើយ)។ សូមចុចលើវីដេអូដែលចង់បាន រួចចុច Share ➔ Copy Link ដើម្បីទាញយក។"
        return "This is TikTok's 'For You' feed page, not a direct video URL. Please open the video and click Share ➔ Copy Link."

    if "shortdrama" in err_low or "short drama" in err_low:
        if "vip" in err_low or "lock" in err_low or "paywall" in err_low or "coins" in err_low:
            if lang == "km":
                return "TikTok Short Drama: ភាគនេះត្រូវបានការពារដោយប្រព័ន្ធ VIP/Coins Paywall របស់ TikTok។ តម្រូវឱ្យមាន Login/Coins នៅក្នុង TikTok ទើបអាចទស្សនា ឬទាញយកបាន (ឬបើក Browser Cookies ក្នុង Settings ប្រសិនបើបាន Unlock រួច)។"
            return "TikTok Short Drama: This episode is locked behind TikTok VIP/Coin Paywall. Account login with unlocked coins is required."
        if lang == "km":
            return "TikTok Short Drama: ដើម្បីទាញយកភាគនេះ សូមចុចប៊ូតុង Share លើវីដេអូភាគនោះ រួចជ្រើសរើស 'Copy Link' នោះប្រព័ន្ធនឹងទាញយកវីដេអូបាន ១០០%!"
        return "TikTok Short Drama: Please click Share on the episode video and choose 'Copy Link' to download."

    if "sign in to confirm you're not a bot" in err_low or "bot" in err_low:
        if lang == "km":
            return "YouTube តម្រូវឱ្យផ្ទៀងផ្ទាត់ Bot (ប្រព័ន្ធបានបើក Client Rotation Bypass ស្វ័យប្រវត្តិ។ ប្រសិនបើតឹងតែង សូមជ្រើសរើស Browser Cookies ក្នុង Settings)។"
        return "YouTube requires bot verification (Client Rotation bypass applied. If persistent, enable Browser Cookies in Settings)."
        
    if "private video" in err_low or "this video is private" in err_low or "login required" in err_low:
        if lang == "km":
            return "វីដេអូនេះជា Private ឬតម្រូវឱ្យ Login ចូលគណនី (សូមប្រើប្រាស់ Browser Cookies ក្នុង Settings)។"
        return "This video is Private or requires account login. Please enable Browser Cookies in Settings."

    if "video unavailable" in err_low or "does not exist" in err_low or "deleted" in err_low or "removed" in err_low:
        if lang == "km":
            return "វីដេអូ ឬឯកសារនេះត្រូវបានលុបចោល ឬរកមិនឃើញឡើយ។"
        return "This video or file has been deleted or is unavailable."

    if "403" in err_low or "forbidden" in err_low:
        if lang == "km":
            return "Server បដិសេធការទាញយក (HTTP 403 Forbidden) - ប្រព័ន្ធបានព្យាយាម Auto-Bypass រួចរាល់។ សូមចុច Retry ដើម្បីសាកល្បងម្តងទៀត។"
        return "Server rejected request (HTTP 403 Forbidden). Bypass attempted. Please click Retry."

    if "429" in err_low or "too many requests" in err_low:
        if lang == "km":
            return "Server កំពុងជាប់រវល់ ឬ Rate Limit (HTTP 429) - សូមរង់ចាំបន្តិចរួចចុច Retry។"
        return "Server is busy or rate-limited (HTTP 429). Please wait a moment and click Retry."

    if "404" in err_low or "not found" in err_low:
        if lang == "km":
            return "រកមិនឃើញតំណភ្ជាប់ឯកសារលើ Server ឡើយ (HTTP 404 Not Found)។"
        return "File not found on the remote server (HTTP 404 Not Found)."

    if "timeout" in err_low or "timed out" in err_low or "connection reset" in err_low or "10054" in err_low or "remotedisconnected" in err_low:
        if lang == "km":
            return "ការភ្ជាប់បណ្តាញអ៊ីនធឺណិតមានការយឺតយ៉ាវ ឬដាច់ខ្សែបណ្តោះអាសន្ន។ សូមចុច Retry ដើម្បីទាញយកបន្ត។"
        return "Network connection timed out or reset. Please click Retry to resume downloading."

    if "no video formats found" in err_low or "requested format is not available" in err_low:
        if lang == "km":
            return "មិនមានទម្រង់វីដេអូដែលត្រូវនឹងកម្រិតនេះឡើយ (អាចជា Photo Slideshow ឬត្រូវជ្រើសរើស Auto Best)។"
        return "Requested media format not available (may be a photo slideshow; try selecting Auto Best)."

    if "space" in err_low and ("disk" in err_low or "drive" in err_low or "full" in err_low):
        if lang == "km":
            return "ទំហំ Hard Disk (Drive C/D) ពេញ! សូមសម្អាតទំហំទំនេររួចសាកល្បងម្ដងទៀត។"
        return "Disk drive is full! Please free up disk space and retry."

    return str(err_str)

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

def select_file_dialog_native(title: str = "Select File", file_types: Optional[List[Tuple[str, str]]] = None) -> str:
    """Open a native Windows file selection dialog without leaving a Tkinter root window."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        types = file_types or [("Media & Text Files", "*.mp4;*.mkv;*.webm;*.mov;*.avi;*.mp3;*.m4a;*.wav;*.txt;*.csv"), ("All Files", "*.*")]
        selected = filedialog.askopenfilename(title=title, filetypes=types)
        root.destroy()
        return selected or ""
    except Exception:
        return ""

def select_folder_dialog_native(title: str = "Select Folder", initial_dir: str = "") -> str:
    """Open a native Windows directory selection dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(title=title, initialdir=initial_dir or get_default_download_dir())
        root.destroy()
        return selected or ""
    except Exception:
        return ""

def auto_organize_downloaded_file(file_path: str, base_dir: str) -> str:
    """Move file into organized subfolder (Videos, Music, Software, Converted, etc.)."""
    if not file_path or not os.path.exists(file_path):
        return file_path
    
    filename = os.path.basename(file_path)
    target_dir = get_category_path(base_dir, filename)
    target_path = os.path.join(target_dir, filename)
    
    # If already in the target directory, return
    if os.path.normpath(os.path.dirname(file_path)) == os.path.normpath(target_dir):
        return file_path
        
    try:
        import shutil
        counter = 1
        base, ext = os.path.splitext(target_path)
        while os.path.exists(target_path):
            target_path = f"{base}_{counter}{ext}"
            counter += 1
        shutil.move(file_path, target_path)
        return target_path
    except Exception:
        return file_path

def check_file_exists_in_folder(folder: str, filename: str) -> bool:
    """Check if file exists in folder."""
    if not folder or not os.path.exists(folder):
        return False
    target = os.path.join(folder, filename)
    return os.path.exists(target)

def generate_cyber_chime_wav_bytes() -> bytes:
    """Generate in-memory studio crystal chime WAV bytes (Eb5 - G5 - Bb5 - Eb6)."""
    import math
    import struct
    import wave
    import io
    sample_rate = 44100
    duration = 0.95
    num_samples = int(sample_rate * duration)
    notes = [
        (622.25, 0.00, 0.18),
        (783.99, 0.07, 0.20),
        (932.33, 0.14, 0.22),
        (1244.50, 0.22, 0.26)
    ]
    
    raw_audio = bytearray()
    for i in range(num_samples):
        t = float(i) / sample_rate
        sample = 0.0
        for f, note_start, amp in notes:
            if t >= note_start:
                note_t = t - note_start
                env = math.exp(-note_t * 4.5)
                sample += (math.sin(2.0 * math.pi * f * note_t) + 0.25 * math.sin(4.0 * math.pi * f * note_t)) * env * amp
        
        sample = max(-1.0, min(1.0, sample))
        int_sample = int(sample * 32767.0)
        raw_audio.extend(struct.pack('<h', int_sample))
        
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_audio)
    return wav_io.getvalue()

_CACHED_CHIME_WAV: Optional[bytes] = None

def play_completion_sound_and_voice(sound_mode: str = "bell", message: str = ""):
    """
    Play authentic Windows OS notification sound or studio chime asynchronously.
    Modes:
      - 'bell' / 'windows' / 'both': Classic Windows Notification Sound (SystemAsterisk / Notification.Default)
      - 'chime': Studio Crystal Chime
      - 'mute': No sound
    """
    if str(sound_mode).lower() == "mute":
        return

    def _worker():
        global _CACHED_CHIME_WAV
        import winsound

        mode = str(sound_mode).lower()
        
        # 1. Authentic Windows Notification Sound (SystemAsterisk / Notification.Default)
        if mode in ["bell", "windows", "both", "default"]:
            try:
                winsound.PlaySound("Notification.Default", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                try:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                except Exception:
                    pass
        elif mode == "chime":
            try:
                if _CACHED_CHIME_WAV is None:
                    _CACHED_CHIME_WAV = generate_cyber_chime_wav_bytes()
                winsound.PlaySound(_CACHED_CHIME_WAV, winsound.SND_MEMORY | winsound.SND_ASYNC)
            except Exception:
                try:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                except Exception:
                    pass

    threading.Thread(target=_worker, daemon=True).start()

def play_system_alert_sound(sound_mode: str = "both"):
    """Alias for backwards compatibility and bridge invocation."""
    play_completion_sound_and_voice(sound_mode=sound_mode)


# =========================================================================
# 5. CLOUD ACTIVITY LOGGING & TELEMETRY (GOOGLE SHEETS / DATABASE)
# =========================================================================
def get_device_and_user_identity() -> str:
    """
    Returns formatted User and Machine identifier for Cloud Telemetry.
    Combines: Windows Username + Device Hostname + VIP License Plan / HWID.
    Example: 'Visal (Admin Computer) [Lifetime VIP | SKD-2533-59E4]'
    """
    import socket
    import getpass

    username = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if not username:
        try:
            username = getpass.getuser()
        except Exception:
            username = "User"

    hostname = socket.gethostname() or "PC"

    plan_label = "Lifetime VIP"
    hwid_str = ""
    try:
        from licensing import load_and_validate_current_license, get_machine_hwid
        _, lic_data, _ = load_and_validate_current_license()
        if lic_data and isinstance(lic_data, dict):
            plan_label = lic_data.get("plan") or "Lifetime VIP"
        hwid = get_machine_hwid()
        if hwid:
            hwid_str = hwid
    except Exception:
        pass

    if hwid_str:
        return f"{username} ({hostname}) [{plan_label} | {hwid_str}]"
    else:
        return f"{username} ({hostname}) [{plan_label}]"


def send_telegram_download_alert(
    title: str,
    url: str,
    platform: str = "Web",
    quality: str = "Default",
    size: str = "0 MB",
    status: str = "Completed",
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None
):
    """
    Asynchronously logs download activity to Admin's Telegram Bot.
    Runs in a detached daemon thread so UI and download speed are never blocked.
    Automatically includes User Account, Machine HWID, and License Plan.
    """
    import threading
    import requests
    from datetime import datetime

    def _worker():
        try:
            token = (bot_token or DEFAULT_TELEGRAM_BOT_TOKEN).strip()
            cid = (chat_id or DEFAULT_TELEGRAM_CHAT_ID).strip()

            if not token or not cid:
                return

            device_str = get_device_and_user_identity()
            timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

            # Auto-detect platform from URL if empty or generic
            plat_name = platform or "Universal"
            if isinstance(plat_name, dict):
                plat_name = plat_name.get("name", "Universal")
            if (not plat_name or plat_name in ("Universal", "Web", "Default")) and url:
                try:
                    p_info = detect_platform(url)
                    if p_info and isinstance(p_info, dict) and p_info.get("name"):
                        plat_name = p_info.get("name")
                    elif isinstance(p_info, str) and p_info:
                        plat_name = p_info
                except Exception:
                    pass

            # Escape HTML characters for Telegram HTML format
            safe_title = (title or "Media File").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe_device = str(device_str).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe_url = (url or "N/A").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            is_completed = str(status).lower() in ("completed", "done", "success")
            status_icon = "✅" if is_completed else ("⏳" if str(status).lower() == "started" else "⚠️")

            text = (
                f"📥 <b>[SKD TOOL] កំណត់ត្រាទាញយក (Download Alert)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>អ្នកប្រើប្រាស់/ម៉ាស៊ីន:</b> {safe_device}\n"
                f"🌐 <b>វេទិកា (Platform):</b> {plat_name}\n"
                f"🎬 <b>ចំណងជើង:</b> {safe_title}\n"
                f"🔗 <b>តំណភ្ជាប់:</b> {safe_url}\n"
                f"📊 <b>ទំហំ/កម្រិត:</b> {quality or 'Default'} | {size or 'Unknown'}\n"
                f"⏱️ <b>កាលបរិច្ឆេទ:</b> {timestamp}\n"
                f"⚡ <b>ស្ថានភាព:</b> {status_icon} {status}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            )

            api_url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": cid,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            resp = requests.post(api_url, json=payload, timeout=8)
            if resp.status_code != 200:
                # Fallback to plain text if HTML tags cause Telegram API rejection
                payload_plain = {
                    "chat_id": cid,
                    "text": text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""),
                    "disable_web_page_preview": True
                }
                requests.post(api_url, json=payload_plain, timeout=8)
        except Exception:
            # Silently handle network timeouts or API errors without interrupting the client
            pass

    threading.Thread(target=_worker, daemon=True).start()


def test_telegram_bot_connection(bot_token: str, chat_id: str) -> Dict[str, Any]:
    """
    Test sending an instant ping message to the specified Telegram Bot and Chat ID.
    Returns dictionary with success status and descriptive message.
    """
    import requests
    from datetime import datetime

    token = (bot_token or "").strip()
    cid = (chat_id or "").strip()

    if not token:
        return {"success": False, "error": "សូមបញ្ចូល Telegram Bot Token ជាមុនសិន!"}
    if not cid:
        return {"success": False, "error": "សូមបញ្ចូល Telegram Chat ID ឬ Channel ID ជាមុនសិន!"}

    try:
        device_str = get_device_and_user_identity()
        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

        text = (
            f"🚀 <b>[SKD TOOL] តេស្តភ្ជាប់ជោគជ័យ (Bot Test OK)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 Bot ត្រូវបានតភ្ជាប់ទៅកាន់ SKD Tool ដោយជោគជ័យ!\n"
            f"👤 <b>ឧបករណ៍/ម៉ាស៊ីន:</b> {device_str}\n"
            f"⏱️ <b>កាលបរិច្ឆេទ:</b> {timestamp}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>រាល់ពេលដែល User ធ្វើការ Download ព័ត៌មាននឹងផ្ញើមកកាន់ទីនេះភ្លាមៗ។</i>"
        )

        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "HTML"
        }
        resp = requests.post(api_url, json=payload, timeout=10)
        res_json = resp.json()
        if resp.status_code == 200 and res_json.get("ok"):
            return {"success": True, "message": "Bot បានផ្ញើសារសាកល្បងទៅ Telegram ដោយជោគជ័យ! (200 OK)"}
        else:
            err_desc = res_json.get("description") or f"HTTP {resp.status_code}"
            return {"success": False, "error": f"Telegram API Error: {err_desc}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "ដាច់ពេល (Timeout)! សូមពិនិត្យមើលអ៊ីនធឺណិត ឬ Telegram Token។"}
    except Exception as e:
        return {"success": False, "error": f"កំហុសក្នុងការតភ្ជាប់: {str(e)}"}


# Alias for backward compatibility
log_download_to_google_sheet = send_telegram_download_alert


