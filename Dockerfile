FROM python:3.12-slim

WORKDIR /app

# Установка wkhtmltopdf
RUN apt-get update && apt-get install -y --no-install-recommends wkhtmltopdf \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
