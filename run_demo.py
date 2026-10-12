"""
POD Photorealistic Mockup Demo Runner
Executes complete pipeline from validation to side-by-side comparison output.
"""

import os
import sys
import json
import cv2
import numpy as np
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from engine import render_realistic_mockup, auto_trim_alpha
from validator import MockupValidator


def create_side_by_side(naive_img: np.ndarray, realistic_img: np.ndarray, label_height: int = 60):
    """Creates side-by-side comparison: Flat Naive vs Photorealistic"""
    h, w = naive_img.shape[:2]
    combined = np.zeros((h + label_height, w * 2, 3), dtype=np.uint8)
    
    combined[label_height:, :w] = naive_img
    combined[label_height:, w:] = realistic_img
    
    combined[:label_height, :] = (40, 44, 52)
    
    cv2.putText(combined, "TRADITIONAL: Flat Naive Overlay", 
                (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (160, 160, 255), 2, cv2.LINE_AA)
    cv2.putText(combined, "OPTICAL ENGINE: Wrinkle Warp + Shadows", 
                (w + 30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (120, 255, 150), 2, cv2.LINE_AA)
    
    cv2.line(combined, (w, 0), (w, h + label_height), (255, 255, 255), 2)
    return combined


def create_html_viewer(output_dir: str):
    """Creates interactive HTML comparison slider"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mockup Engine - Before & After Comparison</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; text-align: center; }
        .container { max-width: 900px; margin: 0 auto; position: relative; overflow: hidden; border-radius: 12px; }
        .img-comp-container { position: relative; height: 1050px; }
        .img-comp-img { position: absolute; width: 100%; height: 100%; overflow: hidden; }
        .img-comp-img img { width: 100%; height: 100%; object-fit: contain; }
        .img-comp-slider { position: absolute; z-index: 9; cursor: ew-resize; width: 40px; height: 40px; background: #38bdf8; opacity: 0.9; border-radius: 50%; top: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #000; }
        .badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 13px; margin: 10px; }
        .badge-before { background: #ef4444; }
        .badge-after { background: #10b981; }
    </style>
</head>
<body>
    <h1>POD Mockup Engine - Visual Comparison</h1>
    <div>
        <span class="badge badge-before">LEFT: Flat Naive</span>
        <span class="badge badge-after">RIGHT: Photorealistic Optical Engine</span>
    </div>
    <div class="container">
        <div class="img-comp-container" id="compBox">
            <div class="img-comp-img"><img src="05_naive_flat_mockup.jpg" alt="Flat"></div>
            <div class="img-comp-img" id="overlayBox" style="width: 50%; border-right: 3px solid #38bdf8;"><img src="06_photorealistic_mockup.jpg" alt="Realistic"></div>
        </div>
    </div>
</body>
</html>"""
    with open(os.path.join(output_dir, "viewer.html"), "w", encoding="utf-8") as f:
        f.write(html_content)


def run_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    tpl_path = os.path.join(assets_dir, "tshirt_template.jpg")
    dsg_path = os.path.join(assets_dir, "sample_design.png")
    cfg_path = os.path.join(assets_dir, "templates.json")
    
    with open(cfg_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    corners = config["tshirt_cream_front"]["print_corners"]
    
    # 1. Validation
    is_valid, info, _ = MockupValidator.validate_and_convert_design(dsg_path)
    if not is_valid:
        print(f"[ERROR] Design invalid: {info}")
        return
        
    tpl_valid, tpl_info = MockupValidator.validate_template_spec(tpl_path, corners)
    if not tpl_valid:
        print(f"[ERROR] Template invalid: {tpl_info}")
        return
        
    template_bgr = cv2.imread(tpl_path)
    design_pil = Image.open(dsg_path)
    
    # 2. Rendering
    results = render_realistic_mockup(
        template_bgr=template_bgr,
        design_rgba_pil=design_pil,
        print_corners=corners,
        displacement_strength=6.0,
        shadow_strength=0.85,
        is_dark_fabric=False
    )
    
    # 3. Export outputs
    cv2.imwrite(os.path.join(output_dir, "03_displacement_map.png"), results["displacement_map"])
    cv2.imwrite(os.path.join(output_dir, "04_shadow_map.png"), results["shadow_map"])
    cv2.imwrite(os.path.join(output_dir, "05_naive_flat_mockup.jpg"), results["naive_flat"])
    cv2.imwrite(os.path.join(output_dir, "06_photorealistic_mockup.jpg"), results["realistic"])
    
    sbs = create_side_by_side(results["naive_flat"], results["realistic"])
    cv2.imwrite(os.path.join(output_dir, "07_side_by_side_comparison.jpg"), sbs)
    create_html_viewer(output_dir)
    print(f"[SUCCESS] Demo pipeline complete. Outputs saved to: {output_dir}")


if __name__ == "__main__":
    run_pipeline()
