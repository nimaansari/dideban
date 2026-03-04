#!/bin/bash
# Start dashboard + cloudflare tunnel and notify via telegram

cd "$(dirname "$0")"

# Start server
pkill -f "python3 server.py" 2>/dev/null
sleep 1
python3 server.py &>/tmp/dash.log &
sleep 3

# Download cloudflared if missing
if [ ! -f /tmp/cloudflared ]; then
  curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
  chmod +x /tmp/cloudflared
fi

# Start tunnel and capture URL
/tmp/cloudflared tunnel --no-autoupdate --url http://localhost:8080 2>/tmp/tunnel.log &

# Wait for URL
for i in {1..20}; do
  URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/tunnel.log 2>/dev/null | head -1)
  if [ -n "$URL" ]; then
    echo "Tunnel URL: $URL"
    # Send to telegram
    BOT_TOKEN=$(cat /home/nimapro1381/.openclaw/openclaw.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('channels',{}).get('telegram',{}).get('botToken',''))" 2>/dev/null)
    CHAT_ID="92219625"
    if [ -n "$BOT_TOKEN" ]; then
      curl -s "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d "chat_id=$CHAT_ID" \
        -d "text=🔗 داشبورد دیده‌بان: $URL" > /dev/null
    fi
    break
  fi
  sleep 2
done
