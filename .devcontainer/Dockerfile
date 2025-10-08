FROM mcr.microsoft.com/devcontainers/python:3.11

# System dependencies
RUN apt-get update && apt-get install -y \
    git curl wget build-essential ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set work directory
WORKDIR /workspaces/app
