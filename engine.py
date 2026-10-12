"""
POD Photorealistic Mockup Engine (Crystal Clear Edition)
High-precision optical rendering engine simulating Photoshop Smart Object warping:
- Eliminates pixel degradation & edge noise using macro-structure fold filtering.
- Reconstructs smooth displacement gradient vectors with normalized Sobel operators.
- Premium Lanczos-4 interpolation preserving 100% vector-sharp graphics and fine typography.
- Multi-scale optical shading: dual-scale ambient crease shading for light fabrics & CLAHE relief for dark garments.
"""

import cv2
import numpy as np
from PIL import Image


def auto_trim_alpha(pil_img: Image.Image, alpha_threshold: int = 10):
    """
    Scans the Alpha channel to automatically trim 100% of redundant transparent borders.
    """
    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")
        
    alpha = np.array(pil_img.split()[-1])
    non_zero = np.where(alpha > alpha_threshold)
    
    if len(non_zero[0]) == 0 or len(non_zero[1]) == 0:
        return pil_img, (0, 0, pil_img.width, pil_img.height)
        
    min_y, max_y = int(np.min(non_zero[0])), int(np.max(non_zero[0]))
    min_x, max_x = int(np.min(non_zero[1])), int(np.max(non_zero[1]))
    
    # 2px anti-aliasing safety margin
    min_x = max(0, min_x - 2)
    min_y = max(0, min_y - 2)
    max_x = min(pil_img.width, max_x + 2)
    max_y = min(pil_img.height, max_y + 2)
    
    trimmed_img = pil_img.crop((min_x, min_y, max_x, max_y))
    return trimmed_img, (min_x, min_y, max_x - min_x, max_y - min_y)


def fit_design_to_box(design_bgra: np.ndarray, box_w: int, box_h: int, 
                       align: str = "top-center", top_margin_ratio: float = 0.05):
    """
    Fits design into the virtual bounding box while preserving original aspect ratio using Lanczos-4.
    """
    d_h, d_w = design_bgra.shape[:2]
    scale = min(box_w / max(d_w, 1), box_h / max(d_h, 1))
    new_w = max(1, int(d_w * scale))
    new_h = max(1, int(d_h * scale))
    
    resized = cv2.resize(design_bgra, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    canvas = np.zeros((box_h, box_w, 4), dtype=np.uint8)
    
    offset_x = (box_w - new_w) // 2
    offset_y = int(box_h * top_margin_ratio)
    if offset_y + new_h > box_h:
        offset_y = (box_h - new_h) // 2
        
    canvas[offset_y:offset_y+new_h, offset_x:offset_x+new_w] = resized
    return canvas


def render_realistic_mockup(template_bgr: np.ndarray, design_rgba_pil: Image.Image,
                            print_corners: list, displacement_strength: float = 6.0,
                            shadow_strength: float = 0.8, is_dark_fabric: bool = False):
    """
    Photorealistic optical rendering pipeline:
    - Extracts macro fabric wrinkles while eliminating high-frequency noise.
    - Preserves 100% HD clarity of the PNG artwork.
    - Accurately modulates ambient lighting and fold shadows.
    """
    h_tpl, w_tpl = template_bgr.shape[:2]
    
    # 1. Automatically trim redundant empty space from design
    trimmed_pil, bbox_info = auto_trim_alpha(design_rgba_pil)
    design_bgra = cv2.cvtColor(np.array(trimmed_pil), cv2.COLOR_RGBA2BGRA)
    
    # 2. Compute print area geometry
    pts_dst = np.float32(print_corners)
    tl, tr, br, bl = pts_dst
    
    flat_w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    flat_h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    flat_w = max(10, flat_w)
    flat_h = max(10, flat_h)
    
    flat_canvas = fit_design_to_box(design_bgra, flat_w, flat_h, align="top-center")
    
    # 3. 3D Perspective Transform
    pts_src = np.float32([
        [0, 0],
        [flat_w, 0],
        [flat_w, flat_h],
        [0, flat_h]
    ])
    matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)
    warped_design = cv2.warpPerspective(flat_canvas, matrix, (w_tpl, h_tpl), flags=cv2.INTER_LANCZOS4)
    
    # Baseline Flat Naive mockup for comparison
    flat_alpha = (warped_design[:, :, 3].astype(np.float32) / 255.0)[:, :, None]
    flat_bgr = warped_design[:, :, :3].astype(np.float32)
    base_f = template_bgr.astype(np.float32)
    naive_mockup = (base_f * (1.0 - flat_alpha) + flat_bgr * flat_alpha).astype(np.uint8)

    # 4. Macro Folds Extraction (Eliminates Grain Distortion)
    gray_tpl = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    
    mask_print_area = np.zeros((h_tpl, w_tpl), dtype=np.uint8)
    cv2.fillPoly(mask_print_area, [pts_dst.astype(np.int32)], 255)
    
    is_dark = bool(is_dark_fabric)

    if is_dark:
        clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(10, 10))
        base_gray = clahe.apply(gray_tpl)
    else:
        base_gray = gray_tpl

    # Smooth filter to extract real macro fabric folds
    smooth_folds = cv2.GaussianBlur(base_gray, (21, 21), 0)
    
    # Sobel gradient calculation
    grad_x = cv2.Sobel(smooth_folds, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(smooth_folds, cv2.CV_32F, 0, 1, ksize=3)
    
    # Normalize gradients to [-1.0, 1.0]
    roi_gx = np.abs(grad_x[mask_print_area > 0])
    roi_gy = np.abs(grad_y[mask_print_area > 0])
    scale_gx = max(float(np.percentile(roi_gx, 98)) if len(roi_gx) > 0 else 1.0, 8.0)
    scale_gy = max(float(np.percentile(roi_gy, 98)) if len(roi_gy) > 0 else 1.0, 8.0)
    
    norm_gx = np.clip(grad_x / scale_gx, -1.0, 1.0)
    norm_gy = np.clip(grad_y / scale_gy, -1.0, 1.0)
    
    # Coordinate grid
    grid_y, grid_x = np.indices((h_tpl, w_tpl), dtype=np.float32)
    
    # Pixel displacement mapping
    actual_shift = float(displacement_strength)
    map_x = grid_x + norm_gx * actual_shift
    map_y = grid_y + norm_gy * actual_shift
    
    # Remap with Lanczos-4 interpolation for maximum edge clarity
    displaced_design = cv2.remap(warped_design, map_x, map_y, 
                                 interpolation=cv2.INTER_LANCZOS4, 
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

    # 5. Photorealistic Optical Shadow & Lighting Blend
    disp_rgb = displaced_design[:, :, :3].astype(np.float32)
    disp_alpha = (displaced_design[:, :, 3].astype(np.float32) / 255.0)[:, :, None]

    if not is_dark:
        # LIGHT / WHITE / COLOR FABRIC: Multi-scale crease contrast
        fabric_smooth = cv2.GaussianBlur(gray_tpl, (11, 11), 0).astype(np.float32) / 255.0
        bg_ambient = cv2.GaussianBlur(gray_tpl, (51, 51), 0).astype(np.float32) / 255.0
        bg_ambient = np.maximum(bg_ambient, 0.05)
        
        crease_ratio = fabric_smooth / bg_ambient
        torso_mean = max(float(np.mean(bg_ambient[mask_print_area > 0])) if np.any(mask_print_area > 0) else 0.8, 0.1)
        ambient_ratio = bg_ambient / torso_mean
        
        shadow_effect = (1.0 - crease_ratio) * 1.8 + (1.0 - ambient_ratio) * 0.8
        shadow_mult = np.clip(1.0 - shadow_effect * float(shadow_strength), 0.20, 1.30)[:, :, None]
        ink_layer = disp_rgb * shadow_mult
    else:
        # DARK / BLACK FABRIC: Topographical CLAHE relief (DTG Underbase Simulation)
        clahe_light = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        dark_enhanced = clahe_light.apply(gray_tpl).astype(np.float32) / 255.0
        
        smooth_wrinkles = cv2.GaussianBlur(dark_enhanced, (11, 11), 0)
        bg_dark = cv2.GaussianBlur(dark_enhanced, (51, 51), 0)
        relief = smooth_wrinkles - bg_dark
        
        dark_shadow_mult = np.clip(1.0 + relief * 2.8 * float(shadow_strength), 0.25, 1.50)[:, :, None]
        ink_layer = disp_rgb * dark_shadow_mult

    # Alpha composition
    final_float = base_f * (1.0 - disp_alpha) + ink_layer * disp_alpha
    realistic_mockup = np.clip(final_float, 0, 255).astype(np.uint8)

    disp_vis = cv2.normalize(norm_gx, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    active_mult = shadow_mult if not is_dark else dark_shadow_mult
    shadow_vis = np.clip(255.0 * active_mult[:, :, 0] / 1.3, 0, 255).astype(np.uint8)

    return {
        "realistic": realistic_mockup,
        "naive_flat": naive_mockup,
        "trimmed_design": cv2.cvtColor(np.array(trimmed_pil), cv2.COLOR_RGBA2BGRA),
        "displacement_map": disp_vis,
        "shadow_map": shadow_vis,
        "bbox": bbox_info,
        "is_dark": is_dark
    }
