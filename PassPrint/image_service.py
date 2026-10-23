import io
from PIL import Image

def process_background_removal(image_bytes: bytes, bg_color_hex: str = "#FFFFFF") -> bytes:
    """
    รับภาพจาก Canvas มาใส่สีพื้นหลังใหม่กรณีมีส่วนโปร่งแสง
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    
    hex_color = bg_color_hex.lstrip("#")
    if len(hex_color) != 6:
        hex_color = "FFFFFF"
    bg_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    background = Image.new("RGBA", img.size, bg_rgb + (255,))
    final_img = Image.alpha_composite(background, img).convert("RGB")
    
    img_byte_arr = io.BytesIO()
    final_img.save(img_byte_arr, format="JPEG", quality=95)
    return img_byte_arr.getvalue()