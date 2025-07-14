FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

COPY . .


RUN apt update && apt install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt
RUN apt-get update && \
    apt-get install -y aria2

RUN pip install yt-dlp
CMD ["python", "bot.py"]
