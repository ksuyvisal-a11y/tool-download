# ⚡ SKD TOOL - Ultimate Media Downloader v6.5 (Standalone .exe & Installer Edition)

កម្មវិធី Download Tool ជំនាន់ថ្មីកម្រិត VIP របស់ **SKD TOOL** ដែលភ្ជាប់មកជាមួយ **Standalone Windows .exe (មិនចាំបាច់មាន Python)**, **ប្រព័ន្ធការពារ License Key & HWID Machine Locking** ពេញលេញ ព្រមទាំងរចនាបថ **Next-Gen Obsidian Glass & Electric Cyan UI**។

---

## 📦 របៀបបង្កើតកម្មវិធីជា Standalone Executable (.exe) & Installer

### វិធីទី ១ (1-Click Build Script)៖
- ចុច Double-Click លើ **[BUILD_STANDALONE_EXE.bat](file:///d:/Sal/tool%20download/BUILD_STANDALONE_EXE.bat)**
- ប្រព័ន្ធនឹង Compile កូដទាំងអស់ទៅជា **`dist\SKD_TOOL.exe`** ដោយស្វ័យប្រវត្តិ។
- File `.exe` នេះអាច Copy ទៅដាក់លើកុំព្យូទ័រ Windows ផ្សេងៗបានភ្លាមៗ ដោយមិនបាច់ដំឡើង Python ឬ pip ឡើយ!

### វិធីទី ២ (Compile ទាំង Main App និង Admin Key Generator)៖
- ចុច Double-Click លើ **[BUILD_ALL_EXECUTABLES.bat](file:///d:/Sal/tool%20download/BUILD_ALL_EXECUTABLES.bat)**
- ទទួលបានទាំង៖
  1. `dist\SKD_TOOL.exe` (កម្មវិធីសម្រាប់អតិថិជន)
  2. `dist\ADMIN_KEY_GENERATOR.exe` (កម្មវិធីសម្រាប់ Admin បង្កើត Key)

### វិធីទី ៣ (បង្កើត Installer Wizard Setup .exe តាម Inno Setup)៖
- ដំឡើងកម្មវិធី [Inno Setup 6](https://jrsoftware.org/isinfo.php)
- បើក file **[installer_setup.iss](file:///d:/Sal/tool%20download/installer_setup.iss)** រួចចុច `Compile` (Ctrl + F9)
- នឹងទទួលបាន Setup Installer ឈ្មោះ `SKD_Tool_Setup_v6.5.exe` នៅក្នុង folder `installer_output/` សម្រាប់ផ្ញើឲ្យគេដំឡើង (Install) មាន icon លើ Desktop និង Start Menu!

---

## 🛠️ របៀប Admin បង្កើត Key ជូនអតិថិជន (Admin Key Generator)

នៅពេលអតិថិជន Chat មកទិញ/សុំ Key តាម Telegram (`@SKD_ADMIN`) និងផ្ញើលេខ **Machine HWID** របស់គេមក៖

### វិធីទី ១ (ងាយស្រួលបំផុត - 1-Click GUI)៖
ចុច **Double-Click លើ file `ADMIN_GENERATE_KEY.bat`** (ឬរត់ `dist\ADMIN_KEY_GENERATOR.exe` ឬ `python admin_gui.py`)
1. **Paste HWID** របស់អតិថិជនចូល (ឬទុកទទេដើម្បីបង្កើត Key ប្រើបានគ្រប់កុំព្យូទ័រ)
2. **ជ្រើសរើស Plan** (30 ថ្ងៃ, 90 ថ្ងៃ, 180 ថ្ងៃ, 1 ឆ្នាំ, ឬ Lifetime VIP)
3. ចុច **`⚡ GENERATE LICENSE KEY NOW`**
4. ចុច **`📋 Copy Key`** រួចផ្ញើទៅឲ្យអតិថិជនតាម Telegram ជាការស្រេច!

---

## 🚀 របៀបអតិថិជនបើកដំណើរការកម្មវិធី SKD TOOL

1. ចុច **Double-Click លើ file `dist\SKD_TOOL.exe`** (ឬ `run.bat`)
2. ផ្ទាំង **3D SKD Logo Intro (Splash Screen)** នឹងបង្ហាញឡើងកំឡុងពេល ~២ វិនាទី
3. ផ្ទាំង **Activation Lock Screen** នឹងបង្ហាញឡើង៖
   - អតិថិជនចុច `📋 Copy HWID` ផ្ញើទៅ Admin
   - យក Key ដែល Admin ផ្ញើឲ្យមក Paste ចូល រួចចុច **`⚡ ACTIVATE LICENSE`**
4. កម្មវិធីនឹងដោះសោរបើកចូល **SKD TOOL Main Workspace** ភ្លាមៗ!

---

## 📁 រចនាសម្ព័ន្ធកូដ (Project Files)

- [BUILD_STANDALONE_EXE.bat](file:///d:/Sal/tool%20download/BUILD_STANDALONE_EXE.bat) : 1-Click Script បង្កើត Standalone SKD_TOOL.exe
- [BUILD_ADMIN_EXE.bat](file:///d:/Sal/tool%20download/BUILD_ADMIN_EXE.bat) : 1-Click Script បង្កើត ADMIN_KEY_GENERATOR.exe
- [BUILD_ALL_EXECUTABLES.bat](file:///d:/Sal/tool%20download/BUILD_ALL_EXECUTABLES.bat) : 1-Click Script បង្កើតទាំងពីរ
- [installer_setup.iss](file:///d:/Sal/tool%20download/installer_setup.iss) : Inno Setup Script សម្រាប់បង្កើត Windows Installer (.exe Setup Wizard)
- [skd_tool.spec](file:///d:/Sal/tool%20download/skd_tool.spec) : PyInstaller Bundle Configuration
- [app.py](file:///d:/Sal/tool%20download/app.py) : Desktop GUI SKD TOOL ជាមួយ Splash Screen និង Activation Modal
- [admin_gui.py](file:///d:/Sal/tool%20download/admin_gui.py) : Desktop GUI Dashboard សម្រាប់ Admin Generate Key
- [licensing.py](file:///d:/Sal/tool%20download/licensing.py) : Cryptographic HWID & License Key Verification Engine
- [downloader.py](file:///d:/Sal/tool%20download/downloader.py) : Turbo Engine (Bypass 403, Multi-chunk, Cookies, FFmpeg)
- [utils.py](file:///d:/Sal/tool%20download/utils.py) : Path resolution, localization, data storage, helpers
