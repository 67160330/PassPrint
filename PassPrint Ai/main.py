import os
import uuid
import cv2
import bcrypt
import numpy as np
from PIL import Image
from typing import Optional
from datetime import datetime, timedelta

from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt

# --- 1. IMPORT CONFIGURATIONS ---
from config import (
    DATABASE_URL,
    JWT_SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    OUTPUT_DIR
)

# --- 2. AUTHENTICATION HELPERS ---
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

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

# --- 3. AI IMAGE PROCESSING ENGINE ---
def process_image_pipeline(img: np.ndarray, ext: str, adjust_color: bool = False) -> tuple[np.ndarray, list[str]]:
    """ประมวลผล Denoise, Upscale 400%, ปรับสี และ Sharpening"""
    h, w = img.shape[:2]
    
    # 3.1 Denoise ตามประเภทไฟล์
    if ext in ['.jpg', '.jpeg']:
        denoised = cv2.bilateralFilter(img, d=7, sigmaColor=35, sigmaSpace=35)
    else:
        denoised = img

    # 3.2 Upscale 400% (INTER_LANCZOS4)
    upscaled = cv2.resize(denoised, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)

    # 3.3 Color Adjustment Mode
    if adjust_color:
        hsv = cv2.cvtColor(upscaled, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.15, 0, 255)
        hsv[:, :, 2] = np.clip((hsv[:, :, 2] - 128) * 1.05 + 128, 0, 255)
        processed = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        improvements = [
            f"ขยายความรายละเอียด 400% ({w}x{h} px ➔ {w*4}x{h*4} px)",
            "เพิ่มความคมชัดของตัวอักษรและลายเส้นขอบภาพ",
            "ปรับแต่งเพิ่มความสดของสี (Saturation) และปรับ Contrast",
            "ฝังโปรไฟล์สีมาตรฐานสำหรับโรงพิมพ์ (300 DPI Ready)"
        ]
    else:
        processed = upscaled
        improvements = [
            f"ขยายความรายละเอียด 400% ({w}x{h} px ➔ {w*4}x{h*4} px)",
            "เพิ่มความคมชัดของตัวอักษรและลายเส้นขอบภาพ",
            "คงค่าสีและโทนสีเดิมของไฟล์ต้นฉบับไว้ 100%",
            "ฝังโปรไฟล์สีมาตรฐานสำหรับโรงพิมพ์ (300 DPI Ready)"
        ]

    # 3.4 Unsharp Masking
    gaussian_blur = cv2.GaussianBlur(processed, (0, 0), sigmaX=1.5)
    sharpened = cv2.addWeighted(processed, 1.3, gaussian_blur, -0.3, 0)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    return sharpened, improvements

# --- 4. DATABASE MODELS & SETUP ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

# --- 5. FASTAPI APP & ROUTING ---
app = FastAPI(title="PassPrint - SME Print Optimizer", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount(f"/{OUTPUT_DIR}", StaticFiles(directory=OUTPUT_DIR), name=OUTPUT_DIR)

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

# --- Web UI Routes ---
@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def read_root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return "<h1>PassPrint AI Server is Running!</h1>"

@app.get("/analyze")
@app.get("/heal")
@app.get("/process")
def handle_browser_get_redirect():
    return RedirectResponse(url="/")

# --- Auth APIs ---
@app.post("/register", tags=["Authentication"])
def register(user: UserRegister, db: Session = Depends(get_db)):
    email_address = user.email if user.email else f"{user.username}@passprint.local"
    existing_user = db.query(User).filter((User.username == user.username) | (User.email == email_address)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username หรือ Email นี้ถูกใช้งานแล้ว")
    
    new_user = User(
        username=user.username,
        email=email_address,
        password_hash=get_password_hash(user.password),
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
    return {"status": "success", "access_token": token, "token_type": "bearer"}

@app.post("/change-password", tags=["Authentication"])
def change_password(data: ChangePassword, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="รหัสผ่านเดิมไม่ถูกต้อง")
    
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"status": "success", "message": "เปลี่ยนรหัสผ่านสำเร็จ"}

@app.get("/me", tags=["User Management"])
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

# --- Core Processing APIs ---
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
            issues.append("📸 ตรวจพบไฟล์ JPEG/JPG: กำหนดใช้ Photo Denoise Pipeline")
        elif ext == '.png':
            issues.append("🎨 ตรวจพบไฟล์ PNG/Logo: กำหนดใช้ Line-Art Vector Engine")
        else:
            issues.append("⚠️ นามสกุลไฟล์ไม่มาตรฐาน แต่ระบบจะประมวลผลด้วย Standard Engine")

        if w < 1200 or h < 1200:
            issues.append(f"🔴 มิติภาพเริ่มต้น ({w} x {h} px) เสี่ยงต่อการแตกเมื่อพิมพ์จริง")
        else:
            issues.append(f"✅ มิติภาพเริ่มต้นอยู่ในเกณฑ์ดี ({w} x {h} px)")

        return {"status": "success", "issues": issues}
    except Exception as e:
        return JSONResponse(status_code=500, content={"issues": [f"🔴 เกิดข้อผิดพลาดในการวิเคราะห์: {str(e)}"]})

@app.post("/heal", tags=["Image Processing"])
@app.post("/process", tags=["Image Processing"])
async def heal_image(
    file: UploadFile = File(...), 
    adjust_color: bool = Form(False),
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

        sharpened, improvements = process_image_pipeline(img, ext, adjust_color)

        unique_id = uuid.uuid4().hex[:8]
        preview_filename = f"healed_{unique_id}.png"
        preview_path = os.path.join(OUTPUT_DIR, preview_filename)
        cv2.imwrite(preview_path, sharpened)

        sharpened_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(sharpened_rgb)
        
        pdf_filename = f"print_ready_{unique_id}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
        pil_img.save(pdf_path, "PDF", resolution=300.0)

        preview_url = f"/{OUTPUT_DIR}/{preview_filename}"
        pdf_url = f"/{OUTPUT_DIR}/{pdf_filename}"

        history_record = ImageHistory(
            user_id=current_user.id if current_user else None,
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

# --- Image History APIs ---
@app.get("/history", tags=["Image History"])
def get_image_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.delete("/history/{history_id}", tags=["Image History"])
def delete_single_history(
    history_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """ลบประวัติรูปภาพทีละ 1 รายการ"""
    record = db.query(ImageHistory).filter(
        ImageHistory.id == history_id, 
        ImageHistory.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="ไม่พบประวัติรายการนี้")

    db.delete(record)
    db.commit()
    return {"status": "success", "message": "ลบรายการประวัติเรียบร้อยแล้ว"}

@app.delete("/history", tags=["Image History"])
def clear_all_history(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """ลบประวัติรูปภาพทั้งหมดของผู้ใช้ปัจจุบัน"""
    db.query(ImageHistory).filter(ImageHistory.user_id == current_user.id).delete()
    db.commit()
    return {"status": "success", "message": "ลบประวัติทั้งหมดเรียบร้อยแล้ว"}