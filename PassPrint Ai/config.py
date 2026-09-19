import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "fixed_files")

# ตรวจสอบว่ามีการตั้งค่า Key ที่จำเป็นครบหรือไม่
if not DATABASE_URL or not JWT_SECRET_KEY:
    raise ValueError("❌ ไม่พบ DATABASE_URL หรือ JWT_SECRET_KEY กรุณระบุในไฟล์ .env")