#!/bin/bash
cd ../backend
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
python -m flask run --port=5001
