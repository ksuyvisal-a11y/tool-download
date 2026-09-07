import os
import sys
import time
import json
import uuid
import threading
import subprocess
from datetime import datetime, date
from typing import Callable, Optional, Dict, Any, List
from utils import get_app_data_path

SCHEDULER_DB_PATH = get_app_data_path("scheduler_jobs.json")
AUTOMATION_DB_PATH = get_app_data_path("automation_settings.json")

DEFAULT_AUTOMATION_SETTINGS = {
    "auto_download": False,
    "clipboard_sniffer": False,
    "auto_start_download": True,
    "auto_retry_failed": True,
    "max_retries": 3,
    "auto_organize_files": True,
    "auto_convert_enabled": False,
    "auto_convert_format": "mp3",
    "auto_open_folder": True,
    "sound_alert_on_complete": True,
    "sound_mode": "bell",
    "shutdown_pc_after_complete": False,
    "max_simultaneous_downloads": 3,
    "max_speed_limit_kb": 0
}

def load_scheduler_jobs() -> List[Dict[str, Any]]:
    """Load scheduled jobs from persistent JSON."""
    if os.path.exists(SCHEDULER_DB_PATH):
        try:
            with open(SCHEDULER_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_scheduler_jobs(jobs: List[Dict[str, Any]]):
    """Save scheduled jobs to persistent JSON."""
    try:
        with open(SCHEDULER_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def load_automation_settings() -> Dict[str, Any]:
    """Load automation config."""
    if os.path.exists(AUTOMATION_DB_PATH):
        try:
            with open(AUTOMATION_DB_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                merged = dict(DEFAULT_AUTOMATION_SETTINGS)
                merged.update(saved)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_AUTOMATION_SETTINGS)

def save_automation_settings(settings: Dict[str, Any]):
    """Save automation config."""
    try:
        with open(AUTOMATION_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


class DownloadScheduler:
    """
    Background Timed Scheduler & Smart Automation Service.
    Monitors upcoming scheduled jobs, speed rules, clipboard events, and system shutdown routines.
    """
    def __init__(self, on_trigger_job: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.on_trigger_job = on_trigger_job
        self.jobs: List[Dict[str, Any]] = load_scheduler_jobs()
        self.settings: Dict[str, Any] = load_automation_settings()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_checked_minute = ""
        self._shutdown_timer: Optional[threading.Timer] = None
        self._is_shutdown_scheduled = False

    def start(self):
        """Start the background scheduler thread."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop scheduler."""
        self._running = False

    def add_job(
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
        """
        Add a new timed job.
        start_time: 'HH:MM' (24-hour format)
        schedule_date: 'YYYY-MM-DD' or '' for today/any
        repeat: 'once', 'daily', 'weekdays'
        """
        job = {
            "id": f"job_{uuid.uuid4().hex[:8]}",
            "name": name or f"Scheduled Job {len(self.jobs) + 1}",
            "start_time": start_time.strip(),
            "end_time": end_time.strip(),
            "date": schedule_date.strip() or datetime.now().strftime("%Y-%m-%d"),
            "repeat": repeat.lower(),
            "urls": urls or [],
            "preset": preset,
            "speed_limit_kb": speed_limit_kb,
            "max_streams": max_streams,
            "status": "scheduled",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.jobs = load_scheduler_jobs()
        self.jobs.append(job)
        save_scheduler_jobs(self.jobs)
        return job

    def remove_job(self, job_id: str) -> bool:
        """Remove job by ID."""
        self.jobs = load_scheduler_jobs()
        orig_len = len(self.jobs)
        self.jobs = [j for j in self.jobs if j.get("id") != job_id]
        save_scheduler_jobs(self.jobs)
        return len(self.jobs) < orig_len

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Return all scheduled jobs."""
        self.jobs = load_scheduler_jobs()
        return self.jobs

    def _scheduler_loop(self):
        while self._running:
            try:
                now = datetime.now()
                current_hm = now.strftime("%H:%M")
                current_ymd = now.strftime("%Y-%m-%d")
                is_weekday = now.weekday() < 5

                # Check jobs once per minute
                if current_hm != self._last_checked_minute:
                    self._last_checked_minute = current_hm
                    self.jobs = load_scheduler_jobs()
                    updated = False

                    for job in self.jobs:
                        if job.get("status") != "scheduled":
                            continue

                        job_time = job.get("start_time", "")
                        job_date = job.get("date", "")
                        repeat = job.get("repeat", "once")

                        should_trigger = False
                        if job_time == current_hm:
                            if repeat == "daily":
                                should_trigger = True
                            elif repeat == "weekdays" and is_weekday:
                                should_trigger = True
                            elif repeat == "once" and (not job_date or job_date == current_ymd):
                                should_trigger = True
                                job["status"] = "completed"
                                updated = True

                        if should_trigger:
                            job["last_triggered"] = now.strftime("%Y-%m-%d %H:%M:%S")
                            if self.on_trigger_job:
                                threading.Thread(target=self.on_trigger_job, args=(job,), daemon=True).start()

                    if updated:
                        save_scheduler_jobs(self.jobs)
            except Exception:
                pass
            time.sleep(15)

    def trigger_system_shutdown(self, delay_seconds: int = 30, callback: Optional[Callable] = None):
        """Schedule Windows PC shutdown with safety delay."""
        if self._is_shutdown_scheduled:
            return

        self._is_shutdown_scheduled = True

        def _do_shutdown():
            try:
                if sys.platform == "win32":
                    subprocess.run(["shutdown", "/s", "/t", "0"], check=False)
            except Exception:
                pass

        self._shutdown_timer = threading.Timer(delay_seconds, _do_shutdown)
        self._shutdown_timer.daemon = True
        self._shutdown_timer.start()

        if callback:
            callback(delay_seconds)

    def cancel_system_shutdown(self):
        """Cancel scheduled PC shutdown."""
        if self._shutdown_timer:
            self._shutdown_timer.cancel()
            self._shutdown_timer = None
        self._is_shutdown_scheduled = False
        try:
            if sys.platform == "win32":
                subprocess.run(["shutdown", "/a"], check=False)
        except Exception:
            pass
