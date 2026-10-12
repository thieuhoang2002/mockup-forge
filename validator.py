"""
Pre-flight Validator & Image Sanitizer
Automatically validates, sanitizes, and normalizes user design & template inputs to RGBA.
"""

import os
from PIL import Image
import numpy as np


class MockupValidator:
    @staticmethod
    def validate_and_convert_design(input_path: str, save_path: str = None):
        """
        Validate and standardize design file:
        - Automatically converts any mode (RGBA, RGB, P, LA, CMYK) to standard RGBA.
        - Computes real dimension specs and colored pixel coverage.
        """
        if not os.path.exists(input_path):
            return False, f"File not found: {input_path}", None
            
        try:
            with Image.open(input_path) as raw_img:
                w, h = raw_img.size
                orig_mode = raw_img.mode
                
                # Standardize to RGBA
                if raw_img.mode != "RGBA":
                    converted = raw_img.convert("RGBA")
                else:
                    converted = raw_img.copy()

            out_file = save_path if save_path else input_path
            converted.save(out_file, "PNG")

            # Calculate actual colored pixel coverage
            alpha = np.array(converted.split()[-1])
            colored_pixels = int(np.count_nonzero(alpha > 10))
            coverage_pct = round((colored_pixels / max(w * h, 1)) * 100, 2)

            info = {
                "width": w,
                "height": h,
                "original_mode": orig_mode,
                "mode": "RGBA",
                "colored_pixels": colored_pixels,
                "coverage_percent": coverage_pct,
                "has_transparency": (colored_pixels < w * h)
            }
            return True, info, out_file

        except Exception as e:
            return False, f"Error reading image file: {str(e)}", None

    @staticmethod
    def validate_template_spec(template_img_path: str, print_corners: list):
        """Validate template image and 4-point print area coordinates"""
        if not os.path.exists(template_img_path):
            return False, f"Template file not found: {template_img_path}"
            
        if len(print_corners) != 4:
            return False, "Print area requires exactly 4 corner coordinates!"
            
        try:
            with Image.open(template_img_path) as img:
                w, h = img.size
                
            pts = np.array(print_corners, dtype=np.float32)
            for i, (x, y) in enumerate(pts):
                if x < 0 or x > w or y < 0 or y > h:
                    return False, f"Point {i+1} ({int(x)}, {int(y)}) is out of template bounds ({w}x{h})!"
                    
            return True, {
                "template_size": (w, h),
                "print_corners": print_corners
            }
        except Exception as e:
            return False, f"Template validation error: {str(e)}"
