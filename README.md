# 🎨 PassPrint AI - Single Page Print Fixer (Frontend Showcase)

🌐 **Live Demo (เข้าชมหน้าเว็บจริง):** https://67160330.github.io/ai_autofix/  
🏭 **กลุ่มอุตสาหกรรม:** กลุ่มอุตสาหกรรมการพิมพ์และบรรจุภัณฑ์

---

## 📌 ที่มาและปัญหาในอุตสาหกรรม (Problem Statement)
ในอุตสาหกรรมโรงพิมพ์และร้านสกรีน ปัญหาที่พบเจอเป็นประจำคือผู้ใช้/ลูกค้าส่งไฟล์ภาพความละเอียดต่ำ (Low DPI) หรือโลโก้ที่แคปหน้าจอมาสั่งพิมพ์ ส่งผลให้เมื่อนำไปพิมพ์ลงบนสิ่งพิมพ์จริง ภาพจะแตกเป็นพิกเซล และสีเพี้ยน โรงพิมพ์ต้องเสียเวลาในการปฏิเสธงานหรือขอไฟล์ใหม่ 

**PassPrint AI (Frontend)** ถูกออกแบบมาเพื่อแก้ปัญหานี้ โดยเป็นอินเทอร์เฟซที่ช่วยให้ผู้ใช้สแกนปัญหาไฟล์พิมพ์ และพรีวิวผลลัพธ์การขยายความละเอียดภาพ (Super-Resolution) ได้แบบเรียลไทม์ก่อนส่งเข้ากระบวนการพิมพ์จริง

---

## ✨ ฟังก์ชันเด่นในฝั่ง Frontend (Key Features)
1. **Single Page Application (SPA) Flow:** รวบรวมลำดับขั้นตอนการทำงาน 4 ขั้นตอน (อัปโหลด -> ตรวจ Pre-flight -> ประมวลผล -> ดาวน์โหลด) ไว้ในแดชบอร์ดเดียว
2. **Interactive Image Comparison Slider:** แถบเลื่อนรูดเปรียบเทียบภาพ Before (ต้นฉบับ) และ After (หลังซ่อม) เพื่อดูความคมชัดระดับพิกเซล
3. **Real-time Metadata Matrix:** แสดงข้อมูลมิติพิกเซล (Width x Height) เปรียบเทียบระหว่างไฟล์เดิมและไฟล์หลังซ่อมแซมเชิงตัวเลข
4. **Dynamic File Management:** ระบบจัดการไฟล์ที่สามารถกด "เปลี่ยนรูปใหม่" ได้โดยไม่ทำให้หน้าจอทับซ้อนกัน

---

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)
* **HTML5 / JavaScript (ES6):** จัดการ DOM Events, Touch/Mouse Tracking Slider
* **Tailwind CSS (via CDN):** จัดเลย์เอาต์หน้าจอแบบ Modern Dark-mode Dashboard
* **GitHub Pages:** ใช้สำหรับ Deploy หน้าเว็บฝั่ง Frontend ให้สามารถใช้งานออนไลน์ได้ทันที

---

## 🚀 วิธีกดรันเพื่อตรวจโปรเจกต์ (How to Run)
1. สามารถเข้าใช้งานผ่าน **Live Demo** ได้ทันทีที่: https://67160330.github.io/ai_autofix/
2. หรือดาวน์โหลดไฟล์ `index.html` ไปเปิดบนเว็บเบราว์เซอร์ในเครื่องคอมพิวเตอร์ได้ทันทีโดยไม่ต้องติดตั้งแพ็กเกจเสริม

## 🏗️ Technology Stack & Microservices Architecture

```mermaid
graph TD
    %% Styling Definitions
    classDef client fill:#f97316,stroke:#ea580c,stroke-width:2px,color:#ffffff;
    classDef auth fill:#2563eb,stroke:#1d4ed8,stroke-width:2px,color:#ffffff;
    classDef core fill:#0d9488,stroke:#0f766e,stroke-width:2px,color:#ffffff;
    classDef business fill:#eab308,stroke:#ca8a04,stroke-width:2px,color:#000000;
    classDef db fill:#475569,stroke:#334155,stroke-width:2px,color:#ffffff;
    classDef batch fill:#16a34a,stroke:#15803d,stroke-width:2px,color:#ffffff;

    subgraph Client_Layer ["📱 Client Layer"]
        Client["Web Frontend & Mobile App<br/>(React / Flutter)"]:::client
    end

    subgraph Auth_Layer ["🔒 Authentication & Credit Control"]
        AuthService["JWT Authentication Service<br/>(FastAPI, Bcrypt, python-jose)"]:::auth
        CreditTracker["User Credits & Usage Tracker<br/>(Freemium Quota Checker)"]:::auth
    end

    subgraph Core_Services ["🖼️ Core Processing & AI Services"]
        PresetService["Document Presets Catalog Service<br/>(ICAO Standards / Visa Profiles)"]:::core
        ImageEngine["Image Processing Engine<br/>(OpenCV Headless, Pillow, NumPy)"]:::core
        AIService["AI Background AI Service<br/>(rembg, MediaPipe AI)"]:::core
    end

    subgraph Business_Layer ["💰 Business & Monetization Services"]
        PricingService["Subscription & Pricing Plan Service<br/>(FastAPI, Pydantic)"]:::business
        APIKeyService["API Key & Monetization Service<br/>(FastAPI, API Key Middleware)"]:::business
    end

    subgraph Storage_Layer ["🐘 Database & Cloud Storage"]
        CloudStorage[("☁️ Image Cloud Storage<br/>(AWS S3 / Supabase / Cloudinary)")]:::db
        UserDB[("🐘 User Profile & Credits DB<br/>(PostgreSQL)")]:::db
        PricingDB[("🐘 Pricing & API Key DB<br/>(PostgreSQL)")]:::db
        PresetDB[("🐘 Document Standards DB<br/>(PostgreSQL)")]:::db
        LogDB[("🐘 Usage & Transaction Logs DB<br/>(PostgreSQL)")]:::db
    end

    subgraph Batch_Layer ["⚡ Async Stream & Batch Processing"]
        Kafka["Async Usage Event Stream<br/>(Apache Kafka / Redis Streams)"]:::batch
        SparkJob["Apache Spark Powered<br/>Scheduled Data Reconciliation & Cleanup Jobs"]:::batch
    end

    %% Relationships / Flow
    Client --> AuthService
    AuthService --> CreditTracker

    CreditTracker --> PresetService
    CreditTracker --> ImageEngine
    CreditTracker --> AIService
    CreditTracker --> PricingService
    CreditTracker --> APIKeyService

    PresetService --> PresetDB
    ImageEngine --> CloudStorage
    AIService --> CloudStorage

    PricingService --> PricingDB
    APIKeyService --> PricingDB

    CreditTracker --> UserDB
    CreditTracker --> Kafka
    Kafka --> LogDB

    LogDB --> SparkJob
    CloudStorage --> SparkJob
    SparkJob --> UserDB
