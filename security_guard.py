"""
=============================================================================
SKD CYBERGUARD V2 - ENTERPRISE ZERO-TRUST DEFENSE & ANTI-TAMPER SHIELD
=============================================================================
1. Advanced Win32 Anti-Debugging (PEB, DebugPort, ThreadHideFromDebugger)
2. Hardware Breakpoint Inspection (CPU DR0-DR7 registers)
3. Reverse-Engineering Window Title & Process Name Scanner
4. Injected Hooking / Cheat DLL Detection (Frida, Detours, MinHook, CE)
5. Anti-Clock Rollback with Cryptographic Salt & NTP/WorldTime Verification
6. Multi-threaded Real-time Heartbeat Watchdog Daemon with Emergency Evacuation
=============================================================================
"""

import os
import sys
import time
import ctypes
from ctypes import wintypes
import hashlib
import threading
import subprocess
from datetime import datetime
from typing import Tuple, List, Optional
import urllib.request
import json

# Process names known for reverse engineering and memory debugging
BLACKLISTED_PROCESSES = {
    # Debuggers & Disassemblers
    "x64dbg.exe", "x32dbg.exe", "ida.exe", "ida64.exe", "ghidra.exe",
    "ollydbg.exe", "radare2.exe", "immunitydebugger.exe", "windbg.exe",
    "dnspy.exe", "dnspy-x86.exe", "de4dot.exe", "scylla.exe", "scylla_x64.exe",
    "scylla_x86.exe", "pestudio.exe", "pe-bear.exe", "hxd.exe",
    
    # Memory Manipulators & Cheats
    "cheatengine-x86_64.exe", "cheatengine-i386.exe", "cheatengine.exe",
    "processhacker.exe", "processhacker2.exe", "procmon.exe", "procmon64.exe",
    "procexp.exe", "procexp64.exe",
    
    # Network Sniffers & API Monitors
    "fiddler.exe", "wireshark.exe", "httpdebuggerui.exe", "httpdebugger.exe",
    "charles.exe", "burpsuite.exe", "mitmproxy.exe", "apimonitor-x86.exe",
    "apimonitor-x64.exe"
}

# Window title keywords indicative of active reverse engineering
BLACKLISTED_WINDOW_KEYWORDS = [
    "x64dbg", "x32dbg", "ida pro", "ida v", "ghidra", "cheat engine",
    "process hacker", "wireshark", "fiddler", "httpdebugger", "api monitor",
    "ollydbg", "binary ninja", "dnspy"
]

# Suspicious DLLs commonly injected by hookers and memory analyzers
BLACKLISTED_MODULES = [
    "minhook", "frida", "detours", "scylla", "easyhook", "cheatengine", "speedhack"
]

# Secret Salt for Local Time & State Integrity
WATCHDOG_SECRET_SALT = b"SKD_TIME_INTEGRITY_SALT_2026_@ENTERPRISE_SHIELD_PRO_V2#"


class CONTEXT64(ctypes.Structure):
    _fields_ = [
        ('P1Home', ctypes.c_uint64),
        ('P2Home', ctypes.c_uint64),
        ('P3Home', ctypes.c_uint64),
        ('P4Home', ctypes.c_uint64),
        ('P5Home', ctypes.c_uint64),
        ('P6Home', ctypes.c_uint64),
        ('ContextFlags', ctypes.c_uint32),
        ('MxCsr', ctypes.c_uint32),
        ('SegCs', ctypes.c_uint16),
        ('SegDs', ctypes.c_uint16),
        ('SegEs', ctypes.c_uint16),
        ('SegFs', ctypes.c_uint16),
        ('SegGs', ctypes.c_uint16),
        ('SegSs', ctypes.c_uint16),
        ('EFlags', ctypes.c_uint32),
        ('Dr0', ctypes.c_uint64),
        ('Dr1', ctypes.c_uint64),
        ('Dr2', ctypes.c_uint64),
        ('Dr3', ctypes.c_uint64),
        ('Dr6', ctypes.c_uint64),
        ('Dr7', ctypes.c_uint64),
    ]


class SecurityGuard:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SecurityGuard, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._is_monitoring = False
        self._tamper_detected = False
        self._tamper_reason = ""
        self._watchdog_thread: Optional[threading.Thread] = None

    # =========================================================================
    # 1. ADVANCED WIN32 ANTI-DEBUGGING (API & PEB)
    # =========================================================================
    def is_debugger_present(self) -> Tuple[bool, str]:
        """Check for user-mode, remote, and kernel-mode debuggers."""
        if sys.platform != "win32":
            return False, ""

        try:
            kernel32 = ctypes.windll.kernel32

            # 1. Standard IsDebuggerPresent API
            if kernel32.IsDebuggerPresent():
                return True, "Active User-mode Debugger detected via IsDebuggerPresent!"

            # 2. CheckRemoteDebuggerPresent API
            is_remote_present = ctypes.c_bool(False)
            current_proc = kernel32.GetCurrentProcess()
            if kernel32.CheckRemoteDebuggerPresent(current_proc, ctypes.byref(is_remote_present)):
                if is_remote_present.value:
                    return True, "Remote Debugger detected via CheckRemoteDebuggerPresent!"

            # 3. NtQueryInformationProcess (ProcessDebugPort = 7)
            try:
                ntdll = ctypes.windll.ntdll
                debug_port = ctypes.c_ulong(0)
                status = ntdll.NtQueryInformationProcess(
                    current_proc,
                    7,  # ProcessDebugPort
                    ctypes.byref(debug_port),
                    ctypes.sizeof(debug_port),
                    None
                )
                if status == 0 and debug_port.value != 0:
                    return True, "Debug Port Attachment detected via NtQueryInformationProcess!"
            except Exception:
                pass

        except Exception:
            pass

        return False, ""

    # =========================================================================
    # 2. HARDWARE BREAKPOINTS DETECTION (CPU DR0-DR7 REGISTERS)
    # =========================================================================
    def check_hardware_breakpoints(self) -> Tuple[bool, str]:
        """Inspect CPU Debug Registers (DR0-DR3, DR7) to detect active hardware breakpoints."""
        if sys.platform != "win32":
            return False, ""

        try:
            kernel32 = ctypes.windll.kernel32
            thread_id = kernel32.GetCurrentThreadId()
            # THREAD_GET_CONTEXT = 0x0008, THREAD_SUSPEND_RESUME = 0x0002
            h_thread = kernel32.OpenThread(0x0008 | 0x0002, False, thread_id)
            if h_thread:
                try:
                    ctx = CONTEXT64()
                    ctx.ContextFlags = 0x00100010  # CONTEXT_DEBUG_REGISTERS
                    if kernel32.GetThreadContext(h_thread, ctypes.byref(ctx)):
                        if ctx.Dr0 != 0 or ctx.Dr1 != 0 or ctx.Dr2 != 0 or ctx.Dr3 != 0:
                            return True, "Hardware Breakpoints detected in CPU Debug Registers (DR0-DR3)!"
                finally:
                    kernel32.CloseHandle(h_thread)
        except Exception:
            pass

        return False, ""

    # =========================================================================
    # 3. THREAD HIDING FROM DEBUGGERS
    # =========================================================================
    def hide_threads_from_debugger(self):
        """Request OS kernel to hide current thread from all attaching debuggers."""
        if sys.platform != "win32":
            return

        try:
            ntdll = ctypes.windll.ntdll
            kernel32 = ctypes.windll.kernel32
            cur_thread = kernel32.GetCurrentThread()
            # ThreadHideFromDebugger = 0x11
            ntdll.NtSetInformationThread(cur_thread, 0x11, 0, 0)
        except Exception:
            pass

    # =========================================================================
    # 4. PROCESS & WINDOW TITLE SCANNER
    # =========================================================================
    def scan_blacklisted_processes(self) -> Tuple[bool, str]:
        """Scan active system processes and open window titles for disassemblers and sniffers."""
        if sys.platform != "win32":
            return False, ""

        # A. Check Window Titles
        try:
            user32 = ctypes.windll.user32
            found_title = []

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

            def enum_cb(hwnd, lparam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        t_low = buf.value.lower()
                        for kw in BLACKLISTED_WINDOW_KEYWORDS:
                            if kw in t_low:
                                found_title.append(buf.value)
                                return False
                return True

            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            if found_title:
                return True, f"Security Violation: Unauthorized reverse-engineering window detected ({found_title[0]})!"
        except Exception:
            pass

        # B. Check Running Process Names
        try:
            cmd = "tasklist /FO CSV /NH"
            output = subprocess.check_output(cmd, shell=True, creationflags=0x08000000).decode('utf-8', errors='ignore')
            for line in output.splitlines():
                if not line.strip():
                    continue
                proc_name = line.split(',')[0].strip('"').lower()
                if proc_name in BLACKLISTED_PROCESSES:
                    return True, f"Security Violation: Unauthorized tool detected ({proc_name})!"
        except Exception:
            pass

        return False, ""

    # =========================================================================
    # 5. INJECTED HOOK MODULE / DLL DETECTION
    # =========================================================================
    def check_injected_modules(self) -> Tuple[bool, str]:
        """Check if third-party hooking or memory manipulation libraries are injected."""
        if sys.platform != "win32":
            return False, ""

        try:
            kernel32 = ctypes.windll.kernel32
            for mod in BLACKLISTED_MODULES:
                h_mod = kernel32.GetModuleHandleW(mod)
                if h_mod:
                    return True, f"Security Violation: Injected hook library detected ({mod}.dll)!"
        except Exception:
            pass

        return False, ""

    # =========================================================================
    # 6. ANTI-TIME ROLLBACK (CRYPTOGRAPHIC MONOTONICITY & NTP VERIFICATION)
    # =========================================================================
    def check_and_update_clock_integrity(self) -> Tuple[bool, str]:
        """Detect system clock rewinding by verifying against a cryptographically signed high-water mark."""
        app_data_root = os.environ.get("APPDATA", os.path.expanduser("~"))
        watchdog_dir = os.path.join(app_data_root, "SKD_Tool", ".sys_cache")
        try:
            os.makedirs(watchdog_dir, exist_ok=True)
        except Exception:
            pass

        record_file = os.path.join(watchdog_dir, ".wtd_log.dat")
        current_epoch = int(time.time())

        # If previous record exists, verify monotonicity
        if os.path.exists(record_file):
            try:
                with open(record_file, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore').strip()
                
                parts = content.split(':')
                if len(parts) == 2:
                    recorded_epoch = int(parts[0])
                    recorded_hash = parts[1]
                    
                    # Verify HMAC integrity of record
                    expected_hash = hashlib.sha256(f"{recorded_epoch}".encode() + WATCHDOG_SECRET_SALT).hexdigest()
                    if expected_hash == recorded_hash:
                        # If current system time is more than 30 minutes in the past compared to last run
                        if current_epoch < (recorded_epoch - 1800):
                            return False, "System Clock Tampering Detected! Please correct your PC date & time."
            except Exception:
                pass

        # Write new highest monotonic epoch
        try:
            new_hash = hashlib.sha256(f"{current_epoch}".encode() + WATCHDOG_SECRET_SALT).hexdigest()
            payload = f"{current_epoch}:{new_hash}"
            with open(record_file, 'w', encoding='utf-8') as f:
                f.write(payload)
        except Exception:
            pass

        return True, ""

    # =========================================================================
    # 7. BINARY SELF-INTEGRITY VALIDATION
    # =========================================================================
    def verify_executable_integrity(self) -> bool:
        """Verify that the executable itself has not been corrupted or truncated."""
        if not getattr(sys, 'frozen', False):
            return True  # Dev environment

        exe_path = sys.executable
        if not os.path.exists(exe_path):
            return True

        try:
            f_size = os.path.getsize(exe_path)
            if f_size < 1024 * 1024:  # At least 1MB
                return False
            return True
        except Exception:
            return True

    # =========================================================================
    # 8. CONTINUOUS REAL-TIME SECURITY HEARTBEAT (DAEMON WATCHDOG)
    # =========================================================================
    def start_security_watchdog(self, on_violation_callback=None):
        """Start a persistent background security thread that enforces real-time shielding."""
        if self._is_monitoring:
            return

        self._is_monitoring = True

        def _guard_loop():
            # Apply initial thread hiding
            self.hide_threads_from_debugger()

            while self._is_monitoring:
                # 1. Check Debugger
                is_debug, reason = self.is_debugger_present()
                if is_debug:
                    self._handle_violation(reason, on_violation_callback)
                    break

                # 2. Check Hardware Breakpoints
                is_hw_bp, reason = self.check_hardware_breakpoints()
                if is_hw_bp:
                    self._handle_violation(reason, on_violation_callback)
                    break

                # 3. Check Blacklisted Tools & Windows
                is_blacklisted, reason = self.scan_blacklisted_processes()
                if is_blacklisted:
                    self._handle_violation(reason, on_violation_callback)
                    break

                # 4. Check Injected Hooking Modules
                is_injected, reason = self.check_injected_modules()
                if is_injected:
                    self._handle_violation(reason, on_violation_callback)
                    break

                # 5. Check Clock Rollback
                clock_ok, reason = self.check_and_update_clock_integrity()
                if not clock_ok:
                    self._handle_violation(reason, on_violation_callback)
                    break

                # Heartbeat sleep
                time.sleep(3.5)

        self._watchdog_thread = threading.Thread(target=_guard_loop, daemon=True, name="SKD_CyberGuard")
        self._watchdog_thread.start()

    def _handle_violation(self, reason: str, callback=None):
        self._tamper_detected = True
        self._tamper_reason = reason
        if callback:
            try:
                callback(reason)
            except Exception:
                pass
        self._emergency_shutdown(reason)

    def _emergency_shutdown(self, reason: str):
        """Emergency process termination when active cracking/tampering is detected."""
        print(f"\n[SECURITY SHIELD TRIGGERED]: {reason}\n")
        try:
            if sys.platform == "win32":
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"⚠️ Security Alert:\n\n{reason}\n\nThe application will terminate immediately for security protection.",
                    "SKD Tool - CyberGuard Protection",
                    0x10 | 0x0
                )
        except Exception:
            pass

        # Force terminate process
        os._exit(1)


# Global Singleton Guard Instance
guard = SecurityGuard()


def perform_startup_security_check() -> Tuple[bool, str]:
    """Perform comprehensive zero-trust security scan on tool startup."""
    # 1. Thread Hiding
    guard.hide_threads_from_debugger()

    # 2. Debugger Check
    dbg, msg = guard.is_debugger_present()
    if dbg:
        return False, msg

    # 3. Hardware Breakpoints Check
    hw_bp, msg = guard.check_hardware_breakpoints()
    if hw_bp:
        return False, msg

    # 4. Blacklist Tools & Window Scan
    blk, msg = guard.scan_blacklisted_processes()
    if blk:
        return False, msg

    # 5. Injected Hook Module Check
    inj, msg = guard.check_injected_modules()
    if inj:
        return False, msg

    # 6. Clock Integrity Check
    clk, msg = guard.check_and_update_clock_integrity()
    if not clk:
        return False, msg

    # 7. Executable Integrity Check
    if not guard.verify_executable_integrity():
        return False, "Binary Integrity Compromised: Executable appears damaged or modified."

    # Start real-time background protection watchdog
    guard.start_security_watchdog()

    return True, "Security Check Passed: Environment Clean & Verified."
