#!/bin/bash
# Start DIDEBAN dashboard + Cloudflare tunnel

cd "$(dirname "$0")"

echo "Starting dashboard server..."
python3 server.py &
SERVER_PID=$!
sleep 3

echo "Starting Cloudflare tunnel..."
/tmp/cloudflared tunnel --no-autoupdate --url http://localhost:8080 2>&1 | tee /tmp/tunnel.log | grep -m1 "trycloudflare.com" | grep -oP 'https://[^\s]+' | while read url; do
  echo "Dashboard live at: $url"
  # Optional: send URL via telegram notification
done &

echo "Server PID: $SERVER_PID"
echo "Press Ctrl+C to stop"
wait $SERVER_PID
