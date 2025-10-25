import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv


# Load the shared .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api = FastAPI()

# Enable local dev communication
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/api/message")
def read_message():
    return {"message": "Hello from FastAPI!"}
