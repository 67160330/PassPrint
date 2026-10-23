# 🖨️ PassPrint Studio v4.0 (SME Print Optimizer)

ระบบวิเคราะห์และแต่งรูปภาพสำหรับส่งโรงพิมพ์สำหรับธุรกิจ SME และร้านพิมพ์ออนไลน์ ช่วยวิเคราะห์สเปกไฟล์เบื้องต้น (Pre-flight Analysis), ขยายความละเอียดภาพ 400% (4x Upscaling), ปรับแต่งภาพและลบพื้นหลังด้วยตัวเองผ่าน Canvas Studio (Magic Wand / แปรงยางลบ) และสร้างไฟล์ PDF ความละเอียดสูง 300 DPI ที่รักษามิติพื้นหลังโปร่งใส (PNG Alpha Channel) พร้อมส่งโรงพิมพ์ได้ทันที

---

## 🌐 ระบบบริการและเอกสาร API (Application Links)

- **Web Application:** `http://localhost:8000`
- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **ReDoc API Documentation:** `http://localhost:8000/redoc`

---

## ✨ ฟีเจอร์หลัก (Key Features)

- 🤖 **Mode 1: OpenCV Auto Engine (ใช้งานฟรีไม่จำกัด)**
  - ขยายข้อมูลภาพ 400% ด้วย **INTER_LANCZOS4 Interpolation**
  - ดึงความคมชัดขอบภาพและตัวอักษรด้วย **Unsharp Masking (Soft Sharpening)**
  - ลดเม็ดบีบอัด/Noise ด้วย **Bilateral Filter**
  - ตัวเลือกปรับเร่งมิติสีสดใสด้วย **HSV Color Space**
- 🎨 **Mode 2: Interactive Canvas Studio (โควตาฟรี 7 รอบ/วัน)**
  - **✨ Magic Wand (คลิกดูดลบสีพื้นหลัง):** คลิกเมาส์ลบสีพื้นหลังให้อัตโนมัติด้วยอัลกอริทึม Flood Fill พร้อมสไลเดอร์ปรับค่าความไว (Tolerance)
  - **🧹 แปรงยางลบ (Eraser Brush):** ปรับขนาดหัวแปรงขูดลบส่วนที่ไม่ต้องการออกได้เอง
  - **↺/↻ Undo & Redo System:** ระบบย้อนกลับและทำซ้ำประวัติการแต่งรูป (รองรับคีย์ลัด `Ctrl+Z` / `Ctrl+Y`)
  - **🖼️ Transform & Color Grading:** หมุนภาพ 90°, กลับภาพซ้าย-ขวา/บน-ล่าง และปรับ Brightness / Contrast / Saturation
  - **🔄 Change Image:** ปุ่มเปลี่ยนรูปภาพใหม่เข้าสู่กระดานแต่งรูปได้ทันทีโดยไม่ต้องโหลดหน้าเว็บใหม่
- 🏁 **PNG Transparency & 300 DPI Export:** รองรับการรักษาช่องสีโปร่งใส (4-Channel BGRA Alpha Channel) และส่งออกไฟล์ PDF 300 DPI
- 📜 **Image History & Account Management:** ดูประวัติการแต่งรูปรวมถึงดาวน์โหลดไฟล์ย้อนหลัง (PNG/PDF) และระบบลบบัญชีผู้ใช้พร้อมข้อมูลล้างระบบ

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, FastAPI, PostgreSQL, SQLAlchemy, OpenCV (`opencv-python-headless`), Pillow (PIL), NumPy, Uvicorn, Bcrypt, PyJWT
- **Frontend:** HTML5, Tailwind CSS, JavaScript (Vanilla ES6 Canvas API)
- **Containerization:** Docker, Docker Compose (FastAPI Web + PostgreSQL + pgAdmin)

---

## 🚀 วิธีการติดตั้งและรันใช้งาน (Getting Started)

### รันด้วย Docker Compose (แนะนำ)

```bash
docker-compose up -d --build
```
ระบบจะทำการ Build Container ของทั้ง Web Application (FastAPI), Database Service (PostgreSQL) และ pgAdmin พร้อมเปิดให้บริการที่พอร์ต 8000 อัตโนมัติ📡 REST API Documentation Overview1. Auto Processing & Pre-flight AnalysisPOST /analyze - สแกนวิเคราะห์ขนาดภาพและความหนาแน่น DPIPOST /heal-auto - ขยายภาพ 400% และเพิ่มความคมชัดด้วย OpenCV อัตโนมัติ (ฟรีไม่จำกัด)2. Canvas Processing (หัก 1 Credit)POST /heal (หรือ /process) - ประมวลผลภาพจาก Canvas Studio ขยาย 400% และบันทึกประวัติลงฐานข้อมูล3. Authentication & Account ManagementPOST /register - สมัครสมาชิกใหม่POST /login - เข้าสู่ระบบและรับ Access TokenGET /me - ดึงข้อมูลโปรไฟล์ผู้ใช้ และรีเซ็ตโควตาประจำวัน (7/7)DELETE /account - ลบบัญชีผู้ใช้และประวัติภาพทั้งหมดออกจากฐานข้อมูล4. Image History ManagementGET /history - ดึงรายการประวัติรูปภาพที่เคยประมวลผลของผู้ใช้DELETE /history/{history_id} - ลบรายการประวัติภาพตาม ID🏗️ Architecture DiagramsSystem Architecture WorkflowCode snippetgraph TD
    subgraph Clients ["📱 Client Layer"]
        WebApp["Web Client (HTML5 Canvas + Tailwind)"]
    end

    subgraph Gateway ["🚪 Gateway & Auth Layer"]
        APIGateway["FastAPI Router"]
        AuthSvc["Auth Middleware (JWT / Bcrypt)"]
        CreditSvc["Daily Credit Manager (7 Credits/Day)"]
    end

    subgraph CoreServices ["⚙️ Processing Engines"]
        AutoEngine["OpenCV Auto Engine (4x Upscaling & Sharpening)"]
        CanvasEngine["Canvas Studio Engine (Magic Wand / Eraser / Undo-Redo)"]
        ExportEngine["Export Engine (PNG Transparency / 300 DPI PDF)"]
    end

    subgraph StorageLayer ["💾 Database & Files"]
        MainDB[("🐘 PostgreSQL DB<br/>(Users, History, Credits)")]
        LocalStore[("📁 Fixed Files Storage<br/>(Output PNG / PDF)")]
    end

    WebApp --> APIGateway
    APIGateway --> AuthSvc
    AuthSvc --> CreditSvc

    CreditSvc --> AutoEngine
    CreditSvc --> CanvasEngine

    AutoEngine --> ExportEngine
    CanvasEngine --> ExportEngine

    ExportEngine --> LocalStore
    CreditSvc --> MainDB
Technology Stack DiagramCode snippetgraph LR
    subgraph Layer1 ["💻 Frontend"]
        HTML5["HTML5 / Canvas API"]
        Tailwind["Tailwind CSS"]
        JS["Vanilla JS Engine"]
    end

    subgraph Layer2 ["⚡ Backend Framework"]
        Python["Python 3.12"]
        FastAPI["FastAPI Framework"]
        Uvicorn["Uvicorn Server"]
    end

    subgraph Layer3 ["👁️ Image Processing Engine"]
        OpenCV["OpenCV Headless"]
        Pillow["Pillow (PIL)"]
        NumPy["NumPy"]
    end

    subgraph Layer4 ["🐘 Database & Auth"]
        PostgreSQL["PostgreSQL DB"]
        SQLAlchemy["SQLAlchemy ORM"]
        JWT["PyJWT / Bcrypt"]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer2 --> Layer4
📊 ความคืบหน้าโครงการ (Project Progress)ภาพรวมความคืบหน้าทั้งหมด (Overall Progress): 85%โมดูลงาน (Modules)รายละเอียด (Tasks)สถานะ (Status)ความคืบหน้า (%)1. Environment & Setupคอนฟิก Docker Compose, FastAPI, PostgreSQL และ pgAdmin✅ เสร็จสิ้น100%2. Database & Data Layerออกแบบ Schema ผู้ใช้ (users) และประวัติภาพ (image_histories)✅ เสร็จสิ้น100%3. Security & Accountระบบ JWT Authentication, Bcrypt Hashing และระบบลบบัญชีผู้ใช้ (DELETE /account)✅ เสร็จสิ้น100%4. OpenCV Auto Engineขยายภาพ 400% (INTER_LANCZOS4), Bilateral Filter และ Unsharp Masking✅ เสร็จสิ้น100%5. Interactive Canvas Studioระบบลบสีพื้นหลังเป็น PNG โปร่งใส (Magic Wand Flood-fill), แปรงยางลบ, ปรับแสงสี, เปลี่ยนรูป และ Undo/Redo Stack✅ เสร็จสิ้น100%6. Daily Credit Systemระบบจำกัดโควตาฟรี 7 รอบ/วัน พร้อมรีเซ็ตอัตโนมัติเมื่อเข้าสู่สัปดาห์/วันใหม่✅ เสร็จสิ้น100%7. Payment & Monetizationระบบชำระเงินจริง (PromptPay QR Code / Payment Gateway) และสมาชิกระดับ PRO🔴 วางแผนพัฒนา20%
