# SEMI Deployment Guide

## Local Run
```bash
python -m backend.cli run --input test_input.csv --output output/
```

## Live API (Local)
```bash
uvicorn backend.live_app:app --port 8000 --reload
```

## Render Deployment
Simply link the repository to Render and use the provided `render.yaml`.
