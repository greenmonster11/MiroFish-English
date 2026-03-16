#!/bin/bash
# Start nginx and backend together

# Start nginx in background
nginx

# Start Flask backend
cd /app/backend
exec python3 run.py
