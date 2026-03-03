import numpy as np
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import LeaveOneOut, cross_val_score
import joblib
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))

from backend.feature_extractor import extract_feature_array

# Sample files and their known milk percentages
samples = {
    "ab_8.s2p": 0,    # pure water
    "ab_7.s2p": 10,
    "ab_5.s2p": 25,
    "ab_3.s2p": 50,
    "ab_4.s2p": 75,
    "ab_2.s2p": 100,
}

SAMPLE_DIR = os.path.join(os.path.dirname(BASE_DIR), "sample_data")

# Extract features from all samples
print("Extracting features from sample files...")
X = []
y = []
for filename, milk_pct in samples.items():
    filepath = os.path.join(SAMPLE_DIR, filename)
    features = extract_feature_array(filepath)
    X.append(features)
    y.append(milk_pct)
    print(f"  {filename}: milk={milk_pct}%, features={np.round(features, 4)}")

X = np.array(X)
y = np.array(y)

print(f"\nFeature matrix shape: {X.shape}")
print(f"Features: [resonant_freq, min_s11, bandwidth, q_factor, mean_s11, s11_variance]\n")

# Try multiple models and pick the best
models = {
    "Ridge (Poly deg=2)": Pipeline([
        ("scaler", StandardScaler()),
        ("poly", PolynomialFeatures(degree=2, include_bias=False)),
        ("ridge", Ridge(alpha=1.0)),
    ]),
    "SVR (RBF)": Pipeline([
        ("scaler", StandardScaler()),
        ("svr", SVR(kernel="rbf", C=100, gamma="scale", epsilon=5)),
    ]),
    "Gradient Boosting": Pipeline([
        ("scaler", StandardScaler()),
        ("gb", GradientBoostingRegressor(
            n_estimators=50, max_depth=2, learning_rate=0.1, random_state=42
        )),
    ]),
}

loo = LeaveOneOut()
best_name = None
best_score = -np.inf
best_model = None

print("Evaluating models (Leave-One-Out cross-validation):")
print("-" * 55)
for name, pipeline in models.items():
    scores = cross_val_score(pipeline, X, y, cv=loo, scoring="neg_mean_absolute_error")
    mean_mae = -scores.mean()
    print(f"  {name:<25} MAE = {mean_mae:.2f}%")
    if -mean_mae > best_score:
        best_score = -mean_mae
        best_name = name
        best_model = pipeline

print(f"\nBest model: {best_name} (MAE = {-best_score:.2f}%)")

# Train the best model on all data
best_model.fit(X, y)

# Show predictions on training data
predictions = best_model.predict(X)
print(f"\nTraining predictions:")
for i, (filename, milk_pct) in enumerate(samples.items()):
    pred = np.clip(predictions[i], 0, 100)
    print(f"  {filename}: actual={milk_pct}%, predicted={pred:.1f}%")

# Save model
model_path = os.path.join(BASE_DIR, "regression_model.pkl")
joblib.dump(best_model, model_path)
print(f"\nModel saved to {model_path}")