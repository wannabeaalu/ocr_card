"""
scan_id.py
Lightweight CPU-only ID Card OCR Scanner using Webcam and RapidOCR.
"""

import sys
import time
import re
import cv2
import numpy as np
from rapidocr import RapidOCR

# Ensure line-buffered stdout for real-time terminal output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)



def extract_10_digit_uids(text: str) -> list[str]:
    """
    Detect any 10-digit number (\\b\\d{10}\\b) after stripping spaces and hyphens.
    Handles formats like:
      - '9876543210'
      - '9876 543 210'
      - '9876-543-210'
      - 'ID: 9876 543 210'
      - 'CARD 9876 543 210'
    """
    # 1. Direct check on stripped string
    stripped = re.sub(r'[\s\-]+', '', text)
    matches = re.findall(r'\b\d{10}\b', stripped)
    if not matches:
        matches = re.findall(r'(?<!\d)\d{10}(?!\d)', stripped)

    # 2. Token-by-token check for mixed alphanumeric lines
    if not matches:
        for tok in text.split():
            clean_tok = re.sub(r'[\s\-]+', '', tok)
            m = re.findall(r'\b\d{10}\b', clean_tok) or re.findall(r'(?<!\d)\d{10}(?!\d)', clean_tok)
            matches.extend(m)

    return list(dict.fromkeys(matches))


def get_guide_box_coords(w: int, h: int):
    """Calculate centered rectangular guide box (standard ID card aspect ratio ~ 1.586)."""
    target_ratio = 1.586  # Width to Height ratio of standard ID-1 card

    box_w = int(min(w * 0.65, 640))
    box_h = int(box_w / target_ratio)

    if box_h > h * 0.75:
        box_h = int(h * 0.75)
        box_w = int(box_h * target_ratio)

    x1 = (w - box_w) // 2
    y1 = (h - box_h) // 2
    x2 = x1 + box_w
    y2 = y1 + box_h
    return x1, y1, x2, y2


def draw_guide_box(frame, x1, y1, x2, y2):
    """Draw centered ID card guide box with corner accents."""
    # Guide box rectangle
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 215, 255), 2)

    # Corner brackets for clear visual framing
    corner_len = 24
    corner_color = (0, 255, 0)
    thickness = 4

    # Top-left
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), corner_color, thickness)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), corner_color, thickness)
    # Top-right
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), corner_color, thickness)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), corner_color, thickness)
    # Bottom-left
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), corner_color, thickness)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), corner_color, thickness)
    # Bottom-right
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), corner_color, thickness)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), corner_color, thickness)

    # Box guide tag
    cv2.putText(frame, "HOLD ID CARD INSIDE BOX", (x1 + 10, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 1, cv2.LINE_AA)


def draw_hud(frame, auto_scan: bool, last_infer_ms: float, matched_uids: list, total_detected: int):
    """Draw clean instructions bar and status banner."""
    h, w = frame.shape[:2]

    # Top instructions overlay
    top_overlay = frame.copy()
    cv2.rectangle(top_overlay, (0, 0), (w, 48), (25, 25, 25), -1)
    cv2.rectangle(top_overlay, (0, h - 45), (w, h), (25, 25, 25), -1)
    cv2.addWeighted(top_overlay, 0.8, frame, 0.2, 0, frame)

    # Instructions
    inst_text = "SPACE: Capture & OCR   |   A: Toggle Auto-Scan (every 1.5s)   |   Q: Quit"
    cv2.putText(frame, inst_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    # Auto-scan indicator badge
    auto_badge = "AUTO-SCAN: ON" if auto_scan else "AUTO-SCAN: OFF"
    auto_color = (0, 255, 0) if auto_scan else (160, 160, 160)
    (aw, _), _ = cv2.getTextSize(auto_badge, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    cv2.putText(frame, auto_badge, (w - aw - 15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, auto_color, 2, cv2.LINE_AA)

    # Bottom status bar
    status_msg = []
    if last_infer_ms > 0:
        status_msg.append(f"Inference: {last_infer_ms:.1f}ms (CPU)")
        status_msg.append(f"Lines: {total_detected}")

    if matched_uids:
        status_msg.append(f"10-DIGIT UID DETECTED: {', '.join(matched_uids)}")
        bot_color = (0, 255, 0)
    elif last_infer_ms > 0:
        status_msg.append("No 10-digit UID found")
        bot_color = (0, 200, 255)
    else:
        status_msg.append("Awaiting scan (Press SPACE or 'A' to start)")
        bot_color = (200, 200, 200)

    cv2.putText(frame, "   |   ".join(status_msg), (15, h - 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, bot_color, 2, cv2.LINE_AA)


def parse_ocr_output(ocr_output):
    """
    Standardize RapidOCR output across different version return types.
    Returns list of items: (box_pts, text, score)
    """
    items = []
    if ocr_output is None:
        return items

    # RapidOCR 3.x RapidOCROutput object
    if hasattr(ocr_output, 'txts') and hasattr(ocr_output, 'boxes'):
        boxes = ocr_output.boxes
        txts = ocr_output.txts
        scores = ocr_output.scores
        if txts is not None and boxes is not None:
            for i in range(len(txts)):
                box = boxes[i]
                text = str(txts[i]).strip()
                score = float(scores[i]) if (scores is not None and i < len(scores)) else 1.0
                items.append((box, text, score))
        return items

    # RapidOCR tuple/list format: (result_list, elapse)
    if isinstance(ocr_output, (list, tuple)):
        first_el = ocr_output[0]
        if isinstance(first_el, list):
            for row in first_el:
                if len(row) >= 3:
                    box = row[0]
                    text = str(row[1]).strip()
                    score = float(row[2])
                    items.append((box, text, score))
        return items

    return items


def main():
    print("=" * 65)
    print("Initializing CPU-only RapidOCR engine...")
    engine = RapidOCR()
    print("RapidOCR engine ready.")
    print("=" * 65)

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open default laptop webcam (device 0).")
        print("Please check that your webcam is connected and camera permissions are granted.")
        sys.exit(1)

    # Request 1280x720 resolution (fallback if unsupported)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Webcam active at resolution: {actual_w}x{actual_h}")
    print("\nControls:")
    print("  [SPACE] : Capture & OCR ID Card")
    print("  [A]     : Toggle Auto-Scan (every 1.5s)")
    print("  [Q/ESC] : Quit")
    print("=" * 65)

    window_name = "ID Card OCR Scanner (CPU-Only)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    auto_scan = False
    last_scan_time = 0.0
    auto_scan_interval = 1.5  # seconds

    # Persist last detection results on screen
    last_detections = []
    last_infer_ms = 0.0
    matched_uids_global = []

    def perform_ocr(crop_img, offset_x, offset_y):
        nonlocal last_detections, last_infer_ms, matched_uids_global

        t_start = time.perf_counter()
        raw_output = engine(crop_img)
        t_end = time.perf_counter()
        last_infer_ms = (t_end - t_start) * 1000.0

        items = parse_ocr_output(raw_output)
        detections = []
        matched_uids = []

        print(f"\n[{time.strftime('%H:%M:%S')}] OCR SCAN COMPLETED in {last_infer_ms:.1f} ms")
        if not items:
            print("  (No text detected)")
        else:
            for box_pts, text, score in items:
                uids = extract_10_digit_uids(text)
                is_uid = len(uids) > 0
                uid_str = uids[0] if is_uid else ""

                if is_uid:
                    matched_uids.extend(uids)
                    print(f"  [>>> MATCHED 10-DIGIT UID: {uid_str} <<<] (Confidence: {score:.2f}) | Raw: '{text}'")
                else:
                    print(f"  [Text] '{text}' (Confidence: {score:.2f})")

                # Shift coordinates from crop to full frame
                pts = np.array([[int(pt[0] + offset_x), int(pt[1] + offset_y)] for pt in box_pts], dtype=np.int32)
                detections.append({
                    'pts': pts,
                    'text': text,
                    'score': score,
                    'is_uid': is_uid,
                    'uid': uid_str
                })

        last_detections = detections
        matched_uids_global = list(dict.fromkeys(matched_uids))
        if matched_uids_global:
            print(f"  ==> Summary Matched UID(s): {', '.join(matched_uids_global)}")
        print("-" * 65)

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Warning: Failed to read frame from webcam.")
                break

            h, w = frame.shape[:2]
            x1, y1, x2, y2 = get_guide_box_coords(w, h)

            # Auto-Scan timer logic
            current_time = time.time()
            trigger_scan = False
            if auto_scan and (current_time - last_scan_time >= auto_scan_interval):
                trigger_scan = True
                last_scan_time = current_time

            # Keyboard events
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q') or key == 27:  # 'q' or ESC
                print("Quit requested. Closing scanner...")
                break
            elif key == ord(' '):  # SPACE
                trigger_scan = True
            elif key == ord('a') or key == ord('A'):  # Toggle auto-scan
                auto_scan = not auto_scan
                status_str = "ENABLED (every 1.5s)" if auto_scan else "DISABLED"
                print(f"[Auto-Scan] {status_str}")
                if auto_scan:
                    trigger_scan = True
                    last_scan_time = current_time

            # Trigger OCR
            if trigger_scan:
                crop = frame[y1:y2, x1:x2]
                if crop.size > 0:
                    perform_ocr(crop, x1, y1)

            # Clone frame for UI display
            display_frame = frame.copy()

            # 1. Draw centered ID guide box
            draw_guide_box(display_frame, x1, y1, x2, y2)

            # 2. Draw bounding boxes and text overlays for detected lines
            for det in last_detections:
                pts = det['pts']
                text = det['text']
                score = det['score']
                is_uid = det['is_uid']

                if is_uid:
                    # Highlighted 10-digit UID in bright green
                    box_color = (0, 255, 0)
                    thickness = 3
                    tag_text = f"UID: {det['uid']} ({score:.2f})"
                    tag_bg_color = (0, 150, 0)
                    tag_fg_color = (255, 255, 255)
                    font_scale = 0.65
                    font_thick = 2
                else:
                    # Regular text in bright cyan/yellow
                    box_color = (0, 215, 255)
                    thickness = 1
                    tag_text = f"{text} ({score:.2f})"
                    tag_bg_color = (30, 30, 30)
                    tag_fg_color = (255, 255, 255)
                    font_scale = 0.5
                    font_thick = 1

                # Draw bounding polygon around text
                cv2.polylines(display_frame, [pts], isClosed=True, color=box_color, thickness=thickness)

                # Label tag
                min_x = int(np.min(pts[:, 0]))
                min_y = int(np.min(pts[:, 1]))
                label_x = max(min_x, 5)
                label_y = max(min_y - 6, 22)

                (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)
                cv2.rectangle(display_frame, (label_x - 3, label_y - th - 4), (label_x + tw + 3, label_y + 3), tag_bg_color, -1)
                cv2.putText(display_frame, tag_text, (label_x, label_y),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, tag_fg_color, font_thick, cv2.LINE_AA)

            # 3. Draw HUD (instructions and status bar)
            draw_hud(display_frame, auto_scan, last_infer_ms, matched_uids_global, len(last_detections))

            # 4. Show live window
            cv2.imshow(window_name, display_frame)

            # Check if window was closed via titlebar 'X'
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("Window closed by user.")
                break

    except KeyboardInterrupt:
        print("\nExiting by user interrupt...")
    except Exception as exc:
        print(f"Error during runtime: {exc}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released. OpenCV windows closed cleanly.")


if __name__ == "__main__":
    main()
