FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive

# სისტემური პაკეტები
RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    gcc \
    python3-rpi.gpio \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements.txt ჩატვირთვა
COPY requirements.txt .

# Python ბიბლიოთეკების ინსტალაცია
RUN pip install --no-cache-dir -r requirements.txt

# კოდის ჩატვირთვა
COPY . .

EXPOSE 5537

# Default command
CMD ["python", "sensor.py"]

