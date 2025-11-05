# === STAGE 1: Build Stage (Uses uv for fast dependency resolution) ===
# Use a Python base image
FROM python:3.11-slim as builder

# Install uv (replace version if necessary)
RUN pip install uv

# Set the working directory
WORKDIR /app

# Copy only the requirements file
COPY requirements.txt .
# COPY pyproject.toml .

# RUN pip install -r requirements.txt
# Install dependencies into a virtual environment using uv
# This step is highly cacheable. Changes only trigger a rebuild here.

# === STAGE 2: Runtime Stage (Lightweight image) ===
# Use a fresh, minimal Python base image
FROM python:3.11-slim

# Copy the application code
WORKDIR /app
COPY . /app

# Copy the virtual environment from the builder stage
# COPY --from=builder /app/.venv /app/.venv

# Ensure the virtual environment is sourced
# ENV PATH="/app/.venv/bin:$PATH"

# Expose the port your application runs on (e.g., 8000 for FastAPI/Flask)
EXPOSE 8000

# Command to run your application
# CMD ['uv', 'run', 'uvicorn', "main:web"]
CMD ['bash']