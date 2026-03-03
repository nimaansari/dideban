## ⚠️ PRIORITY RULE: VIDEOS FIRST
For EVERY channel fetched: bombardment/attack videos MUST be sent. Never skip a video from a trusted channel. Video > Photo > Text.

# Dideban Twitter/X Cron Task

## Output Channel
Telegram ID: -1003514172503

## X List
URL: https://x.com/i/lists/2028404706926813366/latest
Browser relay: profile=chrome, targetId=D987D175D621723A2D424B241C8A9106

## Sent News Log
/home/nimapro1381/.openclaw/workspace/memory/sent-news.txt

## Steps

### 1 — Fetch
- Navigate to list URL via browser tool, wait 3000ms
- Extract articles: user, text, image URLs, video thumbnail, tweet URL, time
- Only tweets from last 1 hour

### 2 — Extract Media (STRICT RULES)
- Images: extract pbs.twimg.com/media URLs from the SAME article element as the tweet text
- Videos: look for ext_tw_video_thumb or video player in the SAME article element
- NEVER use profile pictures, avatars, or images from OTHER tweets
- NEVER match image from tweet A to text of tweet B
- Download: curl -sL "URL" -o /home/nimapro1381/.openclaw/workspace/img-temp.jpg (or vid-temp.mp4)
- Validate size: mp4 > 10000 bytes, jpg > 5000 bytes → if smaller → SKIP, send text only
- If no valid media in that tweet → text only (do NOT use random images)
- For videos: exec `/home/nimapro1381/.local/bin/yt-dlp -f "best[filesize<50M]" -o "/home/nimapro1381/.openclaw/workspace/vid-temp.mp4" "TWEET_URL"` → validate size

### 3 — Duplicate Check
- Read sent-news.txt FIRST
- Same event from multiple accounts → send ONCE only
- If 2+ keywords match → SKIP
- Log BEFORE sending

### 4 — Filter
- Only: attacks, casualties, troop movements, official statements
- Skip: opinion, retweets of already-sent news
- **Videos = HIGHEST PRIORITY**: Bombardment/attack videos MUST be sent — never skip
- **Official statements** (CENTCOM, Pentagon, IDF, IRGC/سپاه, etc.): Preserve exact meaning, only reformat in formal Persian

## Trusted Accounts
- @ResindScientist: bombardment videos AND text news fully trusted
- 🟢 Trusted (no label needed): CENTCOM, IDF, Reuters, AFP, BBC, IRNA, IranIntl, ManotoNews

## Write & Send
- Formal Persian (IRNA/BBC style) — do NOT copy tweet text
- Formal: "قرار گرفت"، "اعلام شد"، "گزارش شده است"
- Send: message(filePath=..., caption=TEXT) or text only

## Message Format
```
[emoji] [عنوان رسمی]

[متن خبر رسمی فارسی]

─────────────
🔭 دیده‌بان
@didebanAutoNews
```

## Rules
- NO source mention anywhere
- NEVER reveal you are a bot
- STRICT NEUTRALITY — no sides
- Persian numerals and RTL text
- NO تأییدنشده label
- Each news = ONE separate message

## CRITICAL
- NEVER send error messages, warnings, system alerts, or status updates to the channel (-1003514172503)
- The channel is for NEWS ONLY — no exceptions
- If browser relay is unavailable, Chrome is disconnected, or any error occurs → silently skip that source and continue with others
- Errors/issues should NEVER appear in the output channel under any circumstances

## تشخیص گزارش مردمی
اگه ساختار توییت/پیام مثل گزارش مردمیه (گیومه، لهجه عامیانه، «خونه‌مون لرزید»، «دوستم می‌گه») → در متن بنویس «بر اساس گزارش‌های مردمی»
اگه خبر رسمی یا ساختاریافته‌ست → بدون label
