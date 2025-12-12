#!/bin/bash
set -e

echo "🚀 Starting SaaS Contabil Converter..."
echo "📊 PORT: ${PORT:-8000}"
echo "🌍 Environment: ${ENVIRONMENT:-production}"

# Use PORT environment variable, default to 8000
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info