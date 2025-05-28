FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

COPY . .


RUN apt update && apt install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt
RUN apt-get update && \
    apt-get install -y aria2

RUN apt-get update && apt-get install -y libtorrent-rasterbar-dev
RUN pip install yt-dlp
RUN pip install gdown
RUN pip install lxml_html_clean
CMD ["python", "bot.py"]
