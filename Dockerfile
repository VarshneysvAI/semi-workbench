# Stage 1: Build the Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY dashboard/ ./dashboard/
RUN cd dashboard && npm install && npm run build

# Stage 2: Build the Backend and serve everything
FROM python:3.11-slim
# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Copy the built frontend from Stage 1
COPY --from=frontend-builder /app/dashboard/dist /app/dashboard/dist

RUN pip install --no-cache-dir -r backend/requirements.txt
RUN playwright install
RUN playwright install-deps

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "backend.live_app:app", "--host", "0.0.0.0", "--port", "8000"]
