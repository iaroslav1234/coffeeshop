#!/bin/sh
. /opt/venv/bin/activate
exec gunicorn --chdir backend --bind 0.0.0.0:$PORT app:app
