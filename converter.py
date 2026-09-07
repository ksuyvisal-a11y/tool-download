import os
import sys
import re
import time
import subprocess
import shutil
from typing import Callable, Optional, Dict, Any, List
from downloader import get_ffmpeg_location
from utils import sanitize_filename, format_bytes

class MediaConverterEngine:
    """
    High-Performance Media Converter & Audio Extractor Engine using FFmpeg.
    Supports Video-to-Video transcoding, Video-to-Audio extraction,
    custom bitrates, resolutions, sample rates, FPS, and real-time progress parsing.
    """
    def __init__(self):
        self.ffmpeg_dir = get_ffmpeg_location()
        self._is_cancelled = False
        self._current_process: Optional[subprocess.Popen] = None

    def cancel(self):
        """Cancel the active conversion process."""
        self._is_cancelled = True
        if self._current_process:
            try:
                self._current_process.terminate()
            except Exception:
                pass

    def get_ffmpeg_exe(self) -> str:
        """Get full absolute path to ffmpeg.exe."""
        if self.ffmpeg_dir:
            exe = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
            if os.path.exists(exe):
                return exe
            # Try imageio_ffmpeg default
            try:
                import imageio_ffmpeg
                p = imageio_ffmpeg.get_ffmpeg_exe()
                if p and os.path.exists(p):
                    return p
            except Exception:
                pass
        return "ffmpeg"

    def get_media_duration(self, file_path: str) -> float:
        """Inspect media file duration in seconds using ffmpeg."""
        if not os.path.exists(file_path):
            return 0.0
        ffmpeg_exe = self.get_ffmpeg_exe()
        cmd = [ffmpeg_exe, "-i", file_path]
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo
            )
            _, stderr = proc.communicate(timeout=10)
            # Find Duration: 00:03:45.67
            match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.?\d*)", stderr)
            if match:
                hours = float(match.group(1))
                minutes = float(match.group(2))
                seconds = float(match.group(3))
                return hours * 3600 + minutes * 60 + seconds
        except Exception:
            pass
        return 0.0

    def convert_media(
        self,
        input_path: str,
        output_format: str,
        output_dir: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Convert local media file or extract audio.
        
        output_format: 'mp4', 'mkv', 'webm', 'mov', 'mp3', 'm4a', 'wav', 'flac', 'aac'
        options:
            - preset: '4k', '1080p', '720p', 'mp3_320k', 'mp3_192k', 'wav_lossless', 'custom'
            - resolution: 'original', '3840x2160', '1920x1080', '1280x720', '854x480'
            - fps: 'original', '60', '30', '24'
            - video_bitrate: 'auto', '8000k', '4000k', '2000k', '1000k'
            - audio_bitrate: '320k', '256k', '192k', '128k', '96k'
            - audio_sample_rate: '48000', '44100', '22050'
            - channels: '2' (stereo), '1' (mono)
            - custom_name: optional custom base name
        """
        self._is_cancelled = False
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        options = options or {}
        out_fmt = output_format.lower().replace(".", "").strip()
        if not output_dir:
            output_dir = os.path.dirname(input_path)
        os.makedirs(output_dir, exist_ok=True)

        base_name = options.get("custom_name") or os.path.splitext(os.path.basename(input_path))[0]
        base_name = sanitize_filename(base_name)
        output_filename = f"{base_name}_converted.{out_fmt}"
        output_path = os.path.join(output_dir, output_filename)

        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{base_name}_converted_{counter}.{out_fmt}")
            counter += 1

        total_duration = self.get_media_duration(input_path)
        ffmpeg_exe = self.get_ffmpeg_exe()

        cmd = [ffmpeg_exe, "-y", "-i", input_path]

        is_audio_output = out_fmt in ["mp3", "m4a", "wav", "flac", "aac", "ogg"]
        preset = options.get("preset", "custom")

        # Apply Presets or Custom Configurations
        if out_fmt == "gif" or preset == "gif_animation":
            gif_fps = options.get("fps")
            if not gif_fps or gif_fps == "original":
                gif_fps = "15"
            gif_scale = "480"
            res = options.get("resolution", "")
            if res and "x" in res:
                gif_scale = res.split("x")[0]
            cmd.extend([
                "-vf", f"fps={gif_fps},scale={gif_scale}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0"
            ])
        elif preset == "mp3_320k" or (is_audio_output and out_fmt == "mp3" and options.get("audio_bitrate") == "320k"):
            cmd.extend(["-vn", "-c:a", "libmp3lame", "-b:a", "320k", "-ar", "48000"])
        elif preset == "mp3_192k" or (is_audio_output and out_fmt == "mp3"):
            b_rate = options.get("audio_bitrate", "192k")
            s_rate = options.get("audio_sample_rate", "44100")
            cmd.extend(["-vn", "-c:a", "libmp3lame", "-b:a", b_rate, "-ar", str(s_rate)])
        elif is_audio_output and out_fmt == "m4a":
            b_rate = options.get("audio_bitrate", "256k")
            cmd.extend(["-vn", "-c:a", "aac", "-b:a", b_rate, "-ar", "48000"])
        elif is_audio_output and out_fmt == "wav":
            cmd.extend(["-vn", "-c:a", "pcm_s16le", "-ar", "44100"])
        elif is_audio_output and out_fmt == "flac":
            cmd.extend(["-vn", "-c:a", "flac"])
        elif is_audio_output:
            cmd.extend(["-vn", "-c:a", "libmp3lame", "-b:a", options.get("audio_bitrate", "256k")])
        else:
            # Video Conversion
            res = options.get("resolution", "original")
            fps = options.get("fps", "original")
            v_bitrate = options.get("video_bitrate", "auto")
            a_bitrate = options.get("audio_bitrate", "192k")

            if preset == "4k_video":
                res = "3840x2160"
                v_bitrate = "12000k"
            elif preset == "1080p_video":
                res = "1920x1080"
                v_bitrate = "4500k"
            elif preset == "720p_video":
                res = "1280x720"
                v_bitrate = "2200k"

            # Video codec
            if out_fmt == "webm":
                cmd.extend(["-c:v", "libvpx-vp9", "-c:a", "libopus"])
            else:
                cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])

            if res and res != "original" and "x" in res:
                cmd.extend(["-vf", f"scale={res}:force_original_aspect_ratio=decrease,pad={res}:(ow-iw)/2:(oh-ih)/2"])

            if fps and fps != "original":
                cmd.extend(["-r", str(fps)])

            if v_bitrate and v_bitrate != "auto":
                cmd.extend(["-b:v", v_bitrate])

            if a_bitrate:
                cmd.extend(["-b:a", a_bitrate])

        # Audio Volume Booster (e.g. 1.5 = 150%, 2.0 = 200%, 3.0 = 300%)
        audio_volume = options.get("audio_volume") or options.get("audio_boost")
        if audio_volume and str(audio_volume) not in ["1.0", "1", "normal", "original"] and out_fmt != "gif":
            try:
                vol_f = float(audio_volume)
                cmd.extend(["-filter:a", f"volume={vol_f:.2f}"])
            except Exception:
                pass

        cmd.append(output_path)

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

        start_time = time.time()
        self._current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            universal_newlines=True,
            startupinfo=startupinfo
        )

        time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.?\d*)")
        speed_pattern = re.compile(r"speed=\s*([\d\.]+)x")

        # Notify Start
        if progress_callback:
            progress_callback({
                "status": "processing",
                "percent": 0.0,
                "percent_str": "0.0%",
                "speed_str": "Initializing FFmpeg Engine...",
                "time_str": "00:00 / " + (f"{int(total_duration//60):02d}:{int(total_duration%60):02d}" if total_duration > 0 else "--:--"),
                "filename": os.path.basename(output_path)
            })

        while True:
            if self._is_cancelled:
                self._current_process.terminate()
                if os.path.exists(output_path):
                    try: os.remove(output_path)
                    except Exception: pass
                raise Exception("Conversion cancelled by user.")

            line = self._current_process.stderr.readline()
            if not line and self._current_process.poll() is not None:
                break

            if line:
                t_match = time_pattern.search(line)
                s_match = speed_pattern.search(line)

                if t_match:
                    hrs = float(t_match.group(1))
                    mins = float(t_match.group(2))
                    secs = float(t_match.group(3))
                    curr_secs = hrs * 3600 + mins * 60 + secs

                    percent = 0.0
                    if total_duration > 0:
                        percent = min((curr_secs / total_duration) * 100.0, 99.5)

                    speed_x = s_match.group(1) if s_match else "1.0"
                    
                    if progress_callback:
                        progress_callback({
                            "status": "processing",
                            "percent": round(percent, 1),
                            "percent_str": f"{percent:.1f}%",
                            "speed_str": f"Transcoding Speed: {speed_x}x",
                            "time_str": f"{int(curr_secs//60):02d}:{int(curr_secs%60):02d} / {int(total_duration//60):02d}:{int(total_duration%60):02d}" if total_duration > 0 else f"{int(curr_secs//60):02d}:{int(curr_secs%60):02d}",
                            "filename": os.path.basename(output_path)
                        })

        return_code = self._current_process.wait()
        if return_code != 0:
            if self._is_cancelled:
                raise Exception("Conversion cancelled.")
            raise Exception(f"FFmpeg conversion failed with return code {return_code}")

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        if progress_callback:
            progress_callback({
                "status": "completed",
                "percent": 100.0,
                "percent_str": "100%",
                "speed_str": f"Done in {int(time.time() - start_time)}s",
                "time_str": "Completed",
                "filename": os.path.basename(output_path),
                "file_path": output_path,
                "size_str": format_bytes(file_size)
            })

        return {
            "success": True,
            "filename": os.path.basename(output_path),
            "file_path": output_path,
            "size": file_size,
            "size_str": format_bytes(file_size),
            "format": out_fmt,
            "duration": total_duration,
            "duration_str": f"{int(total_duration//60):02d}:{int(total_duration%60):02d}" if total_duration > 0 else "00:00"
        }

# Global Singleton instance
media_converter = MediaConverterEngine()
