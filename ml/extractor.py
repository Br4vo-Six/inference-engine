import pandas as pd
from ml.features import get_additional_output_features, get_address_features, get_basic_features, get_corr_coeff_features, get_derived_features, get_stat_features
from ml.scaler import get_scaler
from models.tx import Tx


def extract_tx_features(tx: Tx):
    features = dict()
    features = get_basic_features(features, tx)
    features = get_stat_features(features, tx)
    features = get_derived_features(features, tx)
    features, m1, m2 = get_address_features(features, tx)
    features = get_additional_output_features(features, tx, m1, m2)
    features = get_corr_coeff_features(features, tx)
    return features


def get_node_features(df: pd.DataFrame):
    txs = df['tx_id']
    tx_to_idx_map = {txh: i for i, txh in enumerate(txs)}

    feat = df.drop(['tx_id'], axis=1).values
    scaler = get_scaler()
    X = scaler.transform(feat)
    return tx_to_idx_map, X


def get_edge_index(edges: list[tuple[str, str]], tx_to_id_map: dict[str, int]):
    edge_index = [
        [tx_to_id_map[edge[0]], tx_to_id_map[edge[1]]]
        for edge in edges
    ]
    return edge_index


def extract_txs(txs: list[Tx], edges: list[tuple[str, str]]):
    data_map = {'tx_id': []}
    for tx in txs:
        data_map['tx_id'].append(tx.hash)
        features = extract_tx_features(tx)
        for k, v in features.items():
            if k not in data_map:
                data_map[k] = []
            data_map[k].append(v)
    df = pd.DataFrame.from_dict(data_map)
    tx_to_idx_map, X = get_node_features(df)
    edge_index = get_edge_index(edges, tx_to_idx_map)
    return X, edge_index
