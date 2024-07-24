from fastapi import APIRouter, Body, Request, Response, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from typing import List
import os
import json
from dotenv import dotenv_values
from models import wallet, tx
from pydantic.tools import parse_obj_as
from scraper import scraper

router = APIRouter()

config = dotenv_values(".env")

@router.get(
        "/wallet/{addr}/trust-score", 
        response_description="Seed initial training dataset from local json file", 
        status_code=status.HTTP_200_OK,
    )
async def trust_score(addr:str, request: Request):
    txs_old = []
    txs = {}
    if (wallet := request.app.database["wallets"].find_one({"address": addr})) is not None:
        txs_old = wallet['txrefs']
    txs_new = scraper.randomized_addr_fetch(addr)['txrefs']
    queries = []
    if len(txs_old) > 0:
        for tx in txs_old:
            txs[tx["hash"]] = tx
        for tx in txs_new:
            if tx["hash"] not in txs:
                queries.append(tx["hash"])
            if txs[tx["hash"]]['spent'] != tx['spent']:
                queries.append(tx["hash"])
            txs[tx["hash"]] = tx
    else:
        txs = txs_new
    txs = list(txs.values())
    request.app.database['wallets'].update_one({"address": addr}, {"txrefs": txs})

    res = []
    for tx in txs:
        # Scrape the data
        res.append(scraper.randomized_tx_fetch(tx['hash']))
    request.app.database['transactions'].insert_many(res)

    # Begin inference on all queries

    

