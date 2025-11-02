FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py ./

ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_PATH=/usr/bin/chromium

EXPOSE 4444

CMD ["python", "server.py"]
