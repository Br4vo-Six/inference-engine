from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TxRef(BaseModel):
    tx_hash: str
    block_height: Optional[int] = Field(default=None)
    tx_input_n: int
    tx_output_n: int
    value: Optional[int] = Field(default=0)
    # ref_balance: Optional[int] = Field(default=None)
    confirmed: Optional[datetime] = Field(default=False)
    # double_spend: Optional[bool] = Field(default=None)
    spent: Optional[bool] = Field(default=None)
    spent_by: Optional[str] = Field(default=None)
    # True if tx is licit, False if illicit
    licit: Optional[bool] = Field(
        default=None, description="Is the transaction licit or illicit?")

    class Config:
        extra = 'ignore'


class Wallet(BaseModel):
    address: str
    total_received: Optional[int] = Field(default=0)
    total_sent: Optional[int] = Field(default=0)
    balance: Optional[int] = Field(default=0)
    n_tx: Optional[int] = Field(default=0)
    txrefs: Optional[List[TxRef]] = Field(default=[])

    class Config:
        extra = 'ignore'
