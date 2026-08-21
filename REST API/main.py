import os
import io
import uuid
import cv2
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="PassPrint AI - Engine Services",
    description="ระบบวิเคราะห์และเพิ่มความละเอียดไฟล์พิมพ์อัตโนมัติ สำหรับร้านค้าออนไลน์ & SME",
    version="2.0.0"
)

# 1. ตั้งค่า CORS อนุญาตให้ Frontend เชื่อมต่อได้ทุกช่องทาง
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. จัดการโฟลเดอร์สำหรับเก็บไฟล์ผลลัพธ์
OUTPUT_DIR = "fixed_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/fixed_files", StaticFiles(directory=OUTPUT_DIR), name="fixed_files")


# -------------------------------------------------------------
# 🌐 0. Router หน้าเว็บหลัก และป้องกัน Error 405 Method Not Allowed
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def read_root():
    """แสดงผลหน้าเว็บหลัก index.html"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return "<h1>PassPrint AI Server is Running! (index.html not found)</h1>"

@app.get("/analyze")
@app.get("/heal")
@app.get("/process")
@app.get("/upscale")
def handle_browser_get_redirect():
    """ดักจับคำสั่ง GET ในกรณีที่ผู้ใช้พิมพ์ URL บนแถบเบราว์เซอร์ตรงๆ ให้เด้งกลับหน้าหลัก"""
    return RedirectResponse(url="/")


# -------------------------------------------------------------
# 🔍 1. Pre-flight Analysis Endpoint (สำหรับกล่องวิเคราะห์ข้อ 2)
# -------------------------------------------------------------
@app.post("/analyze", tags=["Image Processing"])
async def analyze_image(file: UploadFile = File(...)):
    """วิเคราะห์สเปกไฟล์พิมพ์ และส่งรายการประเมินกลับไปที่หน้าเว็บ"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return JSONResponse(
                status_code=400,
                content={"issues": ["🔴 ไฟล์ที่อัปโหลดไม่ถูกต้องหรือชำรุด"]}
            )

        h, w, c = img.shape
        issues = []

        # ประเมินขนาดพิกเซล
        if w < 1200 or h < 1200:
            issues.append(f"🔴 มิติภาพเริ่มต้นค่อนข้างเล็ก ({w} x {h} px) เสี่ยงต่อการแตกเมื่อนำไปพิมพ์จริง")
        else:
            issues.append(f"🟢 มิติภาพเริ่มต้นอยู่ในเกณฑ์ดี ({w} x {h} px)")

        # ประเมินความหนาแน่นพิกเซล (DPI Estimate)
        if w < 1000:
            issues.append("🔴 ความหนาแน่นพิกเซลต่ำ (ประมาณ 72-150 DPI) จำเป็นต้องเกลี่ยและเพิ่มข้อมูลภาพ 400%")
        else:
            issues.append("🟢 ระดับ DPI พร้อมสำหรับการประมวลผลขึ้นงานพิมพ์")

        # ประเมินระบบสี
        if c == 3:
            issues.append("🟢 โครงสร้างสี RGB สมบูรณ์ พร้อมสำหรับอัลกอริทึมดึงรายละเอียดพิกเซล")

        return {"status": "success", "issues": issues}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"issues": [f"🔴 เกิดข้อผิดพลาดในการวิเคราะห์: {str(e)}"]}
        )


# -------------------------------------------------------------
# ✨ 2. PassPrint AI Heal & Upscale Endpoint (ปรับปรุงภาพเนียนคม)
# -------------------------------------------------------------
@app.post("/heal", tags=["Image Processing"])
@app.post("/process", tags=["Image Processing"])
async def heal_image(file: UploadFile = File(...)):
    """ขยายภาพ 4 เท่า ลบรอยแตกเม็ดสเปกตรัม และสร้างไฟล์ PDF 300 DPI"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="ไฟล์รูปภาพไม่ถูกต้อง")

        h, w = img.shape[:2]

        # Step 1: เกลี่ยรอยแตกและ Noise เดิมของภาพออกก่อน (Bilateral Filter)
        denoised = cv2.bilateralFilter(img, d=5, sigmaColor=30, sigmaSpace=30)

        # Step 2: ขยายมิติภาพ 4 เท่า ด้วย INTER_CUBIC (ลดขอบหยักและรอยแตก)
        upscaled = cv2.resize(denoised, (w * 4, h * 4), interpolation=cv2.INTER_CUBIC)

        # Step 3: เพิ่มความคมชัดแบบนุ่มนวล (Soft Sharpening) ป้องกันการเกิด Noise เพิ่ม
        gaussian_blur = cv2.GaussianBlur(upscaled, (0, 0), sigmaX=1.0)
        sharpened = cv2.addWeighted(upscaled, 1.15, gaussian_blur, -0.15, 0)

        # ✅ สุ่ม ID ภาษาอังกฤษ (UUID) สำหรับชื่อไฟล์ ป้องกันปัญหาภาษาไทยติด Error 404
        unique_id = uuid.uuid4().hex[:8]

        # บันทึกไฟล์รูปภาพสำหรับพรีวิวบน Slider (PNG)
        preview_filename = f"healed_{unique_id}.png"
        preview_path = os.path.join(OUTPUT_DIR, preview_filename)
        cv2.imwrite(preview_path, sharpened)

        # Step 4: แปลงภาพเป็น PDF คุณภาพสูง (300 DPI Target)
        sharpened_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(sharpened_rgb)
        
        pdf_filename = f"print_ready_{unique_id}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
        pil_img.save(pdf_path, "PDF", resolution=300.0)

        preview_url = f"/fixed_files/{preview_filename}"
        pdf_url = f"/fixed_files/{pdf_filename}"

        # ส่งคืนค่าตรงตามคีย์ตัวแปรที่ index.html เรียกใช้
        return {
            "status": "success",
            "message": "repaired and upscaled successfully",
            "preview_url": preview_url,
            "pdf_url": pdf_url,
            "url": preview_url,
            "file_url": preview_url,
            "original_resolution": f"{w} x {h} px",
            "healed_resolution": f"{w * 4} x {h * 4} px"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Processing error: {str(e)}"}
        )


# -------------------------------------------------------------
# 📂 3. REST APIs เสริมสำหรับจัดการไฟล์และผู้ใช้
# -------------------------------------------------------------
@app.get("/api/v1/images", tags=["Management API"])
def list_processed_images():
    files = os.listdir(OUTPUT_DIR)
    return {
        "status": "success",
        "total_files": len(files),
        "files": [f"/fixed_files/{f}" for f in files]
    }

@app.delete("/api/v1/images/{filename}", tags=["Management API"])
def delete_image(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(file_path)
    return {"status": "success", "message": f"Deleted {filename}"}

@app.get("/users/me", tags=["Management API"])
def get_user_profile():
    return {
        "user_id": "usr_sme_889",
        "username": "passprint_official",
        "package": "PassPrint Pro",
        "status": "Active"
    }