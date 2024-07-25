from fastapi import APIRouter, Body, Request, Response, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from typing import List
import os
import json
from dotenv import dotenv_values
import models
from pydantic.tools import parse_obj_as
import models.wallet
from scraper import scraper
import math
from pymongo import UpdateOne
import concurrent.futures
from pydantic.tools import parse_obj_as

router = APIRouter()
config = dotenv_values(".env")

def multi_upsert_tx(txs, request):
    operations = [
        UpdateOne({"hash": tx["hash"]}, {"$set": tx}, upsert=True)
        for tx in txs
    ]
    request.app.database['transactions'].bulk_write(operations)
    for tx in txs:
        print(f"Successfully upserted tx {tx['hash']}")

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
        if (new_wallet := request.app.database["wallets"].find_one({"address": addr})) is not None:
            txs_old = new_wallet['txrefs']
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
        new_wallet_obj = parse_obj_as(models.wallet.Wallet, new_wallet).dict()
        print(new_wallet_obj)
        _ = request.app.database['wallets'].update_one(
            {"address": addr},
            {"$set": new_wallet_obj},
            upsert=True  # Optional: to insert the document if it doesn't exist
        )
        
        res = parallelize_fetch_tx([tx['tx_hash'] for tx in txs])
        
        # Update/insert new txs
        multi_upsert_tx(res,request)

        filters = [tx_new['tx_hash'] for tx_new in txs_new]
        print(f"n0 filters: {filters}")
        n0_txs = list(request.app.database["transactions"].find({"hash": {"$in": filters}}))
        print(f"n0 vertices: {[n0_tx['hash'] for n0_tx in n0_txs]}")

        # Update/insert new txs neighbors
        upsert_txs = {}
        edges = []
        e = 0
        for n0 in n0_txs:
            upsert_txs[n0['hash']] = n0
            for n0_input_tx in n0['inputs']:
                edges.append((n0['hash'], n0_input_tx['prev_hash']))
            filters = [n0_input_tx['prev_hash'] for n0_input_tx in n0['inputs']]
            print(f"n1 filters: {filters}")
            n1_fetch = list(request.app.database["transactions"].find({"hash": {"$in": filters}}))
            n1_exist = [item["hash"] for item in n1_fetch]
            n1_not_exist = [tx_hash for tx_hash in filters if tx_hash not in n1_exist]
            if len(n1_not_exist) > 0:
                n1_res = parallelize_fetch_tx(n1_not_exist)
            else:
                n1_res = []
            n1_txs = n1_fetch + n1_res
            print(f"n1 vertices: {[n1_tx['hash'] for n1_tx in n1_txs]}")
            for n1 in n1_txs:
                upsert_txs[n1['hash']] = n1
                for n1_input_tx in n1['inputs']:
                    edges.append((n1['hash'], n1_input_tx['prev_hash']))
                filters = [n1_input_tx['prev_hash'] for n1_input_tx in n1['inputs']]
                print(f"n2 filters: {filters}")
                n2_fetch = list(request.app.database["transactions"].find({"hash": {"$in": filters}}))
                n2_exist = [item["hash"] for item in n2_fetch]
                n2_not_exist = [tx_hash for tx_hash in filters if tx_hash not in n2_exist]
                if len(n2_not_exist) > 0:
                    n2_res = parallelize_fetch_tx(n2_not_exist)
                else:
                    n2_res = []
                n2_txs = n2_fetch + n2_res
                print(f"n2 vertices: {[n2_tx['hash'] for n2_tx in n2_txs]}")
                for n2 in n2_txs:
                    upsert_txs[n2['hash']] = n2
            e += 1
            print(f"Edge done: {e}/{len(res)}")
        print(edges)
        all_txs = [v for _, v in upsert_txs.items()]
        multi_upsert_tx(all_txs, request)

        # Begin inference on all queries
        # Create edges: list[tuple[str, str]]
        # Create all_txs: list[Tx]
        
        inference_res = {}

        filters = {"address": addr}
        update_operations = {"$set": {}}
        array_filters =  []
        i = 0
        for tx_hash, flag in inference_res:
            update_operations["$set"][f"txrefs.$elem{i}.licit": flag]
            array_filters.append({f"elem{i}.tx_hash": tx_hash})
            i += 1
        request.app.database["wallets"].update_one(filters, update_operations, array_filters=array_filters)

        # Fetch the wallet again and recalculate the score
        wallet = request.app.database["wallets"].find_one({"address": addr})
        print(f"Wallet: {wallet}")
        try:
            score = calc_trust(wallet)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=e)
        return {"address": addr, "score": score, "txrefs": wallet['txrefs']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
