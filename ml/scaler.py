import pickle
from sklearn.preprocessing import StandardScaler


def get_scaler() -> StandardScaler:
    filename = './assets/B6_scaler.pkl'
    with open(filename, 'rb') as f:
        scaler = pickle.load(f)
    return scaler
