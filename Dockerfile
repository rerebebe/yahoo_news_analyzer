FROM python:3.11-slim


RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Tell scraper.py where to find them (指定容器內剛安裝好的 chromium 瀏覽器與 chromedriver 的路徑，讓 scraper.py 直接讀取使用，不用在執行時另外下載。)
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

# Install Python deps first(no ccache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# `print()` shows up in `docker logs`
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]