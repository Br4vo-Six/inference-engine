from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TxRef(BaseModel):
    tx_hash: str
    block_height: int
    tx_input_n: Optional[int] = Field(default=0)
    tx_output_n: Optional[int] = Field(default=0)
    value: Optional[int] = Field(default=0)
    ref_balance: Optional[int] = Field(default=None)
    confirmed: Optional[datetime] = Field(default=False)
    double_spend: Optional[bool] = Field(default=None)
    spent: Optional[bool] = Field(default=False)
    spent_by: Optional[str] = Field(default=None)
    licit: Optional[bool] = Field(default=None, description="Is the transaction licit or illicit?") # True if tx is licit, False if illicit

    class Config:
        extra = 'ignore' 

class Wallet(BaseModel):
    address: str
    total_received: Optional[int] = Field(default=0)
    total_sent: Optional[int] = Field(default=0)
    balance: Optional[int] = Field(default=0)
    n_tx: Optional[int] = Field(default=0)
    final_n_tx: Optional[int] = Field(default=0)
    txrefs: Optional[List[TxRef]] = Field(default=[])

    class Config:
        extra = 'ignore' 