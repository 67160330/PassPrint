# 🖨️ PassPrint AI - Engine v3.0 (SME Print Optimizer)

ระบบวิเคราะห์ เพิ่มความละเอียดไฟล์พิมพ์ และจัดการผู้ใช้สำหรับธุรกิจ SME และร้านพิมพ์ออนไลน์ ด้วย AI และ Computer Vision ช่วยตรวจเช็กสเปกไฟล์เบื้องต้น (Pre-flight Analysis), ขยายความละเอียดภาพ 400% (4x Upscaling), เกลี่ย Noise และแปลงเป็นไฟล์ PDF ความละเอียด 300 DPI ที่พร้อมส่งโรงพิมพ์ได้ทันที

---

## 🌐 ระบบบริการและเอกสาร API (Application Links)

- **Web Application:** `http://localhost:8000`
- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **ReDoc API Documentation:** `http://localhost:8000/redoc`

---

## ✨ ฟีเจอร์หลัก (Key Features)

- 🔑 **Authentication & User Management:** ระบบสมัครสมาชิก, เข้าสู่ระบบ, เปลี่ยนรหัสผ่าน, ดูโปรไฟล์ และจัดการสิทธิ์ผู้ใช้ (CRUD Users)
- 📋 **Auto Pre-flight Analysis:** สแกนตรวจสอบมิติพิกเซล ประเมินความหนาแน่น DPI และโหมดสีของภาพเริ่มต้นอัตโนมัติก่อนส่งพิมพ์
- 🎨 **Smart AI Upscaling & Denoising:** 
  - ลดเม็ดบีบอัด/Noise ด้วย **Bilateral Filter**
  - ขยายข้อมูลภาพ 4 เท่าด้วย **INTER_LANCZOS4 Interpolation**
  - ปรับความสดและมิติสีบนระบบ **HSV Color Space**
  - ดึงขอบภาพให้คมนุ่มนวลด้วย **Unsharp Masking (Soft Sharpening)**
- 🖼️ **Interactive Before/After Slider:** เปรียบเทียบความแตกต่างระหว่างภาพต้นฉบับกับภาพที่ซ่อมแซมแล้วแบบเรียลไทม์
- 📄 **Print-Ready PDF Export:** แปลงภาพเป็นไฟล์ PDF ความละเอียดสูง (300 DPI Target) พร้อมส่งเข้าเครื่องพิมพ์
- 📂 **Cloud History Management:** เรียกดูรายการไฟล์ภาพ/PDF ที่ซ่อมแซมแล้วย้อนหลัง และจัดการลบไฟล์จากเซิร์ฟเวอร์ได้

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, FastAPI (v3.0.0), PostgreSQL, SQLAlchemy, OpenCV (`opencv-python-headless`), Pillow (PIL), NumPy, Uvicorn
- **Frontend:** HTML5, Tailwind CSS (via CDN), JavaScript (Vanilla ES6)
- **Containerization:** Docker, Docker Compose

---

## 🚀 วิธีการติดตั้งและรันใช้งาน (Getting Started)

### ออปชันที่ 1: รันด้วย Docker Compose (แนะนำ)

```bash
docker-compose up --build
