FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Set working directory
WORKDIR /workspace

# Install project dependencies
RUN poetry install --no-interaction --no-ansi || true

# Clean up
RUN rm -rf /tmp/* /var/tmp/*
