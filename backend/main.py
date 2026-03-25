from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import joblib
import shutil
import os
import numpy as np
import tempfile

try:
    from backend.feature_extractor import extract_features, extract_feature_array
except ImportError:
    from feature_extractor import extract_features, extract_feature_array

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load all available per-liquid models at startup
models = {}

def load_models():
    """Load all .pkl models from the models/ directory, plus legacy fallback."""
    global models
    # Load per-liquid models from models/ folder
    if os.path.isdir(MODELS_DIR):
        for f in os.listdir(MODELS_DIR):
            if f.endswith("_model.pkl"):
                liquid = f.replace("_model.pkl", "")
                models[liquid] = joblib.load(os.path.join(MODELS_DIR, f))
                print(f"  Loaded model: {liquid}")

    # Fallback: load legacy regression_model.pkl for milk if not already loaded
    if "milk" not in models:
        legacy_path = os.path.join(BASE_DIR, "regression_model.pkl")
        if os.path.isfile(legacy_path):
            models["milk"] = joblib.load(legacy_path)
            print("  Loaded legacy milk model (regression_model.pkl)")

    print(f"  Available models: {list(models.keys())}")

load_models()

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "LiquidSense API is running",
        "available_models": list(models.keys()),
    }

@app.get("/models")
async def list_models():
    """Return which liquid types have trained models."""
    return {"models": list(models.keys())}

@app.post("/predict")
async def predict(file: UploadFile = File(...), liquid_type: str = Form("milk")):
    # Check if model exists for this liquid
    if liquid_type not in models:
        available = list(models.keys())
        return {
            "error": f"No trained model for '{liquid_type}'. Available: {available}",
            "available_models": available,
        }

    suffix = os.path.splitext(file.filename or "")[1] or ".tmp"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=BASE_DIR)
    file_path = temp_file.name
    temp_file.close()

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        features = extract_features(file_path)
        feature_array = extract_feature_array(file_path).reshape(1, -1)
    except Exception as exc:
        return {
            "error": "Could not parse uploaded file for prediction.",
            "details": str(exc),
        }
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    model = models[liquid_type]
    prediction = model.predict(feature_array)

    purity = max(0.0, min(100.0, float(prediction[0])))
    adulteration = 100 - purity

    return {
        "Purity_Percentage": round(purity, 2),
        "Adulteration": round(adulteration, 2),
        "Liquid_Type": liquid_type,
        "Resonant_Frequency_GHz": round(features["resonant_freq_ghz"], 4),
        "Min_S21_dB": round(features["min_s21_db"], 2),
        "Q_Factor": round(features["q_factor"], 2),
    }