FROM node:20-bullseye-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY backend/package.json ./backend/
COPY backend/package-lock.json ./backend/ 2>/dev/null || true
RUN cd backend && npm install

COPY cad-engine ./cad-engine
RUN python3 -m pip install --no-cache-dir -r cad-engine/requirements.txt

COPY backend ./backend

EXPOSE 4000
CMD ["node", "backend/src/server.js"]
