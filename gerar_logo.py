from PIL import Image, ImageDraw, ImageFont
import os

# Garante que a pasta existe
os.makedirs("assets", exist_ok=True)

img = Image.new('RGB', (400, 150), color='white')
d = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype("arial.ttf", 40)
except:
    font = ImageFont.load_default()

d.text((50, 50), "Stock Famous", fill=(255, 0, 0), font=font)
img.save("assets/logo.png")
print("✅ Logo criada em assets/logo.png")
