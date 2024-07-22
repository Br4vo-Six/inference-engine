from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
import os
import json
from dotenv import dotenv_values
from models import wallet, tx
from pydantic.tools import parse_obj_as

router = APIRouter()

config = dotenv_values(".env")

@router.get(
        "/init/training", 
        response_description="Seed initial training dataset from local json file", 
        status_code=status.HTTP_201_CREATED,
    )
async def load_training(request: Request):
    with open(os.path.join(config['DATASET_DIR'], config['MERGED_JSON'])) as f:
        data = json.load(f)
    data_model = [parse_obj_as(tx.Tx, entry['res']).dict() for entry in data]
    print(data_model[0])
    request.app.database['transactions'].insert_many(data_model)