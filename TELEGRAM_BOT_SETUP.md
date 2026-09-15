# ការណែនាំអំពីការភ្ជាប់ Telegram Bot ជាមួយ SKD TOOL (Download Telemetry)

SKD TOOL គាំទ្រការផ្ញើដំណឹងសកម្មភាពទាញយករបស់ User ទាំងអស់មកកាន់ **Telegram Bot ផ្ទាល់ខ្លួនរបស់ Admin** ដោយស្វ័យប្រវត្តិក្នងពេល Real-time ភ្លាមៗ (ក្រោម ១ វិនាទី)។

---

## ជំហានទី ១: បង្កើត Telegram Bot (យក Bot Token)
1. បើកកម្មវិធី Telegram រួចស្វែងរក **[@BotFather](https://t.me/BotFather)** (មានសញ្ញា Verified ពណ៌ខៀវ)។
2. ចុច **Start** រួចផ្ញើពាក្យបញ្ជា `/newbot`។
3. បញ្ចូលឈ្មោះ Bot របស់អ្នក (ឧទាហរណ៍៖ `SKD Telemetry Bot`)។
4. បញ្ចូល username របស់ Bot ដែលត្រូវបញ្ចប់ដោយពាក្យ `bot` (ឧទាហរណ៍៖ `skd_download_logger_bot`)។
5. **@BotFather** នឹងផ្ញើសារអបអរសាទរជាមួយ **HTTP API Token** (ឧទាហរណ៍៖ `7823456789:AAFxY...`)។ សូម Copy ទុក!

---

## ជំហានទី ២: ស្វែងរក Telegram Chat ID របស់អ្នក
1. ស្វែងរក Bot ឈ្មោះ **[@userinfobot](https://t.me/userinfobot)** នៅលើ Telegram។
2. ចុច **Start**។
3. វានឹងបង្ហាញលេខសម្គាល់របស់អ្នក `Id: 123456789`។ យកលេខនេះធ្វើជា **Chat ID**។
*(ចំណាំ៖ ប្រសិនបើចង់ផ្ញើចូល Channel ឯកជន សូម Add Bot ចូលជា Admin ក្នុង Channel រួចប្រើ `@channel_username` ឬ Channel ID)*។

---

## ជំហានទី ៣: ភ្ជាប់ទៅកាន់ SKD TOOL
1. បើកកម្មវិធី **SKD TOOL**។
2. ចុចលើ Menu **Settings** (រូបធ្មេញកង់) នៅចំហៀងខាងឆ្វេង។
3. នៅផ្ទាំង **Telegram Bot Activity Telemetry**:
   - បញ្ចូល **Telegram Bot Token** ក្នុងប្រអប់ Token។
   - បញ្ចូល **Telegram Chat ID** ក្នុងប្រអប់ Chat ID។
   - ចុចប៊ូតុង **"តេស្ត Bot (Test)"**។
4. អ្នកនឹងទទួលបានសារសាកល្បង **[SKD TOOL] តេស្តភ្ជាប់ជោគជ័យ** លើ Telegram ភ្លាមៗ!
5. ចុច **"Save Settings"** ជាការស្រេច។

---

## ទម្រង់សារដែល Bot នឹងផ្ញើពេល User ទាញយក៖
```text
📥 [SKD TOOL] កំណត់ត្រាទាញយក (Download Alert)
━━━━━━━━━━━━━━━━━━━━━━
👤 អ្នកប្រើប្រាស់/ម៉ាស៊ីន: Visal (DESKTOP-PC) [Lifetime VIP | SKD-2533-59E4]
🌐 វេទិកា (Platform): YouTube
🎬 ចំណងជើង: How to Build Modern Apps
🔗 តំណភ្ជាប់: https://www.youtube.com/watch?v=...
📊 ទំហំ/កម្រិត: 1080p Full HD | 45.2 MB
⏱️ កាលបរិច្ឆេទ: 2026-09-15 01:00:15 PM
⚡ ស្ថានភាព: ✅ Completed
━━━━━━━━━━━━━━━━━━━━━━
```
