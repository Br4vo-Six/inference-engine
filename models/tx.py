from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Input(BaseModel):
    prev_hash: Optional[str] = Field(None, description="Previous transaction hash")
    output_index: Optional[int] = Field(None, description="Output index")
    output_value: Optional[int] = Field(None, description="Output value")
    addresses: Optional[List[str]] = Field(None, description="List of addresses")
    script_type: Optional[str] = Field(None, description="Script type")
    age: Optional[int] = Field(None, description="Age of the transaction")

    class Config:
        extra = 'ignore' 

class Output(BaseModel):
    value: Optional[int] = Field(None, description="Output value")
    script: Optional[str] = Field(None, description="Script")
    spent_by: Optional[str] = Field(None, description="Transaction that spent this output")
    addresses: Optional[List[str]] = Field(None, description="List of addresses")
    script_type: Optional[str] = Field(None, description="Script type")

    class Config:
        extra = 'ignore' 

class Tx(BaseModel):
    hash: str = Field(description="Transaction hash")
    block_hash: Optional[str] = Field(None, description="Block hash")
    block_height: Optional[int] = Field(None, description="Block height")
    addresses: Optional[List[str]] = Field(None, description="List of addresses")
    total: Optional[int] = Field(None, description="Total amount")
    fees: Optional[int] = Field(None, description="Transaction fees")
    size: Optional[int] = Field(None, description="Transaction size")
    vsize: Optional[int] = Field(None, description="Virtual transaction size")
    confirmed: Optional[datetime] = Field(None, description="Confirmation timestamp")
    received: Optional[datetime] = Field(None, description="Reception timestamp")
    ver: Optional[int] = Field(None, description="Transaction version")
    double_spend: Optional[bool] = Field(None, description="Double spend flag")
    vin_sz: Optional[int] = Field(None, description="Number of inputs")
    vout_sz: Optional[int] = Field(None, description="Number of outputs")
    inputs: Optional[List[Input]] = Field(None, description="List of inputs")
    outputs: Optional[List[Output]] = Field(None, description="List of outputs")
    licit: Optional[bool] = Field(default=None, description="Is the transaction licit or illicit?") # True if tx is licit, False if illicit

    class Config:
        extra = 'ignore' 