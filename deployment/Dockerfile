# ---------------------------
# Base image
# ---------------------------
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy entire source
COPY . /app

# Copy Nginx config
COPY deployment/nginx.conf /etc/nginx/nginx.conf

# Copy Supervisor config
COPY deployment/supervisor.conf /etc/supervisor/conf.d/supervisor.conf

# Expose ports
EXPOSE 80

# Run Supervisor (manages Gunicorn + Nginx)
CMD ["supervisord", "-n"]
