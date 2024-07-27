import numpy as np
import torch
from ml.features import extract_tx_features
from ml.scaler import get_scaler
from models.tx import Tx
import math

def get_tx_map(txs: list[Tx]):
    return {tx.hash: i for i, tx in enumerate(txs)}


def get_edge_index(edges: list[tuple[str, str]], tx_map: dict[str, int]):
    edge_index = [
        [tx_map[edge[0]], tx_map[edge[1]]]
        for edge in edges
    ]
    edge_index = np.array(edge_index).T
    edge_index = torch.tensor(edge_index, dtype=torch.long).contiguous()
    return edge_index


def transform_txs(txs: list[Tx]):
    features = [
        np.array(list(extract_tx_features(tx).values()), dtype=np.float32)
        for tx in txs
    ]
    scaler = get_scaler()
    X = scaler.transform(np.array(features))
    print(np.argwhere(np.isnan(X)))
    return X
