#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "Installing Playwright browsers for Crawl4AI..."
playwright install chromium

echo "Build complete!"
