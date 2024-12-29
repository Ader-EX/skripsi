from typing import List
from fastapi import Depends, FastAPI, HTTPException,status
import os
from os.path import splitext
from database import Base
from database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow specific origin
    allow_credentials=True,  # If you need to support credentials (e.g., cookies)
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def test_hello():
    return {
        "message" : "Test"
    }