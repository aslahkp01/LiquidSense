"""
Extract all features from each .s2p file in sample_data/.

Usage:
    cd D:\\LiquidSense
    .venv\\Scripts\\python.exe extract_all.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.feature_extractor import extract_features

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")

print("=" * 80)
print("FEATURE EXTRACTION REPORT")
print("=" * 80)

for filename in sorted(os.listdir(SAMPLE_DIR)):
    if filename.endswith(".s2p"):
        filepath = os.path.join(SAMPLE_DIR, filename)
        features = extract_features(filepath)
        print(f"\n  {filename}:")
        print(f"    Resonant Frequency : {features['resonant_freq_ghz']:.4f} GHz")
        print(f"    Min S21 (dip depth): {features['min_s21_db']:.2f} dB")
        print(f"    -3dB Bandwidth     : {features['bandwidth_ghz']:.4f} GHz")
        print(f"    Q-Factor           : {features['q_factor']:.2f}")
        print(f"    Mean S21           : {features['mean_s21_db']:.2f} dB")
        print(f"    S21 Variance       : {features['s21_variance']:.2f}")

print("\n" + "=" * 80)

