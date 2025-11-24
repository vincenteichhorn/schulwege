FROM python:3.12-slim

ENV FRONTEND_PORT=5173

WORKDIR /schulwege

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pipx \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install poetry
ENV PATH="/root/.local/bin:$PATH"

COPY scripts/wait_for.sh /usr/local/bin/wait_for.sh
RUN chmod +x /usr/local/bin/wait_for.sh

EXPOSE $FRONTEND_PORT
HEALTHCHECK CMD curl --fail http://localhost:$FRONTEND_PORT/ || exit 1

ENTRYPOINT /bin/sh -c "\
  wait_for.sh http://schulwege-nominatim:8080/status && \
  wait_for.sh http://schulwege-opentripplanner:8080 && \
  poetry install && \
  poetry run streamlit run schulwege/app.py --server.port $FRONTEND_PORT"
