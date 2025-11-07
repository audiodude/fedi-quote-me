# Multi-stage build for Mastodon Quotability Manager Web App

# Stage 1: Build Vue frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY webapp/frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY webapp/frontend/ ./

# Build for production
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

WORKDIR /app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Python dependency files
COPY Pipfile Pipfile.lock* ./

# Install Python dependencies
RUN pipenv install --system --deploy --ignore-pipfile

# Copy Python library
COPY mastodon_quotability/ ./mastodon_quotability/

# Copy backend
COPY webapp/backend/ ./webapp/backend/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./webapp/frontend/dist

# Create directory for credentials (will be mounted as volume in production)
RUN mkdir -p /root/.mastodon_quotability && chmod 700 /root/.mastodon_quotability

# Expose port
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=webapp/backend/app.py
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "webapp/backend/app.py"]
