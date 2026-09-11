"""
=============================================================================
SKD TOOL - ULTIMATE UNIVERSAL DOWNLOADER ENGINE (ENTERPRISE MULTI-TIER)
=============================================================================
Architecture:
- Tier 1: Specialized Direct API Resolvers (TikTok, Douyin, Pinterest, Facebook, Instagram, Cloud Drives)
- Tier 2: Full Native M3U8 / HLS Stream Downloader (AES-128 Decryption, Multi-Threaded TS Merger)
- Tier 3: Universal Web Stream & Chinese Drama / Movie Sniffer (HTML5/IFrame/JS Player Parser)
- Tier 4: Turbo yt-dlp Engine with Client Rotation, n-sig Deciphering & Browser Cookie Auto-Fallback
- Tier 5: Direct Lossless FFmpeg Stream Capture
- Tier 6: Resilient Multi-Chunk Direct HTTP Streamer with Auto-Healing & Retry Shield
=============================================================================
"""

import os
import sys
import time
import shutil
import uuid
import re
import json
import threading
import subprocess
from datetime import datetime
import urllib.parse
import urllib3
import requests
from typing import Callable, Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Disable SSL insecure warnings for maximum compatibility with CDN streams
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try importing AES decryption for encrypted M3U8 HLS streams
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

import yt_dlp
from utils import (
    sanitize_filename,
    format_bytes,
    categorize_file,
    get_category_path,
    is_video_platform_url,
    play_completion_sound_and_voice,
    transform_cloud_url,
    humanize_download_error,
    detect_platform
)

# Modern Browser User-Agent Pool for Anti-Bot & 403 Forbidden Bypasses
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
]

def get_ffmpeg_location() -> Optional[str]:
    """Dynamically locate FFmpeg binary via imageio_ffmpeg, bundled assets, or system PATH."""
    try:
        import imageio_ffmpeg
        orig_path = imageio_ffmpeg.get_ffmpeg_exe()
        if orig_path and os.path.exists(orig_path):
            ffmpeg_dir = os.path.dirname(orig_path)
            target_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
            if not os.path.exists(target_exe):
                try:
                    shutil.copy(orig_path, target_exe)
                except Exception:
                    pass

            if ffmpeg_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

            return ffmpeg_dir
    except Exception:
        pass

    # Ensure Node.js is in PATH for yt-dlp JS runtime / n-sig execution
    node_dir = r"C:\Program Files\nodejs"
    if os.path.exists(os.path.join(node_dir, "node.exe")) and node_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = node_dir + os.pathsep + os.environ.get("PATH", "")

    return None

def parse_time_seconds(t_str: str) -> float:
    """Parse HH:MM:SS, MM:SS, or seconds string to float seconds."""
    if not t_str or str(t_str).lower() in ["inf", "end", ""]:
        return float('inf')
    try:
        parts = [float(p) for p in str(t_str).strip().split(':')]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:
            return parts[0]
    except Exception:
        pass
    return 0.0

class CancelledException(Exception):
    """Exception raised when download is cancelled by user."""
    pass


# =============================================================================
# M3U8 / HLS STREAM ENGINE (WITH AES-128 DECRYPTION & PARALLEL TS DOWNLOADER)
# =============================================================================
class M3U8StreamDownloader:
    """
    Dedicated Multi-Threaded M3U8 / HLS Live & VOD Stream Downloader.
    Supports:
    - Master Playlists (Auto-selects highest resolution/bandwidth)
    - AES-128 Stream Decryption via cryptography
    - 16 Parallel TS Segment Download Workers
    - Automatic Lossless MP4 / MKV / MP3 Merging with FFmpeg
    - Direct FFmpeg Stream Capture Fallback
    """
    def __init__(self, headers: Optional[dict] = None, proxy: str = ""):
        self.headers = headers or {
            'User-Agent': USER_AGENTS[0],
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Mode': 'cors',
            'Referer': ''
        }
        self.proxy = proxy

    def is_m3u8_url(self, url: str) -> bool:
        """Check if URL is an M3U8 playlist or HLS stream."""
        u = url.lower().split('?')[0]
        return u.endswith('.m3u8') or '.m3u8' in url.lower() or 'm3u8' in u

    def resolve_m3u8_playlist(self, url: str, referer: str = "") -> Tuple[str, str]:
        """Fetch M3U8 content and resolve master playlist to best media stream URL."""
        headers = dict(self.headers)
        if referer:
            headers['Referer'] = referer

        proxies = {'http': self.proxy, 'https': self.proxy} if self.proxy else None
        resp = requests.get(url, headers=headers, timeout=12, verify=False, proxies=proxies)
        resp.raise_for_status()
        content = resp.text

        if '#EXT-X-STREAM-INF' in content:
            # Master Playlist -> parse sub-playlists and select highest resolution and bandwidth
            best_score = -1
            best_url = url
            lines = content.splitlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('#EXT-X-STREAM-INF'):
                    m_bw = re.search(r'BANDWIDTH=(\d+)', line)
                    bw = int(m_bw.group(1)) if m_bw else 0
                    m_res = re.search(r'RESOLUTION=(\d+)x(\d+)', line)
                    res_val = (int(m_res.group(1)) * int(m_res.group(2))) if m_res else 0
                    score = (res_val * 1000) + bw

                    for j in range(i + 1, len(lines)):
                        sub_line = lines[j].strip()
                        if sub_line and not sub_line.startswith('#'):
                            if score > best_score:
                                best_score = score
                                best_url = urllib.parse.urljoin(url, sub_line)
                            break
            if best_url != url:
                resp2 = requests.get(best_url, headers=headers, timeout=12, verify=False, proxies=proxies)
                if resp2.status_code == 200:
                    return best_url, resp2.text

        return url, content

    def download_hls_stream(
        self,
        m3u8_url: str,
        save_path: str,
        quality: str = "1080p",
        title: str = "M3U8 Stream",
        thumbnail: str = "",
        referer: str = "",
        progress_callback: Optional[Callable] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        pause_check: Optional[Callable[[], bool]] = None,
        record_speed: Optional[Callable[[float], None]] = None
    ) -> str:
        """Download M3U8 HLS segments in parallel and merge seamlessly into MP4/MP3."""
        proxies = {'http': self.proxy, 'https': self.proxy} if self.proxy else None
        req_headers = dict(self.headers)
        if referer:
            req_headers['Referer'] = referer

        # 1. Resolve master playlist
        media_url, content = self.resolve_m3u8_playlist(m3u8_url, referer=referer)
        base_url = media_url

        # 2. Parse segments and AES-128 keys
        segments = []
        lines = content.splitlines()
        current_key = None
        seq = 0

        for line in lines:
            line = line.strip()
            if line.startswith('#EXT-X-KEY:'):
                method_m = re.search(r'METHOD=([^,\s]+)', line)
                uri_m = re.search(r'URI="([^"]+)"', line)
                iv_m = re.search(r'IV=0x([0-9a-fA-F]+)', line)
                
                method = method_m.group(1) if method_m else 'NONE'
                uri = uri_m.group(1) if uri_m else ''
                iv_hex = iv_m.group(1) if iv_m else ''

                if method.upper() == 'AES-128' and uri:
                    full_key_uri = urllib.parse.urljoin(base_url, uri)
                    try:
                        k_resp = requests.get(full_key_uri, headers=req_headers, timeout=10, verify=False, proxies=proxies)
                        if k_resp.status_code == 200 and len(k_resp.content) == 16:
                            current_key = {
                                'method': 'AES-128',
                                'uri': full_key_uri,
                                'key_bytes': k_resp.content,
                                'iv_hex': iv_hex
                            }
                    except Exception:
                        pass
                else:
                    current_key = {'method': method, 'uri': '', 'key_bytes': None, 'iv_hex': ''}

            elif line and not line.startswith('#'):
                full_seg_url = urllib.parse.urljoin(base_url, line)
                segments.append({
                    'index': seq,
                    'url': full_seg_url,
                    'key': dict(current_key) if current_key else None
                })
                seq += 1

        if not segments:
            return self._download_via_ffmpeg_direct(m3u8_url, save_path, quality, progress_callback, req_headers)

        tmp_dir = f"{save_path}_ts_tmp_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        os.makedirs(tmp_dir, exist_ok=True)

        total_segs = len(segments)
        completed_segs = 0
        total_downloaded_bytes = 0
        lock = threading.Lock()
        start_time = time.time()
        last_update_time = start_time
        bytes_since_last = 0
        segment_files = [None] * total_segs

        def decrypt_segment_data(raw_data: bytes, seg_info: dict) -> bytes:
            k = seg_info.get('key')
            if not k or k.get('method') != 'AES-128' or not k.get('key_bytes') or not HAS_CRYPTOGRAPHY:
                return raw_data
            try:
                key_bytes = k['key_bytes']
                if k.get('iv_hex'):
                    iv_bytes = bytes.fromhex(k['iv_hex'])
                else:
                    iv_bytes = seg_info['index'].to_bytes(16, byteorder='big')
                
                cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes), backend=default_backend())
                decryptor = cipher.decryptor()
                decrypted = decryptor.update(raw_data) + decryptor.finalize()
                
                pad_len = decrypted[-1]
                if 1 <= pad_len <= 16 and decrypted[-pad_len:] == bytes([pad_len] * pad_len):
                    return decrypted[:-pad_len]
                return decrypted
            except Exception:
                return raw_data

        def fetch_single_segment(seg_info: dict):
            nonlocal completed_segs, total_downloaded_bytes, bytes_since_last, last_update_time
            if cancel_check and cancel_check():
                raise CancelledException("Download cancelled.")

            while pause_check and pause_check():
                time.sleep(0.4)
                if cancel_check and cancel_check():
                    raise CancelledException("Download cancelled.")

            idx = seg_info['index']
            seg_url = seg_info['url']
            part_path = os.path.join(tmp_dir, f"seg_{idx:06d}.ts")

            for attempt in range(4):
                try:
                    r = requests.get(seg_url, headers=req_headers, timeout=18, verify=False, proxies=proxies)
                    if r.status_code == 200 and len(r.content) > 0:
                        decrypted_content = decrypt_segment_data(r.content, seg_info)
                        with open(part_path, 'wb') as f_seg:
                            f_seg.write(decrypted_content)
                        segment_files[idx] = part_path

                        with lock:
                            completed_segs += 1
                            total_downloaded_bytes += len(decrypted_content)
                            bytes_since_last += len(decrypted_content)

                            now = time.time()
                            elapsed = now - last_update_time

                            if elapsed >= 0.22 or completed_segs == total_segs:
                                speed = bytes_since_last / elapsed if elapsed > 0 else 0
                                pct = (completed_segs / total_segs) * 96.0
                                est_total_bytes = int((total_downloaded_bytes / completed_segs) * total_segs) if completed_segs > 0 else 0
                                eta = (total_segs - completed_segs) * (elapsed / (completed_segs or 1)) if completed_segs > 0 else 0

                                if record_speed:
                                    record_speed(speed)

                                if progress_callback:
                                    progress_callback({
                                        'status': 'downloading',
                                        'downloaded_bytes': total_downloaded_bytes,
                                        'total_bytes': est_total_bytes,
                                        'speed': speed,
                                        'eta': eta,
                                        'percent': pct,
                                        'filename': title,
                                        'title': title,
                                        'thumbnail': thumbnail
                                    })
                                last_update_time = now
                                bytes_since_last = 0
                        return
                except Exception:
                    time.sleep(0.5)

            with open(part_path, 'wb') as f_seg:
                pass
            segment_files[idx] = part_path

        try:
            with ThreadPoolExecutor(max_workers=16) as executor:
                futures = [executor.submit(fetch_single_segment, s) for s in segments]
                for fut in as_completed(futures):
                    fut.result()

            merged_ts = os.path.join(tmp_dir, "combined_stream.ts")
            with open(merged_ts, 'wb') as out_f:
                for sf in segment_files:
                    if sf and os.path.exists(sf):
                        with open(sf, 'rb') as in_f:
                            out_f.write(in_f.read())

            if progress_callback:
                progress_callback({
                    'status': 'downloading',
                    'downloaded_bytes': total_downloaded_bytes,
                    'total_bytes': total_downloaded_bytes,
                    'speed': 0,
                    'eta': 1,
                    'percent': 98.0,
                    'filename': title,
                    'title': f"Merging & Finalizing {title}...",
                    'thumbnail': thumbnail
                })

            ffmpeg_dir = get_ffmpeg_location()
            ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe") if ffmpeg_dir else "ffmpeg"

            if quality in ['audio_mp3', 'mp3']:
                cmd = [
                    ffmpeg_exe, '-y', '-i', merged_ts,
                    '-vn', '-ab', '320k', '-ar', '44100', '-f', 'mp3',
                    save_path
                ]
            else:
                cmd = [
                    ffmpeg_exe, '-y', '-i', merged_ts,
                    '-c', 'copy', '-bsf:a', 'aac_adtstoasc',
                    save_path
                ]

            try:
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' and hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            except Exception:
                # Fallback: copy video and re-encode audio to AAC if bitstream filter fails
                cmd_fb = [
                    ffmpeg_exe, '-y', '-i', merged_ts,
                    '-c:v', 'copy', '-c:a', 'aac',
                    save_path
                ]
                subprocess.run(
                    cmd_fb,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' and hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )

        finally:
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

        if record_speed:
            record_speed(0)

        if progress_callback:
            progress_callback({
                'status': 'finished',
                'downloaded_bytes': os.path.getsize(save_path) if os.path.exists(save_path) else total_downloaded_bytes,
                'total_bytes': os.path.getsize(save_path) if os.path.exists(save_path) else total_downloaded_bytes,
                'speed': 0,
                'eta': 0,
                'percent': 100.0,
                'filename': os.path.basename(save_path),
                'file_path': save_path,
                'thumbnail': thumbnail,
                'title': title
            })

        return save_path

    def _download_via_ffmpeg_direct(
        self,
        stream_url: str,
        save_path: str,
        quality: str,
        progress_callback: Optional[Callable],
        headers: dict
    ) -> str:
        ffmpeg_dir = get_ffmpeg_location()
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe") if ffmpeg_dir else "ffmpeg"

        header_str = "".join(f"{k}: {v}\r\n" for k, v in headers.items() if k.lower() in ['user-agent', 'referer'])
        
        if quality in ['audio_mp3', 'mp3']:
            cmd = [
                ffmpeg_exe, '-y',
                '-headers', header_str,
                '-i', stream_url,
                '-vn', '-ab', '320k', '-ar', '44100',
                save_path
            ]
        else:
            cmd = [
                ffmpeg_exe, '-y',
                '-headers', header_str,
                '-i', stream_url,
                '-c', 'copy', '-bsf:a', 'aac_adtstoasc',
                save_path
            ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' and hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        except Exception:
            cmd_fb = [
                ffmpeg_exe, '-y',
                '-headers', header_str,
                '-i', stream_url,
                '-c:v', 'copy', '-c:a', 'aac',
                save_path
            ]
            subprocess.run(
                cmd_fb,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' and hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        return save_path


# =============================================================================
# UNIVERSAL WEBPAGE VIDEO & DRAMA SNIFFER
# =============================================================================
class UniversalWebSniffer:
    """
    Intelligent Webpage Video & Stream Sniffer.
    Extracts direct .m3u8 playlists, .mp4 streams, HTML5 <video> tags,
    iframe players, and JSON configs from Chinese drama/movie websites and web portals.
    """
    def __init__(self, proxy: str = ""):
        self.proxy = proxy

    def sniff_stream(self, page_url: str) -> Optional[Dict[str, Any]]:
        headers = {
            'User-Agent': USER_AGENTS[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,km;q=0.7',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate'
        }
        proxies = {'http': self.proxy, 'https': self.proxy} if self.proxy else None

        try:
            resp = requests.get(page_url, headers=headers, timeout=10, verify=False, proxies=proxies)
            if resp.status_code != 200:
                return None

            html = resp.text

            # 1. Extract Page Title & Thumbnail
            title_m = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
            raw_title = title_m.group(1).strip() if title_m else 'Web_Media_Stream'
            raw_title = re.sub(r'(\s*-\s*|\||_)(Watch Online|Free Drama|HD|Movies|Streaming).*$', '', raw_title, flags=re.IGNORECASE)
            title = sanitize_filename(raw_title[:80])

            thumb_m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            thumbnail = thumb_m.group(1) if thumb_m else ''

            # 2. Match direct .m3u8 URLs in HTML or JS
            m3u8_matches = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html, re.IGNORECASE)
            if m3u8_matches:
                clean_stream = m3u8_matches[0].replace('\\/', '/').replace('&amp;', '&')
                return {
                    'stream_url': clean_stream,
                    'type': 'm3u8',
                    'title': title,
                    'thumbnail': thumbnail,
                    'referer': page_url
                }

            # 3. Match direct .mp4 URLs
            mp4_matches = re.findall(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', html, re.IGNORECASE)
            if mp4_matches:
                clean_mp4 = mp4_matches[0].replace('\\/', '/').replace('&amp;', '&')
                return {
                    'stream_url': clean_mp4,
                    'type': 'direct',
                    'title': title,
                    'thumbnail': thumbnail,
                    'referer': page_url
                }

            # 4. Search common JavaScript player configs
            js_stream_m = re.search(r'(?:url|source|file|hlsUrl|videoUrl|src)\s*:\s*["\'](https?://[^"\']+)["\']', html, re.IGNORECASE)
            if js_stream_m:
                st_url = js_stream_m.group(1).replace('\\/', '/').replace('&amp;', '&')
                is_m3u8 = '.m3u8' in st_url.lower()
                return {
                    'stream_url': st_url,
                    'type': 'm3u8' if is_m3u8 else 'direct',
                    'title': title,
                    'thumbnail': thumbnail,
                    'referer': page_url
                }

            # 5. Check iframes for video embed players
            iframe_m = re.findall(r'<iframe\s+[^>]*src=["\'](https?://[^"\']+)["\']', html, re.IGNORECASE)
            for if_url in iframe_m:
                if any(x in if_url.lower() for x in ['player', 'embed', 'video', 'm3u8', 'stream', 'share']):
                    try:
                        if_resp = requests.get(if_url, headers=headers, timeout=8, verify=False, proxies=proxies)
                        if if_resp.status_code == 200:
                            sub_html = if_resp.text
                            sub_m3u8 = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', sub_html, re.IGNORECASE)
                            if sub_m3u8:
                                return {
                                    'stream_url': sub_m3u8[0].replace('\\/', '/').replace('&amp;', '&'),
                                    'type': 'm3u8',
                                    'title': title,
                                    'thumbnail': thumbnail,
                                    'referer': if_url
                                }
                    except Exception:
                        pass

        except Exception:
            pass

        return None


# =============================================================================
# CORE DOWNLOADER ENGINE (ENTERPRISE MULTI-PLATFORM)
# =============================================================================
class DownloaderEngine:
    def __init__(self):
        self._is_cancelled = False
        self._is_paused = False
        self.speed_limit_bytes = 0  # 0 means unlimited
        self.browser_cookies = "none"
        self.proxy_url = ""
        self.speed_history: List[float] = [0.0] * 30
        self._metadata_cache: Dict[str, Any] = {}

        # Sub-engines
        self.m3u8_engine = M3U8StreamDownloader(proxy=self.proxy_url)
        self.web_sniffer = UniversalWebSniffer(proxy=self.proxy_url)

        # Initialize FFmpeg dynamically
        get_ffmpeg_location()

    def cancel(self):
        self._is_cancelled = True

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def reset_cancel(self):
        self._is_cancelled = False
        self._is_paused = False

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def is_paused(self) -> bool:
        return self._is_paused

    def check_pause(self):
        """Helper to block while paused, immediately unblocking on cancel."""
        while self._is_paused and not self._is_cancelled:
            time.sleep(0.15)
        if self._is_cancelled:
            raise CancelledException("Download cancelled by user.")

    def set_speed_limit(self, max_kb_s: float):
        self.speed_limit_bytes = int(max_kb_s * 1024)

    def set_network_options(self, browser_cookies: str = "none", proxy_url: str = ""):
        self.browser_cookies = browser_cookies or "none"
        self.proxy_url = proxy_url.strip()
        self.m3u8_engine.proxy = self.proxy_url
        self.web_sniffer.proxy = self.proxy_url

    def record_speed(self, speed_bytes_per_sec: float):
        kb_s = speed_bytes_per_sec / 1024.0
        self.speed_history.append(round(kb_s, 1))
        if len(self.speed_history) > 40:
            self.speed_history.pop(0)

    # -------------------------------------------------------------------------
    # TIER 1: TIKTOK / DOUYIN RESOLVER
    # -------------------------------------------------------------------------
    def _fetch_tiktok_data(self, url: str) -> Optional[Dict[str, Any]]:
        clean_url = url.split('?')[0] if 'tiktok.com' in url else url
        urls_to_try = [url] if url == clean_url else [clean_url, url]
        headers = {
            'User-Agent': USER_AGENTS[0],
            'Accept': 'application/json, text/plain, */*'
        }
        endpoints = [
            "https://www.tikwm.com/api/?hd=1&url=",
            "https://tikwm.com/api/?hd=1&url=",
            "https://api.tikwm.com/api/?hd=1&url="
        ]
        proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None

        for u in urls_to_try:
            for base_ep in endpoints:
                try:
                    full_api = f"{base_ep}{requests.utils.quote(u)}"
                    r = requests.get(full_api, headers=headers, timeout=9, verify=False, proxies=proxies)
                    if r.status_code == 200:
                        j = r.json()
                        if j.get('code') == 0 and j.get('data'):
                            return j['data']
                except Exception:
                    continue
        return None

    def download_tiktok(
        self,
        url: str,
        output_dir: str,
        quality: str = '1080p',
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        self.reset_cancel()
        os.makedirs(output_dir, exist_ok=True)
        clean_url = url.split('?')[0] if 'tiktok.com' in url else url

        data = None
        cached_entry = self._metadata_cache.get(clean_url) or self._metadata_cache.get(url)
        if cached_entry and (time.time() - cached_entry['time'] < 300):
            data = cached_entry.get('raw_data')

        if not data:
            data = self._fetch_tiktok_data(url)

        if not data:
            raise Exception("TikTok API resolver unreachable, switching to next engine...")

        raw_title = data.get('title') or f"TikTok_{data.get('id', int(time.time()))}"
        title = sanitize_filename(raw_title[:80])
        cover_url = data.get('cover') or data.get('origin_cover') or data.get('dynamic_cover') or ''
        duration = data.get('duration', 0)

        images = data.get('images')
        if images and isinstance(images, list) and len(images) > 0 and quality not in ['audio_mp3', 'mp3']:
            folder_name = f"{title}_photos"
            photos_dir = os.path.join(output_dir, folder_name)
            os.makedirs(photos_dir, exist_ok=True)
            downloaded_photos = []
            headers = {'User-Agent': USER_AGENTS[0]}
            proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None

            for idx, img_url in enumerate(images):
                if not img_url:
                    continue
                if self._is_cancelled:
                    raise CancelledException("Download cancelled by user.")
                while self._is_paused and not self._is_cancelled:
                    time.sleep(0.2)
                if self._is_cancelled:
                    raise CancelledException("Download cancelled by user.")
                img_name = f"photo_{idx + 1:02d}.jpg"
                img_path = os.path.join(photos_dir, img_name)
                try:
                    r_img = requests.get(img_url, headers=headers, timeout=15, verify=False, proxies=proxies)
                    if r_img.status_code == 200:
                        with open(img_path, 'wb') as f_img:
                            f_img.write(r_img.content)
                        downloaded_photos.append(img_path)
                except Exception:
                    pass
                if progress_callback:
                    pct = round(((idx + 1) / len(images)) * 100, 1)
                    progress_callback({
                        'percent': pct,
                        'downloaded_bytes': idx + 1,
                        'total_bytes': len(images),
                        'speed': 1024 * 500,
                        'eta': max(0, len(images) - idx - 1),
                        'status': 'downloading',
                        'title': f"Downloading TikTok Photos ({idx + 1}/{len(images)})",
                        'thumbnail': cover_url
                    })

            music_url = data.get('music')
            if music_url:
                try:
                    m_resp = requests.get(music_url, headers=headers, timeout=15, verify=False, proxies=proxies)
                    if m_resp.status_code == 200:
                        with open(os.path.join(photos_dir, "audio.mp3"), 'wb') as f_m:
                            f_m.write(m_resp.content)
                except Exception:
                    pass

            total_s = sum(os.path.getsize(p) for p in downloaded_photos if os.path.exists(p))
            return {
                'filename': folder_name,
                'path': photos_dir,
                'size': total_s,
                'thumbnail': cover_url,
                'title': f"{raw_title} ({len(downloaded_photos)} Photos)",
                'duration': 0
            }

        if quality in ['audio_mp3', 'mp3']:
            stream_url = data.get('music')
            ext = ".mp3"
        else:
            # Prioritize HD 1080p crystal clear stream (hdplay)
            stream_url = data.get('hdplay')
            if not stream_url:
                # Fallback to turbo yt-dlp to extract high-bitrate original camera stream
                try:
                    saved_path = self.download_ytdlp(
                        url=url,
                        output_dir=output_dir,
                        quality=quality,
                        progress_callback=progress_callback
                    )
                    return {
                        'filename': os.path.basename(saved_path),
                        'path': saved_path,
                        'size': os.path.getsize(saved_path) if os.path.exists(saved_path) else 0,
                        'thumbnail': cover_url,
                        'title': raw_title,
                        'duration': duration
                    }
                except Exception:
                    stream_url = data.get('play') or data.get('wmplay')
            ext = ".mp4"

        if stream_url and stream_url.startswith('/'):
            stream_url = f"https://www.tikwm.com{stream_url}"

        if not stream_url:
            raise Exception("No valid stream found for TikTok video.")

        save_path = os.path.join(output_dir, f"{title}{ext}")
        base, extension = os.path.splitext(save_path)
        counter = 1
        while os.path.exists(save_path):
            save_path = f"{base}_{counter}{extension}"
            counter += 1

        saved_file = self._download_single_stream(
            url=stream_url,
            save_path=save_path,
            total_bytes=0,
            progress_callback=progress_callback,
            thumbnail=cover_url,
            title=raw_title,
            duration=duration
        )
        return {
            'filename': os.path.basename(saved_file),
            'path': saved_file,
            'size': os.path.getsize(saved_file) if os.path.exists(saved_file) else 0,
            'thumbnail': cover_url,
            'title': raw_title,
            'duration': duration
        }

    # -------------------------------------------------------------------------
    # TIER 1: PINTEREST RESOLVER
    # -------------------------------------------------------------------------
    def _resolve_pinterest_url(self, url: str) -> str:
        headers = {'User-Agent': USER_AGENTS[0]}
        if 'pin.it' in url or '/sent/' in url:
            try:
                proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None
                r = requests.head(url, allow_redirects=True, timeout=8, headers=headers, verify=False, proxies=proxies)
                return r.url
            except Exception:
                pass
        return url

    def download_pinterest(
        self,
        url: str,
        output_dir: str,
        quality: str = '1080p',
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        self.reset_cancel()
        os.makedirs(output_dir, exist_ok=True)
        canonical_url = self._resolve_pinterest_url(url)

        headers = {
            'User-Agent': USER_AGENTS[0],
            'X-Pinterest-PWS-Handler': 'www/[username].js'
        }
        proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None

        d = None
        m = re.search(r'/pin/(\d+)', canonical_url)
        if m:
            pin_id = m.group(1)
            try:
                q = json.dumps({'options': {'id': pin_id, 'field_set_key': 'unauth_react_main_pin'}})
                api_url = f"https://www.pinterest.com/resource/PinResource/get/?data={requests.utils.quote(q)}"
                res = requests.get(api_url, headers=headers, timeout=10, verify=False, proxies=proxies).json()
                d = res.get('resource_response', {}).get('data', {})
            except Exception:
                pass

        if not d or not d.get('videos'):
            saved_path = self.download_ytdlp(
                url=canonical_url,
                output_dir=output_dir,
                quality=quality,
                progress_callback=progress_callback
            )
            return {
                'filename': os.path.basename(saved_path),
                'path': saved_path,
                'size': os.path.getsize(saved_path) if os.path.exists(saved_path) else 0,
                'thumbnail': '',
                'title': os.path.basename(saved_path),
                'duration': 0
            }

        videos = d.get('videos', {}).get('video_list', {})
        raw_title = d.get('title') or d.get('grid_title') or f"Pinterest_{d.get('id', int(time.time()))}"
        title = sanitize_filename(raw_title[:70])
        cover_url = d.get('images', {}).get('orig', {}).get('url') or ''
        duration = 0

        stream_url = None
        for key in ['V_720P', 'V_EXP7', 'V_EXP6']:
            if key in videos and videos[key].get('url', '').endswith('.mp4'):
                stream_url = videos[key]['url']
                duration = int(videos[key].get('duration', 0) / 1000)
                break

        if not stream_url:
            for k, v in videos.items():
                if v.get('url', '').endswith('.mp4'):
                    stream_url = v['url']
                    duration = int(v.get('duration', 0) / 1000)
                    break

        if not stream_url and 'V_HLSV4' in videos:
            stream_url = videos['V_HLSV4'].get('url')

        if not stream_url:
            saved_path = self.download_ytdlp(url=canonical_url, output_dir=output_dir, quality=quality, progress_callback=progress_callback)
            return {
                'filename': os.path.basename(saved_path),
                'path': saved_path,
                'size': os.path.getsize(saved_path) if os.path.exists(saved_path) else 0,
                'thumbnail': cover_url,
                'title': raw_title,
                'duration': duration
            }

        ext = ".mp3" if quality in ['audio_mp3', 'mp3'] else ".mp4"
        save_path = os.path.join(output_dir, f"{title}{ext}")
        base, extension = os.path.splitext(save_path)
        counter = 1
        while os.path.exists(save_path):
            save_path = f"{base}_{counter}{extension}"
            counter += 1

        if '.m3u8' in stream_url:
            self.m3u8_engine.download_hls_stream(
                m3u8_url=stream_url,
                save_path=save_path,
                quality=quality,
                title=raw_title,
                thumbnail=cover_url,
                progress_callback=progress_callback,
                cancel_check=self.is_cancelled,
                pause_check=self.is_paused,
                record_speed=self.record_speed
            )
        else:
            self._download_single_stream(
                url=stream_url,
                save_path=save_path,
                total_bytes=0,
                progress_callback=progress_callback,
                thumbnail=cover_url,
                title=raw_title,
                duration=duration
            )

        return {
            'filename': os.path.basename(save_path),
            'path': save_path,
            'size': os.path.getsize(save_path) if os.path.exists(save_path) else 0,
            'thumbnail': cover_url,
            'title': raw_title,
            'duration': duration
        }

    # -------------------------------------------------------------------------
    # TIER 1: FACEBOOK DIRECT RESOLVER FALLBACK
    # -------------------------------------------------------------------------
    def download_facebook(
        self,
        url: str,
        output_dir: str,
        quality: str = '1080p',
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        self.reset_cancel()
        os.makedirs(output_dir, exist_ok=True)

        try:
            saved_file = self.download_ytdlp(
                url=url,
                output_dir=output_dir,
                quality=quality,
                progress_callback=progress_callback
            )
            return {
                'filename': os.path.basename(saved_file),
                'path': saved_file,
                'size': os.path.getsize(saved_file) if os.path.exists(saved_file) else 0,
                'thumbnail': '',
                'title': os.path.basename(saved_file)
            }
        except Exception:
            pass

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Mode': 'navigate'
        }
        proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None

        resp = requests.get(url, headers=headers, timeout=12, verify=False, proxies=proxies)
        html = resp.text

        hd_match = (
            re.search(r'hd_src:"([^"]+)"', html) or 
            re.search(r'"browser_native_hd_url":"([^"]+)"', html) or
            re.search(r'"playable_url_quality_hd":"([^"]+)"', html) or
            re.search(r'"hd_src_no_ratelimit":"([^"]+)"', html) or
            re.search(r'"representation_id":\s*"[^"]*hd[^"]*".*?"base_url":\s*"([^"]+)"', html, re.IGNORECASE)
        )
        sd_match = (
            re.search(r'sd_src:"([^"]+)"', html) or 
            re.search(r'"browser_native_sd_url":"([^"]+)"', html) or
            re.search(r'"playable_url":"([^"]+)"', html) or
            re.search(r'"sd_src_no_ratelimit":"([^"]+)"', html) or
            re.search(r'"representation_id":.*?"base_url":\s*"([^"]+)"', html)
        )

        raw_stream = (hd_match.group(1) if hd_match else (sd_match.group(1) if sd_match else ""))
        stream_url = raw_stream.replace('\\/', '/').replace('\\u0025', '%').replace('\\u0026', '&')

        if not stream_url:
            raise Exception("Facebook video stream extraction failed. Please ensure video is public.")

        title = f"Facebook_Video_{int(time.time())}"
        ext = ".mp3" if quality in ['audio_mp3', 'mp3'] else ".mp4"
        save_path = os.path.join(output_dir, f"{title}{ext}")

        saved_file = self._download_single_stream(
            url=stream_url,
            save_path=save_path,
            total_bytes=0,
            progress_callback=progress_callback,
            title="Facebook Video"
        )
        return {
            'filename': os.path.basename(saved_file),
            'path': saved_file,
            'size': os.path.getsize(saved_file) if os.path.exists(saved_file) else 0,
            'thumbnail': '',
            'title': "Facebook Video"
        }

    # -------------------------------------------------------------------------
    # THUMBNAIL DOWNLOADER
    # -------------------------------------------------------------------------
    def download_thumbnail_file(self, url: str, output_dir: str) -> Dict[str, Any]:
        meta = self.analyze_url_advanced(url)
        thumb_url = meta.get('thumbnail', '')
        if not thumb_url:
            raise Exception("No thumbnail image found for this media URL.")
        title = sanitize_filename(meta.get('title', 'Thumbnail')[:70])
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, f"{title}_Cover.jpg")
        counter = 1
        base, ext = os.path.splitext(save_path)
        while os.path.exists(save_path):
            save_path = f"{base}_{counter}{ext}"
            counter += 1

        headers = {'User-Agent': USER_AGENTS[0]}
        proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None
        resp = requests.get(thumb_url, headers=headers, timeout=15, verify=False, proxies=proxies)
        if resp.status_code != 200:
            raise Exception(f"Failed to download cover image: HTTP {resp.status_code}")

        with open(save_path, 'wb') as f:
            f.write(resp.content)

        return {
            'filename': os.path.basename(save_path),
            'path': save_path,
            'size': os.path.getsize(save_path),
            'thumbnail': thumb_url,
            'title': meta.get('title', 'Media Cover')
        }

    # -------------------------------------------------------------------------
    # UNIFIED CASCADE DOWNLOAD ENTRY POINT (ZERO-ERROR ARCHITECTURE)
    # -------------------------------------------------------------------------
    def download(
        self,
        url: str,
        output_dir: str,
        quality: str = '1080p',
        progress_callback: Optional[Callable] = None,
        download_subs: bool = False,
        bitrate: str = '320k',
        trim_start: str = '',
        trim_end: str = ''
    ) -> Dict[str, Any]:
        self.reset_cancel()
        os.makedirs(output_dir, exist_ok=True)
        u_clean = url.strip()
        u_lower = u_clean.lower()

        q_map = {'4k': '4k', '1080p': '1080p', '720p': '720p', 'mp3': 'audio_mp3'}
        eff_quality = q_map.get(quality.lower(), quality)

        # TIER 1: SPECIALIZED PLATFORM RESOLVERS
        if 'tiktok.com' in u_lower or 'douyin.com' in u_lower:
            try:
                tk_res = self.download_tiktok(url=u_clean, output_dir=output_dir, quality=eff_quality, progress_callback=progress_callback)
                return tk_res
            except CancelledException:
                raise
            except Exception as e:
                if self.is_cancelled() or "cancelled" in str(e).lower():
                    raise CancelledException("Download cancelled by user.")
                pass

        elif 'pinterest.com' in u_lower or 'pin.it' in u_lower or 'pinterest.' in u_lower:
            try:
                pin_res = self.download_pinterest(url=u_clean, output_dir=output_dir, quality=eff_quality, progress_callback=progress_callback)
                return pin_res
            except CancelledException:
                raise
            except Exception as e:
                if self.is_cancelled() or "cancelled" in str(e).lower():
                    raise CancelledException("Download cancelled by user.")
                pass

        elif 'facebook.com' in u_lower or 'fb.watch' in u_lower or 'fb.com' in u_lower:
            try:
                fb_res = self.download_facebook(url=u_clean, output_dir=output_dir, quality=eff_quality, progress_callback=progress_callback)
                return fb_res
            except CancelledException:
                raise
            except Exception as e:
                if self.is_cancelled() or "cancelled" in str(e).lower():
                    raise CancelledException("Download cancelled by user.")
                pass

        # TIER 2: DIRECT M3U8 / HLS STREAMS
        if '.m3u8' in u_lower:
            try:
                title = f"Stream_{int(time.time())}"
                ext = ".mp3" if eff_quality in ['audio_mp3', 'mp3'] else ".mp4"
                save_path = os.path.join(output_dir, f"{title}{ext}")
                self.m3u8_engine.download_hls_stream(
                    m3u8_url=u_clean,
                    save_path=save_path,
                    quality=eff_quality,
                    title="M3U8 HLS Stream",
                    progress_callback=progress_callback,
                    cancel_check=self.is_cancelled,
                    pause_check=self.is_paused,
                    record_speed=self.record_speed
                )
                return {
                    'filename': os.path.basename(save_path),
                    'path': save_path,
                    'size': os.path.getsize(save_path) if os.path.exists(save_path) else 0,
                    'thumbnail': '',
                    'title': os.path.basename(save_path)
                }
            except CancelledException:
                raise
            except Exception as e:
                if self.is_cancelled() or "cancelled" in str(e).lower():
                    raise CancelledException("Download cancelled by user.")
                pass

        # TIER 3: UNIVERSAL WEBPAGE VIDEO & CHINESE DRAMA SNIFFER
        if not is_video_platform_url(u_clean) and not any(u_lower.endswith(ext) for ext in ['.mp4', '.mkv', '.zip', '.rar', '.exe', '.mp3']):
            try:
                sniffed = self.web_sniffer.sniff_stream(u_clean)
                if sniffed and sniffed.get('stream_url'):
                    st_url = sniffed['stream_url']
                    st_title = sniffed.get('title') or f"Web_Video_{int(time.time())}"
                    st_thumb = sniffed.get('thumbnail', '')
                    ext = ".mp3" if eff_quality in ['audio_mp3', 'mp3'] else ".mp4"
                    save_path = os.path.join(output_dir, f"{st_title}{ext}")

                    if sniffed.get('type') == 'm3u8':
                        self.m3u8_engine.download_hls_stream(
                            m3u8_url=st_url,
                            save_path=save_path,
                            quality=eff_quality,
                            title=st_title,
                            thumbnail=st_thumb,
                            referer=sniffed.get('referer', u_clean),
                            progress_callback=progress_callback,
                            cancel_check=self.is_cancelled,
                            pause_check=self.is_paused,
                            record_speed=self.record_speed
                        )
                    else:
                        self._download_single_stream(
                            url=st_url,
                            save_path=save_path,
                            total_bytes=0,
                            progress_callback=progress_callback,
                            thumbnail=st_thumb,
                            title=st_title
                        )
                    return {
                        'filename': os.path.basename(save_path),
                        'path': save_path,
                        'size': os.path.getsize(save_path) if os.path.exists(save_path) else 0,
                        'thumbnail': st_thumb,
                        'title': st_title
                    }
            except CancelledException:
                raise
            except Exception as e:
                if self.is_cancelled() or "cancelled" in str(e).lower():
                    raise CancelledException("Download cancelled by user.")
                pass

        # TIER 4: TURBO YT-DLP ENGINE
        try:
            file_path = self.download_ytdlp(
                url=u_clean,
                output_dir=output_dir,
                quality=eff_quality,
                audio_bitrate=bitrate,
                download_subtitles=download_subs,
                start_time=trim_start,
                end_time=trim_end,
                progress_callback=progress_callback
            )
            cached = self._metadata_cache.get(u_clean) or {}
            thumb_out = cached.get('info', {}).get('thumbnail', '')
            title_out = cached.get('info', {}).get('title', '') or os.path.basename(file_path)

            return {
                'filename': os.path.basename(file_path),
                'path': file_path,
                'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'thumbnail': thumb_out,
                'title': title_out
            }
        except CancelledException:
            raise
        except Exception as e_ytdlp:
            if self.is_cancelled() or "cancelled" in str(e_ytdlp).lower():
                raise CancelledException("Download cancelled by user.")
            # TIER 5 & 6: DIRECT STREAM RESILIENT HTTP CHUNKER FALLBACK
            try:
                file_path = self.download_direct_file(
                    url=u_clean,
                    output_dir=output_dir,
                    progress_callback=progress_callback
                )
                return {
                    'filename': os.path.basename(file_path),
                    'path': file_path,
                    'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    'thumbnail': '',
                    'title': os.path.basename(file_path)
                }
            except CancelledException:
                raise
            except Exception as e_direct:
                if self.is_cancelled() or "cancelled" in str(e_direct).lower():
                    raise CancelledException("Download cancelled by user.")
                friendly_err = humanize_download_error(str(e_ytdlp))
                raise Exception(friendly_err)

    # -------------------------------------------------------------------------
    # YT-DLP CONFIGURATION BUILDER (FIXES N-SIG, 403 & BOT CHECK)
    # -------------------------------------------------------------------------
    def _build_ytdlp_base_opts(self) -> Dict[str, Any]:
        ffmpeg_dir = get_ffmpeg_location()
        opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'ignoreerrors': False,
            'retries': 100,
            'fragment_retries': 100,
            'skip_unavailable_fragments': False,
            'concurrent_fragment_downloads': 8,
            'socket_timeout': 45,
            'buffersize': 8388608,
            'continuedl': True,
            'windowsfilenames': True,
            'js_runtimes': {
                'node': {}
            },
            'format_sort': [
                'res', 'fps',
                'codec:av01', 'codec:vp9.2', 'codec:vp9', 'codec:h264',
                'quality', 'vbr', 'abr', 'size', 'br'
            ],
            'format_sort_force': True,
            'prefer_free_formats': False,
            'extractor_args': {
                'tiktok': {
                    'webpage_download': True
                }
            },
            'http_headers': {
                'User-Agent': USER_AGENTS[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        if ffmpeg_dir:
            opts['ffmpeg_location'] = ffmpeg_dir
            opts['merge_output_format'] = 'mp4'

        if self.browser_cookies and self.browser_cookies.lower() not in ["none", ""]:
            opts['cookiesfrombrowser'] = (self.browser_cookies.lower(),)

        if self.proxy_url:
            opts['proxy'] = self.proxy_url

        return opts

    # -------------------------------------------------------------------------
    # METADATA ANALYZER & URL INSPECTOR
    # -------------------------------------------------------------------------
    def detect_media_platform(self, url: str) -> Dict[str, str]:
        return detect_platform(url)

    def fetch_url_info(self, url: str) -> Dict[str, Any]:
        return self.analyze_url_advanced(url)

    def analyze_url_advanced(self, url: str) -> Dict[str, Any]:
        if not url:
            return {'type': 'unknown', 'title': 'Media File', 'thumbnail': '', 'duration': 0, 'platform': {'name': 'Unknown'}}

        clean_url = url.split('?')[0] if 'tiktok.com' in url else url
        platform_info = self.detect_media_platform(url)

        cached = self._metadata_cache.get(clean_url) or self._metadata_cache.get(url)
        if cached and (time.time() - cached['time'] < 300):
            return cached['info']

        # TikTok Fast Inspection
        if 'tiktok.com' in url.lower() or 'douyin.com' in url.lower():
            try:
                d = self._fetch_tiktok_data(url)
                if d:
                    dur = d.get('duration', 0)
                    dur_str = f"{int(dur//60):02d}:{int(dur%60):02d}" if dur > 0 else "00:00"
                    res = {
                        'type': 'video',
                        'platform': platform_info,
                        'title': d.get('title', 'TikTok Video'),
                        'thumbnail': d.get('cover') or d.get('origin_cover') or '',
                        'duration': dur,
                        'duration_str': dur_str,
                        'uploader': d.get('author', {}).get('nickname', 'TikTok Creator'),
                        'upload_date': datetime.now().strftime("%Y-%m-%d"),
                        'subtitles': [],
                        'has_4k': False,
                        'has_1080p': True,
                        'qualities': ['1080p', '720p', 'audio_mp3'],
                        'formats': ['MP4 (HD No Watermark)', 'MP3 (Audio 320kbps)'],
                        'estimated_size_str': '15 - 60 MB',
                        'raw_info': d
                    }
                    self._metadata_cache[clean_url] = {'time': time.time(), 'info': res, 'raw_data': d}
                    self._metadata_cache[url] = self._metadata_cache[clean_url]
                    return res
            except Exception:
                pass

        # Pinterest Fast Inspection
        if 'pinterest.com' in url.lower() or 'pin.it' in url.lower() or 'pinterest.' in url.lower():
            try:
                can_url = self._resolve_pinterest_url(url)
                m = re.search(r'/pin/(\d+)', can_url)
                if m:
                    pin_id = m.group(1)
                    q = json.dumps({'options': {'id': pin_id, 'field_set_key': 'unauth_react_main_pin'}})
                    api_url = f"https://www.pinterest.com/resource/PinResource/get/?data={requests.utils.quote(q)}"
                    headers = {'User-Agent': USER_AGENTS[0], 'X-Pinterest-PWS-Handler': 'www/[username].js'}
                    proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None
                    res = requests.get(api_url, headers=headers, timeout=8, proxies=proxies).json()
                    d = res.get('resource_response', {}).get('data', {})
                    if d:
                        raw_title = d.get('title') or d.get('grid_title') or f"Pinterest_{pin_id}"
                        cover_url = d.get('images', {}).get('orig', {}).get('url') or ''
                        videos = d.get('videos', {}).get('video_list', {})
                        dur = 0
                        for v in videos.values():
                            if v.get('duration'):
                                dur = int(v['duration'] / 1000)
                                break
                        dur_str = f"{int(dur//60):02d}:{int(dur%60):02d}" if dur > 0 else "00:00"
                        res_info = {
                            'type': 'video' if videos else 'image',
                            'platform': platform_info,
                            'title': raw_title,
                            'thumbnail': cover_url,
                            'duration': dur,
                            'duration_str': dur_str,
                            'uploader': d.get('pinner', {}).get('username', 'Pinterest Creator'),
                            'upload_date': datetime.now().strftime("%Y-%m-%d"),
                            'subtitles': [],
                            'has_4k': False,
                            'has_1080p': True,
                            'qualities': ['1080p', '720p', 'audio_mp3'],
                            'formats': ['MP4 (High Definition)', 'MP3 (Audio 320kbps)'],
                            'estimated_size_str': '5 - 40 MB',
                            'raw_info': d
                        }
                        self._metadata_cache[clean_url] = {'time': time.time(), 'info': res_info, 'raw_data': d}
                        self._metadata_cache[url] = self._metadata_cache[clean_url]
                        return res_info
            except Exception:
                pass

        # M3U8 Direct Link Fast Inspection
        if '.m3u8' in url.lower():
            res = {
                'type': 'video',
                'platform': platform_info,
                'title': f"M3U8_Stream_{int(time.time())}",
                'thumbnail': '',
                'duration': 0,
                'duration_str': 'Live / VOD',
                'uploader': 'HLS Stream Server',
                'upload_date': datetime.now().strftime("%Y-%m-%d"),
                'subtitles': [],
                'has_4k': True,
                'has_1080p': True,
                'qualities': ['1080p', '720p', 'audio_mp3'],
                'formats': ['MP4 (Lossless HLS Merge)', 'MP3 (Audio 320kbps)'],
                'estimated_size_str': 'Auto HLS Stream'
            }
            self._metadata_cache[url] = {'time': time.time(), 'info': res, 'raw_data': res}
            return res

        # Direct Media Link Fast Inspection
        if any(url.lower().endswith(ext) or ext in url.lower() for ext in ['.mp4', '.mkv', '.webm', '.mov', '.avi', '.mp3', '.m4a', '.wav', '.zip', '.rar', '.iso', '.exe']):
            try:
                proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None
                headers = {'User-Agent': USER_AGENTS[0], 'Accept': '*/*'}
                resp = requests.head(url, headers=headers, allow_redirects=True, timeout=8, proxies=proxies, verify=False)
                content_length = int(resp.headers.get('Content-Length', 0))
                content_type = resp.headers.get('Content-Type', 'application/octet-stream')
                accept_ranges = resp.headers.get('Accept-Ranges', '').lower() == 'bytes'

                filename = url.split('/')[-1].split('?')[0] or 'media_stream.mp4'
                cd = resp.headers.get('Content-Disposition')
                if cd and 'filename=' in cd:
                    filename = cd.split('filename=')[-1].strip('"\'')

                res = {
                    'type': 'direct',
                    'platform': platform_info,
                    'title': filename,
                    'file_size': content_length,
                    'estimated_size_bytes': content_length,
                    'estimated_size_str': format_bytes(content_length) if content_length > 0 else "Direct Stream",
                    'content_type': content_type,
                    'accept_ranges': accept_ranges,
                    'thumbnail': '',
                    'duration': 0,
                    'duration_str': '--:--',
                    'uploader': 'Direct Web Server',
                    'upload_date': datetime.now().strftime("%Y-%m-%d"),
                    'qualities': ['direct'],
                    'formats': ['Direct Stream']
                }
                self._metadata_cache[clean_url] = {'time': time.time(), 'info': res, 'raw_data': res}
                self._metadata_cache[url] = self._metadata_cache[clean_url]
                return res
            except Exception:
                pass

        # Turbo yt-dlp Deep Inspection
        ydl_opts = self._build_ytdlp_base_opts()
        ydl_opts['skip_download'] = True

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    if 'entries' in info:
                        entries = [e for e in info.get('entries', []) if e]
                        dur_total = sum(e.get('duration', 0) for e in entries if e and e.get('duration'))
                        dur_str = f"{int(dur_total//3600):02d}:{int((dur_total%3600)//60):02d}:{int(dur_total%60):02d}" if dur_total >= 3600 else f"{int(dur_total//60):02d}:{int(dur_total%60):02d}"
                        res = {
                            'type': 'playlist',
                            'platform': platform_info,
                            'title': info.get('title', 'Media Playlist'),
                            'thumbnail': entries[0].get('thumbnail', '') if entries else '',
                            'duration': dur_total,
                            'duration_str': dur_str,
                            'uploader': info.get('uploader', info.get('channel', 'Playlist')),
                            'upload_date': info.get('upload_date', datetime.now().strftime("%Y-%m-%d")),
                            'item_count': len(entries),
                            'qualities': ['2160p', '1440p', '1080p', '720p', 'audio_mp3'],
                            'formats': ['MP4', 'MKV', 'WEBM', 'MP3', 'M4A', 'WAV'],
                            'entries': entries
                        }
                        self._metadata_cache[url] = {'time': time.time(), 'info': res, 'raw_data': info}
                        return res

                    title = info.get('title', 'Unknown Title')
                    thumbnail = info.get('thumbnail', '')
                    duration = info.get('duration', 0)
                    dur_str = f"{int(duration//3600):02d}:{int((duration%3600)//60):02d}:{int(duration%60):02d}" if duration >= 3600 else f"{int(duration//60):02d}:{int(duration%60):02d}"
                    uploader = info.get('uploader', info.get('channel', 'Unknown Creator'))
                    subtitles = list(info.get('subtitles', {}).keys())
                    raw_formats = info.get('formats', [])

                    heights = set(f.get('height') for f in raw_formats if f.get('height'))
                    qualities = []
                    if any(h >= 2160 for h in heights): qualities.append('2160p')
                    if any(h >= 1440 for h in heights): qualities.append('1440p')
                    if any(h >= 1080 for h in heights) or not qualities: qualities.append('1080p')
                    if any(h >= 720 for h in heights): qualities.append('720p')
                    if any(h >= 480 for h in heights): qualities.append('480p')
                    qualities.append('audio_mp3')

                    f_size = info.get('filesize') or info.get('filesize_approx', 0)
                    if not f_size and raw_formats:
                        f_size = int(duration * 500000) if duration > 0 else 0

                    date_raw = str(info.get('upload_date', ''))
                    date_fmt = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(date_raw) == 8 else (date_raw or datetime.now().strftime("%Y-%m-%d"))

                    res = {
                        'type': 'video',
                        'platform': platform_info,
                        'title': title,
                        'thumbnail': thumbnail,
                        'duration': duration,
                        'duration_str': dur_str,
                        'uploader': uploader,
                        'upload_date': date_fmt,
                        'subtitles': subtitles,
                        'has_4k': any(h >= 2160 for h in heights),
                        'has_1080p': any(h >= 1080 for h in heights),
                        'qualities': qualities,
                        'formats': ['MP4', 'MKV', 'WEBM', 'MP3', 'M4A', 'WAV'],
                        'estimated_size_bytes': f_size,
                        'estimated_size_str': format_bytes(f_size) if f_size > 0 else "Auto-Stream",
                        'raw_info': info
                    }
                    self._metadata_cache[url] = {'time': time.time(), 'info': res, 'raw_data': info}
                    return res
        except Exception:
            pass

        # Universal Web Sniffer Inspection Fallback
        try:
            sniffed = self.web_sniffer.sniff_stream(url)
            if sniffed and sniffed.get('stream_url'):
                res = {
                    'type': 'video',
                    'platform': platform_info,
                    'title': sniffed.get('title', 'Web Media Stream'),
                    'thumbnail': sniffed.get('thumbnail', ''),
                    'duration': 0,
                    'duration_str': '--:--',
                    'uploader': 'Web Media',
                    'upload_date': datetime.now().strftime("%Y-%m-%d"),
                    'qualities': ['1080p', '720p', 'audio_mp3'],
                    'formats': ['MP4', 'MP3'],
                    'estimated_size_str': 'Universal Web Stream'
                }
                self._metadata_cache[url] = {'time': time.time(), 'info': res, 'raw_data': res}
                return res
        except Exception:
            pass

        res = {
            'type': 'unknown',
            'platform': platform_info,
            'title': url.split('/')[-1].split('?')[0] or 'Download Media',
            'thumbnail': '',
            'duration': 0,
            'duration_str': '--:--',
            'uploader': 'Web Stream',
            'upload_date': datetime.now().strftime("%Y-%m-%d"),
            'qualities': ['1080p', '720p', 'audio_mp3'],
            'formats': ['MP4', 'MP3'],
            'estimated_size_str': 'Universal Stream'
        }
        return res

    def extract_playlist_info(self, url: str) -> List[Dict[str, Any]]:
        ydl_opts = self._build_ytdlp_base_opts()
        ydl_opts['extract_flat'] = 'in_playlist'
        ydl_opts['skip_download'] = True

        items = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and 'entries' in info:
                    for idx, entry in enumerate(info['entries']):
                        if entry:
                            dur = entry.get('duration', 0)
                            dur_str = f"{int(dur//60):02d}:{int(dur%60):02d}" if dur > 0 else "--:--"
                            items.append({
                                'index': idx + 1,
                                'id': entry.get('id', ''),
                                'title': entry.get('title', f'Video #{idx+1}'),
                                'url': entry.get('url') or (f"https://www.youtube.com/watch?v={entry.get('id')}" if entry.get('id') else url),
                                'duration': dur,
                                'duration_str': dur_str,
                                'uploader': entry.get('uploader', 'Unknown Creator'),
                                'thumbnail': entry.get('thumbnail', ''),
                                'selected': True
                            })
        except Exception as e:
            print(f"Playlist extraction error: {e}")
        return items

    # -------------------------------------------------------------------------
    # RESILIENT DIRECT FILE DOWNLOADER (MULTI-CHUNK PARALLEL WITH AUTO-RETRY)
    # -------------------------------------------------------------------------
    def download_direct_file(
        self,
        url: str,
        output_dir: str,
        filename: Optional[str] = None,
        auto_categorize: bool = False,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        num_chunks: int = 16
    ) -> str:
        self.reset_cancel()
        effective_url = transform_cloud_url(url)
        proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None
        headers = {
            'User-Agent': USER_AGENTS[0],
            'Accept': '*/*'
        }

        total_bytes = 0
        accept_ranges = False

        try:
            resp = requests.head(effective_url, headers=headers, allow_redirects=True, timeout=12, proxies=proxies, verify=False)
            if resp.status_code in [200, 206, 302]:
                total_bytes = int(resp.headers.get('Content-Length', 0))
                accept_ranges = resp.headers.get('Accept-Ranges', '').lower() == 'bytes'
                if not filename:
                    cd = resp.headers.get('Content-Disposition')
                    if cd:
                        if "filename*=" in cd:
                            m = re.search(r"filename\*=UTF-8''([^;]+)", cd, re.IGNORECASE)
                            if m:
                                filename = urllib.parse.unquote(m.group(1))
                        if not filename and "filename=" in cd:
                            filename = cd.split('filename=')[-1].split(';')[0].strip('"\'')
        except Exception:
            pass

        if not filename:
            filename = effective_url.split('/')[-1].split('?')[0] or 'downloaded_media'
            if '.' not in filename:
                filename += ".mp4"

        filename = sanitize_filename(filename)
        target_dir = get_category_path(output_dir, filename) if auto_categorize else output_dir
        os.makedirs(target_dir, exist_ok=True)
        save_path = os.path.join(target_dir, filename)
        base, ext = os.path.splitext(save_path)
        counter = 1
        while os.path.exists(save_path):
            save_path = f"{base}_{counter}{ext}"
            counter += 1

        if not accept_ranges or total_bytes < 1024 * 1024 or num_chunks <= 1 or total_bytes == 0:
            return self._download_single_stream(effective_url, save_path, total_bytes, progress_callback, proxies)

        actual_chunks = min(max(num_chunks, 4), 32)
        chunk_size = total_bytes // actual_chunks
        ranges = []
        for i in range(actual_chunks):
            start = i * chunk_size
            end = (start + chunk_size - 1) if i < actual_chunks - 1 else (total_bytes - 1)
            ranges.append((start, end, i))

        part_files = [f"{save_path}.part{i}" for i in range(actual_chunks)]
        downloaded_bytes_map = {i: 0 for i in range(actual_chunks)}
        lock = threading.Lock()
        start_time = time.time()
        last_update_time = start_time
        bytes_since_last = 0

        def download_chunk(start: int, end: int, chunk_id: int):
            nonlocal bytes_since_last, last_update_time
            part_path = part_files[chunk_id]

            for attempt in range(5):
                try:
                    existing_bytes = os.path.getsize(part_path) if os.path.exists(part_path) else 0
                    current_start = start + existing_bytes
                    if current_start > end:
                        with lock:
                            downloaded_bytes_map[chunk_id] = (end - start + 1)
                        return

                    c_headers = {
                        'Range': f'bytes={current_start}-{end}',
                        'User-Agent': USER_AGENTS[0],
                        'Accept': '*/*'
                    }
                    r = requests.get(effective_url, headers=c_headers, stream=True, timeout=25, proxies=proxies, verify=False)
                    r.raise_for_status()

                    mode = 'ab' if existing_bytes > 0 else 'wb'
                    with open(part_path, mode) as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            if self._is_cancelled:
                                raise CancelledException("Download cancelled by user.")

                            while self._is_paused:
                                time.sleep(0.4)
                                if self._is_cancelled:
                                    raise CancelledException("Download cancelled by user.")

                            if chunk:
                                f.write(chunk)
                                with lock:
                                    downloaded_bytes_map[chunk_id] += len(chunk)
                                    bytes_since_last += len(chunk)
                                    total_dl = sum(downloaded_bytes_map.values())

                                    now = time.time()
                                    elapsed = now - last_update_time

                                    if self.speed_limit_bytes > 0 and bytes_since_last > self.speed_limit_bytes * elapsed:
                                        sleep_time = (bytes_since_last / self.speed_limit_bytes) - elapsed
                                        if sleep_time > 0:
                                            time.sleep(sleep_time)
                                            now = time.time()
                                            elapsed = now - last_update_time

                                    if elapsed >= 0.22 or total_dl == total_bytes:
                                        speed = bytes_since_last / elapsed if elapsed > 0 else 0
                                        eta = (total_bytes - total_dl) / speed if (speed > 0 and total_bytes > 0) else 0
                                        percent = (total_dl / total_bytes * 100) if total_bytes > 0 else 0.0

                                        self.record_speed(speed)

                                        if progress_callback:
                                            progress_callback({
                                                'status': 'downloading',
                                                'downloaded_bytes': total_dl,
                                                'total_bytes': total_bytes,
                                                'speed': speed,
                                                'eta': eta,
                                                'percent': percent,
                                                'filename': os.path.basename(save_path)
                                            })
                                        last_update_time = now
                                        bytes_since_last = 0
                    return
                except CancelledException:
                    raise
                except Exception:
                    time.sleep(0.8)

        try:
            with ThreadPoolExecutor(max_workers=actual_chunks) as executor:
                futures = [executor.submit(download_chunk, start, end, cid) for start, end, cid in ranges]
                for future in as_completed(futures):
                    future.result()

            with open(save_path, 'wb') as outfile:
                for part in part_files:
                    if os.path.exists(part):
                        with open(part, 'rb') as infile:
                            outfile.write(infile.read())
                        try:
                            os.remove(part)
                        except Exception:
                            pass
        except Exception:
            for part in part_files:
                if os.path.exists(part):
                    try: os.remove(part)
                    except Exception: pass
            raise

        self.record_speed(0)
        if progress_callback:
            progress_callback({
                'status': 'finished',
                'downloaded_bytes': total_bytes,
                'total_bytes': total_bytes,
                'speed': 0,
                'eta': 0,
                'percent': 100.0,
                'filename': os.path.basename(save_path),
                'file_path': save_path
            })

        return save_path

    # -------------------------------------------------------------------------
    # RESILIENT SINGLE STREAM DOWNLOADER (AUTO-RECONNECTING BUFFER)
    # -------------------------------------------------------------------------
    def _download_single_stream(
        self, url: str, save_path: str, total_bytes: int, progress_callback: Optional[Callable],
        proxies: Optional[dict] = None, thumbnail: str = "", title: str = "", duration: int = 0
    ) -> str:
        headers = {
            'User-Agent': USER_AGENTS[0],
            'Accept': '*/*'
        }
        resp = requests.get(url, headers=headers, stream=True, timeout=25, proxies=proxies, verify=False)
        resp.raise_for_status()
        if total_bytes <= 0:
            total_bytes = int(resp.headers.get('Content-Length', 0))

        display_name = title or os.path.basename(save_path)

        if progress_callback:
            progress_callback({
                'status': 'downloading',
                'downloaded_bytes': 0,
                'total_bytes': total_bytes,
                'speed': 0,
                'eta': 0,
                'percent': 3.0,
                'filename': display_name,
                'title': display_name,
                'thumbnail': thumbnail,
                'duration': duration
            })

        downloaded_bytes = 0
        start_time = time.time()
        last_update_time = start_time
        bytes_since_last = 0

        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if self._is_cancelled:
                    f.close()
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    raise CancelledException("Download cancelled by user.")

                while self._is_paused:
                    time.sleep(0.4)
                    if self._is_cancelled:
                        raise CancelledException("Download cancelled by user.")

                if chunk:
                    f.write(chunk)
                    downloaded_bytes += len(chunk)
                    bytes_since_last += len(chunk)

                    now = time.time()
                    elapsed = now - last_update_time

                    if elapsed >= 0.22 or downloaded_bytes == total_bytes:
                        speed = bytes_since_last / elapsed if elapsed > 0 else 0
                        eta = (total_bytes - downloaded_bytes) / speed if (speed > 0 and total_bytes > 0) else 0
                        percent = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0.0

                        self.record_speed(speed)

                        if progress_callback:
                            progress_callback({
                                'status': 'downloading',
                                'downloaded_bytes': downloaded_bytes,
                                'total_bytes': total_bytes,
                                'speed': speed,
                                'eta': eta,
                                'percent': percent,
                                'filename': display_name,
                                'title': display_name,
                                'thumbnail': thumbnail,
                                'duration': duration
                            })
                        last_update_time = now
                        bytes_since_last = 0

        self.record_speed(0)
        if progress_callback:
            progress_callback({
                'status': 'finished',
                'downloaded_bytes': downloaded_bytes,
                'total_bytes': downloaded_bytes,
                'speed': 0,
                'eta': 0,
                'percent': 100.0,
                'filename': display_name,
                'file_path': save_path,
                'thumbnail': thumbnail,
                'title': display_name,
                'duration': duration
            })
        return save_path

    # -------------------------------------------------------------------------
    # TURBO YT-DLP DOWNLOAD WORKER (WITH AUTO BROWSER COOKIES & CLIENT ROTATION)
    # -------------------------------------------------------------------------
    def download_ytdlp(
        self,
        url: str,
        output_dir: str,
        quality: str = '1080p',
        audio_bitrate: str = '320k',
        download_subtitles: bool = False,
        start_time: str = '',
        end_time: str = '',
        auto_categorize: bool = False,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> str:
        self.reset_cancel()
        target_dir = get_category_path(output_dir, "video.mp4") if auto_categorize else output_dir
        try:
            drive_root = os.path.splitdrive(os.path.abspath(target_dir))[0] + "\\"
            if os.path.exists(drive_root) and shutil.disk_usage(drive_root).free < 1.0 * 1024 * 1024 * 1024:
                from utils import get_best_available_drive_folder
                target_dir = get_best_available_drive_folder("Downloads")
        except Exception:
            pass
        os.makedirs(target_dir, exist_ok=True)

        ffmpeg_dir = get_ffmpeg_location()

        if ffmpeg_dir:
            if quality in ['8k', '4320p']:
                format_str = 'bestvideo[height<=4320]+bestaudio/bestvideo+bestaudio/best[height<=4320]/best'
            elif quality in ['4k', '2160p']:
                format_str = 'bestvideo[height<=2160]+bestaudio/bestvideo+bestaudio/best[height<=2160]/best'
            elif quality in ['1440p', '2k']:
                format_str = 'bestvideo[height<=1440]+bestaudio/bestvideo+bestaudio/best[height<=1440]/best'
            elif quality == '1080p':
                format_str = 'bestvideo[height<=1080]+bestaudio/bestvideo+bestaudio/best[height<=1080]/best'
            elif quality == '720p':
                format_str = 'bestvideo[height<=720]+bestaudio/bestvideo+bestaudio/best[height<=720]/best'
            elif quality == '480p':
                format_str = 'bestvideo[height<=480]+bestaudio/bestvideo+bestaudio/best[height<=480]/best'
            elif quality in ['audio_mp3', 'audio_m4a', 'audio_wav', 'audio_flac', 'audio_opus', 'mp3', 'm4a', 'wav', 'flac']:
                format_str = 'bestaudio[ext=m4a]/bestaudio/best'
            else:
                # Default / Auto / Best -> maximum available resolution & highest bitrate audio
                format_str = 'bestvideo+bestaudio/best'
        else:
            if quality in ['8k', '4320p']:
                format_str = 'best[height<=4320]/best'
            elif quality in ['4k', '2160p']:
                format_str = 'best[height<=2160]/best'
            elif quality in ['1440p', '2k']:
                format_str = 'best[height<=1440]/best'
            elif quality == '1080p':
                format_str = 'best[height<=1080]/best'
            elif quality == '720p':
                format_str = 'best[height<=720]/best'
            elif quality in ['audio_mp3', 'audio_m4a', 'audio_wav', 'audio_flac', 'audio_opus', 'mp3', 'm4a', 'wav', 'flac']:
                format_str = 'bestaudio/best'
            else:
                format_str = 'best'

        outtmpl = os.path.join(target_dir, '%(title).160s.%(ext)s')
        _last_hook_time = 0.0

        def ytdlp_hook(d):
            nonlocal _last_hook_time
            if self._is_cancelled:
                raise CancelledException("Download cancelled by user.")

            while self._is_paused and not self._is_cancelled:
                if progress_callback:
                    try:
                        progress_callback({
                            'status': 'paused',
                            'speed': 0,
                            'eta': 0,
                            'filename': os.path.basename(d.get('filename', 'video'))
                        })
                    except Exception:
                        pass
                time.sleep(0.15)

            if self._is_cancelled:
                raise CancelledException("Download cancelled by user.")

            if d['status'] == 'downloading':
                now = time.time()
                if (now - _last_hook_time < 0.20):
                    return
                _last_hook_time = now

                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                speed = d.get('speed') or 0
                eta = d.get('eta') or 0

                percent = 0.0
                if total > 0:
                    percent = (downloaded / total) * 100
                elif d.get('_percent_str'):
                    try:
                        clean_p = d['_percent_str'].replace('%', '').strip()
                        percent = float(clean_p)
                    except ValueError:
                        pass

                self.record_speed(speed)
                filename = os.path.basename(d.get('filename', 'video'))

                if progress_callback:
                    try:
                        progress_callback({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded,
                            'total_bytes': total,
                            'speed': speed,
                            'eta': eta,
                            'percent': percent,
                            'filename': filename
                        })
                    except Exception:
                        pass

            elif d['status'] == 'finished':
                self.record_speed(0)
                filename = os.path.basename(d.get('filename', 'video'))
                if progress_callback:
                    try:
                        progress_callback({
                            'status': 'finished',
                            'downloaded_bytes': d.get('total_bytes', 0),
                            'total_bytes': d.get('total_bytes', 0),
                            'speed': 0,
                            'eta': 0,
                            'percent': 100.0,
                            'filename': filename,
                            'file_path': d.get('filename', '')
                        })
                    except Exception:
                        pass

        ydl_opts = self._build_ytdlp_base_opts()
        if 'pinterest' in url.lower() or 'pin.it' in url.lower():
            ydl_opts.pop('http_chunk_size', None)
            if 'bestvideo' in format_str:
                format_str = f"best[protocol^=http]/{format_str}"

        ydl_opts.update({
            'format': format_str,
            'outtmpl': outtmpl,
            'progress_hooks': [ytdlp_hook],
        })

        if self.speed_limit_bytes > 0:
            ydl_opts['ratelimit'] = self.speed_limit_bytes

        if download_subtitles:
            ydl_opts['writesubtitles'] = True
            ydl_opts['allsubtitles'] = True
            ydl_opts['subtitlesformat'] = 'srt'

        if start_time or end_time:
            s_val = parse_time_seconds(start_time)
            e_val = parse_time_seconds(end_time) if end_time else float('inf')
            ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(s_val, e_val)])

        clean_kbps = str(audio_bitrate).replace('k', '') or '320'
        if quality in ['audio_mp3', 'mp3']:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': clean_kbps,
            }]
        elif quality in ['audio_m4a', 'm4a']:
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}]
        elif quality in ['audio_wav', 'wav']:
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}]
        elif quality in ['audio_flac', 'flac']:
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'flac'}]
        elif quality in ['audio_opus', 'opus']:
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'opus'}]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise Exception("Failed to retrieve media stream.")
                filename = ydl.prepare_filename(info)

                for audio_ext in ['.mp3', '.m4a', '.wav', '.flac', '.opus']:
                    if quality.lower().endswith(audio_ext.lstrip('.')):
                        base_name, _ = os.path.splitext(filename)
                        audio_p = base_name + audio_ext
                        if os.path.exists(audio_p):
                            return audio_p

                return filename
        except Exception as e:
            if self._is_cancelled or "cancelled" in str(e).lower() or isinstance(e, CancelledException):
                raise CancelledException("Download cancelled by user.")
            err_str = str(e).lower()
            if ("403" in err_str or "forbidden" in err_str or "bot" in err_str) and self.browser_cookies == "none":
                for fallback_browser in ["chrome", "edge", "firefox", "brave", "opera"]:
                    try:
                        ydl_opts['cookiesfrombrowser'] = (fallback_browser,)
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl_retry:
                            info = ydl_retry.extract_info(url, download=True)
                            if info:
                                return ydl_retry.prepare_filename(info)
                    except Exception as e_retry:
                        if self._is_cancelled or "cancelled" in str(e_retry).lower() or isinstance(e_retry, CancelledException):
                            raise CancelledException("Download cancelled by user.")
                        continue
            raise


# =============================================================================
# ENTERPRISE MULTI-THREADED DOWNLOAD QUEUE ENGINE
# =============================================================================
class AdvancedQueueEngine:
    """
    Enterprise Multi-Threaded Download Queue Engine.
    Features:
    - Multi-stream concurrent downloads (1 to 10 active streams)
    - Full State Machine: waiting -> analyzing -> downloading -> processing -> completed / failed / paused / cancelled
    - Live speed, ETA, percent, and file size tracking
    - Priority Reordering (Move Up / Move Down)
    - Individual & Global Pause, Resume, Cancel, Retry
    """
    def __init__(self, engine: DownloaderEngine, max_concurrent: int = 3):
        self.engine = engine
        self.max_concurrent = max_concurrent
        self.items: List[Dict[str, Any]] = []
        self.is_running = False
        self.is_paused = False
        self._lock = threading.Lock()
        self._active_workers: Dict[str, threading.Thread] = {}
        self._item_cancel_flags: Dict[str, bool] = {}
        self._item_pause_flags: Dict[str, bool] = {}
        self.on_queue_change: Optional[Callable[[], None]] = None
        self.on_item_update: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_concurrency(self, limit: int):
        self.max_concurrent = max(1, min(int(limit), 10))

    def add_items(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        added = []
        with self._lock:
            for it in raw_items:
                url = (it.get('url') or '').strip()
                if not url:
                    continue

                item_id = it.get('id') or f"dl_{uuid.uuid4().hex[:8]}"
                preset = it.get('preset') or it.get('quality') or '1080p'

                queue_item = {
                    'id': item_id,
                    'url': url,
                    'title': it.get('title') or (url.split('/')[-1].split('?')[0][:40] or 'Media Stream'),
                    'thumbnail': it.get('thumbnail', ''),
                    'uploader': it.get('uploader', 'Unknown Creator'),
                    'duration': it.get('duration', 0),
                    'duration_str': it.get('duration_str', '--:--'),
                    'preset': preset,
                    'format': it.get('format', 'MP4' if 'mp3' not in preset.lower() else 'MP3'),
                    'output_dir': it.get('output_dir', ''),
                    'status': 'waiting',
                    'percent': 0.0,
                    'percent_str': '0.0%',
                    'speed_str': '0 KB/s',
                    'eta_str': '--:--',
                    'downloaded_str': '0 B',
                    'total_str': 'Calculating...',
                    'error': '',
                    'file_path': '',
                    'subtitles': it.get('subtitles', False),
                    'bitrate': it.get('bitrate', '320k'),
                    'trim_start': it.get('trim_start', ''),
                    'trim_end': it.get('trim_end', ''),
                    'created_at': time.time(),
                    'retries': 0
                }
                self.items.append(queue_item)
                added.append(queue_item)

        self._trigger_queue_change()
        if self.is_running and not self.is_paused:
            self._spawn_next_workers()
        return added

    def get_items(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.items)

    def remove_item(self, item_id: str) -> bool:
        self.cancel_item(item_id)
        with self._lock:
            orig_len = len(self.items)
            self.items = [it for it in self.items if it['id'] != item_id]
            removed = len(self.items) < orig_len
        self._trigger_queue_change()
        self._spawn_next_workers()
        return removed

    def clear_completed(self):
        with self._lock:
            self.items = [it for it in self.items if it['status'] in ['waiting', 'analyzing', 'downloading', 'processing', 'paused']]
        self._trigger_queue_change()

    def clear_all(self):
        self.cancel_all()
        with self._lock:
            self.items.clear()
        self._trigger_queue_change()

    def reorder_items(self, item_ids: List[str]):
        with self._lock:
            item_map = {it['id']: it for it in self.items}
            reordered = []
            for iid in item_ids:
                if iid in item_map:
                    reordered.append(item_map[iid])
            for it in self.items:
                if it['id'] not in item_map:
                    reordered.append(it)
            self.items = reordered
        self._trigger_queue_change()

    def move_item(self, item_id: str, direction: str):
        with self._lock:
            idx = next((i for i, it in enumerate(self.items) if it['id'] == item_id), -1)
            if idx == -1: return
            if direction == 'up' and idx > 0:
                self.items[idx], self.items[idx - 1] = self.items[idx - 1], self.items[idx]
            elif direction == 'down' and idx < len(self.items) - 1:
                self.items[idx], self.items[idx + 1] = self.items[idx + 1], self.items[idx]
        self._trigger_queue_change()

    def pause_item(self, item_id: str):
        with self._lock:
            it = next((it for it in self.items if it['id'] == item_id), None)
            if it and it['status'] in ['waiting', 'downloading', 'analyzing']:
                it['status'] = 'paused'
                self._item_pause_flags[item_id] = True
        self._trigger_item_update(item_id)
        self._trigger_queue_change()

    def resume_item(self, item_id: str):
        with self._lock:
            it = next((it for it in self.items if it['id'] == item_id), None)
            if it and it['status'] == 'paused':
                it['status'] = 'waiting'
                self._item_pause_flags.pop(item_id, None)
        self._trigger_item_update(item_id)
        self._trigger_queue_change()
        self._spawn_next_workers()

    def retry_item(self, item_id: str):
        with self._lock:
            it = next((it for it in self.items if it['id'] == item_id), None)
            if it and it['status'] in ['failed', 'cancelled']:
                it['status'] = 'waiting'
                it['error'] = ''
                it['percent'] = 0.0
                it['percent_str'] = '0.0%'
                it['speed_str'] = '0 KB/s'
                it['eta_str'] = '--:--'
                it['retries'] += 1
                self._item_cancel_flags.pop(item_id, None)
                self._item_pause_flags.pop(item_id, None)
        self._trigger_item_update(item_id)
        self._trigger_queue_change()
        self._spawn_next_workers()

    def cancel_item(self, item_id: str):
        self._item_cancel_flags[item_id] = True
        with self._lock:
            it = next((it for it in self.items if it['id'] == item_id), None)
            if it and it['status'] in ['waiting', 'analyzing', 'downloading', 'processing', 'paused']:
                it['status'] = 'cancelled'
        self._trigger_item_update(item_id)
        self._trigger_queue_change()

    def start_queue(self):
        self.is_running = True
        self.is_paused = False
        with self._lock:
            for it in self.items:
                if it['status'] == 'paused':
                    it['status'] = 'waiting'
        self._trigger_queue_change()
        self._spawn_next_workers()

    def pause_queue(self):
        self.is_paused = True
        with self._lock:
            for it in self.items:
                if it['status'] in ['downloading', 'analyzing']:
                    it['status'] = 'paused'
                    self._item_pause_flags[it['id']] = True
        self._trigger_queue_change()

    def resume_queue(self):
        self.is_paused = False
        self.is_running = True
        self._item_pause_flags.clear()
        with self._lock:
            for it in self.items:
                if it['status'] == 'paused':
                    it['status'] = 'waiting'
        self._trigger_queue_change()
        self._spawn_next_workers()

    def cancel_all(self):
        self.is_running = False
        with self._lock:
            for it in self.items:
                self._item_cancel_flags[it['id']] = True
                if it['status'] in ['waiting', 'analyzing', 'downloading', 'processing', 'paused']:
                    it['status'] = 'cancelled'
        self._trigger_queue_change()

    def _spawn_next_workers(self):
        if not self.is_running or self.is_paused:
            return

        with self._lock:
            active_count = len([it for it in self.items if it['status'] in ['analyzing', 'downloading', 'processing']])
            slots_available = self.max_concurrent - active_count
            if slots_available <= 0:
                return

            waiting_items = [it for it in self.items if it['status'] == 'waiting']
            to_start = waiting_items[:slots_available]
            for it in to_start:
                it['status'] = 'analyzing'
                t = threading.Thread(target=self._worker_thread, args=(it['id'],), daemon=True)
                self._active_workers[it['id']] = t
                t.start()

    def _worker_thread(self, item_id: str):
        with self._lock:
            it = next((x for x in self.items if x['id'] == item_id), None)
            if not it:
                return
            url = it['url']
            preset = it['preset']
            output_dir = it['output_dir'] or ''
            options = {
                'subtitles': it.get('subtitles', False),
                'bitrate': it.get('bitrate', '320k'),
                'trim_start': it.get('trim_start', ''),
                'trim_end': it.get('trim_end', '')
            }

        try:
            if self._item_cancel_flags.get(item_id):
                with self._lock: it['status'] = 'cancelled'
                self._finish_item(item_id)
                return

            meta = self.engine.fetch_url_info(url)
            with self._lock:
                if meta:
                    it['title'] = meta.get('title') or it['title']
                    it['thumbnail'] = meta.get('thumbnail') or it['thumbnail']
                    it['duration'] = meta.get('duration') or it['duration']
                    it['duration_str'] = meta.get('duration_str') or it['duration_str']
                    it['uploader'] = meta.get('uploader') or it['uploader']
                it['status'] = 'downloading'
            self._trigger_item_update(item_id)

            def progress_cb(data):
                if self._item_cancel_flags.get(item_id):
                    raise CancelledException("Download cancelled.")
                while self._item_pause_flags.get(item_id) or self.is_paused:
                    time.sleep(0.4)
                    if self._item_cancel_flags.get(item_id):
                        raise CancelledException("Download cancelled.")

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

                with self._lock:
                    it['percent'] = round(pct, 1)
                    it['percent_str'] = f"{pct:.1f}%"
                    it['speed_str'] = speed_str
                    it['eta_str'] = eta_str
                    it['downloaded_str'] = format_bytes(dl_bytes)
                    it['total_str'] = format_bytes(tot_bytes) if tot_bytes > 0 else 'Calculating...'
                    if data.get('thumbnail'): it['thumbnail'] = data['thumbnail']
                    if data.get('title'): it['title'] = data['title']

                self._trigger_item_update(item_id)

            res = self.engine.download(
                url=url,
                output_dir=output_dir,
                quality=preset,
                progress_callback=progress_cb,
                download_subs=options.get('subtitles', False),
                bitrate=options.get('bitrate', '320k'),
                trim_start=options.get('trim_start', ''),
                trim_end=options.get('trim_end', '')
            )

            with self._lock:
                it['status'] = 'completed'
                it['percent'] = 100.0
                it['percent_str'] = '100%'
                it['speed_str'] = 'Finished'
                it['eta_str'] = '00:00'
                it['file_path'] = res.get('path', '')
                if res.get('thumbnail'): it['thumbnail'] = res['thumbnail']
                if res.get('title'): it['title'] = res['title']

        except CancelledException:
            with self._lock:
                it['status'] = 'cancelled'
                it['speed_str'] = 'Cancelled'
        except Exception as e:
            friendly_err = humanize_download_error(str(e))
            with self._lock:
                it['status'] = 'failed'
                it['error'] = friendly_err
                it['speed_str'] = 'Failed'

        self._finish_item(item_id)

    def _finish_item(self, item_id: str):
        self._active_workers.pop(item_id, None)
        self._trigger_item_update(item_id)
        self._trigger_queue_change()
        self._spawn_next_workers()

    def _trigger_queue_change(self):
        if self.on_queue_change:
            try: self.on_queue_change()
            except Exception: pass

    def _trigger_item_update(self, item_id: str):
        if self.on_item_update:
            with self._lock:
                it = next((x for x in self.items if x['id'] == item_id), None)
                if it:
                    try: self.on_item_update(dict(it))
                    except Exception: pass

# Backward compatibility alias
BatchQueueEngine = AdvancedQueueEngine
