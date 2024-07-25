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
import concurrent.futures

router = APIRouter()

config = dotenv_values(".env")

def multi_upsert_tx(txs, request):
    operations = [
        UpdateOne({"hash": tx["hash"]}, {"$set": tx}, upsert=True)
        for tx in txs
    ]
    request.app.database['transactions'].bulk_write(operations)
    for tx in txs:
        print(f"Successfully upsertex tx {tx['hash']}")

def parallelize_fetch_tx(txs):
    workers = len(txs)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(scraper.randomized_tx_fetch, txs[i]) for i in range(len(txs))]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results

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
                txs[tx["tx_hash"]] = tx
            for tx in txs_new:
                if tx["tx_hash"] not in txs:
                    queries.append(tx["tx_hash"])
        else:
            for tx in txs_new:
                txs[tx["tx_hash"]] = tx
        txs = list(txs.values())
        _ = request.app.database['wallets'].update_one(
            {"address": addr},
            {"$set": {"txrefs": txs}},
            upsert=True  # Optional: to insert the document if it doesn't exist
        )

        res = parallelize_fetch_tx([tx['tx_hash'] for tx in txs])
        
        # Update/insert new txs
        multi_upsert_tx(res,request)

        # Update/insert new txs neighbors
        neighbors = {}
        edges = []
        e = 0
        for n0 in res:
            if n0['hash'] not in neighbors:
                neighbors[n0['hash']] = []
            for n0_input_tx in n0['inputs']:
                edges.append((n0['hash'], n0_input_tx['prev_hash']))
                res_n1 = parallelize_fetch_tx([n0_input_tx['prev_hash']])
                neighbors[n0['hash']].append(res_n1)
                for n1 in res_n1:
                    if n1['hash'] not in neighbors:
                        neighbors[n1['hash']] = []
                    for n1_input_tx in n1['inputs']:
                        edges.append((n1['hash'], n1_input_tx['prev_hash']))
                        res_n2 = parallelize_fetch_tx([n1_input_tx['prev_hash']])
                        neighbors[n1['hash']].append(res_n2)
            e += 1
            print(f"Edge done: {e}/{len(res)}")
        multi_upsert_tx([v for _, v in neighbors.items()], request)

        # Begin inference on all queries
        
        inference_res = {}

        for hash, flag in inference_res:
            filter = {"address": addr, "txrefs.hash": hash}
            request.app.database['wallets'].update_one(filter, {"licit": flag})    

        # Fetch the wallet again and recalculate the score
        wallet = request.app.database["wallets"].find_one({"address": addr})
        try:
            score = calc_trust(wallet)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=e)
        return {"address": addr, "score": score, "txrefs": wallet['txrefs']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
