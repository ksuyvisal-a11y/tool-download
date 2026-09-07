# 🚀 ការណែនាំអំពីការដាក់ឱ្យដំណើរការ Cloud API Server ដោយឥតគិតថ្លៃ ១០០% (Free Cloud Deployment Guide)

ឯកសារនេះបង្ហាញពីរបៀបដាក់ឱ្យដំណើរការ **SKD Cloud Zero-Trust API Server** នៅលើ Cloud ដោយ **មិនអស់លុយសូម្បីតែ ១ រៀល (Free Tier 100%)** មិនបាច់ដាក់កាតធនាគារ (No Credit Card Required)។

---

## 🌟 ជម្រើសទី ១៖ Deploy លើ Render.com (ងាយស្រួលបំផុត & Free ២៤/៧)

1. បង្កើតគណនី Free នៅលើ [https://render.com](https://render.com) (ចុះឈ្មោះដោយប្រើ GitHub ឬ Google)។
2. បង្កើត GitHub Repository ថ្មីមួយ រួច Upload Folder `server` នេះឡើង។
3. នៅលើផ្ទាំង Dashboard របស់ Render៖
   - ចុចលើប៊ូតុង **"New +"** -> ជ្រើសរើស **"Web Service"**
   - ភ្ជាប់ (Connect) ជាមួយ GitHub Repository របស់អ្នក
   - កំណត់ការ Settings៖
     - **Name**: `skd-cloud-api`
     - **Region**: `Singapore` (សម្រាប់ល្បឿនលឿនបំផុតមកកម្ពុជា)
     - **Branch**: `main`
     - **Root Directory**: `server`
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
     - **Instance Type**: ជ្រើសរើស **"Free" ($0/month)**
4. ចុច **"Create Web Service"** រួចរង់ចាំប្រហែល ១ ទៅ ២ នាទី។
5. អ្នកនឹងទទួលបាន Link HTTPS មួយ (ឧទាហរណ៍៖ `https://skd-cloud-api.onrender.com`)។

---

## 🌟 ជម្រើសទី ២៖ Deploy លើ Koyeb.com (Free & ល្បឿនលឿន)

1. ចុះឈ្មោះគណនី Free នៅ [https://www.koyeb.com](https://www.koyeb.com)
2. ចុច **"Create Service"** -> ជ្រើសរើស **"GitHub"**
3. ជ្រើសរើស Folder `server`
4. Koyeb នឹងចាប់យក `Dockerfile` ដោយស្វ័យប្រវត្តិ ហើយ Deploy Free ២៤/៧។

---

## 🌟 ជម្រើសទី ៣៖ Run Local នៅលើកុំព្យូទ័រខ្លួនឯង (Localhost)

ប្រសិនបើអ្នកចង់តេស្តនៅលើកុំព្យូទ័រផ្ទាល់ខ្លួន៖
1. Double-click លើ File `RUN_CLOUD_SERVER.bat` ក្នុង Folder `server`
2. Server នឹងដំណើរការលើ `http://127.0.0.1:8000` ភ្លាមៗ!
