from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import joblib
import shutil
import os
import numpy as np

try:
    from backend.feature_extractor import extract_features, extract_feature_array
except ImportError:
    from feature_extractor import extract_features, extract_feature_array

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load(os.path.join(BASE_DIR, "regression_model.pkl"))

@app.get("/")
async def root():
    return {"status": "ok", "message": "LiquidSense API is running"}

@app.post("/predict")
async def predict(file: UploadFile = File(...), liquid_type: str = Form("milk")):
    file_path = os.path.join(BASE_DIR, "temp.s2p")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    features = extract_features(file_path)
    feature_array = extract_feature_array(file_path).reshape(1, -1)
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