from typing import Optional
from fastapi import HTTPException
from torch import sigmoid, tensor, float32
from dotenv import dotenv_values
from ml.extractor import get_tx_map, get_edge_index, transform_txs
from ml.model import get_gnn_model, get_rf_model
from models.tx import Tx


config = dotenv_values(".env")
model_type = config['MODEL']


def get_gnn_label(out, threshold=0.5):
    labels = (sigmoid(out) > threshold).float()
    return labels


def begin_inference(txs: list[Tx], edges: Optional[list[tuple[str, str]]] = None):
    tx_map = get_tx_map(txs)
    X = transform_txs(txs)

    if model_type == 'GNN':
        if edges is None:
            raise HTTPException(
                status_code=500, detail="edges arg required"
            )
        X = tensor(X, dtype=float32)
        edge_index = get_edge_index(edges, tx_map)
        model = get_gnn_model()
        model.eval()
        out = model(X, edge_index)
        labels = get_gnn_label(out)
        label_map = {txh: int(labels[idx]) for txh, idx in tx_map.items()}
        return label_map
    elif model_type == 'RANDOM_FOREST':
        model = get_rf_model()
        labels = model.predict(X)
        label_map = {txh: int(labels[idx]) for txh, idx in tx_map.items()}
        return label_map
    else:
        raise HTTPException(
            status_code=500, detail="Model env variable not found"
        )
