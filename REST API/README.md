# 🖨️ PassPrint AI - Single Page Print Fixer

ระบบวิเคราะห์และเพิ่มความละเอียดไฟล์พิมพ์อัตโนมัติด้วย AI และ Computer Vision สำหรับร้านค้าออนไลน์และธุรกิจ SME ช่วยตรวจเช็กสเปกไฟล์ (Pre-flight Analysis) และขยายความละเอียดภาพ 400% โดยไม่ทำให้ภาพแตก พร้อมแปลงเป็นไฟล์ PDF 300 DPI สำหรับส่งโรงพิมพ์ทันที

---

## 🌐 เว็บไซต์และระบบบริการ (Web Application Links)

- **Local Access (เครื่องตนเอง):** `http://localhost:8000`
- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **ReDoc API Documentation:** `http://localhost:8000/redoc`

---

## 🌍 วิธีเปิดให้คนอื่น / อาจารย์ เข้าใช้งานหน้าเว็บได้ (Public Access)

หากต้องการส่งลิงก์ให้คนอื่นทดลองใช้งาน สามารถเลือกทำได้ 2 วิธีง่ายๆ ดังนี้:

### วิธีที่ 1: สร้างลิงก์สาธารณะด้วย ngrok (แนะนำ - ง่ายที่สุด)
เปิดให้คนอื่นเข้าใช้งานผ่านอินเทอร์เน็ตได้ทันทีจากเครื่องของคุณเอง:
1. สั่งรันเซิร์ฟเวอร์ Backend ด้วยคำสั่ง:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. เปิด Terminal อีกหน้าต่าง แล้วพิมพ์คำสั่ง ngrok:
   ```bash
   ngrok http 8000
   ```
3. ก๊อปปี้ลิงก์ `Forwarding` (เช่น `https://xxxx.ngrok-free.app`) ส่งให้ผู้อื่นเปิดใช้งานได้ทันที

### วิธีที่ 2: เปิดให้เข้าใช้งานในวง Wi-Fi เดียวกัน (Local Network)
1. รันเซิร์ฟเวอร์ด้วยคำสั่ง:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. เช็ก IP เครื่องของคุณ (เช่น `192.168.1.50`)
3. เครื่องอื่นที่ต่อ Wi-Fi เดียวกันสามารถเข้าผ่าน: `http://192.168.1.50:8000`

---

## ✨ ฟีเจอร์หลัก (Key Features)

- 📥 **Image Upload & Management:** อัปโหลดและเปลี่ยนรูปภาพได้ง่าย
- 📋 **Pre-flight Analysis:** สแกนตรวจสอบมิติพิกเซล ประเมินความหนาแน่น DPI และระบบสีของไฟล์เริ่มต้น
- 🎨 **Smart Upscaling & Denoising:** 
  - ลบเม็ดสเปกตรัม/Noise ด้วย **Bilateral Filter**
  - ขยายข้อมูลภาพ 4 เท่าด้วย **INTER_CUBIC Interpolation**
  - ดึงขอบภาพให้ชัดนุ่มนวลด้วย **Soft Sharpening**
- 🖼️ **Interactive Before/After Slider:** เปรียบเทียบความแตกต่างระหว่างภาพต้นฉบับกับภาพที่ซ่อมแซมแล้วแบบเรียลไทม์
- 📄 **Print-Ready PDF Export:** แปลงภาพเป็นไฟล์ PDF ความละเอียดสูง (300 DPI Target) พร้อมส่งโรงพิมพ์

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, OpenCV (`opencv-python-headless`), Pillow (PIL), Uvicorn
- **Frontend:** HTML5, Tailwind CSS (via CDN), JavaScript (Vanilla ES6)
- **Containerization:** Docker, Docker Compose

---

## 🚀 วิธีการติดตั้งและรันใช้งาน (Getting Started)

### ออปชันที่ 1: รันด้วย Python โดยตรง

1. **ติดตั้ง Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **สั่งรันเซิร์ฟเวอร์ Backend:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **เปิดใช้งานหน้าเว็บ:**
   เปิดเบราว์เซอร์ไปที่ `http://127.0.0.1:8000` หรือ `http://localhost:8000`

---

### ออปชันที่ 2: รันด้วย Docker Compose

```bash
docker-compose up --build
```
ระบบจะสร้าง Container และเปิดให้บริการที่พอร์ต `8000` อัตโนมัติ

---

## 📡 REST API Documentation

### 1. Pre-flight Analysis (สแกนวิเคราะห์ภาพ)
วิเคราะห์สเปกไฟล์รูปภาพเบื้องต้นก่อนทำการซ่อมแซม

* **Endpoint:** `POST /analyze`
* **Content-Type:** `multipart/form-data`
* **Body Parameters:**
  * `file`: (UploadFile) ไฟล์รูปภาพที่ต้องการสแกน
* **Response Example (200 OK):**
  ```json
  {
    "status": "success",
    "issues": [
      "🔴 มิติภาพเริ่มต้นค่อนข้างเล็ก (600 x 450 px) เสี่ยงต่อการแตกเมื่อนำไปพิมพ์จริง",
      "🔴 ความหนาแน่นพิกเซลต่ำ (ประมาณ 72-150 DPI) จำเป็นต้องเกลี่ยและเพิ่มข้อมูลภาพ 400%",
      "🟢 โครงสร้างสี RGB สมบูรณ์ พร้อมสำหรับอัลกอริทึมดึงรายละเอียดพิกเซล"
    ]
  }
  ```

---

### 2. Heal & Upscale Image (ประมวลผลเพิ่มความคมชัด)
ลบ Noise/เม็ดแตก, ขยายภาพ 400% และสร้างไฟล์ PDF 300 DPI

* **Endpoint:** `POST /heal` (หรือ `POST /process`)
* **Content-Type:** `multipart/form-data`
* **Body Parameters:**
  * `file`: (UploadFile) ไฟล์รูปภาพที่ต้องการประมวลผล
* **Response Example (200 OK):**
  ```json
  {
    "status": "success",
    "message": "repaired and upscaled successfully",
    "preview_url": "/fixed_files/healed_sample.png",
    "pdf_url": "/fixed_files/print_ready_sample.pdf",
    "original_resolution": "600 x 450 px",
    "healed_resolution": "2400 x 1800 px"
  }
  ```

---

### 3. List Processed Images (เรียกดูรายการไฟล์ทั้งหมด)
ดึงรายชื่อไฟล์ภาพและ PDF ที่ประมวลผลแล้วในระบบ

* **Endpoint:** `GET /api/v1/images`
* **Response Example (200 OK):**
  ```json
  {
    "status": "success",
    "total_files": 2,
    "files": [
      "/fixed_files/healed_sample.png",
      "/fixed_files/print_ready_sample.pdf"
    ]
  }
  ```

---

### 4. Delete Processed Image (ลบไฟล์ผลลัพธ์)
ลบไฟล์ที่ประมวลผลแล้วออกจากเซิร์ฟเวอร์

* **Endpoint:** `DELETE /api/v1/images/{filename}`
* **Response Example (200 OK):**
  ```json
  {
    "status": "success",
    "message": "Deleted healed_sample.png"
  }
  ```

---

### 5. Get Current User Profile (ดึงข้อมูลผู้ใช้)
แสดงข้อมูลจำลองสิทธิ์การใช้งานระบบ PassPrint AI

* **Endpoint:** `GET /users/me`
* **Response Example (200 OK):**
  ```json
  {
    "user_id": "usr_sme_889",
    "username": "passprint_official",
    "package": "PassPrint Pro",
    "status": "Active"
  }
  ```

---

## 📂 โครงสร้างโฟลเดอร์โปรเจกต์ (Project Structure)

```text
passprint-ai/
├── main.py              # โค้ด Backend API (FastAPI)
├── index.html            # โค้ด Frontend UI
├── requirements.txt      # รายชื่อไลบรารี Python
├── Dockerfile            # คอนฟิกการสร้าง Docker Container
├── docker-compose.yml    # คอนฟิกการรันบริการ Docker
└── README.md             # เอกสารอธิบายโปรเจกต์
```
