from fastapi import APIRouter, Body, Request, Response, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from typing import List
import os
import json
from dotenv import dotenv_values
from models import wallet, tx
from pydantic.tools import parse_obj_as
from scraper import scraper
import math
from pymongo import UpdateOne

router = APIRouter()

config = dotenv_values(".env")

def multi_upsert_tx(txs, request):
    operations = [
        UpdateOne({"hash": entry["hash"]}, {"$set": entry}, upsert=True)
        for entry in txs
    ]
    request.app.database['transactions'].bulk_write(operations)

def calc_trust(wallet, r=9):
    nc = 0
    nd = 0
    sc = 0
    sd = 0
    for tx in wallet['txrefs']:
        if tx['licit'] == False:
            nd += 1
            sd += tx['value']
        else:
            nc += 1
            sc += tx['value']
    fc = sc*math.sqrt(nc)
    fd = sd*math.sqrt(nd)
    return fc/(fc+(r*fd))

@router.get(
        "/wallet/{addr}/trust-score", 
        response_description="Seed initial training dataset from local json file", 
        status_code=status.HTTP_200_OK,
    )
async def trust_score(addr:str, request: Request):
    try:
        txs_old = []
        txs = {}
        if (wallet := request.app.database["wallets"].find_one({"address": addr})) is not None:
            txs_old = wallet['txrefs']
        txs_new = scraper.randomized_addr_fetch(addr)['txrefs']
        if txs_new == None:
            raise HTTPException(status_code=404, detail="Wallet address not found on public ledger")
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
        
        # Update/insert new txs
        multi_upsert_tx(res,request)

        # Update/insert new txs neighbors
        for el in res:
            # input_queries = []
            # output_queries = []
            res = []
            for input_tx in el['inputs']:
                res.append(scraper.randomized_tx_fetch(input_tx['prev_hash']))
                # input_queries.append(input_tx['prev_hash'])
            for output_tx in el['outputs']:
                if output_tx['spent_by'] != None:
                    res.append(scraper.randomized_tx_fetch(output_tx['spent_by']))
                    # output_queries.append(output_tx['spent_by'])
            multi_upsert_tx(res,request)

        # Begin inference on all queries
        
        inference_res = {}

        for hash, flag in inference_res:
            filter = {"address": addr, "txrefs.hash": hash}
            request.app.database['wallets'].update_one(filter, {"licit": flag})    

        # Fetch the wallet again and recalculate the score
        wallet = request.app.database["wallets"].find_one({"address": addr})
        score = calc_trust(wallet)
        return {"address": addr, "score": score, "txrefs": wallet['txrefs']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
