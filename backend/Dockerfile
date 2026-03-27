FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    nftables \
    iproute2 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema.sql ./schema.sql
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY app/ ./app/

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

CMD ["docker-entrypoint.sh"]
