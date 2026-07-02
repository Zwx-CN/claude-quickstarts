FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    DISPLAY=:99 \
    CU_SCREEN_WIDTH=1280 \
    CU_SCREEN_HEIGHT=720

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dbus-x11 \
    fonts-dejavu \
    novnc \
    openbox \
    procps \
    python3-tk \
    websockify \
    x11vnc \
    xauth \
    xclip \
    xdotool \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts

RUN pip install --no-cache-dir -e .

EXPOSE 8000 6080 5900

CMD ["bash", "scripts/start_desktop_api.sh"]
