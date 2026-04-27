"""
Remove Gemini watermarks from generated images.

Detects and removes two common Gemini watermarks:
1. Top-left faint text (e.g. "BLUEPRINT_AESTHETIC")
2. Bottom-right star/sparkle logo

Uses OpenCV inpainting with threshold-based mask detection.

Usage:
    python remove-watermark.py --target "path/to/visual_director/run-N"
    python remove-watermark.py --file "path/to/single/image.png"
    python remove-watermark.py --target "path/to/run-N" --skip-top-left
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def remove_watermark(img_path: Path, skip_top_left: bool = False) -> bool:
    """Remove Gemini watermarks from a single image. Returns True if processed."""
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"[WARN] Cannot read: {img_path}")
        return False

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = np.zeros((h, w), dtype=np.uint8)
    kernel = np.ones((5, 5), np.uint8)
    has_watermark = False

    # 1) Bottom-right star/sparkle logo
    # Scan bottom-right corner for bright pixels (logo is typically 60-100px)
    br_y1, br_y2 = max(0, h - 150), h
    br_x1, br_x2 = max(0, w - 180), w
    br_region = gray[br_y1:br_y2, br_x1:br_x2]
    _, br_mask = cv2.threshold(br_region, 50, 255, cv2.THRESH_BINARY)
    br_bright_count = np.count_nonzero(br_mask)

    # Only treat as watermark if there's a concentrated bright cluster (star shape)
    if 200 < br_bright_count < 15000:
        br_mask_dilated = cv2.dilate(br_mask, kernel, iterations=3)
        mask[br_y1:br_y2, br_x1:br_x2] = br_mask_dilated
        has_watermark = True

    # 2) Top-left faint text watermark
    if not skip_top_left:
        # The text is extremely faint (pixel values 12-25 on dark ~5-8 background)
        # Scan rows 90-170, cols 0-700 for threshold-based detection
        tl_y1, tl_y2 = 90, min(170, h)
        tl_x1, tl_x2 = 0, min(700, w)
        tl_region = gray[tl_y1:tl_y2, tl_x1:tl_x2]
        _, tl_mask = cv2.threshold(tl_region, 12, 255, cv2.THRESH_BINARY)
        tl_bright_count = np.count_nonzero(tl_mask)

        # Only if region has significant bright pixels (text present)
        if tl_bright_count > 500:
            tl_mask_dilated = cv2.dilate(tl_mask, kernel, iterations=2)
            mask[tl_y1:tl_y2, tl_x1:tl_x2] = tl_mask_dilated
            has_watermark = True

    if not has_watermark:
        print(f"[SKIP] No watermark detected: {img_path.name}")
        return False

    # Inpaint using Navier-Stokes method
    result = cv2.inpaint(img, mask, inpaintRadius=12, flags=cv2.INPAINT_NS)

    # Overwrite original file
    cv2.imwrite(str(img_path), result)
    removed = []
    if np.count_nonzero(mask[br_y1:br_y2, br_x1:br_x2]) > 0:
        removed.append("star-logo")
    if not skip_top_left and np.count_nonzero(mask[tl_y1:tl_y2, tl_x1:tl_x2]) > 0:
        removed.append("top-text")
    print(f"[OK] Removed {'+'.join(removed)}: {img_path.name}")
    return True


def process_directory(target: Path, skip_top_left: bool = False) -> int:
    """Process all images in scene-* and thumbnail/ directories. Returns count."""
    count = 0

    # Scene images
    for scene_dir in sorted(target.glob("scene-*")):
        if not scene_dir.is_dir():
            continue
        for img_file in scene_dir.iterdir():
            if img_file.suffix.lower() in IMAGE_EXTENSIONS:
                if remove_watermark(img_file, skip_top_left):
                    count += 1

    # Thumbnail images
    thumb_dir = target / "thumbnail"
    if thumb_dir.exists():
        for img_file in thumb_dir.iterdir():
            if img_file.suffix.lower() in IMAGE_EXTENSIONS:
                if remove_watermark(img_file, skip_top_left):
                    count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="Remove Gemini watermarks from images")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", help="Visual director run directory (processes all scene-*/thumbnail/ images)")
    group.add_argument("--file", help="Single image file path")
    parser.add_argument("--skip-top-left", action="store_true", help="Skip top-left text watermark detection")
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"[ERROR] File not found: {path}")
            sys.exit(1)
        success = remove_watermark(path, args.skip_top_left)
        sys.exit(0 if success else 1)
    else:
        target = Path(args.target)
        if not target.exists():
            print(f"[ERROR] Directory not found: {target}")
            sys.exit(1)
        count = process_directory(target, args.skip_top_left)
        print(f"\n[OK] Done. Processed {count} images.")


if __name__ == "__main__":
    main()
