#!/bin/sh

# Start backend
python backend/app.py &

# Start frontend dev server
cd frontend
npm install
npm run dev -- --host 0.0.0.0

wait
