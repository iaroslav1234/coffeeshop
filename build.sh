#!/bin/sh
cd frontend
npm install
npm run build
cd ..
mkdir -p backend/static
cp -r frontend/build/* backend/static/
