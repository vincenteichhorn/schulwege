#!/usr/bin/env bash

export $(grep -v '^#' .env | xargs)

cd backend && poetry run uvicorn src.api:api --reload --host 127.0.0.1 --port $BACKEND_PORT
