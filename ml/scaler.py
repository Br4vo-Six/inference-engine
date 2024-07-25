import pickle
from typing import Optional
from sklearn.preprocessing import StandardScaler

b6_scaler: Optional[StandardScaler] = None


def get_scaler() -> StandardScaler:
    global b6_scaler
    if b6_scaler is None:
        filename = './assets/B6_scaler.pkl'
        with open(filename, 'rb') as f:
            b6_scaler = pickle.load(f)
    return b6_scaler
