FROM ubuntu:22.04

# Es gibt kein offizielles biolab/orange3-Image auf Docker Hub (nur nicht
# vertrauenswuerdige Drittanbieter-Images) - Orange3 wird deshalb hier per
# pip in einem eigenen Ubuntu-Image installiert und per Xvfb/x11vnc/noVNC
# im Browser bereitgestellt.
# Ubuntu 22.04 (Python 3.10) statt 24.04, weil dafuer auf aarch64 (Raspberry
# Pi) noch vorgebaute PyQt5/scipy/numpy-Wheels existieren. build-essential
# & Co. sind der Fallback, falls pip trotzdem aus dem Quellcode bauen muss.
ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    RESOLUTION=1600x900x24

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv python3-dev \
        build-essential gfortran pkg-config cmake ninja-build \
        libopenblas-dev liblapack-dev \
        xvfb x11vnc fluxbox novnc websockify \
        libgl1 libegl1 libxkbcommon0 libxcb-cursor0 libnss3 libxcomposite1 \
        libxdamage1 libxrandr2 libasound2 libxi6 libxtst6 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/orange-venv \
    && /opt/orange-venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
    && /opt/orange-venv/bin/pip install --no-cache-dir --prefer-binary orange3

ENV PATH="/opt/orange-venv/bin:${PATH}"

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 6080
ENTRYPOINT ["/start.sh"]
