"""人工データで実験記録の動作を確認する。Titanic の分析結果ではない。"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    seed = config["seed"]
    params = config["parameters"]
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({"feature": rng.normal(size=params["rows"])})
    target = rng.integers(0, 2, size=len(frame))
    train, test = train_test_split(
        np.arange(len(frame)),
        test_size=params["test_size"],
        random_state=seed,
        stratify=target,
    )
    model = DummyClassifier(strategy="most_frequent", random_state=seed)
    model.fit(frame.iloc[train], target[train])
    prediction = model.predict(frame.iloc[test])
    metrics = {"accuracy": float(accuracy_score(target[test], prediction))}
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (args.output_dir / "split.json").write_text(
        json.dumps({"train": train.tolist(), "test": test.tolist()}, indent=2) + "\n"
    )
    pd.DataFrame({"row": test, "actual": target[test], "prediction": prediction}).to_csv(
        args.output_dir / "predictions.csv", index=False
    )
    print(f"人工データで動作確認完了: {metrics}", flush=True)


if __name__ == "__main__":
    main()
