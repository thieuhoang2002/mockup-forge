"""
Sample Assets Generator
Creates test dataset for instant verification:
1. Synthetic t-shirt mockup template with realistic wrinkles & shadows.
2. Sample design PNG with transparent padding to test auto-trimming.
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def create_synthetic_tshirt_template(output_path: str, size: tuple = (1200, 1400)):
    """Generate realistic t-shirt template with fabric wrinkles & natural drape"""
    w, h = size
    base_color = np.array([238, 240, 242], dtype=np.float32)
    img = np.ones((h, w, 3), dtype=np.float32) * base_color
    
    # 1. T-shirt silhouette mask
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array([
        [w * 0.35, h * 0.12], # neck left
        [w * 0.50, h * 0.16], # neck bottom
        [w * 0.65, h * 0.12], # neck right
        [w * 0.88, h * 0.22], # shoulder right
        [w * 0.95, h * 0.42], # sleeve right outer
        [w * 0.82, h * 0.46], # sleeve right inner
        [w * 0.78, h * 0.88], # bottom right
        [w * 0.22, h * 0.88], # bottom left
        [w * 0.18, h * 0.46], # sleeve left inner
        [w * 0.05, h * 0.42], # sleeve left outer
        [w * 0.12, h * 0.22], # shoulder left
    ], dtype=np.int32)
    
    cv2.fillPoly(mask, [pts], 255)
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    
    # 2. Fabric folds & wrinkle waves
    y_coords, x_coords = np.indices((h, w))
    fold1 = np.sin((x_coords * 0.015 + y_coords * 0.012) * 1.5) * 18.0
    fold2 = np.cos((x_coords * 0.02 - y_coords * 0.008) * 1.8) * 12.0
    fold3 = np.sin((x_coords * 0.008 + y_coords * 0.025) * 1.2) * 14.0
    
    folds = (fold1 + fold2 + fold3) * (mask / 255.0)
    
    # 3. Micro-texture grain
    np.random.seed(42)
    grain = (np.random.randn(h, w) * 3.5) * (mask / 255.0)
    
    # 4. Vignette ambient shading
    dist_center = np.sqrt(((x_coords - w/2) / (w/2))**2 + ((y_coords - h/2) / (h/2))**2)
    vignette = -np.clip(dist_center * 25.0, 0, 35) * (mask / 255.0)
    
    shading = folds + grain + vignette
    for c in range(3):
        img[:, :, c] += shading
        
    # Background outside shirt (light studio gray)
    bg_color = np.array([215, 220, 225], dtype=np.float32)
    alpha = (mask / 255.0)[:, :, None]
    final_img = img * alpha + bg_color * (1.0 - alpha)
    final_img = np.clip(final_img, 0, 255).astype(np.uint8)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cv2.imwrite(output_path, final_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"[OK] Generated sample template: {output_path} ({w}x{h})")


def create_synthetic_design_png(output_path: str, size: tuple = (1600, 1600)):
    """Creates sample transparent PNG with intentional empty borders for auto-trim testing"""
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw centered badge inside padding
    cx, cy = w // 2, h // 2
    radius = 360
    
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], 
                 outline=(255, 107, 107, 255), width=24)
                 
    inner_r = radius - 50
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], 
                 fill=(46, 204, 113, 230))
                 
    star_r = inner_r - 70
    points = []
    for i in range(10):
        r = star_r if i % 2 == 0 else star_r * 0.45
        angle = i * np.pi / 5 - np.pi / 2
        px = cx + r * np.cos(angle)
        py = cy + r * np.sin(angle)
        points.append((px, py))
    draw.polygon(points, fill=(241, 196, 15, 255))
    
    # Typography
    try:
        font_large = ImageFont.truetype("arial.ttf", 68)
        font_small = ImageFont.truetype("arial.ttf", 44)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = font_large
        
    text_top = "RETRO ADVENTURE"
    text_bot = "AUTHENTIC APPAREL - 1984"
    
    draw.text((cx, cy - radius - 60), text_top, fill=(255, 255, 255, 255), 
              font=font_large, anchor="mm")
    draw.text((cx, cy + radius + 60), text_bot, fill=(243, 156, 18, 255), 
              font=font_small, anchor="mm")
              
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"[OK] Generated sample design: {output_path} ({w}x{h})")


if __name__ == "__main__":
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    tpl_file = os.path.join(assets_dir, "tshirt_template.jpg")
    dsg_file = os.path.join(assets_dir, "sample_design.png")
    
    create_synthetic_tshirt_template(tpl_file)
    create_synthetic_design_png(dsg_file)
