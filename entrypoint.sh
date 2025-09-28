#!/bin/sh

echo "\n==== Applying migrations ===="
alembic -c app/database/alembic.ini upgrade head

# Starting Application
echo "\n==== Running application ===="
gunicorn -b 0.0.0.0:8300 app.main:app \
    --workers=1 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --reload \
    --timeout 600
