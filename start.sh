#!/bin/sh
# Startup script for Render deployment
# Uses PORT environment variable set by Render

exec uvicorn script.api:app --host 0.0.0.0 --port ${PORT:-8011}

