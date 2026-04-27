"""
Copy images from Downloads directory to video-maker scene directories.

Sorts images by modification time (oldest first) and maps them to scene
numbers in ascending order. Remaining images are assigned to thumbnail
(main first, then alt).

Usage:
    python copy-images-from-downloads.py \
        --source "C:/Users/Administrator/Downloads" \
        --target "path/to/visual_director/run-N" \
        --scenes 03,05,07,11 \
        --include-thumbnail \
        --prefix "Gemini_Generated_Image" \
        --after "2026-03-22 09:00"
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def get_images_sorted_by_time(
    source: Path,
    prefix: str | None = None,
    after: datetime | None = None,
) -> list[Path]:
    """Get image files sorted by modification time (oldest first)."""
    images = []
    for f in source.iterdir():
        if not f.is_file() or f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if prefix and not f.stem.startswith(prefix):
            continue
        if after and datetime.fromtimestamp(f.stat().st_mtime) < after:
            continue
        images.append(f)
    images.sort(key=lambda f: f.stat().st_mtime)
    return images


def main():
    parser = argparse.ArgumentParser(description="Copy images from Downloads to scene dirs")
    parser.add_argument("--source", required=True, help="Source directory (e.g. Downloads)")
    parser.add_argument("--target", required=True, help="Target visual_director run dir")
    parser.add_argument("--scenes", required=True, help="Comma-separated narration scene numbers (e.g. 03,05,07)")
    parser.add_argument("--include-thumbnail", action="store_true", help="Also copy thumbnail images")
    parser.add_argument("--prefix", default=None, help="Only include files whose name starts with this prefix (e.g. Gemini_Generated_Image)")
    parser.add_argument("--after", default=None, help="Only include files modified after this time (e.g. '2026-03-22 09:00')")
    args = parser.parse_args()

    source = Path(args.source)
    target = Path(args.target)
    scene_nums = [s.strip() for s in args.scenes.split(",") if s.strip()]

    after_dt = None
    if args.after:
        try:
            after_dt = datetime.strptime(args.after, "%Y-%m-%d %H:%M")
        except ValueError:
            after_dt = datetime.strptime(args.after, "%Y-%m-%d")

    if not source.exists():
        print(f"[ERROR] Source directory not found: {source}")
        sys.exit(1)

    images = get_images_sorted_by_time(source, prefix=args.prefix, after=after_dt)
    if not images:
        print(f"[ERROR] No image files found in {source}")
        sys.exit(1)

    needed = len(scene_nums) + (2 if args.include_thumbnail else 0)
    print(f"[INFO] Found {len(images)} images in {source}")
    print(f"[INFO] Need {needed} images ({len(scene_nums)} scenes{' + 2 thumbnails' if args.include_thumbnail else ''})")

    # When --include-thumbnail, last 2 images are thumbnails (alt_bg, then bg)
    # Split images into scene pool and thumbnail pool
    if args.include_thumbnail and len(images) >= 2:
        scene_images = images[:-2]
        thumb_alt_img = images[-2]
        thumb_bg_img = images[-1]
    else:
        scene_images = images
        thumb_alt_img = None
        thumb_bg_img = None

    if len(scene_images) < len(scene_nums):
        print(f"[WARN] Only {len(scene_images)} scene images for {len(scene_nums)} scenes")

    idx = 0

    # Copy scene images (first N images → scenes in order)
    for scene_num in scene_nums:
        if idx >= len(scene_images):
            print(f"[WARN] No image left for scene-{scene_num}, skipping")
            continue
        scene_dir = target / f"scene-{scene_num}"
        scene_dir.mkdir(parents=True, exist_ok=True)
        dest = scene_dir / "image.png"
        shutil.copy2(scene_images[idx], dest)
        print(f"[OK] {scene_images[idx].name} -> scene-{scene_num}/image.png")
        idx += 1

    # Copy thumbnail images (last 2: [-2]=alt_bg, [-1]=bg)
    if args.include_thumbnail:
        thumb_dir = target / "thumbnail"
        thumb_dir.mkdir(parents=True, exist_ok=True)

        if thumb_alt_img:
            dest = thumb_dir / "thumbnail_alt_bg.png"
            shutil.copy2(thumb_alt_img, dest)
            print(f"[OK] {thumb_alt_img.name} -> thumbnail/thumbnail_alt_bg.png")
        else:
            print("[WARN] No image for thumbnail_alt_bg.png")

        if thumb_bg_img:
            dest = thumb_dir / "thumbnail_bg.png"
            shutil.copy2(thumb_bg_img, dest)
            print(f"[OK] {thumb_bg_img.name} -> thumbnail/thumbnail_bg.png")
        else:
            print("[WARN] No image for thumbnail_bg.png")

    copied = idx + (1 if thumb_alt_img else 0) + (1 if thumb_bg_img else 0)
    unused = len(images) - needed if len(images) > needed else 0
    if unused > 0:
        print(f"[INFO] {unused} unused images remaining in {source}")

    print(f"\n[OK] Done. Copied {copied} images.")


if __name__ == "__main__":
    main()
