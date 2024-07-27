import os
from typing import Optional
from torch import load as load_model
from torch.nn import Module, BatchNorm1d
from torch.nn.functional import leaky_relu
from torch_geometric.nn.conv import TAGConv
from sklearn.ensemble import RandomForestClassifier
import joblib


# B6TAGCN
class B6Model(Module):
    def __init__(self):
        super().__init__()
        dim_in = 67
        dim_h = 128
        dim_out = 1
        k = 3
        self.norm1 = BatchNorm1d(dim_in)
        self.tgn1 = TAGConv(dim_in, dim_h, K=k)
        self.norm2 = BatchNorm1d(dim_h)
        self.tgn2 = TAGConv(dim_h, dim_out, K=k)
        self.load()

    def load(self):
        filename = './assets/B6_TAGCN_noscr.pt'
        if not os.path.exists(filename):
            print('Not found')
            return
        state_dict_data = load_model(filename)
        self.load_state_dict(state_dict_data)
        print(f'Model loaded')

    def forward(self, x, edge_index):
        h = self.norm1(x)
        h = self.tgn1(h, edge_index)
        h = self.norm2(h)
        h = leaky_relu(h)
        out = self.tgn2(h, edge_index)
        return out


b6_gnn_model: Optional[B6Model] = None


def get_gnn_model() -> B6Model:
    global b6_gnn_model
    if b6_gnn_model is None:
        b6_gnn_model = B6Model()
    return b6_gnn_model


b6_rf_model: Optional[RandomForestClassifier] = None


def get_rf_model() -> RandomForestClassifier:
    global b6_rf_model
    if b6_rf_model is None:
        filename = './assets/B6_rf.joblib'
        b6_rf_model = joblib.load(filename)
    return b6_rf_model
