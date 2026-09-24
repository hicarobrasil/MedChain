#!/bin/sh

echo "\n==== Applying migrations ===="
alembic -c app/database/alembic.ini upgrade head

# Starting Application
echo "\n==== Running application ===="
uvicorn app.main:app --host 0.0.0.0 --port 8300 --reload
