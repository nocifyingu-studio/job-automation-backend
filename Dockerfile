# Use an official, fully configured Selenium image that already has Chrome installed
FROM seleniarm/standalone-chromium:latest

# Switch to root to configure Python paths smoothly
USER root

# Install Python 3 and pip securely without relying on breaking OS bundles
RUN apt-get update && apt-get install -y python3 python3-pip --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Map operational environment pointers to the pre-installed Chromium paths
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromiumdriver

WORKDIR /app

# Pull installation configurations securely
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
