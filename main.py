from fastapi import FastAPI
from dotenv import dotenv_values
from pymongo import MongoClient
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

config = dotenv_values(".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = MongoClient(config["MONGODB_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to the MongoDB database!")
    yield
    app.mongodb_client.close()
    print("Connection to MongoDB is closed")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"Bravo Six": "Going Dark"}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
