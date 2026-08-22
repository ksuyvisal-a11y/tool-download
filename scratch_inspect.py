import os
from PIL import Image

src_path = r"C:\Users\M\.gemini\antigravity-ide\brain\85c13d51-741d-46a7-9832-da8a9ad280aa\.user_uploaded\media_1787190864446.png"

img = Image.open(src_path)
print("Image format:", img.format)
print("Image size:", img.size)
print("Image mode:", img.mode)

# Check corner pixel to see background color
corners = [
    img.getpixel((0, 0)),
    img.getpixel((img.width - 1, 0)),
    img.getpixel((0, img.height - 1)),
    img.getpixel((img.width - 1, img.height - 1))
]
print("Corners:", corners)
