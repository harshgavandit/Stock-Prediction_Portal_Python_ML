"""Inference for the repository's two LSTM layers and two linear Dense layers.

Weights are exported unchanged from stock_prediction_model.keras. No retraining,
network calls, or approximation is used. See scripts/export_model.py.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

MODEL_DIR = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def weights():
    with np.load(MODEL_DIR / "stock_prediction_weights.npz", allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def _sigmoid(value):
    return 1.0 / (1.0 + np.exp(-np.clip(value, -80, 80)))


def _lstm(inputs, kernel, recurrent_kernel, bias, return_sequences):
    batch, steps, _ = inputs.shape
    units = recurrent_kernel.shape[0]
    hidden = np.zeros((batch, units), dtype=np.float32)
    cell = np.zeros_like(hidden)
    # Project all input timesteps once; recurrent projection still runs per step.
    projected = inputs @ kernel + bias
    sequence = []
    for step in range(steps):
        gates = projected[:, step, :] + hidden @ recurrent_kernel
        input_gate, forget_gate, candidate, output_gate = np.split(gates, 4, axis=1)
        cell = _sigmoid(forget_gate) * cell + _sigmoid(input_gate) * np.tanh(candidate)
        hidden = _sigmoid(output_gate) * np.tanh(cell)
        if return_sequences:
            sequence.append(hidden)
    return np.stack(sequence, axis=1) if return_sequences else hidden


def predict(sequences):
    sequences = np.asarray(sequences, dtype=np.float32)
    if sequences.ndim != 3 or sequences.shape[1:] != (100, 1) or not np.isfinite(sequences).all():
        raise ValueError("Expected finite sequences with shape (batch, 100, 1).")
    model = weights()
    outputs = []
    with threadpool_limits(limits=1, user_api="blas"):
        for offset in range(0, len(sequences), 64):
            value = sequences[offset:offset + 64]
            value = _lstm(value, model["lstm_0"], model["lstm_1"], model["lstm_2"], True)
            value = _lstm(value, model["lstm_1_0"], model["lstm_1_1"], model["lstm_1_2"], False)
            value = value @ model["dense_0"] + model["dense_1"]
            value = value @ model["dense_1_0"] + model["dense_1_1"]
            outputs.append(value)
    return np.concatenate(outputs, axis=0) if outputs else np.empty((0, 1), dtype=np.float32)
