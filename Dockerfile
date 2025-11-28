FROM python:3.9-slim

# Install build tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY repo /app

RUN if [ -f "/app/requirements.txt" ]; then \
    pip install --no-cache-dir -r /app/requirements.txt; \
    fi

CMD ["python3", "main.py"]
