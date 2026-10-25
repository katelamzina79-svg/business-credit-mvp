"""Inference: load (or deterministically re-train) the model and score one application."""
import logging
from functools import lru_cache

import joblib
import numpy as np
import sklearn

from app.ml.config import ARTIFACT_PATH, FEATURES, MODEL_VERSION

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_artifact() -> dict:
    """Saved artifact if it matches this code/sklearn; otherwise train in memory (same seed)."""
    try:
        art = joblib.load(ARTIFACT_PATH)
        if (art["model_version"], art["features"], art["sklearn_version"]) == (
            MODEL_VERSION, FEATURES, sklearn.__version__
        ):
            return art
        log.warning("ML artifact does not match the code or sklearn version; re-training in memory")
    except Exception as exc:  # missing/corrupt file, incompatible pickle
        log.warning("ML artifact not loaded (%s); re-training in memory", exc)
    from app.ml.train import train_model
    return train_model()


def _sigmoid(z: float) -> float:
    return float(1.0 / (1.0 + np.exp(-z)))


def predict(features: dict) -> dict:
    """features: dict with every name in FEATURES; None = unknown (filled with the train median).

    Returns risk_probability in [0, 1], score = round(100 * (1 - p)), model_version, the names
    of median-filled features, and top_factors sorted by how many probability points each
    feature adds compared with an average applicant (risk_delta, 0..1).
    """
    art = get_artifact()
    medians = art["medians"]
    imputed = [n for n in FEATURES if features.get(n) is None]
    row = np.array([[float(features[n]) if features.get(n) is not None else medians[n] for n in FEATURES]])

    scaler, clf = art["pipeline"][0], art["pipeline"][-1]
    contrib = clf.coef_[0] * scaler.transform(row)[0]          # per-feature logit contribution
    z = float(clf.intercept_[0] + contrib.sum())
    p = _sigmoid(z)
    top_factors = sorted(
        ({"feature": n, "risk_delta": round(p - _sigmoid(z - float(c)), 4)} for n, c in zip(FEATURES, contrib)),
        key=lambda f: f["risk_delta"], reverse=True,
    )
    return {
        "risk_probability": round(p, 4),
        "score": round(100 * (1 - p)),
        "model_version": art["model_version"],
        "imputed_features": imputed,
        "top_factors": top_factors,
    }
