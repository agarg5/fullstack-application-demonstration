# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install SQLite (included in Python image, but ensure dev tools if needed)
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./backend/

# Create directory for SQLite database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/database.db

# Expose port (adjust as needed)
EXPOSE 8000
EXPOSE 3000

# Run the application
COPY start.sh .

RUN chmod +x start.sh

# Run both frontend and backend
CMD ["./start.sh"]
