# ⚡ SKD TOOL - Ultimate Media Downloader & Studio v1.1.1 (Standalone .exe & Installer Edition)

កម្មវិធី Download Tool ជំនាន់ថ្មីកម្រិត VIP របស់ **SKD TOOL v1.1.1** ដែលភ្ជាប់មកជាមួយ **Standalone Windows .exe (មិនចាំបាច់មាន Python)**, **7 Workspaces ពេញលេញ (Instant Downloader, Download Queue, Batch & Playlist, Video Converter & Studio, Scheduler & Automation, Media Vault, System Settings)**, **Admin Real-Time Cloud Activity Sync (Google Sheets / Database 1-2s)**, **ប្រព័ន្ធប្តូរភាសាពេញលេញ (ភាសាខ្មែរ 🇰🇭 / English 🇺🇸)**, **In-App Media Player ចាក់វីដេអូ & ស្តាប់ភ្លេងផ្ទាល់ក្នុង Tool**, **Video to GIF Maker**, **Audio Volume Booster (150%, 200%, 300%)**, **TikTok Photos Carousel Downloader**, **HD Cover/Thumbnail Downloader**, **Universal License Auto-Sync (Never loses license on updates)**, ព្រមទាំង **ប្រព័ន្ធការពារ License Key & HWID Machine Locking** ពេញលេញ។

---

## 🌟 មុខងារពិសេសៗក្នុងជំនាន់ v1.1.1 (What's New in v1.1.1)

1. **📊 Admin Real-Time Tracking (Google Sheets / Database):** កត់ត្រាាល់រាល់សកម្មភាព Download របស់ User ចូល Google Sheet ភ្លាមៗ (១-២ វិនាទី) ដោយស្វ័យប្រវត្តិ។
2. **⚡ Automated Google Sheets Headers & Setup:** បង្កើតក្បាលតារាង (Headers) ស្វ័យប្រវត្តិតាមរយៈ Google Apps Script Webhook មិនបាច់រៀបចំ Columns មុនឡើយ។
3. **🧪 One-Click Google Sheets Webhook Tester:** មានប៊ូតុងតេស្តតំណភ្ជាប់ Webhook ផ្ទាល់ចេញពី Settings។
4. **🎨 Redesigned 5.0s Cinematic Splash:** ផ្ទាំង Splash Card Glassmorphism ស្អាតបាត Logo ធំច្បាស់ និង Progress រលូន។
5. **🎯 Unified Action Buttons:** រៀបចំប៊ូតុងសកម្មភាព (Add to Queue) ចូលក្នុងកាត Preview យ៉ាងស្អាតបាត។
6. **⚡ 7 Complete Workspaces:** បន្ថែមផ្ទាំងគ្រប់គ្រងពេញលេញទាំង ៧ (ទាញយកភ្លាមៗ, តម្រង់ជួរ Batch Queue, Playlist Extractor, Video Converter, កំណត់ម៉ោងទាញយក & បិទកុំព្យូទ័រ Scheduler, ឃ្លាំងផ្ទុក Media Vault, ការកំណត់ Settings)។
7. **🎬 Studio Converter & Volume Booster:** បំលែងវីដេអូទៅជា MP4/MKV/WebM/GIF និងកាត់សំឡេង MP3 320k Studio រួមទាំង Boost សំឡេងដល់ 300%។
8. **🛡️ YouTube Anti-Bot & Throttling Bypass:** បន្ថែមប្រព័ន្ធបង្វិល Client (iOS/Android/mWeb) ការពារ Error 403 និងទាញយកល្បឿនអតិបរមា។
9. **⭐ Auto-Detect Best Resolution:** ស្វ័យប្រវត្តិចាប់យកកម្រិតច្បាស់បំផុត (4K UHD / 1080p 60fps) ភ្លាមៗពេល Paste Link។
10. **🎬 TikTok 1080p Original No-Watermark:** ទាញយកកម្រិត HD Original ភ្លឺច្បាស់ 100% គ្មានជាប់ Logo។
11. **🛡️ Zero-Error Remux Shield:** FFmpeg 7.1 Lossless Remux ធានាការ Merge Stream បានជោគជ័យឥតខ្ចោះ។
12. **🚀 Facebook & Instagram Ultra HD:** ចាប់យក Stream កម្រិតច្បាស់ HD មុនគេជានិច្ច។
13. **⚡ Micro-Patch Turbo 2.4 MB:** Update លឿនត្រឹម 0.2 វិនាទី មិនគាំងកុំព្យូទ័រ។

---

## 📦 របៀបបង្កើតកម្មវិធីជា Standalone Executable (.exe) & Installer

### វិធីទី ១ (1-Click Build Script)៖
- ចុច Double-Click លើ **[BUILD_STANDALONE_EXE.bat](BUILD_STANDALONE_EXE.bat)**
- ប្រព័ន្ធនឹង Compile កូដទាំងអស់ទៅជា **dist\SKD_TOOL.exe** ដោយស្វ័យប្រវត្តិ។
- File .exe នេះអាច Copy ទៅដាក់លើកុំព្យូទ័រ Windows ផ្សេងៗបានភ្លាមៗ ដោយមិនបាច់ដំឡើង Python ឬ pip ឡើយ!

### វិធីទី ២ (Compile ទាំង Main App និង Admin Key Generator)៖
- រត់ script **scripts\BUILD_ALL_EXECUTABLES.bat**
- ទទួលបានទាំង៖
  1. dist\SKD_TOOL.exe (កម្មវិធីសម្រាប់អតិថិជន)
  2. dist\ADMIN_KEY_GENERATOR.exe (កម្មវិធីសម្រាប់ Admin បង្កើត Key)

### វិធីទី ៣ (បង្កើត Installer Wizard Setup .exe តាម Inno Setup)៖
- ដំឡើងកម្មវិធី [Inno Setup 6](https://jrsoftware.org/isinfo.php)
- បើក file **[installer_setup.iss](installer_setup.iss)** រួចចុច Compile (Ctrl + F9)
- នឹងទទួលបាន Setup Installer ឈ្មោះ SKD_TOOL_Setup_v1.1.1.exe នៅក្នុង folder installer_output/ សម្រាប់ផ្ញើឲ្យគេដំឡើង (Install) មាន icon លើ Desktop និង Start Menu!

---

## 🛠️ របៀប Admin បង្កើត Key ជូនអតិថិជន (Admin Key Generator)

នៅពេលអតិថិជន Chat មកទិញ/សុំ Key តាម Telegram (@SKD_ADMIN) និងផ្ញើលេខ **Machine HWID** របស់គេមក៖

### វិធីទី ១ (ងាយស្រួលបំផុត - 1-Click GUI)៖
ចុច **Double-Click លើ file ADMIN_GENERATE_KEY.bat** (ឬរត់ dist\ADMIN_KEY_GENERATOR.exe ឬ python admin_gui.py)
1. **Paste HWID** របស់អតិថិជនចូល (ឬទុកទទេដើម្បីបង្កើត Key ប្រើបានគ្រប់កុំព្យូទ័រ)
2. **ជ្រើសរើស Plan** (30 ថ្ងៃ, 90 ថ្ងៃ, 180 ថ្ងៃ, 1 ឆ្នាំ, ឬ Lifetime VIP)
3. ចុច **⚡ GENERATE LICENSE KEY NOW**
4. ចុច **📋 Copy Key** រួចផ្ញើទៅឲ្យអតិថិជនតាម Telegram ជាការស្រេច!

---

## 🚀 របៀបអតិថិជនបើកដំណើរការកម្មវិធី SKD TOOL

1. បើកកម្មវិធី **dist\SKD_TOOL.exe**
2. ប្រសិនបើទើបបើកដំបូង កម្មវិធីនឹងបង្ហាញផ្ទាំង **VIP License Activation Dialog**
3. អតិថិជនគ្រាន់តែ **Copy Machine HWID** ផ្ញើមក Admin រួចយក Key ដែល Admin ផ្តល់ឲ្យមក Paste ចូល រួចចុច **⚡ Activate License Key**
4. កម្មវិធីនឹង Verify Cryptographic Digital Signature និងអនុញ្ញាតឲ្យប្រើប្រាស់មុខងារ VIP ទាំងអស់ភ្លាមៗ!
