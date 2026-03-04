"""
Train per-liquid purity models.

Folder structure expected:
    sample_data/
        milk/       ← .s2p files for milk samples
        honey/      ← .s2p files for honey samples
        oil/        ← .s2p files for oil samples
        juice/      ← .s2p files for juice samples
        water/      ← .s2p files for water samples

Each .s2p filename must contain the purity percentage, e.g.:
    milk_100.s2p, milk_75.s2p, honey_50.s2p, ab_25.s2p, etc.
    The script extracts the LAST number before .s2p as purity %.

Usage:
    cd D:\\LiquidSense
    .venv\\Scripts\\python.exe -m backend.model            (trains all)
    .venv\\Scripts\\python.exe -m backend.model milk        (trains milk only)
"""

import numpy as np
import re
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import LeaveOneOut, cross_val_score
import joblib
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))

try:
    from backend.feature_extractor import extract_feature_array
except ImportError:
    from feature_extractor import extract_feature_array

SAMPLE_DIR = os.path.join(os.path.dirname(BASE_DIR), "sample_data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Known sample mappings for liquids that don't follow the naming convention.
# Map: liquid_type -> { filename: purity_pct }
# Add overrides here if your filenames don't contain the purity number.
KNOWN_SAMPLES = {
    "milk": {
        "ab_8.s2p": 0,    # pure water / adulterant
        "ab_7.s2p": 10,
        "ab_6.s2p": 15,
        "ab_5.s2p": 25,
        "ab_3.s2p": 50,
        "ab_4.s2p": 75,
        "ab_2.s2p": 100,  # pure milk
    },
    # Example for when you add honey data:
    # "honey": {
    #     "honey_0.s2p": 0,
    #     "honey_50.s2p": 50,
    #     "honey_100.s2p": 100,
    # },
}


def parse_purity_from_filename(filename):
    """Extract purity % from filename. Takes the last number before .s2p."""
    match = re.findall(r"(\d+)", filename.replace(".s2p", ""))
    if match:
        return int(match[-1])
    return None


def get_samples_for_liquid(liquid_type):
    """
    Return dict of { filename: purity_pct } for a liquid type.
    Uses KNOWN_SAMPLES if available, otherwise parses from filenames.
    """
    liquid_dir = os.path.join(SAMPLE_DIR, liquid_type)
    if not os.path.isdir(liquid_dir):
        return {}

    # Use known mapping if defined
    if liquid_type in KNOWN_SAMPLES:
        return KNOWN_SAMPLES[liquid_type]

    # Otherwise, parse purity from filenames
    samples = {}
    for f in sorted(os.listdir(liquid_dir)):
        if f.endswith(".s2p"):
            purity = parse_purity_from_filename(f)
            if purity is not None:
                samples[f] = purity
            else:
                print(f"  WARNING: Could not parse purity from '{f}', skipping.")
    return samples


def get_candidate_models():
    """Return dict of candidate model pipelines."""
    return {
        "Ridge (Poly deg=2)": Pipeline([
            ("scaler", StandardScaler()),
            ("poly", PolynomialFeatures(degree=2, include_bias=False)),
            ("ridge", Ridge(alpha=1.0)),
        ]),
        "Ridge (Poly deg=3)": Pipeline([
            ("scaler", StandardScaler()),
            ("poly", PolynomialFeatures(degree=3, include_bias=False)),
            ("ridge", Ridge(alpha=10.0)),
        ]),
        "SVR (RBF, C=100)": Pipeline([
            ("scaler", StandardScaler()),
            ("svr", SVR(kernel="rbf", C=100, gamma="scale", epsilon=5)),
        ]),
        "SVR (RBF, C=1000)": Pipeline([
            ("scaler", StandardScaler()),
            ("svr", SVR(kernel="rbf", C=1000, gamma="scale", epsilon=1)),
        ]),
        "SVR (Linear)": Pipeline([
            ("scaler", StandardScaler()),
            ("svr", SVR(kernel="linear", C=100, epsilon=2)),
        ]),
        "KNN (k=2)": Pipeline([
            ("scaler", StandardScaler()),
            ("knn", KNeighborsRegressor(n_neighbors=2, weights="distance")),
        ]),
        "Gradient Boosting": Pipeline([
            ("scaler", StandardScaler()),
            ("gb", GradientBoostingRegressor(
                n_estimators=50, max_depth=2, learning_rate=0.1, random_state=42
            )),
        ]),
    }


def train_liquid_model(liquid_type):
    """Train and save a model for a specific liquid type."""
    samples = get_samples_for_liquid(liquid_type)

    if len(samples) < 3:
        print(f"\n  SKIPPING '{liquid_type}': need at least 3 samples, found {len(samples)}.")
        print(f"  Add .s2p files to: sample_data/{liquid_type}/")
        return None

    liquid_dir = os.path.join(SAMPLE_DIR, liquid_type)

    print(f"\n{'='*60}")
    print(f"  Training model for: {liquid_type.upper()}")
    print(f"{'='*60}")

    X, y = [], []
    for filename, purity in samples.items():
        filepath = os.path.join(liquid_dir, filename)
        if not os.path.isfile(filepath):
            print(f"  WARNING: File not found: {filepath}, skipping.")
            continue
        features = extract_feature_array(filepath)
        X.append(features)
        y.append(purity)
        print(f"  {filename}: purity={purity}%, features={np.round(features, 4)}")

    if len(X) < 3:
        print(f"  SKIPPING: only {len(X)} valid files found (need >= 3).")
        return None

    X = np.array(X)
    y = np.array(y)

    print(f"\n  Feature matrix: {X.shape}")
    print(f"  Features: [resonant_freq, min_s21, bandwidth, q_factor, mean_s21, s21_variance]\n")

    # Evaluate candidates
    models = get_candidate_models()
    loo = LeaveOneOut()
    best_name, best_score, best_model = None, -np.inf, None

    print("  Evaluating models (Leave-One-Out CV):")
    print("  " + "-" * 50)
    for name, pipeline in models.items():
        scores = cross_val_score(pipeline, X, y, cv=loo, scoring="neg_mean_absolute_error")
        mean_mae = -scores.mean()
        print(f"    {name:<25} MAE = {mean_mae:.2f}%")
        if -mean_mae > best_score:
            best_score = -mean_mae
            best_name = name
            best_model = pipeline

    print(f"\n  Best model: {best_name} (MAE = {-best_score:.2f}%)")

    # Fit on all data
    best_model.fit(X, y)

    # Show training predictions
    preds = best_model.predict(X)
    print(f"\n  Training predictions:")
    for i, (filename, purity) in enumerate(samples.items()):
        pred = np.clip(preds[i], 0, 100)
        print(f"    {filename}: actual={purity}%, predicted={pred:.1f}%")

    # Save
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, f"{liquid_type}_model.pkl")
    joblib.dump(best_model, model_path)
    print(f"\n  Model saved: {model_path}")

    # Also save as legacy regression_model.pkl for milk (backward compat)
    if liquid_type == "milk":
        legacy_path = os.path.join(BASE_DIR, "regression_model.pkl")
        joblib.dump(best_model, legacy_path)
        print(f"  Legacy copy: {legacy_path}")

    return best_model


def get_available_liquids():
    """Return list of liquid types that have a data folder."""
    if not os.path.isdir(SAMPLE_DIR):
        return []
    return [d for d in sorted(os.listdir(SAMPLE_DIR))
            if os.path.isdir(os.path.join(SAMPLE_DIR, d))]


if __name__ == "__main__":
    # Train specific liquid or all
    target = sys.argv[1] if len(sys.argv) > 1 else None
    liquids = [target] if target else get_available_liquids()

    print(f"Found liquid types: {liquids}")
    trained = []

    for liquid in liquids:
        model = train_liquid_model(liquid)
        if model:
            trained.append(liquid)

    print(f"\n{'='*60}")
    print(f"  DONE. Trained models for: {trained or 'none'}")
    if set(liquids) - set(trained):
        print(f"  Skipped (not enough data): {list(set(liquids) - set(trained))}")
    print(f"{'='*60}")