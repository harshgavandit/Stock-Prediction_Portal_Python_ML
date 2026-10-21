"""Export the trained Keras weights, optionally verify against TensorFlow."""
import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend-drf"
sys.path.insert(0, str(BACKEND))
source = BACKEND / "stock_prediction_model.keras"
parser = argparse.ArgumentParser()
parser.add_argument("--verify", action="store_true")
args = parser.parse_args()
with zipfile.ZipFile(source) as archive:
    config = json.loads(archive.read("config.json"))
    layers = [layer for layer in config["config"]["layers"] if layer["class_name"] != "InputLayer"]
    assert [layer["class_name"] for layer in layers] == ["LSTM", "LSTM", "Dense", "Dense"]
    for layer in layers[:2]:
        assert layer["config"]["activation"] == "tanh"
        assert layer["config"]["recurrent_activation"] == "sigmoid"
        assert not layer["config"]["go_backwards"] and not layer["config"]["stateful"]
    exported = {}
    with h5py.File(io.BytesIO(archive.read("model.weights.h5")), "r") as data:
        for name in ("lstm", "lstm_1", "dense", "dense_1"):
            group = data[f"layers/{name}"]
            variables = group["cell/vars"] if "cell" in group else group["vars"]
            for index in variables:
                exported[f"{name}_{index}"] = np.array(variables[index], dtype=np.float32)
np.savez_compressed(BACKEND / "stock_prediction_weights.npz", **exported)
manifest = {
    "source": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "architecture": "LSTM(128, sequences) -> LSTM(64) -> Dense(25) -> Dense(1)",
    "window": 100, "dtype": "float32",
}
if args.verify:
    import keras
    from api.inference import predict
    original = keras.models.load_model(source, compile=False)
    rng = np.random.default_rng(42)
    inputs = np.concatenate([
        rng.random((8, 100, 1), dtype=np.float32),
        np.zeros((1, 100, 1), dtype=np.float32),
        np.ones((1, 100, 1), dtype=np.float32),
        np.linspace(-0.5, 1.5, 100, dtype=np.float32).reshape(1, 100, 1),
    ])
    expected = np.asarray(original(inputs, training=False))
    actual = predict(inputs)
    np.testing.assert_allclose(actual, expected, rtol=2e-5, atol=2e-6)
    manifest["tensorflow_verification"] = {
        "samples": len(inputs), "max_absolute_error": float(np.max(np.abs(expected - actual))),
        "keras_version": keras.__version__,
    }
    np.savez_compressed(BACKEND / "api" / "model_reference.npz", inputs=inputs, expected=expected)
(BACKEND / "model_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
