#!/usr/bin/env python3
"""
Fetches a Telegram public channel and extracts posts with their media.
Usage: python3 fetch_channel.py CHANNEL_NAME [minutes_ago]
Output: JSON array of posts with text, image_url, video_url
"""
import sys, json, re, urllib.request, time

CHANNEL = sys.argv[1].lstrip('@')
MINUTES = int(sys.argv[2]) if len(sys.argv) > 2 else 30

url = f"https://t.me/s/{CHANNEL}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)

# Split into individual post blocks
post_blocks = re.split(r'(?=<div class="tgme_widget_message\b)', html)

posts = []
now = time.time()
cutoff = now - (MINUTES * 60)

for block in post_blocks:
    if 'tgme_widget_message_text' not in block and 'tgme_widget_message_photo' not in block and 'tgme_widget_message_video' not in block:
        continue

    # Extract post time
    time_match = re.search(r'datetime="([^"]+)"', block)
    if time_match:
        from datetime import datetime, timezone
        try:
            dt = datetime.fromisoformat(time_match.group(1).replace('Z', '+00:00'))
            post_time = dt.timestamp()
            if post_time < cutoff:
                continue
        except:
            pass

    # Extract text (only from this post's text div)
    text_match = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
    text = ''
    if text_match:
        text = re.sub(r'<[^>]+>', '', text_match.group(1)).strip()
    
    # For media-only posts, still include if they have video/image

    # Extract image ONLY from tgme_widget_message_photo_image within this block
    image_url = None
    img_match = re.search(r'tgme_widget_message_photo_image[^>]*src="([^"]+)"', block)
    if not img_match:
        img_match = re.search(r'<img[^>]+class="[^"]*tgme_widget_message_photo[^"]*"[^>]*src="([^"]+)"', block)
    if img_match:
        image_url = img_match.group(1)

    # Extract video — ONLY from video tags inside this exact post's media wrap
    video_url = None
    # Only look inside tgme_widget_message_video wrapper
    video_wrap_match = re.search(
        r'class="tgme_widget_message_video[^"]*".*?<video[^>]*src="([^"]+)"',
        block, re.DOTALL
    )
    if video_wrap_match:
        video_url = video_wrap_match.group(1)
    else:
        # Fallback: video src attribute directly in this block only if text is empty (media-only post)
        if not text:
            vid_match = re.search(r'<video[^>]*src="(https?://[^"]+\.mp4[^"]*)"', block)
            if vid_match:
                video_url = vid_match.group(1)

    # Extract post URL for yt-dlp
    post_url_match = re.search(rf'https://t\.me/{CHANNEL}/(\d+)', block)
    post_url = post_url_match.group(0) if post_url_match else None

    posts.append({
        'text': text[:500],
        'image_url': image_url,
        'video_url': video_url,
        'post_url': post_url,
        'time': time_match.group(1) if time_match else None
    })

print(json.dumps(posts, ensure_ascii=False, indent=2))
