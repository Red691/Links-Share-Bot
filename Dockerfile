# Base image
FROM python:3.8-slim-buster

# Install build tools required for TgCrypto
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Run bot
CMD ["python3", "main.py"]
