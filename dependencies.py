from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

async def check_and_deduct_credit(db: Session, current_user) -> tuple:
    """
    ฟังก์ชันตรวจสอบสิทธิ์และหัก 1 Credit ก่อนรัน AI Process
    """
    # 1. กรณีผู้ใช้งานสมาชิกระดับ Pro
    if current_user.tier == "pro":
        if current_user.subscription_expires_at and current_user.subscription_expires_at > datetime.utcnow():
            return current_user  # ผ่านทันที ไม่ต้องหักเครดิต
        else:
            # หากหมดอายุ ให้ปรับกลับเป็นสิทธิ์ Free
            current_user.tier = "free"
            db.commit()

    # 2. กรณีผู้ใช้งานสมาชิกระดับ Free
    if current_user.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "CREDIT_EXHAUSTED",
                "message": "เครดิตฟรีของคุณหมดแล้ว กรุณาอัปเกรดเป็นสมาชิก Pro เพื่อใช้งานแบบไม่จำกัด!"
            }
        )

    # 3. หัก 1 เครดิตสำหรับผู้ใช้ Free
    current_user.credits -= 1
    db.commit()
    db.refresh(current_user)

    return current_user