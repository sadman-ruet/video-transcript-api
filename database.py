from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Generator

# MongoDB client and database setup
client = MongoClient("mongodb://localhost:27017")
db = client.RecSys
userDB = db.users  # User collection
chatDB = db.chats  # Chat collection
fileDB = db.files  
# Dependency to provide MongoDB collection (userDB)
def get_db() -> Generator:
    try:
        # You can yield the collection here to be used in route functions
        yield userDB
    finally:
        # MongoDB client does not need to explicitly close, but we can handle clean-up here
        pass

