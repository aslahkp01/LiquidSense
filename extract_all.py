"""
Extract all features from each .s2p file in sample_data/<liquid>/.

Usage:
    cd D:\\LiquidSense
    .venv\\Scripts\\python.exe extract_all.py          (all liquids)
    .venv\\Scripts\\python.exe extract_all.py milk      (milk only)
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.feature_extractor import extract_features

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")

target = sys.argv[1] if len(sys.argv) > 1 else None
liquid_dirs = [target] if target else sorted(
    d for d in os.listdir(SAMPLE_DIR)
    if os.path.isdir(os.path.join(SAMPLE_DIR, d))
)

print("=" * 80)
print("FEATURE EXTRACTION REPORT")
print("=" * 80)

for liquid in liquid_dirs:
    liquid_path = os.path.join(SAMPLE_DIR, liquid)
    s2p_files = sorted(f for f in os.listdir(liquid_path) if f.endswith(".s2p"))

    if not s2p_files:
        print(f"\n  [{liquid.upper()}] — no .s2p files found")
        continue

    print(f"\n  [{liquid.upper()}] ({len(s2p_files)} files)")
    print(f"  {'-' * 60}")

    for filename in s2p_files:
        filepath = os.path.join(liquid_path, filename)
        features = extract_features(filepath)
        print(f"\n    {filename}:")
        print(f"      Resonant Frequency : {features['resonant_freq_ghz']:.4f} GHz")
        print(f"      Min S21 (dip depth): {features['min_s21_db']:.2f} dB")
        print(f"      -3dB Bandwidth     : {features['bandwidth_ghz']:.4f} GHz")
        print(f"      Q-Factor           : {features['q_factor']:.2f}")
        print(f"      Mean S21           : {features['mean_s21_db']:.2f} dB")
        print(f"      S21 Variance       : {features['s21_variance']:.2f}")

print("\n" + "=" * 80)

