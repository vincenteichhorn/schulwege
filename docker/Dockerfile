FROM python:3.12-slim

ARG FRONTEND_PORT=5173
ENV FRONTEND_PORT=${FRONTEND_PORT}

WORKDIR /schulwege

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pipx \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/vincenteichhorn/schulwege.git .

RUN pipx install poetry
ENV PATH="/root/.local/bin:$PATH"
RUN poetry install

EXPOSE $FRONTEND_PORT

HEALTHCHECK CMD curl --fail http://localhost:$FRONTEND_PORT/

ENTRYPOINT schulwege