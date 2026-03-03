import skrf as rf
import numpy as np

def extract_resonant_frequency(file_path):
    """Extract just the resonant frequency (kept for backward compatibility)."""
    features = extract_features(file_path)
    return features["resonant_freq_ghz"]

def extract_features(file_path):
    """
    Extract multiple features from an .s2p file for better prediction accuracy.
    Uses S21 (transmission) parameter.
    
    Features:
    - resonant_freq_ghz: frequency at minimum S21 (GHz)
    - min_s21_db: depth of the resonance dip (dB)
    - bandwidth_ghz: -3dB bandwidth around the resonance (GHz)
    - q_factor: quality factor (resonant_freq / bandwidth)
    - mean_s21_db: average S21 across the spectrum (dB)
    - s21_variance: variance of S21 values
    """
    network = rf.Network(file_path)
    
    s21_linear = np.abs(network.s[:, 1, 0])  # S21
    s21_db = 20 * np.log10(s21_linear + 1e-12)  # avoid log(0)
    freq = network.f
    freq_ghz = freq / 1e9

    # Resonant frequency & minimum S21
    min_index = np.argmin(s21_db)
    resonant_freq = freq_ghz[min_index]
    min_s21 = s21_db[min_index]

    # -3dB bandwidth
    threshold = min_s21 + 3  # 3dB above minimum
    below_threshold = np.where(s21_db <= threshold)[0]
    if len(below_threshold) >= 2:
        bw_start = freq_ghz[below_threshold[0]]
        bw_end = freq_ghz[below_threshold[-1]]
        bandwidth = bw_end - bw_start
    else:
        bandwidth = 0.0

    # Q-factor
    q_factor = resonant_freq / bandwidth if bandwidth > 0 else 0.0

    # Statistical features
    mean_s21 = np.mean(s21_db)
    s21_variance = np.var(s21_db)

    return {
        "resonant_freq_ghz": resonant_freq,
        "min_s21_db": min_s21,
        "bandwidth_ghz": bandwidth,
        "q_factor": q_factor,
        "mean_s21_db": mean_s21,
        "s21_variance": s21_variance,
    }

def extract_feature_array(file_path):
    """Return features as a numpy array (for model prediction)."""
    f = extract_features(file_path)
    return np.array([
        f["resonant_freq_ghz"],
        f["min_s21_db"],
        f["bandwidth_ghz"],
        f["q_factor"],
        f["mean_s21_db"],
        f["s21_variance"],
    ])