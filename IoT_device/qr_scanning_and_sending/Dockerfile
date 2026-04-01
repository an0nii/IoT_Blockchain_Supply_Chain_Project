FROM balenalib/raspberrypi5-debian-python:3.11-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3-opencv \
       python3-picamera2 \
       libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
