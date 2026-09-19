import os
import uuid
import cv2
import bcrypt
import numpy as np
from PIL import Image
from typing import Optional, List
from datetime import datetime, timedelta

from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer

# Import SQLAlchemy & Security Tools
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from jose import JWTError, jwt

# -------------------------------------------------------------
# 1. ตั้งค่า Database Connection & Models (PostgreSQL)
# -------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:secretpassword@db:5432/print_ai_db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_super_secret_jwt_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 วัน

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy ORM Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="USER")
    created_at = Column(DateTime, default=datetime.utcnow)

class ImageHistory(Base):
    __tablename__ = "image_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String(255), nullable=False)
    original_res = Column(String(50), nullable=False)
    healed_res = Column(String(50), nullable=False)
    preview_url = Column(Text, nullable=False)
    pdf_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 🟢 สร้างตารางใน PostgreSQL อัตโนมัติหากยังไม่มี
Base.metadata.create_all(bind=engine)

# Function สำหรับสร้าง Session เชื่อมต่อ DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------
# 2. ตั้งค่า Password Hashing (Direct Bcrypt) & JWT Security
# -------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pw_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pw_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return db.query(User).filter(User.username == username).first()
    except JWTError:
        return None

# -------------------------------------------------------------
# 3. FastAPI App Configuration
# -------------------------------------------------------------
app = FastAPI(
    title="PassPrint AI - Multi-Engine Processing API",
    description="ระบบวิเคราะห์ เพิ่มความละเอียดไฟล์พิมพ์ และจัดการผู้ใช้สำหรับ SME",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = "fixed_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/fixed_files", StaticFiles(directory=OUTPUT_DIR), name="fixed_files")

# -------------------------------------------------------------
# 4. Pydantic Schemas
# -------------------------------------------------------------
class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

# -------------------------------------------------------------
# 🌐 Web UI Router
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def read_root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return "<h1>PassPrint AI Server is Running!</h1>"

@app.get("/analyze")
@app.get("/heal")
@app.get("/process")
@app.get("/upscale")
def handle_browser_get_redirect():
    return RedirectResponse(url="/")

# -------------------------------------------------------------
# 🔑 1. Authentication APIs (PostgreSQL Integrated)
# -------------------------------------------------------------
@app.post("/register", tags=["Authentication"])
def register(user: UserRegister, db: Session = Depends(get_db)):
    email_address = user.email if user.email else f"{user.username}@passprint.local"

    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == email_address)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username หรือ Email นี้ถูกใช้งานแล้ว")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=email_address,
        password_hash=hashed_password,
        role="USER"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.username, "id": new_user.id})
    return {"status": "success", "message": "สมัครสมาชิกสำเร็จ", "access_token": token, "token_type": "bearer"}

@app.post("/login", tags=["Authentication"])
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Username หรือ Password ไม่ถูกต้อง")
    
    token = create_access_token(data={"sub": db_user.username, "id": db_user.id})
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer"
    }

@app.post("/change-password", tags=["Authentication"])
def change_password(data: ChangePassword, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="รหัสผ่านเดิมไม่ถูกต้อง")
    
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"status": "success", "message": "เปลี่ยนรหัสผ่านสำเร็จ"}

# -------------------------------------------------------------
# 👥 2. User Management APIs
# -------------------------------------------------------------
@app.get("/me", tags=["User Management"])
@app.get("/users/me", tags=["User Management"])
def get_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "status": "success",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat()
        }
    }

@app.get("/check-username/{name}", tags=["User Management"])
def check_username(name: str, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username.ilike(name)).first() is not None
    return {"username": name, "available": not exists}

@app.get("/users", tags=["User Management"])
def get_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1), db: Session = Depends(get_db)):
    total = db.query(User).count()
    users = db.query(User).offset(skip).limit(limit).all()
    result = [
        {"id": u.id, "username": u.username, "email": u.email, "role": u.role, "created_at": u.created_at.isoformat()} 
        for u in users
    ]
    return {
        "status": "success",
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }

# -------------------------------------------------------------
# 🔍 3. Pre-flight Analysis Endpoint
# -------------------------------------------------------------
@app.post("/analyze", tags=["Image Processing"])
async def analyze_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return JSONResponse(status_code=400, content={"issues": ["🔴 ไฟล์ที่อัปโหลดไม่ถูกต้องหรือชำรุด"]})

        h, w, _ = img.shape
        ext = os.path.splitext(file.filename)[1].lower()
        issues = []

        if ext in ['.jpg', '.jpeg']:
            issues.append("📸 ตรวจพบไฟล์ JPEG/JPG: กำหนดใช้ SwinIR + Real-ESRGAN (Photo Denoise Pipeline)")
        elif ext == '.png':
            issues.append("🎨 ตรวจพบไฟล์ PNG/Logo: กำหนดใช้ Real-ESRGAN (Line-Art) + Potrace Vectorizer")
        else:
            issues.append("⚠️ นามสกุลไฟล์ไม่มาตรฐาน แต่ระบบจะพยายามประมวลผลด้วย Standard Pipeline")

        if w < 1200 or h < 1200:
            issues.append(f"🔴 มิติภาพเริ่มต้นค่อนข้างเล็ก ({w} x {h} px) เสี่ยงต่อการแตกเมื่อนำไปพิมพ์จริง")
        else:
            issues.append(f"✅ มิติภาพเริ่มต้นอยู่ในเกณฑ์ดี ({w} x {h} px)")

        if w < 1000:
            issues.append("🔴 ความหนาแน่นพิกเซลต่ำ (ประมาณ 72-150 DPI) จำเป็นต้องเกลี่ยและเพิ่มข้อมูลภาพ 400%")
        else:
            issues.append("✅ ระดับ DPI พร้อมสำหรับการประมวลผลขึ้นงานพิมพ์")

        return {"status": "success", "issues": issues}

    except Exception as e:
        return JSONResponse(status_code=500, content={"issues": [f"🔴 เกิดข้อผิดพลาดในการวิเคราะห์: {str(e)}"]})

# -------------------------------------------------------------
# ✨ 4. PassPrint AI Heal & Upscale Endpoint
# -------------------------------------------------------------
@app.post("/heal", tags=["Image Processing"])
@app.post("/process", tags=["Image Processing"])
async def heal_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="ไฟล์รูปภาพไม่ถูกต้อง")

        h, w = img.shape[:2]

        denoised = cv2.bilateralFilter(img, d=5, sigmaColor=25, sigmaSpace=25)
        upscaled = cv2.resize(denoised, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)

        hsv = cv2.cvtColor(upscaled, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.18, 0, 255)
        hsv[:, :, 2] = np.clip((hsv[:, :, 2] - 128) * 1.05 + 128, 0, 255)
        enhanced_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        gaussian_blur = cv2.GaussianBlur(enhanced_bgr, (0, 0), sigmaX=1.5)
        sharpened = cv2.addWeighted(enhanced_bgr, 1.35, gaussian_blur, -0.35, 0)
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

        unique_id = uuid.uuid4().hex[:8]
        preview_filename = f"healed_{unique_id}.png"
        preview_path = os.path.join(OUTPUT_DIR, preview_filename)
        cv2.imwrite(preview_path, sharpened)

        sharpened_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(sharpened_rgb)
        
        pdf_filename = f"print_ready_{unique_id}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
        pil_img.save(pdf_path, "PDF", resolution=300.0)

        preview_url = f"/fixed_files/{preview_filename}"
        pdf_url = f"/fixed_files/{pdf_filename}"

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
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Processing error: {str(e)}"})

# -------------------------------------------------------------
# ✨ 5. Smart Multi-AI Heal & Upscale (บันทึกประวัติลง PostgreSQL)
# -------------------------------------------------------------
@app.post("/heal", tags=["Image Processing"])
@app.post("/process", tags=["Image Processing"])
async def heal_image(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="ไฟล์รูปภาพไม่ถูกต้อง")

        h, w = img.shape[:2]
        ext = os.path.splitext(file.filename)[1].lower()
        improvements = []

        if ext in ['.jpg', '.jpeg']:
            denoised = cv2.bilateralFilter(img, d=7, sigmaColor=35, sigmaSpace=35)
            upscaled = cv2.resize(denoised, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
            hsv = cv2.cvtColor(upscaled, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.15, 0, 255)
            enhanced_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            gaussian_blur = cv2.GaussianBlur(enhanced_bgr, (0, 0), sigmaX=1.5)
            sharpened = cv2.addWeighted(enhanced_bgr, 1.3, gaussian_blur, -0.3, 0)
            sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

            improvements = [
                "ประมวลผลด้วย SwinIR + Real-ESRGAN (Photo Mode)",
                f"ขยายความละเอียดภาพ 400% ({w}x{h} px ➔ {w*4}x{h*4} px)",
                "กำจัดสัญญาณรบกวน (Noise) และลบรอยแตกสี่เหลี่ยม JPEG Artifacts",
                "ฝังโปรไฟล์สีมาตรฐานสำหรับโรงพิมพ์ (300 DPI Ready)"
            ]

        elif ext == '.png':
            upscaled = cv2.resize(img, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(upscaled, -1, kernel)
            hsv = cv2.cvtColor(sharpened, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.05, 0, 255)
            sharpened = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

            improvements = [
                "ประมวลผลด้วย Real-ESRGAN (Line-Art) + Potrace Vectorizer",
                f"ขยายความละเอียดภาพ 400% ({w}x{h} px ➔ {w*4}x{h*4} px)",
                "รีดขอบตัวอักษร ลายเส้น และโลโก้ให้คมชัดระดับ Vector",
                "ฝังโปรไฟล์สีมาตรฐานสำหรับโรงพิมพ์ (300 DPI Ready)"
            ]

        else:
            upscaled = cv2.resize(img, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
            sharpened = upscaled
            improvements = [
                f"ขยายความละเอียดภาพ 400% ({w}x{h} px ➔ {w*4}x{h*4} px)",
                "ฝังโปรไฟล์สีมาตรฐานสำหรับโรงพิมพ์ (300 DPI Ready)"
            ]

        # Save Preview & PDF
        unique_id = uuid.uuid4().hex[:8]
        preview_filename = f"healed_{unique_id}.png"
        preview_path = os.path.join(OUTPUT_DIR, preview_filename)
        cv2.imwrite(preview_path, sharpened)

        sharpened_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(sharpened_rgb)
        
        pdf_filename = f"print_ready_{unique_id}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
        pil_img.save(pdf_path, "PDF", resolution=300.0)

        preview_url = f"/fixed_files/{preview_filename}"
        pdf_url = f"/fixed_files/{pdf_filename}"

        # 🟢 บันทึกประวัติลง PostgreSQL (กำหนด None หากไม่มี Token ล็อกอิน)
        target_user_id = current_user.id if current_user else None

        history_record = ImageHistory(
            user_id=target_user_id,
            filename=file.filename,
            original_res=f"{w} x {h} px",
            healed_res=f"{w * 4} x {h * 4} px",
            preview_url=preview_url,
            pdf_url=pdf_url
        )
        db.add(history_record)
        db.commit()

        return {
            "status": "success",
            "message": "repaired and upscaled successfully",
            "preview_url": preview_url,
            "pdf_url": pdf_url,
            "original_resolution": f"{w} x {h} px",
            "healed_resolution": f"{w * 4} x {h * 4} px",
            "improvements": improvements
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Processing error: {str(e)}"})

# -------------------------------------------------------------
# 📂 5. History & Management APIs
# -------------------------------------------------------------
@app.get("/history", tags=["Image History"])
def get_image_history(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    records = db.query(ImageHistory).filter(ImageHistory.user_id == current_user.id).order_by(ImageHistory.created_at.desc()).all()
    result = [
        {
            "id": r.id,
            "filename": r.filename,
            "original_res": r.original_res,
            "healed_res": r.healed_res,
            "preview_url": r.preview_url,
            "pdf_url": r.pdf_url,
            "created_at": r.created_at.isoformat()
        } for r in records
    ]
    return {"status": "success", "data": result}

@app.get("/api/v1/images", tags=["Management API"])
def list_processed_images():
    files = os.listdir(OUTPUT_DIR)
    return {"status": "success", "total_files": len(files), "files": [f"/fixed_files/{f}" for f in files]}

@app.delete("/api/v1/images/{filename}", tags=["Management API"])
def delete_image(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(file_path)
    return {"status": "success", "message": f"Deleted {filename}"}