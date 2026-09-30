# ──────────────────────────────────────────────
# Samsung PRISM Troubleshooting Engine — Dockerfile
# Multi-stage: build React frontend, then serve via FastAPI
# ──────────────────────────────────────────────

# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --prefer-offline
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + built frontend assets
FROM python:3.10-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy data files used by backend
COPY data_quality_report.json raw_troubleshooting.json sources.json Theme2_Knowledge_Brain_Raw_Data.json ./

# Copy architecture visualisation HTML (served by /2d and /3d routes)
COPY samsung-prism-architecture.html project-3d-architecture.html ./

# Copy built frontend dist from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

WORKDIR /app/backend
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
