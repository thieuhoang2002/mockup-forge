"""
Flask Web Studio Backend for Photorealistic POD Mockup Engine
Supports real-time preview, corner adjustments, and 1-click Etsy export.
"""

import os
import uuid
import base64
from flask import Flask, render_template, request, jsonify, send_file
import cv2
import numpy as np
from PIL import Image

from engine import render_realistic_mockup
from validator import MockupValidator

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload_template", methods=["POST"])
def upload_template():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No template file selected!"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename!"}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        return jsonify({"success": False, "error": "Supported formats: JPG, PNG, WEBP!"}), 400
        
    filename = f"tpl_{uuid.uuid4().hex[:8]}{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)
    
    with Image.open(save_path) as img:
        w, h = img.size
        
    default_corners = [
        [int(w * 0.32), int(h * 0.25)],
        [int(w * 0.68), int(h * 0.25)],
        [int(w * 0.68), int(h * 0.65)],
        [int(w * 0.32), int(h * 0.65)]
    ]
    
    return jsonify({
        "success": True,
        "filename": filename,
        "original_name": file.filename,
        "width": w,
        "height": h,
        "default_corners": default_corners
    })


@app.route("/api/upload_design", methods=["POST"])
def upload_design():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No PNG design file selected!"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename!"}), 400
        
    filename = f"dsg_{uuid.uuid4().hex[:8]}.png"
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)
    
    # Auto-validate and sanitize to standard RGBA
    is_valid, info, final_path = MockupValidator.validate_and_convert_design(save_path, save_path)
    if not is_valid:
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"success": False, "error": info}), 400
        
    return jsonify({
        "success": True,
        "filename": filename,
        "original_name": file.filename,
        "width": info["width"],
        "height": info["height"],
        "coverage_percent": info["coverage_percent"],
        "mode": info["mode"]
    })


@app.route("/api/load_default_assets", methods=["GET"])
def load_default_assets():
    sample_tpl = os.path.join(BASE_DIR, "assets", "tshirt_template.jpg")
    sample_dsg = os.path.join(BASE_DIR, "assets", "sample_design.png")
    
    tpl_name = f"tpl_default_{uuid.uuid4().hex[:6]}.jpg"
    dsg_name = f"dsg_default_{uuid.uuid4().hex[:6]}.png"
    
    import shutil
    shutil.copy(sample_tpl, os.path.join(UPLOAD_DIR, tpl_name))
    shutil.copy(sample_dsg, os.path.join(UPLOAD_DIR, dsg_name))
    
    with Image.open(sample_tpl) as img:
        tw, th = img.size
    with Image.open(sample_dsg) as img:
        dw, dh = img.size
        
    return jsonify({
        "success": True,
        "template_filename": tpl_name,
        "design_filename": dsg_name,
        "template_width": tw,
        "template_height": th,
        "design_width": dw,
        "design_height": dh,
        "default_corners": [
            [420, 360],
            [780, 370],
            [770, 840],
            [430, 830]
        ]
    })


@app.route("/api/get_image/<filename>", methods=["GET"])
def get_image(filename):
    safe_path = os.path.join(UPLOAD_DIR, os.path.basename(filename))
    if os.path.exists(safe_path):
        return send_file(safe_path)
    return "Not Found", 404


@app.route("/api/download_etsy/<filename>", methods=["GET"])
def download_etsy(filename):
    """Exports mockup adhering strictly to Etsy standards (2700x2025px 4:3 or 2000x2000px 1:1)"""
    ratio = request.args.get("ratio", "4_3")
    safe_path = os.path.join(UPLOAD_DIR, os.path.basename(filename))
    if not os.path.exists(safe_path):
        return "Not Found", 404
        
    img = cv2.imread(safe_path)
    h, w = img.shape[:2]
    
    if ratio == "4_3":
        target_w, target_h = 2700, 2025  # Etsy Gold Standard 4:3
    elif ratio == "1_1":
        target_w, target_h = 2000, 2000  # Etsy Square 1:1
    else:
        return send_file(safe_path, as_attachment=True, download_name=f"mockup_{filename}")
        
    scale = max(target_w / w, target_h / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    
    x1 = (nw - target_w) // 2
    y1 = (nh - target_h) // 2
    cropped = resized[y1:y1+target_h, x1:x1+target_w]
    
    out_name = f"etsy_{ratio}_{filename}"
    out_path = os.path.join(UPLOAD_DIR, out_name)
    cv2.imwrite(out_path, cropped, [cv2.IMWRITE_JPEG_QUALITY, 96])
    return send_file(out_path, as_attachment=True, download_name=out_name)


@app.route("/api/render_live", methods=["POST"])
def render_live():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Missing payload data!"}), 400
        
    tpl_file = os.path.join(UPLOAD_DIR, os.path.basename(data.get("template_filename", "")))
    dsg_file = os.path.join(UPLOAD_DIR, os.path.basename(data.get("design_filename", "")))
    corners = data.get("corners", [])
    
    if not os.path.exists(tpl_file) or not os.path.exists(dsg_file):
        return jsonify({"success": False, "error": "Template or design file not found!"}), 404
        
    if len(corners) != 4:
        return jsonify({"success": False, "error": "Requires exactly 4 corner coordinates!"}), 400

    displacement = float(data.get("displacement_strength", 6.0))
    shadow_strength = float(data.get("shadow_strength", 0.80))
    is_dark = bool(data.get("is_dark_fabric", False))

    import time
    t0 = time.time()
    
    template_bgr = cv2.imread(tpl_file)
    design_pil = Image.open(dsg_file).convert("RGBA")
    
    try:
        results = render_realistic_mockup(
            template_bgr=template_bgr,
            design_rgba_pil=design_pil,
            print_corners=corners,
            displacement_strength=displacement,
            shadow_strength=shadow_strength,
            is_dark_fabric=is_dark
        )
        
        elapsed_ms = int((time.time() - t0) * 1000)

        _, buf_real = cv2.imencode(".jpg", results["realistic"], [cv2.IMWRITE_JPEG_QUALITY, 92])
        b64_real = base64.b64encode(buf_real).decode("utf-8")

        _, buf_flat = cv2.imencode(".jpg", results["naive_flat"], [cv2.IMWRITE_JPEG_QUALITY, 92])
        b64_flat = base64.b64encode(buf_flat).decode("utf-8")

        out_id = uuid.uuid4().hex[:10]
        out_path = os.path.join(UPLOAD_DIR, f"result_{out_id}.jpg")
        cv2.imwrite(out_path, results["realistic"], [cv2.IMWRITE_JPEG_QUALITY, 98])

        bbox_safe = [int(v) for v in results["bbox"]] if results.get("bbox") else [0, 0, 0, 0]
        is_dark_safe = bool(results.get("is_dark", False))

        return jsonify({
            "success": True,
            "elapsed_ms": elapsed_ms,
            "realistic_base64": f"data:image/jpeg;base64,{b64_real}",
            "flat_base64": f"data:image/jpeg;base64,{b64_flat}",
            "download_id": f"result_{out_id}.jpg",
            "bbox": bbox_safe,
            "is_dark": is_dark_safe
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
