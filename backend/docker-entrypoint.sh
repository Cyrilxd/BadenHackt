#!/bin/sh
set -eu

DATABASE_URL="${DATABASE_URL:-sqlite:////app/data/internet_control.db}"
DATABASE_PATH="${DATABASE_PATH:-/app/data/internet_control.db}"

case "$DATABASE_URL" in
  sqlite:///*)
    mkdir -p "$(dirname "$DATABASE_PATH")"
    if [ ! -f "$DATABASE_PATH" ]; then
      sqlite3 "$DATABASE_PATH" < /app/schema.sql
    fi
    ;;
esac

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
