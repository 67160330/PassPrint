# 🖨️ PassPrint Engine v4.0 (SME Print Optimizer)

ระบบวิเคราะห์ เพิ่มความละเอียดไฟล์พิมพ์ และจัดการผู้ใช้สำหรับธุรกิจ SME และร้านพิมพ์ออนไลน์ ด้วยเทคโนโลยี **Computer Vision** และ **Image Processing** ช่วยตรวจเช็กสเปกไฟล์เบื้องต้น (Pre-flight Analysis), ขยายความละเอียดภาพ 400% (4x Upscaling), เกลี่ย Noise, ปรับโทนสีสำหรับงานพิมพ์ และแปลงเป็นไฟล์ PDF ความละเอียด 300 DPI ที่พร้อมส่งโรงพิมพ์ได้ทันที

---

## 🌐 ระบบบริการและเอกสาร API (Application Links)

- **Web Application:** `http://localhost:8000`
- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **ReDoc API Documentation:** `http://localhost:8000/redoc`
- **Database Management (pgAdmin 4):** `http://localhost:8080` (User: `admin@admin.com` / Pass: `admin`)
- **สไลด์นำเสนอ:** `[https://canva.link/7btqbrr35zko3px](https://canva.link/7btqbrr35zko3px)`

---

## ✨ ฟีเจอร์หลัก (Key Features)

- 🔑 **Authentication & User Management:** ระบบสมัครสมาชิก, เข้าสู่ระบบ, เปลี่ยนรหัสผ่าน และดูโปรไฟล์ผู้ใช้ผ่าน JWT Token
- 📋 **Auto Pre-flight Analysis:** สแกนตรวจสอบมิติพิกเซล ประเมินความหนาแน่น DPI และโหมดสีของภาพเริ่มต้นอัตโนมัติก่อนส่งพิมพ์
- 🎨 **Smart Image Upscaling & Denoising:** 
  - ลดเม็ดบีบอัด/Noise ด้วย **Bilateral Filter**
  - ขยายข้อมูลภาพ 4 เท่าด้วย **INTER_LANCZOS4 Interpolation**
  - ปรับความสดและมิติสีบนระบบ **HSV Color Space**
  - ดึงขอบภาพให้คมนุ่มนวลด้วย **Unsharp Masking (Soft Sharpening)**
- 🖼️ **Interactive Before/After Slider:** เปรียบเทียบความแตกต่างระหว่างภาพต้นฉบับกับภาพที่ซ่อมแซมแล้วแบบเรียลไทม์
- 📄 **Print-Ready PDF Export:** แปลงภาพเป็นไฟล์ PDF ความละเอียดสูง (300 DPI Target) พร้อมส่งเข้าเครื่องพิมพ์
- 📂 **Cloud History Management:** เรียกดูรายการประวัติไฟล์ภาพ/PDF ที่ซ่อมแซมแล้วย้อนหลัง และจัดการลบประวัติแบบเลือกรายการหรือลบทั้งหมดได้

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, FastAPI (v4.0.0), PostgreSQL, SQLAlchemy, OpenCV (`opencv-python-headless`), Pillow (PIL), NumPy, Uvicorn, Python-dotenv
- **Frontend:** HTML5, Tailwind CSS (via CDN), JavaScript (Vanilla ES6)
- **Database & Tooling:** PostgreSQL 15, pgAdmin 4
- **Containerization:** Docker, Docker Compose

---

## 🚀 วิธีการติดตั้งและรันใช้งาน (Getting Started)

### การเตรียมความพร้อมเรื่อง Environment Variables
ก่อนสั่งรันระบบ ให้คัดลอกไฟล์ `.env.example` เป็น `.env` และกำหนดค่าต่าง ๆ :
```bash
cp .env.example .env
```

---

### ออปชันที่ 1: รันด้วย Docker Compose (แนะนำ)

```bash
docker-compose up --build
```
ระบบจะทำการ Build และรัน Container ของ Web Application (FastAPI), Database Service (PostgreSQL) และ pgAdmin พร้อมเปิดให้บริการอัตโนมัติ

---

### ออปชันที่ 2: รันด้วย Python โดยตรง

1. **ติดตั้ง Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **สั่งรันเซิร์ฟเวอร์ Backend:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **เปิดใช้งานหน้าเว็บ:**
   เปิดเบราว์เซอร์ไปที่ `http://localhost:8000`

---

## 📡 REST API Documentation Overview

### 1. Pre-flight Analysis (สแกนวิเคราะห์ภาพ)
* **Endpoint:** `POST /analyze`
* **Content-Type:** `multipart/form-data`
* **Response Example (200 OK):**
  ```json
  {
    "status": "success",
    "issues": [
      "📸 ตรวจพบไฟล์ JPEG/JPG: กำหนดใช้ Photo Denoise Pipeline",
      "🔴 มิติภาพเริ่มต้น (600 x 450 px) เสี่ยงต่อการแตกเมื่อพิมพ์จริง"
    ]
  }
  ```

---

### 2. Heal & Upscale Image (ซ่อมแซมภาพ & สร้าง PDF 300 DPI)
* **Endpoint:** `POST /heal` (หรือ `POST /process`)
* **Content-Type:** `multipart/form-data`
* **Response Example (200 OK):**
  ```json
  {
    "status": "success",
    "message": "repaired and upscaled successfully",
    "preview_url": "/fixed_files/healed_a1b2c3d4.png",
    "pdf_url": "/fixed_files/print_ready_a1b2c3d4.pdf",
    "original_resolution": "600 x 450 px",
    "healed_resolution": "2400 x 1800 px",
    "improvements": [
      "ขยายความรายละเอียด 400% (600x450 px ➔ 2400x1800 px)",
      "เพิ่มความคมชัดของตัวอักษรและลายเส้นขอบภาพ",
      "คงค่าสีและโทนสีเดิมของไฟล์ต้นฉบับไว้ 100%",
      "ฝังโปรไฟล์สีมาตรฐานสำหรับโรงพิมพ์ (300 DPI Ready)"
    ]
  }
  ```

---

### 3. Authentication & User Profile
* **POST `/register`** - สมัครสมาชิกใหม่
* **POST `/login`** - เข้าสู่ระบบและรับ Access Token
* **POST `/change-password`** - เปลี่ยนรหัสผ่าน (Requires Auth Token)
* **GET `/me`** - ดึงข้อมูลโปรไฟล์ผู้ใช้ปัจจุบัน (Requires Auth Token)

---

### 4. Image History Management
* **GET `/history`** - ดึงรายการประวัติภาพและ PDF ทั้งหมดของผู้ใช้ปัจจุบัน
* **DELETE `/history/{history_id}`** - ลบประวัติการซ่อมแซมภาพรายรายการตาม ID
* **DELETE `/history`** - ลบประวัติการซ่อมแซมภาพทั้งหมดของผู้ใช้ปัจจุบัน

---

## 📂 โครงสร้างโฟลเดอร์โปรเจกต์ (Project Structure)

```text
.
├── fixed_files/          # โฟลเดอร์จัดเก็บไฟล์ภาพ PNG และ PDF ที่ประมวลผลแล้ว
├── .env                  # ไฟล์เก็บ Environment Variables & Secret Keys (Ignored on Git)
├── .env.example          # ไฟล์ตัวอย่าง Environment Variables
├── .gitignore            # กำหนดไฟล์ที่ไม่ต้องส่งขึ้น Git
├── config.py             # โค้ดสำหรับอ่านและจัดการค่า Configuration ของระบบ
├── Dockerfile            # คอนฟิกการสร้าง Docker Image
├── docker-compose.yml    # คอนฟิกการรันบริการ Docker (FastAPI Web + PostgreSQL DB + pgAdmin)
├── index.html            # โค้ด Frontend Single Page Application
├── main.py               # โค้ด Backend API Engine หลัก (FastAPI v4.0.0)
├── requirements.txt      # รายชื่อไลบรารี Python Dependencies
└── README.md             # เอกสารอธิบายรายละเอียดโปรเจกต์
```
