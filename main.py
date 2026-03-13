import sys
import logging
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

INPUT_DIR = Path("/app/input")
OUTPUT_DIR = Path("/app/output")

# Colours (BGR for OpenCV)
BOX_COLOR = (0, 200, 0)       # green rectangle
TEXT_COLOR = (255, 255, 255)  # white label text
TEXT_BG_COLOR = (0, 140, 0)  # dark-green label background
BOX_THICKNESS = 2
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.45
FONT_THICKNESS = 1
MIN_CONF = 40  # discard detections below this confidence (0-100)

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def annotate_image(image_path: Path) -> Path:
    """Run OCR on *image_path*, draw bounding boxes for every word, return output path."""

    # --- load with PIL first so pytesseract gets consistent input ---
    pil_img = Image.open(image_path).convert("RGB")
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # --- OCR with full data (bounding boxes + confidence) ---
    data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)

    n_boxes = len(data["text"])
    drawn = 0
    for i in range(n_boxes):
        word = data["text"][i].strip()
        conf = int(data["conf"][i])
        if not word or conf < MIN_CONF:
            continue

        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]

        # bounding box
        cv2.rectangle(img, (x, y), (x + w, y + h), BOX_COLOR, BOX_THICKNESS)

        # label above the box
        label = f"{word} ({conf}%)"
        (lw, lh), baseline = cv2.getTextSize(label, FONT, FONT_SCALE, FONT_THICKNESS)
        label_y = max(y - 4, lh + 4)
        cv2.rectangle(
            img,
            (x, label_y - lh - baseline),
            (x + lw, label_y + baseline),
            TEXT_BG_COLOR,
            cv2.FILLED,
        )
        cv2.putText(img, label, (x, label_y - baseline), FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)
        drawn += 1

    log.info("  %s → %d word(s) annotated", image_path.name, drawn)

    # --- save ---
    out_path = OUTPUT_DIR / f"{image_path.stem}_annotated{image_path.suffix}"
    cv2.imwrite(str(out_path), img)
    return out_path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    images = [p for p in INPUT_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not images:
        log.warning("No supported images found in %s", INPUT_DIR)
        log.warning("Supported formats: %s", ", ".join(sorted(SUPPORTED_EXTENSIONS)))
        return

    log.info("Found %d image(s) to process.", len(images))
    for img_path in sorted(images):
        log.info("Processing: %s", img_path.name)
        try:
            out = annotate_image(img_path)
            log.info("  Saved → %s", out)
        except Exception as exc:
            log.error("  Failed to process %s: %s", img_path.name, exc)

    log.info("Done. Results are in %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
