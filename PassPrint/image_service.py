import io
from PIL import Image, ImageColor
from rembg import remove

def process_background_removal(image_bytes: bytes, bg_hex_color: str = "#FFFFFF") -> bytes:
    """
    ลบพื้นหลังด้วย rembg (AI Engine) และเปลี่ยนสีพื้นหลังใหม่ตาม Hex Color Code
    """
    # 1. อ่านไฟล์รูปภาพและแปลงเป็น RGBA
    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # 2. ประมวลผลลบพื้นหลังเดิมออกด้วย AI rembg
    output_no_bg = remove(input_image)

    # 3. แปลงรหัสสี Hex เป็น RGBA (หากใส่สีผิดจะ Fallback เป็นสีขาว)
    try:
        bg_color_rgba = ImageColor.getcolor(bg_hex_color, "RGBA")
    except ValueError:
        bg_color_rgba = (255, 255, 255, 255)

    # 4. สร้าง Canvas สีใหม่ตามขนาดของรูปภาพ
    new_bg = Image.new("RGBA", output_no_bg.size, bg_color_rgba)

    # 5. วางรูปที่ลบพื้นหลังแล้วลงบน Canvas สีใหม่
    final_image = Image.alpha_composite(new_bg, output_no_bg).convert("RGB")

    # 6. ส่งออกผลลัพธ์เป็น JPEG Bytes
    img_byte_arr = io.BytesIO()
    final_image.save(img_byte_arr, format="JPEG", quality=95)
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue()