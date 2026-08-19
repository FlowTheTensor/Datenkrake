#!/bin/sh
set -e

Xvfb "$DISPLAY" -screen 0 "$RESOLUTION" &
sleep 2

fluxbox &
x11vnc -display "$DISPLAY" -forever -shared -nopw -rfbport 5900 -quiet &
websockify --web=/usr/share/novnc/ 6080 localhost:5900 &

# Orange3-Datenordner (per Volume gemountet) muss vorhanden sein
mkdir -p /root/.local/share/orange3

exec Orange3
