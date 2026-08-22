import os
import time
import shutil
import requests
import threading
import yt_dlp
from typing import Callable, Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import sanitize_filename, format_bytes, categorize_file, get_category_path, is_video_platform_url

def get_ffmpeg_location() -> Optional[str]:
    """Dynamically locate ffmpeg binary via imageio_ffmpeg or system PATH and ensure ffmpeg.exe exists."""
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

            # Inject into system PATH for yt-dlp and ffmpeg subprocesses
            if ffmpeg_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

            return ffmpeg_dir
    except Exception:
        pass
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

class DownloaderEngine:
    def __init__(self):
        self._is_cancelled = False
        self._is_paused = False
        self.speed_limit_bytes = 0  # 0 means unlimited
        self.browser_cookies = "none"
        self.proxy_url = ""
        self.speed_history: List[float] = [0.0] * 30  # Stores last 30 speed data points (in KB/s) for live graph
        self._metadata_cache: Dict[str, Any] = {}  # In-memory cache: url -> (timestamp, info_dict, raw_data)

        # Ensure ffmpeg is initialized on startup
        get_ffmpeg_location()

    def cancel(self):
        """Signal to cancel current download."""
        self._is_cancelled = True

    def pause(self):
        """Signal to pause current download."""
        self._is_paused = True

    def resume(self):
        """Signal to resume current download."""
        self._is_paused = False

    def reset_cancel(self):
        """Reset cancellation & pause flags."""
        self._is_cancelled = False
        self._is_paused = False

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def set_speed_limit(self, max_kb_s: float):
        """Set maximum download speed limit in KB/s (0 = unlimited)."""
        self.speed_limit_bytes = int(max_kb_s * 1024)

    def set_network_options(self, browser_cookies: str = "none", proxy_url: str = ""):
        """Configure browser cookies extraction and proxy."""
        self.browser_cookies = browser_cookies or "none"
        self.proxy_url = proxy_url.strip()

    def record_speed(self, speed_bytes_per_sec: float):
        """Record current speed for analytics graph."""
        kb_s = speed_bytes_per_sec / 1024.0
        self.speed_history.append(round(kb_s, 1))
        if len(self.speed_history) > 40:
            self.speed_history.pop(0)

    def download_tiktok(
        self,
        url: str,
        output_dir: str,
        quality: str = '1080p',
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Specialized high-speed TikTok / Douyin downloader (HD No-Watermark MP4 & MP3).
        Uses intelligent caching and rate-limit auto-retry with seamless yt-dlp fallback.
        """
        self.reset_cancel()
        os.makedirs(output_dir, exist_ok=True)
        clean_url = url.split('?')[0] if 'tiktok.com' in url else url

        # Check metadata cache first to prevent hitting API rate limits
        data = None
        cached_entry = self._metadata_cache.get(clean_url) or self._metadata_cache.get(url)
        if cached_entry and (time.time() - cached_entry['time'] < 300):
            data = cached_entry.get('raw_data')

        if not data:
            api_url = f"https://www.tikwm.com/api/?url={requests.utils.quote(clean_url)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            }
            
            resp_json = None
            for attempt in range(2):
                try:
                    r = requests.get(api_url, headers=headers, timeout=10)
                    resp_json = r.json()
                    if resp_json.get('code') == 0 and resp_json.get('data'):
                        data = resp_json['data']
                        break
                    elif "Free Api Limit" in str(resp_json.get('msg', '')):
                        time.sleep(1.2)  # Back off if rate limited
                        continue
                except Exception:
                    time.sleep(0.8)

            if not data:
                msg = (resp_json.get('msg') if resp_json else "API request limit") or "TikTok video not found"
                raise Exception(f"TikTok Download Error: {msg}")

        raw_title = data.get('title') or f"TikTok_{data.get('id', int(time.time()))}"
        title = sanitize_filename(raw_title[:80])
        cover_url = data.get('cover') or data.get('origin_cover') or data.get('dynamic_cover') or ''
        duration = data.get('duration', 0)
        
        if quality in ['audio_mp3', 'mp3']:
            stream_url = data.get('music')
            ext = ".mp3"
        else:
            stream_url = data.get('hdplay') or data.get('play') or data.get('wmplay')
            ext = ".mp4"
            
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
        """
        Unified download entry point for all media platforms (TikTok, YouTube, Facebook, Instagram, Twitter, Direct, etc.).
        """
        self.reset_cancel()
        os.makedirs(output_dir, exist_ok=True)

        q_map = {
            '4k': '4k',
            '1080p': '1080p',
            '720p': '720p',
            'mp3': 'audio_mp3'
        }
        eff_quality = q_map.get(quality.lower(), quality)

        thumb_out = ""
        title_out = ""
        if 'tiktok.com' in url.lower() or 'douyin.com' in url.lower():
            try:
                tk_res = self.download_tiktok(
                    url=url,
                    output_dir=output_dir,
                    quality=eff_quality,
                    progress_callback=progress_callback
                )
                file_path = tk_res['path'] if isinstance(tk_res, dict) else tk_res
                thumb_out = tk_res.get('thumbnail', '') if isinstance(tk_res, dict) else ''
                title_out = tk_res.get('title', '') if isinstance(tk_res, dict) else ''
            except Exception:
                # Seamless fallback to yt-dlp native extractor if TikTok API is rate limited
                file_path = self.download_ytdlp(
                    url=url,
                    output_dir=output_dir,
                    quality=eff_quality,
                    audio_bitrate=bitrate,
                    download_subtitles=download_subs,
                    start_time=trim_start,
                    end_time=trim_end,
                    progress_callback=progress_callback
                )
                cached = self._metadata_cache.get(url)
                if cached:
                    thumb_out = cached.get('info', {}).get('thumbnail', '')
                    title_out = cached.get('info', {}).get('title', '')
        elif is_video_platform_url(url) or any(x in url.lower() for x in ['youtube.com', 'youtu.be', 'facebook.com', 'fb.watch', 'instagram.com', 'twitter.com', 'x.com', 'vimeo.com', 'dailymotion.com', 'soundcloud.com', 'bilibili.com', 'threads.net', 'pinterest.com', 'reddit.com']):
            file_path = self.download_ytdlp(
                url=url,
                output_dir=output_dir,
                quality=eff_quality,
                audio_bitrate=bitrate,
                download_subtitles=download_subs,
                start_time=trim_start,
                end_time=trim_end,
                progress_callback=progress_callback
            )
        else:
            try:
                file_path = self.download_direct_file(
                    url=url,
                    output_dir=output_dir,
                    progress_callback=progress_callback
                )
            except Exception:
                file_path = self.download_ytdlp(
                    url=url,
                    output_dir=output_dir,
                    quality=eff_quality,
                    audio_bitrate=bitrate,
                    download_subtitles=download_subs,
                    start_time=trim_start,
                    end_time=trim_end,
                    progress_callback=progress_callback
                )

        f_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        return {
            'filename': os.path.basename(file_path),
            'path': file_path,
            'size': f_size,
            'thumbnail': thumb_out,
            'title': title_out or os.path.basename(file_path)
        }

    def _build_ytdlp_base_opts(self) -> Dict[str, Any]:
        """Construct standard ytdlp base options with bypasses for 403 Forbidden, SABR, and PO Token."""
        ffmpeg_dir = get_ffmpeg_location()
        opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'http_chunk_size': 10485760,  # 10MB chunk size prevents YouTube HTTP 403 stream throttling
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'mweb', 'ios'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        if ffmpeg_dir:
            opts['ffmpeg_location'] = ffmpeg_dir
        
        if self.browser_cookies and self.browser_cookies.lower() not in ["none", ""]:
            opts['cookiesfrombrowser'] = (self.browser_cookies.lower(),)
            
        if self.proxy_url:
            opts['proxy'] = self.proxy_url
            
        return opts

    def fetch_url_info(self, url: str) -> Dict[str, Any]:
        """Fetch metadata (Title, Duration, Thumbnail, Uploader, Formats) from URL with smart caching."""
        if not url:
            return {'type': 'unknown', 'title': 'Media File', 'thumbnail': '', 'duration': 0}

        clean_url = url.split('?')[0] if 'tiktok.com' in url else url
        cached = self._metadata_cache.get(clean_url) or self._metadata_cache.get(url)
        if cached and (time.time() - cached['time'] < 300):
            return cached['info']

        if 'tiktok.com' in url.lower() or 'douyin.com' in url.lower():
            try:
                api_url = f"https://www.tikwm.com/api/?url={requests.utils.quote(clean_url)}"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                r = requests.get(api_url, headers=headers, timeout=8).json()
                if r.get('code') == 0 and r.get('data'):
                    d = r['data']
                    res = {
                        'type': 'video',
                        'title': d.get('title', 'TikTok Video'),
                        'thumbnail': d.get('cover') or d.get('origin_cover') or '',
                        'duration': d.get('duration', 0),
                        'uploader': d.get('author', {}).get('nickname', 'TikTok Creator'),
                        'subtitles': [],
                        'has_4k': False,
                        'has_1080p': True,
                        'raw_info': d
                    }
                    self._metadata_cache[clean_url] = {'time': time.time(), 'info': res, 'raw_data': d}
                    self._metadata_cache[url] = self._metadata_cache[clean_url]
                    return res
            except Exception:
                pass

        ydl_opts = self._build_ytdlp_base_opts()
        ydl_opts['skip_download'] = True
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    # Check if it's a playlist
                    if 'entries' in info:
                        entries = list(info.get('entries', []))
                        res = {
                            'type': 'playlist',
                            'title': info.get('title', 'Media Playlist'),
                            'thumbnail': entries[0].get('thumbnail', '') if entries else '',
                            'duration': sum(e.get('duration', 0) for e in entries if e),
                            'uploader': info.get('uploader', info.get('channel', 'Playlist')),
                            'item_count': len(entries),
                            'entries': entries
                        }
                        self._metadata_cache[url] = {'time': time.time(), 'info': res, 'raw_data': info}
                        return res
                    
                    title = info.get('title', 'Unknown Title')
                    thumbnail = info.get('thumbnail', '')
                    duration = info.get('duration', 0)
                    uploader = info.get('uploader', info.get('channel', 'Unknown Creator'))
                    subtitles = list(info.get('subtitles', {}).keys())
                    formats = info.get('formats', [])
                    res = {
                        'type': 'video',
                        'title': title,
                        'thumbnail': thumbnail,
                        'duration': duration,
                        'uploader': uploader,
                        'subtitles': subtitles,
                        'has_4k': any(f.get('height', 0) >= 2160 for f in formats),
                        'has_1080p': any(f.get('height', 0) >= 1080 for f in formats),
                        'raw_info': info
                    }
                    self._metadata_cache[url] = {'time': time.time(), 'info': res, 'raw_data': info}
                    return res
        except Exception:
            pass

        # Direct Link inspection via requests
        try:
            proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None
            resp = requests.head(url, allow_redirects=True, timeout=6, proxies=proxies)
            content_length = int(resp.headers.get('Content-Length', 0))
            content_type = resp.headers.get('Content-Type', 'application/octet-stream')
            accept_ranges = resp.headers.get('Accept-Ranges', '') == 'bytes'
            
            filename = url.split('/')[-1].split('?')[0] or 'file_download'
            cd = resp.headers.get('Content-Disposition')
            if cd and 'filename=' in cd:
                filename = cd.split('filename=')[-1].strip('"\'')

            return {
                'type': 'direct',
                'title': filename,
                'file_size': content_length,
                'content_type': content_type,
                'accept_ranges': accept_ranges,
                'thumbnail': '',
                'duration': 0,
                'uploader': 'Direct Web Server'
            }
        except Exception as e:
            return {
                'type': 'unknown',
                'title': url.split('/')[-1].split('?')[0] or 'Download File',
                'error': str(e),
                'thumbnail': '',
                'duration': 0,
                'uploader': 'Unknown Source'
            }

    def extract_playlist_info(self, url: str) -> List[Dict[str, Any]]:
        """Extract list of all items from a playlist."""
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
                            items.append({
                                'index': idx + 1,
                                'id': entry.get('id', ''),
                                'title': entry.get('title', f'Video #{idx+1}'),
                                'url': entry.get('url') or (f"https://www.youtube.com/watch?v={entry.get('id')}" if entry.get('id') else url),
                                'duration': entry.get('duration', 0),
                                'uploader': entry.get('uploader', 'Unknown'),
                                'thumbnail': entry.get('thumbnail', ''),
                                'selected': True
                            })
        except Exception as e:
            print(f"Playlist extraction error: {e}")
        return items

    def download_direct_file(
        self,
        url: str,
        output_dir: str,
        filename: Optional[str] = None,
        auto_categorize: bool = False,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        num_chunks: int = 8
    ) -> str:
        """
        Turbo Multi-threaded Direct File Downloader (8-16 Chunks Parallel Booster)
        Supports Pause, Resume, Speed Throttling & Cancel.
        """
        self.reset_cancel()
        proxies = {'http': self.proxy_url, 'https': self.proxy_url} if self.proxy_url else None

        resp = requests.head(url, allow_redirects=True, timeout=12, proxies=proxies)
        total_bytes = int(resp.headers.get('Content-Length', 0))
        accept_ranges = resp.headers.get('Accept-Ranges', '') == 'bytes'

        if not filename:
            cd = resp.headers.get('Content-Disposition')
            if cd and 'filename=' in cd:
                filename = cd.split('filename=')[-1].strip('"\'')
            else:
                filename = url.split('/')[-1].split('?')[0] or 'downloaded_file'

        filename = sanitize_filename(filename)

        if auto_categorize:
            target_dir = get_category_path(output_dir, filename)
        else:
            target_dir = output_dir

        os.makedirs(target_dir, exist_ok=True)
        save_path = os.path.join(target_dir, filename)
        base, ext = os.path.splitext(save_path)
        counter = 1
        while os.path.exists(save_path):
            save_path = f"{base}_{counter}{ext}"
            counter += 1

        # Use Single-thread stream if server doesn't support ranges or file is small
        if not accept_ranges or total_bytes < 1024 * 1024 or num_chunks <= 1:
            return self._download_single_stream(url, save_path, total_bytes, progress_callback, proxies)

        # Multi-chunk parallel speed booster (up to 16 chunks)
        actual_chunks = min(num_chunks, 16)
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
            headers = {'Range': f'bytes={start}-{end}'}
            r = requests.get(url, headers=headers, stream=True, timeout=20, proxies=proxies)
            r.raise_for_status()

            part_path = part_files[chunk_id]
            with open(part_path, 'wb') as f:
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

                            # Apply speed limit if specified
                            if self.speed_limit_bytes > 0 and bytes_since_last > self.speed_limit_bytes * elapsed:
                                sleep_time = (bytes_since_last / self.speed_limit_bytes) - elapsed
                                if sleep_time > 0:
                                    time.sleep(sleep_time)
                                    now = time.time()
                                    elapsed = now - last_update_time

                            if elapsed >= 0.25 or total_dl == total_bytes:
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

        try:
            with ThreadPoolExecutor(max_workers=actual_chunks) as executor:
                futures = [executor.submit(download_chunk, start, end, cid) for start, end, cid in ranges]
                for future in as_completed(futures):
                    future.result()

            # Combine part files into target save file
            with open(save_path, 'wb') as outfile:
                for part in part_files:
                    if os.path.exists(part):
                        with open(part, 'rb') as infile:
                            outfile.write(infile.read())
                        os.remove(part)
        except Exception:
            # Clean up part files on error
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

    def _download_single_stream(
        self, url: str, save_path: str, total_bytes: int, progress_callback: Optional[Callable],
        proxies: Optional[dict] = None, thumbnail: str = "", title: str = "", duration: int = 0
    ) -> str:
        resp = requests.get(url, stream=True, timeout=20, proxies=proxies)
        resp.raise_for_status()
        if total_bytes <= 0:
            total_bytes = int(resp.headers.get('Content-Length', 0))

        display_name = title or os.path.basename(save_path)

        # Fire immediate start progress with real thumbnail & title
        if progress_callback:
            progress_callback({
                'status': 'downloading',
                'downloaded_bytes': 0,
                'total_bytes': total_bytes,
                'speed': 0,
                'eta': 0,
                'percent': 5.0,
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

                    if elapsed >= 0.25 or downloaded_bytes == total_bytes:
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
        """
        Download Video/Audio with 4K, 1080p, 720p, MP3, M4A, WAV, Subtitles & Trimming.
        Includes automatic 403 Forbidden & SABR stream bypass.
        """
        self.reset_cancel()
        target_dir = get_category_path(output_dir, "video.mp4") if auto_categorize else output_dir
        os.makedirs(target_dir, exist_ok=True)

        ffmpeg_dir = get_ffmpeg_location()

        # Format string determination
        if ffmpeg_dir:
            if quality in ['4k', '2160p']:
                format_str = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]/best'
            elif quality in ['1440p', '2k']:
                format_str = 'bestvideo[height<=1440]+bestaudio/best[height<=1440]/best'
            elif quality == '1080p':
                format_str = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
            elif quality == '720p':
                format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
            elif quality == '480p':
                format_str = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
            elif quality in ['audio_mp3', 'audio_m4a', 'audio_wav']:
                format_str = 'bestaudio/best'
            else:
                format_str = 'bestvideo+bestaudio/best'
        else:
            if quality in ['4k', '2160p']:
                format_str = 'best[height<=2160]/best'
            elif quality == '1080p':
                format_str = 'best[height<=1080]/best'
            elif quality == '720p':
                format_str = 'best[height<=720]/best'
            elif quality == '480p':
                format_str = 'best[height<=480]/best'
            elif quality in ['audio_mp3', 'audio_m4a', 'audio_wav']:
                format_str = 'bestaudio/best'
            else:
                format_str = 'best'

        outtmpl = os.path.join(target_dir, '%(title)s.%(ext)s')

        def ytdlp_hook(d):
            if self._is_cancelled:
                raise CancelledException("Download cancelled by user.")

            if d['status'] == 'downloading':
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
                    progress_callback({
                        'status': 'downloading',
                        'downloaded_bytes': downloaded,
                        'total_bytes': total,
                        'speed': speed,
                        'eta': eta,
                        'percent': percent,
                        'filename': filename
                    })

            elif d['status'] == 'finished':
                self.record_speed(0)
                filename = os.path.basename(d.get('filename', 'video'))
                if progress_callback:
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

        ydl_opts = self._build_ytdlp_base_opts()
        ydl_opts.update({
            'format': format_str,
            'outtmpl': outtmpl,
            'progress_hooks': [ytdlp_hook],
        })

        if self.speed_limit_bytes > 0:
            ydl_opts['ratelimit'] = self.speed_limit_bytes

        # Subtitles option
        if download_subtitles:
            ydl_opts['writesubtitles'] = True
            ydl_opts['allsubtitles'] = True
            ydl_opts['subtitlesformat'] = 'srt'

        # Video Trimming section option
        if start_time or end_time:
            s_val = parse_time_seconds(start_time)
            e_val = parse_time_seconds(end_time) if end_time else float('inf')
            ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(s_val, e_val)])

        # Audio Conversion options
        if quality == 'audio_mp3':
            clean_kbps = audio_bitrate.replace('k', '')
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': clean_kbps,
            }]
        elif quality == 'audio_m4a':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }]
        elif quality == 'audio_wav':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise Exception("Failed to retrieve media stream information.")
                filename = ydl.prepare_filename(info)
                
                if quality == 'audio_mp3':
                    base_name, _ = os.path.splitext(filename)
                    mp3_path = base_name + ".mp3"
                    if os.path.exists(mp3_path):
                        return mp3_path
                elif quality == 'audio_m4a':
                    base_name, _ = os.path.splitext(filename)
                    m4a_path = base_name + ".m4a"
                    if os.path.exists(m4a_path):
                        return m4a_path
                elif quality == 'audio_wav':
                    base_name, _ = os.path.splitext(filename)
                    wav_path = base_name + ".wav"
                    if os.path.exists(wav_path):
                        return wav_path

                return filename
        except Exception as e:
            err_str = str(e).lower()
            # If HTTP 403 Forbidden occurs and no browser cookies were selected, retry with auto-browser cookies
            if ("403" in err_str or "forbidden" in err_str) and self.browser_cookies == "none":
                for fallback_browser in ["chrome", "edge", "firefox", "brave"]:
                    try:
                        ydl_opts['cookiesfrombrowser'] = (fallback_browser,)
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl_retry:
                            info = ydl_retry.extract_info(url, download=True)
                            if info:
                                filename = ydl_retry.prepare_filename(info)
                                return filename
                    except Exception:
                        continue
            raise


class BatchQueueEngine:
    """Queue manager for processing multiple URLs in sequence."""
    def __init__(self, engine: DownloaderEngine):
        self.engine = engine
        self.queue: List[Dict[str, Any]] = []
        self.is_running = False

    def add_urls(self, urls: List[str], quality: str = '1080p', output_dir: str = ''):
        for u in urls:
            u = u.strip()
            if u:
                self.queue.append({
                    'url': u,
                    'quality': quality,
                    'output_dir': output_dir,
                    'status': 'PENDING',
                    'filename': u.split('/')[-1][:35] or 'URL'
                })

    def clear(self):
        self.queue.clear()
        self.is_running = False

    def process_queue(
        self,
        on_item_start: Optional[Callable] = None,
        on_item_complete: Optional[Callable] = None,
        on_queue_complete: Optional[Callable] = None
    ):
        self.is_running = True
        for idx, item in enumerate(self.queue):
            if not self.is_running or self.engine.is_cancelled():
                break

            if item['status'] == 'COMPLETED':
                continue

            item['status'] = 'DOWNLOADING'
            if on_item_start:
                on_item_start(idx, item)

            try:
                url = item['url']
                out = item['output_dir']
                q = item['quality']

                if 'http' in url:
                    if is_video_platform_url(url):
                        res = self.engine.download_ytdlp(url, out, quality=q)
                    else:
                        res = self.engine.download_direct_file(url, out)
                    item['status'] = 'COMPLETED'
                    item['filepath'] = res
                else:
                    item['status'] = 'FAILED'
            except Exception as e:
                item['status'] = 'FAILED'
                item['error'] = str(e)

            if on_item_complete:
                on_item_complete(idx, item)

        self.is_running = False
        if on_queue_complete:
            on_queue_complete()

