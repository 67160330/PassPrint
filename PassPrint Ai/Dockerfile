FROM python:3.12-slim

# ติดตั้ง System Dependencies สำหรับ OpenCV, Potrace และ Real-ESRGAN Vulkan
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    vulkan-tools \
    potrace \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# คัดลอกไฟล์จัดการ Dependencies และติดตั้ง
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอก Source Code และไฟล์ Executable ทั้งหมดลง Container
COPY . .

# สร้างโฟลเดอร์สำหรับเก็บไฟล์ผลลัพธ์
RUN mkdir -p fixed_files

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]