from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from io import BytesIO

def apply_watermark(image):
    base_img = Image.open(image).convert("RGBA")
    width, height = base_img.size

    # Watermark text
    text = "Sokoletu.co.tz"
    font = ImageFont.truetype("arial.ttf", size=int(width/20))

    watermark_layer = Image.new("RGBA", base_img.size, (0,0,0,0))
    draw = ImageDraw.Draw(watermark_layer)

    # Position bottom-right
    text_width, text_height = draw.textsize(text, font)
    position = (width - text_width - 20, height - text_height - 20)

    draw.text(position, text, font=font, fill=(255,255,255,120))  # 120 = opacity

    combined = Image.alpha_composite(base_img, watermark_layer)
    combined = combined.convert("RGB")

    output = BytesIO()
    combined.save(output, format='JPEG', quality=85)
    return ContentFile(output.getvalue())
