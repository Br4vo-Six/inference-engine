from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
import os
import json
from dotenv import dotenv_values
from models import wallet, tx
from pydantic.tools import parse_obj_as
from fastapi import FastAPI
from dotenv import dotenv_values
from pymongo import MongoClient
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

config = dotenv_values(".env")

def load_training(collection):
    with open(os.path.join(config['DATASET_DIR'], config['MERGED_JSON'])) as f:
        data = json.load(f)
    i = 0
    batch_size = 1000
    for c in range(0, len(data), batch_size):
        data_model = [parse_obj_as(tx.Tx, entry['res']).dict() for entry in data[c:c+batch_size]]
        collection.insert_many(data_model)
        i += 1
        os.system('cls')
        print(f"Inserted {c}/{len(data)} entries")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = MongoClient(config["MONGODB_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to the MongoDB database!")
    app.database['transactions'].create_index("hash", unique=True)
    app.database['wallets'].create_index("address", unique=True)
    load_training(app.database['transactions'])
    yield
    app.mongodb_client.close()
    print("Connection to MongoDB is closed")

app = FastAPI(lifespan=lifespan)
app.mongodb_client = MongoClient(config["MONGODB_URI"])
app.database = app.mongodb_client[config["DB_NAME"]]

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)