"""Train the demo model.  Run from backend/:  python -m app.ml.train [--export-csv PATH]"""
import argparse
import json

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.config import (
    ARTIFACT_DIR, ARTIFACT_PATH, FEATURES, METRICS_PATH, MODEL_VERSION,
    N_SAMPLES, RANDOM_STATE, TEST_SIZE,
)
from app.ml.data import generate_dataset


def train_model() -> dict:
    """Deterministically train on the synthetic data and return the artifact dict."""
    X, y = generate_dataset(N_SAMPLES, RANDOM_STATE)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=RANDOM_STATE))
    pipeline.fit(X_train, y_train)  # train only

    proba = pipeline.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)  # classification cut-off for the metrics only
    metrics = {
        "split": {"n_train": int(len(y_train)), "n_test": int(len(y_test)), "random_state": RANDOM_STATE},
        "base_rate_train": round(float(y_train.mean()), 4),
        "base_rate_test": round(float(y_test.mean()), 4),
        "test": {
            "precision": round(float(precision_score(y_test, pred)), 4),
            "recall": round(float(recall_score(y_test, pred)), 4),
            "f1": round(float(f1_score(y_test, pred)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
            "classification_threshold": 0.5,
        },
        "labels": "synthetic (hand-set logistic rule, see app/ml/config.py LABEL_RULE)",
    }
    return {
        "pipeline": pipeline,
        "features": list(FEATURES),
        "medians": {n: float(np.median(X_train[:, i])) for i, n in enumerate(FEATURES)},  # train only
        "model_version": MODEL_VERSION,
        "sklearn_version": sklearn.__version__,
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-csv", help="also write the synthetic dataset to this CSV path")
    args = parser.parse_args()

    artifact = train_model()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, ARTIFACT_PATH)
    METRICS_PATH.write_text(json.dumps(artifact["metrics"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.export_csv:
        X, y = generate_dataset(N_SAMPLES, RANDOM_STATE)
        np.savetxt(args.export_csv, np.column_stack([X, y]), delimiter=",",
                   header=",".join(FEATURES + ["high_risk"]), comments="", fmt="%.6g")
    print(json.dumps(artifact["metrics"], indent=2, ensure_ascii=False))
    print(f"Saved model -> {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
