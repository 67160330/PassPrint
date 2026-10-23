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
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from jose import JWTError, jwt

from config import (
    DATABASE_URL,
    JWT_SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    OUTPUT_DIR
)

# --- 1. OPENCV IMAGE PROCESSING ENGINE ---
def process_image_pipeline(img: np.ndarray, ext: str, adjust_color: bool = False) -> tuple[np.ndarray, list[str]]:
    h, w = img.shape[:2]
    has_alpha = (img.ndim == 3 and img.shape[2] == 4)

    if has_alpha:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
    else:
        bgr = img
        alpha = None

    if ext in ['.jpg', '.jpeg']:
        denoised_bgr = cv2.bilateralFilter(bgr, d=7, sigmaColor=35, sigmaSpace=35)
    else:
        denoised_bgr = bgr

    upscaled_bgr = cv2.resize(denoised_bgr, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
    if has_alpha:
        upscaled_alpha = cv2.resize(alpha, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)

    if adjust_color:
        hsv = cv2.cvtColor(upscaled_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.15, 0, 255)
        hsv[:, :, 2] = np.clip((hsv[:, :, 2] - 128) * 1.05 + 128, 0, 255)
        processed_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        improvements = [
            f"ขยายความรายละเอียด 400% ({w}x{h} px ➔ {w*4}x{h*4} px)",
            "เพิ่มความคมชัดด้วย Unsharp Masking",
            "ปรับเร่งความสดสีและมิติภาพ",
            "รักษามิติพื้นหลังโปร่งใส PNG"
        ]
    else:
        processed_bgr = upscaled_bgr
        improvements = [
            f"ขยายความรายละเอียด 400% ({w}x{h} px ➔ {w*4}x{h*4} px)",
            "เพิ่มความคมชัดด้วย Unsharp Masking",
            "คงค่าสีและโทนสีเดิมไว้ 100%",
            "รักษามิติพื้นหลังโปร่งใส PNG"
        ]

    gaussian_blur = cv2.GaussianBlur(processed_bgr, (0, 0), sigmaX=1.5)
    sharpened_bgr = cv2.addWeighted(processed_bgr, 1.3, gaussian_blur, -0.3, 0)
    sharpened_bgr = np.clip(sharpened_bgr, 0, 255).astype(np.uint8)

    if has_alpha:
        sharpened = cv2.merge([sharpened_bgr[:, :, 0], sharpened_bgr[:, :, 1], sharpened_bgr[:, :, 2], upscaled_alpha])
    else:
        sharpened = sharpened_bgr

    return sharpened, improvements

# --- 2. DATABASE MODELS & SETUP ---
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

    tier = Column(String(20), default="free")
    credits = Column(Integer, default=7)
    last_credit_reset = Column(DateTime, default=datetime.utcnow)
    subscription_expires_at = Column(DateTime, nullable=True)

    histories = relationship("ImageHistory", back_populates="user", cascade="all, delete-orphan")

class ImageHistory(Base):
    __tablename__ = "image_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    preview_url = Column(String(255), nullable=False)
    pdf_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="histories")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 3. AUTH & CREDIT HELPERS ---
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

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def reset_daily_credits_if_needed(user: User, db: Session):
    now = datetime.utcnow()
    if user.last_credit_reset is None or user.last_credit_reset.date() < now.date():
        user.credits = 7
        user.last_credit_reset = now
        db.commit()
        db.refresh(user)

async def check_and_deduct_credit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.tier == "pro":
        if current_user.subscription_expires_at and current_user.subscription_expires_at > datetime.utcnow():
            return current_user
        else:
            current_user.tier = "free"
            db.commit()

    reset_daily_credits_if_needed(current_user, db)

    if current_user.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="โควตาแต่งรูปเองของคุณหมดแล้ว (0/7 รอบ/วัน) กรุณากลับมาใหม่พรุ่งนี้ หรือใช้งานระบบ OpenCV ปรับให้อัตโนมัติแทน!"
        )

    current_user.credits -= 1
    db.commit()
    db.refresh(current_user)
    return current_user

# --- 4. FASTAPI APP & ROUTING ---
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

@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return "<h1>PassPrint Server Active</h1>"

@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    email_addr = user.email if user.email else f"{user.username}@passprint.local"
    if db.query(User).filter((User.username == user.username) | (User.email == email_addr)).first():
        raise HTTPException(status_code=400, detail="Username หรือ Email นี้ถูกใช้งานแล้ว")
    
    new_user = User(
        username=user.username, 
        email=email_addr, 
        password_hash=get_password_hash(user.password),
        credits=7
    )
    db.add(new_user)
    db.commit()
    token = create_access_token({"sub": new_user.username, "id": new_user.id})
    return {"status": "success", "access_token": token, "token_type": "bearer"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Username หรือ Password ไม่ถูกต้อง")
    
    reset_daily_credits_if_needed(db_user, db)
    token = create_access_token({"sub": db_user.username, "id": db_user.id})
    return {"status": "success", "access_token": token, "token_type": "bearer"}

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reset_daily_credits_if_needed(current_user, db)
    remaining_credits = "Unlimited" if current_user.tier == "pro" else current_user.credits
    return {
        "status": "success", 
        "data": {
            "id": current_user.id, 
            "username": current_user.username, 
            "email": current_user.email,
            "tier": current_user.tier,
            "credits": remaining_credits
        }
    }

# --- 5. ลบบัญชีผู้ใช้ (DELETE ACCOUNT) ---
@app.delete("/account")
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(current_user)
    db.commit()
    return {"status": "success", "message": "ลบบัญชีผู้ใช้เรียบร้อยแล้ว"}

# --- 6. ระบบประวัติภาพ (IMAGE HISTORY) ---
@app.get("/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    histories = db.query(ImageHistory).filter(ImageHistory.user_id == current_user.id).order_by(ImageHistory.created_at.desc()).all()
    return {
        "status": "success",
        "data": [
            {
                "id": h.id,
                "preview_url": h.preview_url,
                "pdf_url": h.pdf_url,
                "created_at": h.created_at.strftime("%d/%m/%Y %H:%M")
            }
            for h in histories
        ]
    }

@app.delete("/history/{history_id}")
def delete_history_item(history_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(ImageHistory).filter(ImageHistory.id == history_id, ImageHistory.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบประวัติภาพนี้")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "ลบประวัติภาพเรียบร้อยแล้ว"}

# Helper Function Save Outputs
def save_processed_outputs(sharpened: np.ndarray) -> tuple[str, str]:
    unique_id = uuid.uuid4().hex[:8]
    preview_filename = f"healed_{unique_id}.png"
    preview_path = os.path.join(OUTPUT_DIR, preview_filename)
    
    cv2.imwrite(preview_path, sharpened)

    if sharpened.ndim == 3 and sharpened.shape[2] == 4:
        sharpened_rgba = cv2.cvtColor(sharpened, cv2.COLOR_BGRA2RGBA)
        pil_img = Image.fromarray(sharpened_rgba)
        background = Image.new("RGBA", pil_img.size, (255, 255, 255, 255))
        pdf_pil = Image.alpha_composite(background, pil_img).convert("RGB")
    else:
        sharpened_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
        pdf_pil = Image.fromarray(sharpened_rgb)

    pdf_filename = f"print_ready_{unique_id}.pdf"
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
    pdf_pil.save(pdf_path, "PDF", resolution=300.0)

    return f"/{OUTPUT_DIR}/{preview_filename}", f"/{OUTPUT_DIR}/{pdf_filename}"

@app.post("/heal-auto")
async def heal_auto_image(
    file: UploadFile = File(...), 
    adjust_color: bool = Form(False)
):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        if img is None:
            raise HTTPException(status_code=400, detail="ไฟล์รูปภาพไม่ถูกต้อง")

        h, w = img.shape[:2]
        ext = os.path.splitext(file.filename)[1].lower()

        sharpened, improvements = process_image_pipeline(img, ext, adjust_color)
        preview_url, pdf_url = save_processed_outputs(sharpened)

        return {
            "status": "success",
            "message": "Auto processed successfully",
            "preview_url": preview_url,
            "pdf_url": pdf_url,
            "original_resolution": f"{w} x {h} px",
            "healed_resolution": f"{w * 4} x {h * 4} px",
            "improvements": improvements
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/heal")
@app.post("/process")
async def heal_canvas_image(
    file: UploadFile = File(...), 
    adjust_color: bool = Form(False),
    current_user: User = Depends(check_and_deduct_credit),
    db: Session = Depends(get_db)
):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        if img is None:
            raise HTTPException(status_code=400, detail="ไฟล์รูปภาพไม่ถูกต้อง")

        h, w = img.shape[:2]
        ext = os.path.splitext(file.filename)[1].lower()

        sharpened, improvements = process_image_pipeline(img, ext, adjust_color)
        preview_url, pdf_url = save_processed_outputs(sharpened)

        # บันทึกลงประวัติภาพ
        new_history = ImageHistory(
            user_id=current_user.id,
            preview_url=preview_url,
            pdf_url=pdf_url
        )
        db.add(new_history)
        db.commit()

        remaining_credits = "Unlimited" if current_user.tier == "pro" else str(current_user.credits)

        return {
            "status": "success",
            "message": "Canvas edited image exported successfully",
            "preview_url": preview_url,
            "pdf_url": pdf_url,
            "original_resolution": f"{w} x {h} px",
            "healed_resolution": f"{w * 4} x {h * 4} px",
            "remaining_credits": remaining_credits,
            "improvements": improvements
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})