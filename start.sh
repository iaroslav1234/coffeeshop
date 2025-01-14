#!/bin/sh
set -e
echo "Activating virtual environment..."
. /opt/venv/bin/activate
echo "Starting gunicorn..."
exec gunicorn --chdir backend --bind 0.0.0.0:$PORT --log-level debug app:app
