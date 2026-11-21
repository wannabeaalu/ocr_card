# User Guide: ID Card OCR Scanner

This guide walks you through using the **ID Card OCR Scanner**, providing tips for best accuracy, understanding the UI, and troubleshooting common webcam scanning issues.

---

## 1. Starting the Application

Ensure your `id-ocr` Conda environment is active, then launch `scan_id.py`:

```powershell
conda activate id-ocr
python scan_id.py
```

Or run directly in one line:
```powershell
conda run -n id-ocr python scan_id.py
```

A live video feed titled **`ID Card OCR Scanner (CPU-Only)`** will appear on your screen.

---

## 2. On-Screen Interface Walkthrough

```text
+-----------------------------------------------------------------------+
| SPACE: Capture & OCR   |   A: Toggle Auto-Scan (every 1.5s)   |   Q: Quit   [AUTO: OFF] |  <-- Top HUD
+-----------------------------------------------------------------------+
|                                                                       |
|                     ┌───────────────────────────┐                     |
|                     │ HOLD ID CARD INSIDE BOX   │                     |
|                     │                           │                     |
|                     │   [ Your ID Card Area ]   │                     |
|                     │                           │                     |
|                     └───────────────────────────┘                     |
|                                                                       |
+-----------------------------------------------------------------------+
| Inference: 118.4ms (CPU)   |   Lines: 6   |   10-DIGIT UID DETECTED: 9876543210        |  <-- Bottom HUD
+-----------------------------------------------------------------------+
```

### Key UI Elements:
1. **Top Instructions Banner:** Shows the keyboard shortcuts and the current state of Auto-Scan (`AUTO-SCAN: ON` in green or `AUTO-SCAN: OFF` in gray).
2. **Central Guide Box:** A highlighted rectangle framed with green corner marks. Its aspect ratio matches standard ID-1 card dimensions (~1.586).
3. **Bounding Boxes & Tags:**
   - **Bright Green Box:** Highlights any text line containing a matched 10-digit UID, tagged with `UID: <number> (<confidence>)`.
   - **Cyan/Yellow Box:** Marks standard detected text lines with their confidence score (e.g. `0.95`).
4. **Bottom Status Bar:** Shows CPU inference latency in milliseconds, number of detected text lines, and a summary list of all detected UIDs.

---

## 3. Scanning Modes

### Manual Scan (Recommended for Best Focus)
1. Hold your ID card inside the central guide box.
2. Ensure the text is sharp and readable.
3. Press **`SPACE`**.
4. The scanner freezes the current frame's text detections on screen and prints detailed scores to your terminal.

### Auto-Scan Mode (Hands-Free Testing)
1. Press **`A`** to enable continuous scanning.
2. The indicator in the top right will change to `AUTO-SCAN: ON`.
3. The app will automatically run OCR every **1.5 seconds**, updating the bounding boxes and terminal output in real time.
4. Press **`A`** again to toggle Auto-Scan off.

---

## 4. Tips for Maximum OCR Accuracy

Laminated plastic ID cards and laptop webcams can present optical challenges. Follow these tips for high confidence scores:

| Challenge | Solution |
|---|---|
| **Glare & Reflection** | Plastic cards reflect overhead LED/fluorescent lighting. **Tilt the card 5° to 10°** relative to the camera to bounce glare away from the lens. |
| **Blur / Out-of-Focus** | Many laptop webcams have a fixed focal length. Keep the card roughly **15 cm to 25 cm (6 to 10 inches)** from the camera lens. |
| **Framing** | Fill the guide box as much as possible without letting card corners spill outside the border. |
| **Lighting** | Ensure your face/card is front-lit rather than backlit. Avoid strong window light directly behind you. |

---

## 5. UID Detection Format

The scanner looks for 10-digit identification numbers (common on national ID cards, employee badges, student IDs, and tax IDs).

The regex engine:
- Strips any whitespace and hyphens within lines.
- Matches strict 10-digit patterns: `\b\d{10}\b` (or `(?<!\d)\d{10}(?!\d)`).
- Valid examples recognized:
  - `9876543210`
  - `9876 543 210`
  - `9876-543-210`
  - `ID NO: 9876 543 210`
  - `UID: 9876-543-210`

---

## 6. Troubleshooting

### Webcam Error: `Could not open webcam (device 0)`
- **Check Privacy Settings:** On Windows, open **Settings > Privacy & Security > Camera** and make sure "Let desktop apps access your camera" is **On**.
- **External Webcams:** If using an external USB webcam, it may be assigned to device index `1`. In `scan_id.py`, change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`.

### Low Resolution or Lag
- The application requests `1280x720` resolution. If your webcam hardware does not support 720p, it will automatically fall back to its native default (typically 640x480) without crashing.
