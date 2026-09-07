"""
=============================================================================
SKD UPDATE MANAGER - DEVELOPER RELEASE PUBLISHER & POLICY CONTROL PANEL
=============================================================================
Allows the administrator to draft releases, write changelogs, set update
policies (Optional / Mandatory Force Update), generate SHA-256 checksums,
and publish update.json feeds.
"""

import os
import sys
import json
import time
import hashlib
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from updater import CURRENT_APP_VERSION, compute_file_sha256

UPDATE_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "update.json")

class AdminUpdateManagerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SKD UPDATE MANAGER - Release & Version Control Panel")
        self.root.geometry("680;720".replace(';', 'x'))
        self.root.minsize(620, 650)
        self.root.configure(bg="#070B16")

        self.selected_exe_path = ""
        self._server_running = False

        self._build_ui()
        self._load_current_feed()

    def _build_ui(self):
        # Header Banner
        header = tk.Frame(self.root, bg="#0D1425", padx=20, pady=16, highlightbackground="#162238", highlightthickness=1)
        header.pack(fill="x", padx=16, pady=(16, 10))

        lbl_brand = tk.Label(header, text="🚀 SKD UPDATE MANAGER", font=("Segoe UI", 14, "bold"), fg="#00E5FF", bg="#0D1425")
        lbl_brand.pack(anchor="w")

        lbl_sub = tk.Label(header, text=f"Client Base Version: v{CURRENT_APP_VERSION}  •  Release Management & Auto-Updater Server Feed", font=("Segoe UI", 9), fg="#8E9CB2", bg="#0D1425")
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Main Form Container
        container = tk.Frame(self.root, bg="#070B16")
        container.pack(fill="both", expand=True, padx=16, pady=4)

        # Version & Date Row
        row1 = tk.Frame(container, bg="#070B16")
        row1.pack(fill="x", pady=6)

        # Version Field
        f_ver = tk.Frame(row1, bg="#070B16")
        f_ver.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(f_ver, text="New Release Version (e.g. 1.1.0):", font=("Segoe UI", 9, "bold"), fg="#E2E8F0", bg="#070B16").pack(anchor="w")
        self.ent_version = tk.Entry(f_ver, font=("Consolas", 10, "bold"), bg="#0D1425", fg="#00E5FF", insertbackground="#00E5FF", relief="flat", highlightbackground="#162238", highlightthickness=1)
        self.ent_version.pack(fill="x", pady=4, ipady=4)
        self.ent_version.insert(0, "1.1.0")

        # Date Field
        f_date = tk.Frame(row1, bg="#070B16")
        f_date.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(f_date, text="Release Date:", font=("Segoe UI", 9, "bold"), fg="#E2E8F0", bg="#070B16").pack(anchor="w")
        self.ent_date = tk.Entry(f_date, font=("Segoe UI", 10), bg="#0D1425", fg="#E2E8F0", insertbackground="#FFFFFF", relief="flat", highlightbackground="#162238", highlightthickness=1)
        self.ent_date.pack(fill="x", pady=4, ipady=4)
        self.ent_date.insert(0, datetime.now().strftime("%d %b %Y"))

        # Update Policy Frame
        f_policy = tk.LabelFrame(container, text="  UPDATE POLICY & BEHAVIOR  ", font=("Segoe UI", 9, "bold"), fg="#A78BFA", bg="#0D1425", padx=14, pady=10, highlightbackground="#162238", highlightthickness=1)
        f_policy.pack(fill="x", pady=8)

        self.var_policy = tk.StringVar(value="optional")
        
        rb1 = tk.Radiobutton(f_policy, text="Optional Update (User can choose 'UPDATE NOW' or 'LATER')", variable=self.var_policy, value="optional", font=("Segoe UI", 9), fg="#E2E8F0", bg="#0D1425", selectcolor="#070B16", activebackground="#0D1425", activeforeground="#00E5FF")
        rb1.pack(anchor="w", pady=2)

        rb2 = tk.Radiobutton(f_policy, text="Mandatory / Force Update (User MUST update to proceed with using the tool)", variable=self.var_policy, value="mandatory", font=("Segoe UI", 9, "bold"), fg="#EF4444", bg="#0D1425", selectcolor="#070B16", activebackground="#0D1425", activeforeground="#EF4444")
        rb2.pack(anchor="w", pady=2)

        # Download URL & Binary Package
        f_dl = tk.Frame(container, bg="#070B16")
        f_dl.pack(fill="x", pady=6)

        tk.Label(f_dl, text="Download URL (Direct link to new .exe file or GitHub Release):", font=("Segoe UI", 9, "bold"), fg="#E2E8F0", bg="#070B16").pack(anchor="w")
        self.ent_url = tk.Entry(f_dl, font=("Consolas", 9), bg="#0D1425", fg="#E2E8F0", insertbackground="#FFFFFF", relief="flat", highlightbackground="#162238", highlightthickness=1)
        self.ent_url.pack(fill="x", pady=4, ipady=4)
        self.ent_url.insert(0, "https://github.com/ksuyvisal-a11y/tool-download/releases/download/v1.1.0/SKD_TOOL.exe")

        # Binary File Inspect Row (Auto Checksum & Size)
        f_bin = tk.Frame(container, bg="#0D1425", padx=12, pady=10, highlightbackground="#162238", highlightthickness=1)
        f_bin.pack(fill="x", pady=6)

        btn_browse = tk.Button(f_bin, text="📁 Browse .EXE to Calculate SHA-256 & Size", font=("Segoe UI", 9, "bold"), bg="#18243E", fg="#00E5FF", relief="flat", cursor="hand2", padx=10, pady=4, command=self._browse_exe)
        btn_browse.pack(side="left")

        self.lbl_checksum = tk.Label(f_bin, text="No binary file inspected yet", font=("Segoe UI", 8), fg="#8E9CB2", bg="#0D1425")
        self.lbl_checksum.pack(side="left", padx=10)

        # Changelog Text Area
        f_change = tk.Frame(container, bg="#070B16")
        f_change.pack(fill="both", expand=True, pady=6)

        tk.Label(f_change, text="What's New / Changelog (One bullet point per line):", font=("Segoe UI", 9, "bold"), fg="#E2E8F0", bg="#070B16").pack(anchor="w")
        self.txt_changelog = tk.Text(f_change, height=6, font=("Segoe UI", 9), bg="#0D1425", fg="#E2E8F0", insertbackground="#00E5FF", relief="flat", highlightbackground="#162238", highlightthickness=1, padx=8, pady=6)
        self.txt_changelog.pack(fill="both", expand=True, pady=4)

        # Actions Footer
        footer = tk.Frame(self.root, bg="#070B16", padx=16, pady=14)
        footer.pack(fill="x")

        btn_save = tk.Button(footer, text="🚀 Publish & Save update.json", font=("Segoe UI", 10, "bold"), bg="#00E5FF", fg="#060913", relief="flat", cursor="hand2", padx=16, pady=8, command=self._publish_update)
        btn_save.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_test_server = tk.Button(footer, text="⚡ Start Local Test Server (Port 8080)", font=("Segoe UI", 9, "bold"), bg="#18243E", fg="#7C5CFF", relief="flat", cursor="hand2", padx=12, pady=8, command=self._toggle_local_server)
        btn_test_server.pack(side="right", padx=(6, 0))
        self.btn_test_server = btn_test_server

    def _load_current_feed(self):
        if os.path.exists(UPDATE_JSON_PATH):
            try:
                with open(UPDATE_JSON_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.ent_version.delete(0, tk.END)
                self.ent_version.insert(0, data.get("version", "1.1.0"))

                self.ent_date.delete(0, tk.END)
                self.ent_date.insert(0, data.get("release_date", datetime.now().strftime("%d %b %Y")))

                self.ent_url.delete(0, tk.END)
                self.ent_url.insert(0, data.get("download_url", ""))

                self.var_policy.set("mandatory" if data.get("mandatory") else "optional")

                cl = data.get("changelog", [])
                self.txt_changelog.delete("1.0", tk.END)
                self.txt_changelog.insert("1.0", "\n".join(cl))

                if data.get("sha256"):
                    self.lbl_checksum.config(text=f"SHA-256: {data.get('sha256')[:16]}... ({data.get('file_size', '')})", fg="#10B981")
            except Exception as e:
                print(f"Error loading update.json: {e}")

    def _browse_exe(self):
        f = filedialog.askopenfilename(title="Select Release Executable", filetypes=[("Executable Files", "*.exe")])
        if f:
            self.selected_exe_path = f
            size_mb = os.path.getsize(f) / (1024 * 1024)
            h = compute_file_sha256(f)
            self.calculated_sha256 = h
            self.calculated_size = f"{size_mb:.1f} MB"
            self.lbl_checksum.config(text=f"✓ {os.path.basename(f)} • {self.calculated_size} • SHA256: {h[:12]}...", fg="#10B981")

    def _publish_update(self):
        ver = self.ent_version.get().strip()
        rel_date = self.ent_date.get().strip()
        dl_url = self.ent_url.get().strip()
        mandatory = (self.var_policy.get() == "mandatory")

        raw_cl = self.txt_changelog.get("1.0", tk.END).strip().splitlines()
        changelog = [line.strip() for line in raw_cl if line.strip()]

        if not ver or not dl_url:
            messagebox.showerror("Missing Information", "Please specify both Version number and Download URL.")
            return

        payload = {
            "version": ver,
            "title": f"SKD TOOL v{ver} Release",
            "release_date": rel_date,
            "mandatory": mandatory,
            "changelog": changelog or ["Performance improvements and bug fixes."],
            "download_url": dl_url,
            "sha256": getattr(self, 'calculated_sha256', ""),
            "file_size": getattr(self, 'calculated_size', "Unknown")
        }

        try:
            with open(UPDATE_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Update Published Successfully!", f"update.json has been written for v{ver}.\n\nPolicy: {'MANDATORY (Force Update)' if mandatory else 'OPTIONAL'}\nChangelog: {len(changelog)} items.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save update.json: {e}")

    def _toggle_local_server(self):
        if not self._server_running:
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            import socketserver

            class Handler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

            def _run():
                try:
                    server = HTTPServer(('127.0.0.1', 8080), Handler)
                    self._server_running = True
                    self.btn_test_server.config(text="🟢 Local Server Running (Port 8080)", bg="#065F46", fg="#FFFFFF")
                    server.serve_forever()
                except Exception as e:
                    print("Local server stopped or port busy:", e)

            threading.Thread(target=_run, daemon=True).start()
            messagebox.showinfo("Local Test Server Started", "Local update server running at:\nhttp://127.0.0.1:8080/update.json\n\nYou can set Download URL to test local updates!")


def main():
    root = tk.Tk()
    app = AdminUpdateManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
