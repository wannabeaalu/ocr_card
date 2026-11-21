# CPU-Only ID Card OCR Scanner

A lightweight, real-time Python desktop application that uses your laptop webcam to perform CPU-only Optical Character Recognition (OCR) on ID cards. Powered by **RapidOCR** and **ONNXRuntime**, it features automatic 10-digit ID/UID detection, on-screen bounding box overlays, and dual scanning modes (manual and auto-scan).

---

## Key Features

- **Strictly CPU-Only:** Zero reliance on heavyweight frameworks like PyTorch or PaddlePaddle. Runs with low CPU overhead using ONNXRuntime.
- **Real-Time Webcam Feed:** Default 1280x720 capture with automatic fallback.
- **Card Alignment Guide:** Centered rectangular overlay matching standard credit card / ID-1 proportions (~1.586:1 aspect ratio).
- **Dual Trigger Modes:**
  - **Manual Scan (`SPACE`):** Instant single-frame OCR capture.
  - **Auto-Scan (`A`):** Hands-free continuous scanning every 1.5 seconds.
- **Targeted UID Recognition:** Strips spaces and hyphens to detect any 10-digit number (`\b\d{10}\b`), highlighting matches in vibrant green.
- **Visual Feedback HUD:** Displays bounding boxes around detected text, confidence scores, CPU inference latency in milliseconds, and matched UID badges directly on the OpenCV stream.

---

## Project Structure

```text
ocr_card/
├── scan_id.py          # Main application script
├── README.md           # Project overview and quickstart
├── USAGE.md            # Detailed user manual & camera alignment tips
├── HOW_IT_WORKS.md     # Technical architecture & pipeline explanation
├── requirements.txt    # Pip dependency list
├── environment.yml     # Conda environment definition
└── .gitignore          # Git ignore rules for Python/Conda
```

---

## Quickstart

### Prerequisites
- [Anaconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed.
- Laptop with a built-in or USB webcam.

### 1. Setup Conda Environment
Create and activate the `id-ocr` environment:
```powershell
conda create -n id-ocr python=3.11 -y
conda activate id-ocr
```

### 2. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

*(Alternatively, create the environment directly from the YAML file: `conda env create -f environment.yml`)*

### 3. Verify Models & Installation
Verify that RapidOCR and default ONNX models download and initialize cleanly:
```powershell
python -c "from rapidocr import RapidOCR; RapidOCR(); print('RapidOCR ready')"
```

### 4. Launch Application
```powershell
python scan_id.py
```
*(Or without activating first: `conda run -n id-ocr python scan_id.py`)*

---

## Controls

| Key | Action |
|---|---|
| **`SPACE`** | Trigger a single OCR capture of the card in the guide box |
| **`A`** | Toggle Auto-Scan mode on / off (scans every 1.5s) |
| **`Q`** / **`ESC`** / **Window `[X]`** | Cleanly exit application and release camera |

---

## Sample Terminal Output

```text
=================================================================
Initializing CPU-only RapidOCR engine...
RapidOCR engine ready.
=================================================================
Webcam active at resolution: 1280x720

Controls:
  [SPACE] : Capture & OCR ID Card
  [A]     : Toggle Auto-Scan (every 1.5s)
  [Q/ESC] : Quit
=================================================================

[17:51:14] OCR SCAN COMPLETED in 124.3 ms
  [Text] 'REPUBLIC OF INDIA' (Confidence: 0.96)
  [Text] 'NAME: JOHN DOE' (Confidence: 0.94)
  [>>> MATCHED 10-DIGIT UID: 9876543210 <<<] (Confidence: 0.98) | Raw: 'UID: 9876 543 210'
  ==> Summary Matched UID(s): 9876543210
-----------------------------------------------------------------
```

---

## Documentation

- [User Guide (USAGE.md)](USAGE.md): Step-by-step scanning instructions, card alignment, lighting tips, and troubleshooting.
- [How It Works (HOW_IT_WORKS.md)](HOW_IT_WORKS.md): Deep dive into the detection/recognition pipeline, coordinate transformations, regex heuristics, and performance notes.
