# LiquidSense

**RF-based liquid adulteration detection system** — upload an `.s2p` file captured from a microwave resonator and get an instant purity prediction.

![License](https://img.shields.io/badge/license-MIT-blue)

---

## Overview

LiquidSense uses S-parameter (S21) measurements from a microwave resonator sensor to detect adulteration in liquids. The system extracts RF features — resonant frequency, dip depth, bandwidth, Q-factor — and feeds them into a machine-learning model to predict purity percentage.

**Supported liquid types:** Milk · Honey · Cooking Oil · Fruit Juice · Water

---

## Architecture

```
┌──────────────┐        POST /predict        ┌───────────────────┐
│   React UI   │  ──────────────────────────► │   FastAPI Backend  │
│  (Vite + JSX)│  ◄──────────────────────────  │  (scikit-learn)   │
└──────────────┘       JSON response          └───────────────────┘
                                                       │
                                                ┌──────┴──────┐
                                                │  .pkl models │
                                                │  (per liquid)│
                                                └─────────────┘
```

---

## Project Structure

```
LiquidSense/
├── backend/
│   ├── main.py               # FastAPI app & /predict endpoint
│   ├── model.py              # Model training (multi-algorithm LOO-CV)
│   ├── feature_extractor.py  # S21 feature extraction from .s2p files
│   ├── models/               # Saved .pkl model files
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── App.css           # Styling (responsive)
│   │   └── main.jsx          # Entry point
│   ├── index.html
│   └── package.json
├── sample_data/              # Training data (.s2p files per liquid)
│   ├── milk/
│   ├── honey/
│   ├── oil/
│   ├── juice/
│   └── water/
├── extract_all.py            # Utility: print features for all samples
└── render.yaml               # Render.com deployment config
```

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**

---

## Quick Start

### 1. Clone & set up Python environment

```bash
git clone <repo-url>
cd LiquidSense

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r backend/requirements.txt
```

### 2. Train models

Place `.s2p` sample files in `sample_data/<liquid>/` then run:

```bash
python -m backend.model          # trains all liquids
python -m backend.model milk     # trains milk only
```

Models are saved to `backend/models/<liquid>_model.pkl`.

### 3. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## API Endpoints

| Method | Path       | Description                          |
|--------|-----------|--------------------------------------|
| GET    | `/`       | Health check & list available models |
| GET    | `/models` | List trained liquid types            |
| POST   | `/predict`| Predict purity from `.s2p` upload    |

### POST `/predict`

**Form fields:**
- `file` — the `.s2p` file (multipart upload)
- `liquid_type` — one of `milk`, `honey`, `oil`, `juice`, `water`

**Response:**

```json
{
  "Purity_Percentage": 87.5,
  "Adulteration": 12.5,
  "Liquid_Type": "milk",
  "Resonant_Frequency_GHz": 2.4512,
  "Min_S21_dB": -28.34,
  "Q_Factor": 45.12
}
```

---

## Sample Data Format

The system reads Touchstone `.s2p` files (2-port S-parameter format). Each file should contain `S21` transmission data across a frequency sweep.

### Naming convention

Files in `sample_data/<liquid>/` must either:

1. Contain the purity percentage in the filename (e.g., `milk_75.s2p`)
2. Be listed in the `KNOWN_SAMPLES` dict in `backend/model.py`

---

## Features Extracted

| Feature               | Description                                     |
|-----------------------|-------------------------------------------------|
| Resonant Frequency    | Frequency at min S21 (GHz)                      |
| Min S21               | Depth of the resonance dip (dB)                 |
| -3 dB Bandwidth       | Bandwidth around resonance (GHz)                |
| Q-Factor              | Quality factor = resonant freq / bandwidth      |
| Mean S21              | Average S21 across the spectrum (dB)            |
| S21 Variance          | Statistical variance of S21 values              |

---

## Deployment

A `render.yaml` is included for one-click deployment on [Render](https://render.com):

- **Backend** — Python web service running uvicorn
- **Frontend** — Static site built with Vite

Set the `VITE_API_URL` environment variable in the frontend build to point to your deployed backend URL.

---

## Tech Stack

- **Frontend:** React 19, Vite 6
- **Backend:** FastAPI, scikit-learn, scikit-rf
- **ML Models:** Ridge Regression, SVR, KNN, Gradient Boosting (auto-selected per liquid via LOO-CV)

---

## License

MIT
