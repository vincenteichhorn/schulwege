#!/usr/bin/env bash

export $(grep -v '^#' .env | xargs)

cd backend && uvicorn src.api:app --reload --host 127.0.0.1 --port $BACKEND_PORT

cd ../frontend && npm run dev -- --host 127.0.0.1 --port $FRONTEND_PORT