FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and dependencies
COPY pyproject.toml poetry.lock* ./
RUN pip install uv && uv pip install --system --requirement <(uv pip compile pyproject.toml)

# Copy application code
COPY . .

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
