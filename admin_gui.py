import os
import sys
import json
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image
from datetime import datetime

from licensing import generate_license_key, get_machine_hwid
from utils import get_base_dir, get_resource_path, get_app_data_path

SKD_THEME = {
    "bg_main": "#060911",
    "header_bg": "#0B101C",
    "card_bg": "#0F1728",
    "card_border": "#1E2B45",
    "input_bg": "#090E1A",
    "primary": "#00F2FE",
    "accent_emerald": "#10B981",
    "accent_rose": "#EF4444",
    "text_muted": "#8395B0"
}

FONT_FAMILY = "Segoe UI"
BASE_DIR = get_base_dir()
LOGO_PATH = get_resource_path(os.path.join("assets", "skd_logo_clean.png"))
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = get_resource_path(os.path.join("assets", "skd_logo.png"))
ICON_PATH = get_resource_path(os.path.join("assets", "app_icon.ico"))


class AdminKeyGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("⚡ SKD TOOL - Admin License Key Generator Dashboard")
        self.geometry("640x680")
        self.minsize(580, 600)
        self.configure(fg_color=SKD_THEME["bg_main"])

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 640) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"+{x}+{y}")

        self.hwid_var = tk.StringVar()
        self.plan_var = tk.StringVar(value="Lifetime VIP (No Expiration)")
        self.custom_days_var = tk.StringVar(value="30")
        self.generated_key_var = tk.StringVar()
        self.history_list = []

        self._load_key_history()
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=SKD_THEME["header_bg"], corner_radius=0)
        hdr.pack(fill="x", pady=(0, 16))

        if os.path.exists(LOGO_PATH):
            try:
                pil_img = Image.open(LOGO_PATH)
                w, h = pil_img.size
                ratio = w / h if h > 0 else 1.0
                disp_w = 70
                disp_h = int(disp_w / ratio)
                self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(disp_w, disp_h))
                ctk.CTkLabel(hdr, image=self.logo_img, text="").pack(pady=(12, 2))
            except Exception:
                pass

        ctk.CTkLabel(
            hdr, text="⚡ SKD TOOL RSA-2048 KEY GENERATOR",
            font=ctk.CTkFont(family=FONT_FAMILY, size=17, weight="bold"), text_color=SKD_THEME["primary"]
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            hdr, text="Enterprise Asymmetric Digital Signatures (Unforgeable Cryptographic Keys)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=SKD_THEME["text_muted"]
        ).pack(pady=(0, 12))

        # Main Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)

        # Form Card
        card = ctk.CTkFrame(body, fg_color=SKD_THEME["card_bg"], corner_radius=12, border_width=1, border_color=SKD_THEME["card_border"])
        card.pack(fill="x", pady=(0, 12))

        # 1. Customer HWID
        ctk.CTkLabel(card, text="1. Customer Machine HWID (Optional, leave blank for Global Key):", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        
        hwid_row = ctk.CTkFrame(card, fg_color="transparent")
        hwid_row.pack(fill="x", padx=16, pady=(0, 10))
        hwid_row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(
            hwid_row, textvariable=self.hwid_var, placeholder_text="e.g. SKD-2533-59E4-5224-CE4D (or leave empty)",
            height=36, font=ctk.CTkFont(family=FONT_FAMILY, size=12), fg_color=SKD_THEME["input_bg"], border_color=SKD_THEME["card_border"]
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            hwid_row, text="📋 Paste", width=75, height=36,
            fg_color="#18253A", hover_color="#243754", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._paste_hwid
        ).grid(row=0, column=1)

        # 2. Plan Duration
        ctk.CTkLabel(card, text="2. Select License Plan Duration:", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")).pack(anchor="w", padx=16, pady=(4, 4))
        
        plan_row = ctk.CTkFrame(card, fg_color="transparent")
        plan_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkOptionMenu(
            plan_row, variable=self.plan_var,
            values=[
                "Lifetime VIP (No Expiration)",
                "365 Days Plan (1 Year)",
                "180 Days Plan (6 Months)",
                "90 Days Plan (3 Months)",
                "30 Days Plan (1 Month)",
                "Custom Days Plan"
            ],
            height=36, width=280, fg_color=SKD_THEME["input_bg"],
            command=self._on_plan_change
        ).pack(side="left", padx=(0, 12))

        self.custom_entry = ctk.CTkEntry(
            plan_row, textvariable=self.custom_days_var, width=80, height=36,
            placeholder_text="Days", fg_color=SKD_THEME["input_bg"], border_color=SKD_THEME["card_border"]
        )

        # Generate Button
        ctk.CTkButton(
            card, text="⚡ GENERATE LICENSE KEY NOW", height=42,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=SKD_THEME["primary"], text_color="#05080E", hover_color="#00D0DA",
            corner_radius=8, command=self._generate_key_action
        ).pack(fill="x", padx=16, pady=(0, 14))

        # Result Card
        res_card = ctk.CTkFrame(body, fg_color=SKD_THEME["card_bg"], corner_radius=12, border_width=1, border_color=SKD_THEME["card_border"])
        res_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(res_card, text="🔑 Generated Activation Key (Send to Customer):", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=SKD_THEME["accent_emerald"]).pack(anchor="w", padx=16, pady=(10, 4))

        res_row = ctk.CTkFrame(res_card, fg_color="transparent")
        res_row.pack(fill="x", padx=16, pady=(0, 12))
        res_row.grid_columnconfigure(0, weight=1)

        self.key_entry = ctk.CTkEntry(
            res_row, textvariable=self.generated_key_var, font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            height=40, fg_color=SKD_THEME["input_bg"], border_color=SKD_THEME["primary"]
        )
        self.key_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            res_row, text="📋 Copy Key", width=95, height=40,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="#10B981", text_color="#05080E", hover_color="#059669",
            command=self._copy_key
        ).grid(row=0, column=1)

        # Recent Keys Log Card
        hist_card = ctk.CTkFrame(body, fg_color=SKD_THEME["card_bg"], corner_radius=12, border_width=1, border_color=SKD_THEME["card_border"])
        hist_card.pack(fill="both", expand=True, pady=(0, 10))
        hist_card.grid_columnconfigure(0, weight=1)
        hist_card.grid_rowconfigure(1, weight=1)

        h_top = ctk.CTkFrame(hist_card, fg_color="transparent")
        h_top.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        h_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(h_top, text="Recent Generated Keys Log", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color="#FFFFFF").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(h_top, text="Export .txt", width=80, height=26, fg_color="#18253A", command=self._export_keys_txt).grid(row=0, column=1)

        self.hist_scroll = ctk.CTkScrollableFrame(hist_card, fg_color=SKD_THEME["input_bg"], corner_radius=8)
        self.hist_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.hist_scroll.grid_columnconfigure(1, weight=1)

        self._render_history_ui()

    def _on_plan_change(self, choice):
        if "Custom" in choice:
            self.custom_entry.pack(side="left")
        else:
            self.custom_entry.pack_forget()

    def _paste_hwid(self):
        try:
            txt = self.clipboard_get().strip()
            if txt:
                self.hwid_var.set(txt)
        except Exception:
            pass

    def _copy_key(self):
        k = self.generated_key_var.get().strip()
        if k:
            self.clipboard_clear()
            self.clipboard_append(k)
            messagebox.showinfo("Copied", f"Key copied to clipboard:\n\n{k}\n\nYou can paste and send it directly to your customer on Telegram!")

    def _generate_key_action(self):
        plan_choice = self.plan_var.get()
        hwid = self.hwid_var.get().strip()

        if "Lifetime" in plan_choice:
            plan_code = "LIFETIME"
            days = 99999
        elif "365" in plan_choice:
            plan_code = "365D"
            days = 365
        elif "180" in plan_choice:
            plan_code = "180D"
            days = 180
        elif "90" in plan_choice:
            plan_code = "90D"
            days = 90
        elif "30" in plan_choice:
            plan_code = "30D"
            days = 30
        else:
            try:
                days = int(self.custom_days_var.get().strip())
                plan_code = f"{days}D"
            except Exception:
                messagebox.showerror("Error", "Invalid custom days number!")
                return

        key = generate_license_key(plan_type=plan_code, hwid=hwid if hwid else "GLOBAL", days=days)
        self.generated_key_var.set(key)

        # Save to local log
        log_entry = {
            "key": key,
            "plan": plan_code,
            "hwid": hwid or "GLOBAL",
            "time": datetime.now().strftime("%Y-%m-%d %I:%M %p")
        }
        self.history_list.insert(0, log_entry)
        self._save_key_history()
        self._render_history_ui()

        try:
            log_path = get_app_data_path("generated_keys_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{log_entry['time']}] Key: {key} | Plan: {plan_code} | HWID: {log_entry['hwid']}\n")
        except Exception:
            pass

    def _render_history_ui(self):
        for w in self.hist_scroll.winfo_children():
            w.destroy()

        if not self.history_list:
            ctk.CTkLabel(self.hist_scroll, text="No keys generated yet.", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=SKD_THEME["text_muted"]).pack(pady=20)
            return

        for item in self.history_list[:30]:
            card = ctk.CTkFrame(self.hist_scroll, fg_color=SKD_THEME["card_bg"], corner_radius=6, border_width=1, border_color=SKD_THEME["card_border"])
            card.pack(fill="x", pady=2)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(card, text="🔑", font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=6)
            
            k_txt = f"{item['key']}   [{item['plan']}]"
            ctk.CTkLabel(card, text=k_txt, font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color="#FFFFFF", anchor="w").grid(row=0, column=1, sticky="w", padx=4)
            
            sub = f"HWID: {item['hwid']}  |  {item['time']}"
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(family=FONT_FAMILY, size=9), text_color=SKD_THEME["text_muted"], anchor="w").grid(row=1, column=1, sticky="w", padx=4, pady=(0, 4))

            ctk.CTkButton(
                card, text="Copy", width=50, height=22, font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                command=lambda k=item['key']: self._copy_specific_key(k)
            ).grid(row=0, column=2, rowspan=2, padx=6)

    def _copy_specific_key(self, k: str):
        self.clipboard_clear()
        self.clipboard_append(k)
        messagebox.showinfo("Copied", f"Copied to clipboard:\n{k}")

    def _export_keys_txt(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if p:
            lines = [f"Key: {i['key']} | Plan: {i['plan']} | HWID: {i['hwid']} | Created: {i['time']}" for i in self.history_list]
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            messagebox.showinfo("Success", f"Keys exported to:\n{p}")

    def _load_key_history(self):
        try:
            hist_path = get_app_data_path("admin_key_history.json")
            if os.path.exists(hist_path):
                with open(hist_path, "r", encoding="utf-8") as f:
                    self.history_list = json.load(f)
        except Exception:
            self.history_list = []

    def _save_key_history(self):
        try:
            hist_path = get_app_data_path("admin_key_history.json")
            with open(hist_path, "w", encoding="utf-8") as f:
                json.dump(self.history_list, f, indent=2)
        except Exception:
            pass


if __name__ == "__main__":
    app = AdminKeyGeneratorApp()
    app.mainloop()
