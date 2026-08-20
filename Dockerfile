FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD uvicorn backend.live_app:app --host 0.0.0.0 --port ${PORT:-8000}
