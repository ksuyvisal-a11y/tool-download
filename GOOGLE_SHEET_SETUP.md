# ការណែនាំអំពីការតភ្ជាប់ Google Sheets / Cloud Database សម្រាប់ Admin 📊

មុខងារ **Admin Real-Time Sync (Google Sheets)** អនុញ្ញាតឱ្យ Admin អាចដឹង និងកត់ត្រាាល់រាល់សកម្មភាពទាញយក (Download) របស់ User ចូលទៅក្នុងតារាង **Google Sheet** ដោយស្វ័យប្រវត្តិក្នុងរយៈពេល **១ ទៅ ២ វិនាទី** បន្ទាប់ពី Download ចប់។

---

### 📋 ទិន្នន័យដែលនឹងរត់ចូល Google Sheet ដោយស្វ័យប្រវត្តិ៖
1. **Timestamp**៖ ថ្ងៃខែ និងម៉ោងជាក់លាក់ (ឧទាហរណ៍៖ `2026-09-11 12:05:00 PM`)
2. **Device / License**៖ ឈ្មោះកុំព្យូទ័រ User + លេខកូដ License VIP
3. **Platform**៖ វេទិកា (YouTube, TikTok, Facebook, Instagram, Threads, Bilibili...)
4. **Video Title**៖ ចំណងជើងវីដេអូ ឬឯកសារ
5. **URL**៖ Link វីដេអូដែល User បាន Download
6. **Quality**៖ កម្រិតគុណភាព (1080p, 4K, MP3 320kbps, etc.)
7. **File Size**៖ ទំហំមេកា (MB / GB)
8. **Status**៖ ស្ថានភាព (`Completed`)

---

## 🚀 ជំហានតម្លើងងាយៗ ៣ នាទី (Step-by-Step Guide)

### ជំហានទី ១៖ បង្កើត Google Sheet ថ្មី
1. បើក Browser រួចចូលទៅកាន់គេហទំព័រ [sheets.new](https://sheets.new) ដើម្បីបង្កើត Google Sheet ថ្មីមួយ។
2. ដាក់ឈ្មោះតារាងរបស់អ្នក ឧទាហរណ៍៖ `SKD Tool - User Download Activity` (មិនបាច់វាយចំណងជើងជួរឈរក៏បាន កូដនឹងបង្កើតក្បាលតារាងដោយស្វ័យប្រវត្តិ)។

---

### ជំហានទី ២៖ បើកផ្ទាំង Apps Script
1. នៅលើ Menu ខាងលើនៃ Google Sheet ចុចលើពាក្យ **Extensions** (ផ្នែកបន្ថែម) ➔ រួចជ្រើសរើស **Apps Script**។
2. លុបកូដចាស់ៗទាំងអស់ដែលមានក្នុងផ្ទាំង Apps Script ចោល។

---

### ជំហានទី ៣៖ Paste កូដខាងក្រោមនេះចូល

ចម្លងកូដ Google Apps Script នេះទាំងស្រុង រួច Paste ចូលក្នុង Apps Script៖

```javascript
// =========================================================================
// GOOGLE APPS SCRIPT WEBHOOK FOR SKD TOOL TELEMETRY
// Real-time user download logging (1-2s sync)
// =========================================================================

function doPost(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();

    // បង្កើតក្បាលតារាងស្វ័យប្រវត្តិ ប្រសិនបើតារាងនៅទទេ
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "Timestamp (កាលបរិច្ឆេទ)",
        "Device / License (ម៉ាស៊ីន/កូដ)",
        "Platform (វេទិកា)",
        "Video Title (ចំណងជើង)",
        "URL (តំណភ្ជាប់)",
        "Quality (កម្រិត)",
        "File Size (ទំហំ)",
        "Status (ស្ថានភាព)"
      ]);
      
      // រៀបចំ Style លើក្បាលតារាងឱ្យស្អាត (Dark Theme Header)
      var headerRange = sheet.getRange(1, 1, 1, 8);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#0f172a");
      headerRange.setFontColor("#38bdf8");
      sheet.setFrozenRows(1);
    }

    var data = {};
    if (e.postData && e.postData.contents) {
      try {
        data = JSON.parse(e.postData.contents);
      } catch (err) {
        data = e.parameter || {};
      }
    } else {
      data = e.parameter || {};
    }

    // បន្ថែមទិន្នន័យ Download ថ្មីចូលជួរដេកបន្ទាប់
    sheet.appendRow([
      data.timestamp || Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss"),
      data.device || "Unknown Device",
      data.platform || "Universal",
      data.title || "Media File",
      data.url || "",
      data.quality || "Default",
      data.size || "Unknown",
      data.status || "Completed"
    ]);

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      message: "Data logged successfully"
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
```

---

### ជំហានទី ៤៖ Deploy ជា Web App (សំខាន់បំផុត!)
1. នៅជ្រុងខាងលើស្ដាំ ចុចលើប៊ូតុងពណ៌ខៀវ **Deploy** ➔ ជ្រើសរើស **New deployment**។
2. ចុចលើរូបកង់ Settings ⚙️ (នៅជិត Select type) ➔ ជ្រើសរើសយក **Web app**។
3. បំពេញព័ត៌មានដូចខាងក្រោម៖
   - **Description**: `SKD Tool Webhook`
   - **Execute as**: `Me (your-email@gmail.com)`
   - **Who has access**: **`Anyone`** ⚠️ *(សំខាន់ខ្លាំង៖ ត្រូវតែជ្រើសរើស Anyone ដើម្បីឱ្យ Tool អាចបញ្ជូនទិន្នន័យចូលបាន)*
4. ចុចប៊ូតុង **Deploy**។
5. ប្រសិនបើមានផ្ទាំង Authorize Access លោតមក៖
   - ចុចលើ **Authorize access** ➔ ជ្រើសរើសគណនី Gmail របស់អ្នក
   - ចុចលើពាក្យ **Advanced** (កម្រិតខ្ពស់) នៅជ្រុងខាងក្រោមឆ្វេង
   - ចុចលើពាក្យ **Go to Untitled project (unsafe)**
   - ចុចលើពាក្យ **Allow** (អនុញ្ញាត)
6. Google នឹងបង្ហាញ **Web app URL** (មានទម្រង់៖ `https://script.google.com/macros/s/.../exec`)។ សូមចុច **Copy** យក URL នោះ!

---

### ជំហានទី ៥៖ Paste ចូលក្នុង SKD Tool
1. បើកកម្មវិធី **SKD Tool** ➔ ចូលទៅកាន់ផ្ទាំង **Settings (ការកំណត់)**។
2. នៅត្រង់ផ្នែក **Admin Real-Time Sync (Google Sheets / Database)**៖
   - Paste តំណភ្ជាប់ Web app URL ចូលក្នុងប្រអប់
3. ចុចប៊ូតុង **តេស្តភ្ជាប់ (Test)** ⚡
   - កម្មវិធីនឹងធ្វើការបញ្ជូនទិន្នន័យសាកល្បងភ្លាមៗក្នុងរយៈពេល **១ វិនាទី**
   - លោកអ្នកអាចត្រឡប់ទៅមើលផ្ទាំង Google Sheet នោះ នឹងឃើញជួរដេកតេស្តពណ៌បៃតងរត់ចូលភ្លាមៗ!
4. ចុច **Save Settings** ជាការស្រេច។

---

### ⚡ លក្ខណៈពិសេសនៃប្រព័ន្ធ៖
- **ដំណើរការល្បឿនលឿន (1-2s)**៖ ប្រើប្រាស់ Detached Asynchronous Thread មិនធ្វើឱ្យកុំព្យូទ័រ User គាំង ឬធ្លាក់ល្បឿន Download ឡើយ។
- **សុវត្ថិភាពខ្ពស់ (Fail-Safe)**៖ ទោះបីជាគ្មានអ៊ីនធឺណិត ឬ Google Apps Script មានបញ្ហា កម្មវិធីនៅតែបន្ត Download ធម្មតា ដោយមិនបង្ហាញ Error រំខាន User ឡើយ។
- **Auto Headers**៖ មិនចាំបាច់រៀបចំ Column ក្នុង Google Sheet មុនឡើយ ប្រព័ន្ធនឹងបង្កើត Header ស្វ័យប្រវត្តិនៅពេលទិន្នន័យរត់ចូលលើកដំបូង។
