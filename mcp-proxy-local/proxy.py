import json
import os
import sys
import threading
import time
from urllib.parse import urljoin

import requests

SSE_URL = os.environ.get("MCP_SSE_URL", "http://datenkrake.local:3001/sse")


def _parse_sse(stream, on_event):
    event = None
    data_lines = []
    for line in stream.iter_lines(decode_unicode=True):
        if line is None:
            continue
        if line == "":
            if data_lines:
                data = "\n".join(data_lines)
                on_event(event, data)
            event = None
            data_lines = []
            continue
        if line.startswith("event:"):
            event = line.split(":", 1)[1].strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())


def main():
    messages_url = {"value": None}
    ready = threading.Event()
    stop = threading.Event()

    def handle_event(event, data):
        if event == "endpoint":
            messages_url["value"] = urljoin(SSE_URL, data)
            ready.set()
            return
        if event == "message":
            sys.stdout.write(data + "\n")
            sys.stdout.flush()

    def sse_thread():
        while not stop.is_set():
            try:
                with requests.get(
                    SSE_URL,
                    stream=True,
                    headers={"Accept": "text/event-stream"},
                    timeout=(10, None)
                ) as resp:
                    resp.raise_for_status()
                    _parse_sse(resp, handle_event)
            except requests.RequestException as exc:
                sys.stderr.write(f"SSE connection error: {exc}\n")
                sys.stderr.flush()
                time.sleep(2)

    thread = threading.Thread(target=sse_thread, daemon=True)
    thread.start()

    if not ready.wait(timeout=20):
        sys.stderr.write("SSE handshake timed out.\n")
        sys.stderr.flush()
        stop.set()
        return

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            sys.stderr.write("Invalid JSON from stdin.\n")
            sys.stderr.flush()
            continue
        try:
            requests.post(
                messages_url["value"],
                data=line,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
        except requests.RequestException as exc:
            sys.stderr.write(f"POST failed: {exc}\n")
            sys.stderr.flush()
            time.sleep(1)


if __name__ == "__main__":
    main()
