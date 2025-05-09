FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./

RUN apt-get update && apt-get install -y gcc build-essential python3-dev

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get remove -y gcc build-essential python3-dev
RUN apt-get autoremove -y
RUN rm -rf /var/lib/apt/lists/*

RUN playwright install chromium && \
    playwright install-deps chromium

COPY . .

EXPOSE 8712

CMD ["python", "api_crawler.py"] 