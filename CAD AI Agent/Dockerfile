FROM python:3.11-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y curl ca-certificates gnupg build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

COPY backend/package.json ./backend/
COPY cad-engine ./cad-engine
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN cd backend && npm install
RUN python3 -m pip install --no-cache-dir -r cad-engine/requirements.txt

COPY backend ./backend

EXPOSE 4000
CMD ["node", "backend/src/server.js"]
