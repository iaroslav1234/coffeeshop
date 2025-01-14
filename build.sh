#!/bin/sh
set -e
cd frontend
npm install
npm run build
cd ..
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/build/* backend/static/
