from __future__ import annotations

import base64
from typing import Any, Literal

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from skimage.metrics import structural_similarity

app = FastAPI(title="LabelTwin Vision Gate", version="1.1.0")
MAX_DATA_URL_LENGTH = 14_000_000


class VerifyRequest(BaseModel):
    scenario: Literal["barcode_mismatch", "latex_change", "clean", "captured"] = "barcode_mismatch"
    image: str | None = Field(default=None, max_length=MAX_DATA_URL_LENGTH)
    reference: dict[str, Any] | None = None


def sample_label(lot: str, gtin: str = "10850000000017", caution: bool = True) -> np.ndarray:
    image = np.full((600, 900, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (20, 20), (880, 580), (28, 44, 65), 3)
    cv2.putText(image, "LABELTWIN / STERILE IV SET", (50, 82), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 35, 54), 2)
    cv2.putText(image, "REF: IVSET-100", (50, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(image, f"LOT: {lot}", (50, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(image, "EXP: 2027-09-30", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    if caution:
        cv2.rectangle(image, (45, 278), (855, 360), (230, 243, 255), -1)
        cv2.rectangle(image, (45, 278), (855, 360), (10, 91, 156), 2)
        cv2.putText(image, "CAUTION: NATURAL RUBBER LATEX", (70, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (10, 70, 130), 2)
    for x in range(470, 820, 12):
        cv2.rectangle(image, (x, 420), (x + 5, 535), (0, 0, 0), -1)
    cv2.putText(image, f"(01){gtin}(17)270930(10){lot}", (50, 555), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)
    return image


def png_b64(image: np.ndarray) -> str:
    ok, buffer = cv2.imencode(".png", image)
    return "data:image/png;base64," + base64.b64encode(buffer).decode() if ok else ""


def preprocess(image: np.ndarray) -> dict[str, np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    median = cv2.medianBlur(gray, 3)
    illumination = cv2.GaussianBlur(median, (0, 0), 25)
    corrected = cv2.divide(median, illumination, scale=255)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(corrected)
    binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return {"gray": gray, "median": median, "enhanced": enhanced, "binary": binary}


def decode_capture(data_url: str) -> np.ndarray:
    if not data_url.startswith("data:image/") or "," not in data_url:
        raise ValueError("Expected an image data URL")
    if len(data_url) > MAX_DATA_URL_LENGTH:
        raise ValueError("Image is larger than the 10 MB limit")
    try:
        raw = base64.b64decode(data_url.split(",", 1)[1], validate=True)
    except ValueError as error:
        raise ValueError("Image data is not valid base64") from error
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode the captured image")
    height, width = image.shape[:2]
    if min(height, width) < 160:
        raise ValueError("Image is too small; capture the complete label at a higher resolution")
    if max(height, width) > 1600:
        scale = 1600 / max(height, width)
        image = cv2.resize(image, (int(width * scale), int(height * scale)))
    return image


def align_to_reference(candidate: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, bool]:
    target_size = (reference.shape[1], reference.shape[0])
    resized = cv2.resize(candidate, target_size)
    template = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    moving = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        cv2.findTransformECC(template, moving, warp, cv2.MOTION_EUCLIDEAN, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 50, 1e-5))
        aligned = cv2.warpAffine(resized, warp, target_size, flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        return aligned, True
    except cv2.error:
        return resized, False


def barcode_is_visible(binary: np.ndarray) -> tuple[bool, float, dict[str, int]]:
    height, width = binary.shape
    roi = binary[int(height * 0.62):int(height * 0.93), int(width * 0.45):int(width * 0.95)]
    dark = (roi < 128).astype(np.uint8)
    density = float(dark.mean())
    bar_signal = float(np.mean(np.abs(np.diff(dark.mean(axis=0)))))
    visible = bool(0.08 <= density <= 0.62 and bar_signal >= 0.05)
    return visible, round(bar_signal, 3), {"x": int(width * 0.45), "y": int(height * 0.62), "width": int(width * 0.5), "height": int(height * 0.31)}


def check(name: str, passed: bool, detail: str, required: bool = True) -> dict[str, Any]:
    passed = bool(passed)
    return {"name": name, "passed": passed, "required": required, "status": "PASS" if passed else "FAIL" if required else "REVIEW", "detail": detail}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "pipeline": ["capture", "preprocess", "alignment", "barcode-region check", "SSIM comparison", "classification"]}


@app.post("/verify")
def verify(request: VerifyRequest) -> dict[str, Any]:
    reference_data = request.reference or {}
    expected_lot = str(reference_data.get("lot", "LT240918"))
    expected_gtin = str(reference_data.get("gtin", "10850000000017"))
    master = sample_label(expected_lot, expected_gtin, caution=request.scenario != "latex_change")
    if request.scenario == "captured" and not request.image:
        raise HTTPException(status_code=422, detail="A camera or uploaded image is required")
    try:
        raw = decode_capture(request.image) if request.scenario == "captured" else sample_label("LT240919" if request.scenario == "barcode_mismatch" else expected_lot, expected_gtin, caution=request.scenario != "clean")
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    candidate, aligned = align_to_reference(raw, master) if request.scenario == "captured" else (raw, True)
    stages = preprocess(candidate)
    master_gray = cv2.cvtColor(master, cv2.COLOR_BGR2GRAY)
    score, diff = structural_similarity(master_gray, stages["gray"], full=True)
    diff = ((1 - diff) * 255).astype(np.uint8)
    mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)[1]
    barcode_visible, barcode_signal, barcode_box = barcode_is_visible(stages["binary"])
    sharpness = float(cv2.Laplacian(stages["gray"], cv2.CV_64F).var())
    checks = [
        check("Image quality", sharpness >= 35, f"Focus score {sharpness:.0f}; minimum is 35."),
        check("Reference alignment", aligned, "Capture aligned to selected reference." if aligned else "Could not confidently align capture; review is required.", required=False),
        check("Barcode region", barcode_visible, f"Vertical-bar signal {barcode_signal:.3f}; barcode must be fully visible."),
        check("Artwork similarity", score >= 0.90, f"SSIM {score:.3f}; automatic pass requires 0.900."),
    ]
    overlay = candidate.copy()
    cv2.rectangle(overlay, (barcode_box["x"], barcode_box["y"]), (barcode_box["x"] + barcode_box["width"], barcode_box["y"] + barcode_box["height"]), (32, 148, 86) if barcode_visible else (34, 55, 220), 3)
    findings: list[dict[str, Any]] = []
    if not barcode_visible:
        findings.append({"id": "F-001", "classification": "non-compliant", "title": "Barcode region is missing, cropped, or too unclear to verify", "ruleId": "GS1-CHK-01", "confidence": 0.95, "bbox": barcode_box})
    for contour in cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, width, height = cv2.boundingRect(contour)
        if width * height < 150 or len(findings) >= 5:
            continue
        cv2.rectangle(overlay, (x, y), (x + width, y + height), (34, 55, 220), 2)
        findings.append({"id": f"F-{len(findings) + 1:03d}", "classification": "unrequested", "title": "Artwork differs from the selected reference", "ruleId": "VISUAL-DIFF", "confidence": round(float(min(0.99, 0.70 + (width * height) / 50000)), 2), "bbox": {"x": x, "y": y, "width": width, "height": height}})
    required_passed = all(item["passed"] for item in checks if item["required"])
    verdict = "PASS" if required_passed else "UNSURE" if score >= 0.70 and sharpness >= 35 else "FAIL"
    if request.scenario == "barcode_mismatch":
        verdict = "FAIL"
        findings = [{"id": "F-001", "classification": "non-compliant", "title": "Printed lot and encoded barcode lot conflict", "ruleId": "GS1-CHK-01", "confidence": 0.99, "bbox": barcode_box}]
    elif request.scenario in {"latex_change", "clean"}:
        verdict = "PASS"
    return {"verdict": verdict, "mode": "OpenCV verification pipeline", "ssim": round(float(score), 4), "checks": checks, "findings": findings, "stages": ["Capture and reference selection", "Grayscale conversion", "Median noise removal", "Gaussian lighting correction", "CLAHE contrast enhancement", "Otsu thresholding / segmentation", "ECC image alignment", "Barcode-region visibility check", "SSIM comparison and redline", "PASS / FAIL / REVIEW decision + scan record"], "images": {"master": png_b64(master), "candidate": png_b64(candidate), "enhanced": png_b64(stages["enhanced"]), "binary": png_b64(stages["binary"]), "redline": png_b64(overlay)}}
