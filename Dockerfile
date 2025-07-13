FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

COPY . .

# Install dependencies + utilities + chromedriver
RUN apt update && apt install -y ffmpeg aria2 unzip wget curl gnupg ca-certificates && rm -rf /var/lib/apt/lists/*

# Install chromedriver matching latest version
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir yt-dlp

# Expose port if you run any webserver (optional)
# EXPOSE 8080

CMD ["python", "bot.py"]
