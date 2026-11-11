# LabelTwin

LabelTwin is a requirement-linked label lifecycle workspace. It maps each label element to its source, approved phrase, rule and change order; calculates change impact; produces a visual verification result; and preserves an auditable release trail.

All records in this repository are synthetic demonstration data. Regulatory rules are examples for workflow demonstration and require qualified review before operational use.

## Stack

- **Console:** React 18, Vite and CSS
- **Workflow API:** Node.js, Express, Mongoose/MongoDB (with seeded in-memory demo fallback)
- **Vision gate:** Python, FastAPI, OpenCV and scikit-image

## Run locally

1. Copy `.env.example` to `.env`.
2. Run `npm install`, then `npm run install:all`.
3. In a second terminal, install the vision dependencies: `pip install -r vision/requirements.txt` and run `uvicorn app.main:app --reload --port 8000` from `vision/`.
4. Run `npm run dev` and open `http://localhost:5173`.

The API remains fully usable without MongoDB; it starts with a deterministic synthetic demo workspace. For persistent storage, start MongoDB with `docker compose up mongodb` and set `MONGODB_URI`.

## Demo flow

Open **Change impact**, submit the supplied natural-rubber-latex change, inspect cited actions, regenerate a label, then use **Verification gate** to see intent-aware visual redlining and a release decision. Open **Audit trail** to verify the hash chain.

## Project status

| Area | Status |
| --- | --- |
| Product/label graph, impact analysis, LBOM | Built demo |
| Rules, change workflow, hash-chain audit | Built demo |
| React console and visual redline | Built demo |
| OpenCV preprocessing, alignment and SSIM diff | Built demo |
| MongoDB connectivity | Configured; the current prototype uses deterministic demo data until persistence models are enabled |
| Barcode/OCR/symbol model training and production e-signatures | Roadmap |
