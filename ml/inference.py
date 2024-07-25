from torch import sigmoid, from_numpy
from ml.extractor import extract_txs
from ml.model import get_ml_model
from models.tx import Tx


def get_prediction_label(out, threshold=0.5):
    labels = (sigmoid(out) > threshold).float()
    return labels


def begin_inference(txs: list[Tx], edges: list[tuple[str, str]]):
    X, edge_index, tx_map = extract_txs(txs, edges)
    model = get_ml_model()
    model.eval()
    out = model(X, edge_index)
    labels = get_prediction_label(out)
    label_map = {txh: int(labels[idx]) for txh, idx in tx_map.items()}
    return label_map
