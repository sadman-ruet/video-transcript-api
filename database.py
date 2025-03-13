from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from gridfs import GridFS
from typing import List, Generator

# MongoDB client and database setup
client = MongoClient("mongodb://localhost:27017")
db = client.RecSys
userDB = db.users  # User collection
chatDB = db.chats  # Chat collection
fileDB = db.files

fs = GridFS(db)

def get_fs() -> Generator:
    try:
        yield fs
    finally:
        pass

