FROM ubuntu:24.04

# Es gibt kein offizielles biolab/orange3-Image auf Docker Hub (nur nicht
# vertrauenswuerdige Drittanbieter-Images) - Orange3 wird deshalb hier per
# pip in einem eigenen Ubuntu-Image installiert und per Xvfb/x11vnc/noVNC
# im Browser bereitgestellt.
ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    RESOLUTION=1600x900x24

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv \
        xvfb x11vnc fluxbox novnc websockify \
        libgl1 libegl1 libxkbcommon0 libxcb-cursor0 libnss3 libxcomposite1 \
        libxdamage1 libxrandr2 libasound2t64 libxi6 libxtst6 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/orange-venv \
    && /opt/orange-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/orange-venv/bin/pip install --no-cache-dir orange3

ENV PATH="/opt/orange-venv/bin:${PATH}"

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 6080
ENTRYPOINT ["/start.sh"]
