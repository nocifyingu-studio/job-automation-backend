# Use a complete stable runtime image to bypass exit code 100 network conflicts
FROM python:3.11-slim

# Force fix apt mirrors and install system dependencies for headless Chromium setup
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Map operational environment pointers cleanly
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromiumdriver

WORKDIR /app

# Pull installation configurations securely
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
