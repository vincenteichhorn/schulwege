#!/usr/bin/env bash

export $(grep -v '^#' .env | xargs)
cd frontend && npm run dev -- --host 127.0.0.1 --port $FRONTEND_PORT