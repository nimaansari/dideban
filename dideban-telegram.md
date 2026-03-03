## ⚠️ PRIORITY RULE: VIDEOS FIRST
For EVERY channel fetched: bombardment/attack videos MUST be sent. Never skip a video from a trusted channel. Video > Photo > Text.

# Dideban Telegram Cron Task

## Output Channel
Telegram ID: -1003514172503

## Source Channels (ALL 15 — this is the ONLY telegram cron now)
Fetch each via fetch_channel.py:
**Media-heavy (video/photo priority):** @VahidOnline, @overlordechokilo, @mamlekate, @ManotoTV, @IranintlTV, @bbcpersian
**Text/news:** @SaberinFa, @tehran_timse, @defender_iran, @final_battle313, @gordanesam313, @sarbazane_g, @Parvazdaroj, @AdsVipz, @irannotam

## Sent News Log
/home/nimapro1381/.openclaw/workspace/memory/sent-news.txt

## Step-by-Step for EACH news item:

### Step 1 — Fetch & Filter
- For EACH channel run: exec `python3 /home/nimapro1381/.openclaw/workspace/fetch_channel.py CHANNELNAME 30`
- This returns JSON posts with: text, image_url, video_url, post_url — already filtered to last 30 min
- Use ONLY image_url/video_url from this script output — do NOT manually parse HTML for images
- Match media STRICTLY to its own post — each t.me/s/ post is in a `tgme_widget_message` div; only use the image/video found INSIDE that exact div, never from another post's div
- Only: attacks, casualties, troop movements, official statements
- **Videos = HIGHEST PRIORITY**: Any bombardment/attack video from trusted channels MUST be sent — never skip videos
- **Official statements** (CENTCOM, Pentagon, IRGC/سپاه, وزارت دفاع, رئیس‌جمهور, etc.): Translate/rewrite in formal Persian but preserve exact meaning — do NOT alter or editorialize their statements
- To get video with auth token: use the Python script that fetches token-authenticated URLs, then download immediately
- Skip: opinion, ideology, emotions
- @sarbazane_g: all posts OK, but IRGC official statements = fully verified
- @mamlekate: گزارش‌های مردمی هستن — در متن خبر بنویس «بر اساس گزارش‌های مردمی» یا «شهروندان گزارش می‌دهند»
- @final_battle313: only videos filmed INSIDE Iran

### Step 2 — Duplicate Check
- Read sent-news.txt
- If 2+ keywords match → SKIP
- IMPORTANT: Log to sent-news.txt BEFORE sending (not after) to prevent duplicates from parallel agents
- Dedup check: before sending, re-read sent-news.txt one more time to catch any entries added by parallel agent
- If 2+ keywords match existing entry → SKIP

### Step 3 — Find Media (MANDATORY — do this for EVERY news item)
Follow this order:

**A. Check for video in the post:**
- Look for video URLs in the fetched HTML (t.me/s/ pages have video thumbnails and links)
- If found, extract the post URL (e.g. https://t.me/VahidOnline/1234)
- Download: exec `"/home/nimapro1381/.local/bin/yt-dlp" -f "best[filesize<50M]" -o "/home/nimapro1381/.openclaw/workspace/vid-temp.mp4" "POST_URL"`
- Trusted for videos without question: @VahidOnline, @overlordechokilo, @mamlekate, @ManotoTV, @IranintlTV
- @bbcpersian: war and bombardment videos and news are fully trusted — always use them
- These channels post a LOT of bombardment videos — actively look for videos in EVERY post from these channels
- Even if the post has no text news, if it has a bombardment/attack video from these channels → download and send it
- Do not wait for text confirmation — videos from these trusted channels are self-validating

**B. Extract images and videos directly from fetched HTML:**
- After web_fetch of t.me/s/CHANNEL, extract ALL URLs matching cdn1.telesco.pe or cdn*.telegram.org
- .mp4 URLs = videos → download with: exec `curl -sL "VIDEO_URL" -o "/home/nimapro1381/.openclaw/workspace/vid-temp.mp4"`
  → VALIDATE: exec `ls -la /home/nimapro1381/.openclaw/workspace/vid-temp.mp4` — if size < 10000 bytes → URL expired, skip this media, try next URL
- .jpg/.webp URLs = images → download with: exec `curl -sL "IMAGE_URL" -o "/home/nimapro1381/.openclaw/workspace/img-temp.jpg"`
  → VALIDATE: exec `ls -la /home/nimapro1381/.openclaw/workspace/img-temp.jpg` — if size < 5000 bytes → URL expired, skip, try next URL
- Match the media URL to its post by proximity in the HTML

**C. If no image in post, search the web:**
- Use web_fetch on news sites to find images:
  Try: web_fetch("https://www.farsnews.ir/search?q=KEYWORDS") or web_fetch("https://www.isna.ir/search?q=KEYWORDS")
- Extract og:image or <img src=> URL from fetched HTML
- Download with curl -sL "URL" -o /home/nimapro1381/.openclaw/workspace/img-temp.jpg

**D. Image validation:**
- Search web for the image filename or description
- If image appears in news BEFORE today → news is likely FAKE → SKIP the entire item
- If image is fresh (not found in old articles) → use it

**E. If absolutely no media found → send text only (last resort)**
**CRITICAL IMAGE RULES — READ CAREFULLY:**
When fetching t.me/s/CHANNEL, the HTML has TWO types of images:
1. Channel avatar (FORBIDDEN): appears in `<img class="tgme_channel_info_header_image">` or as og:image meta tag → NEVER USE THIS
2. Post photos (ALLOWED): appear in `<img class="tgme_widget_message_photo_image">` → USE THESE ONLY

To extract correct images:
- Search HTML for `tgme_widget_message_photo_image` class → get the src URL
- OR search for `cdn1.telesco.pe` URLs that appear AFTER post text content, not at page top
- NEVER use og:image or the first image in the page
- NEVER use images from the `tgme_channel_info` section
- If no `tgme_widget_message_photo_image` found → text only, NO fallback to random images

### Step 4 — Write & Send
- Write news in formal Persian yourself (do NOT copy-paste)
  - Use professional news agency style (like IRNA or BBC Persian)
  - Formal constructions: "قرار گرفت"، "اعلام شد"، "گزارش شده است"، "حاکی است از"
  - Avoid informal words: "زدن"، "رفتن" → use "حمله شد"، "اعزام شد"
- Send via message tool:
  - With video: `message(action=send, channel=telegram, target=-1003514172503, filePath=/home/nimapro1381/.openclaw/workspace/vid-temp.mp4, caption=TEXT)`
  - With image: `message(action=send, channel=telegram, target=-1003514172503, filePath=/home/nimapro1381/.openclaw/workspace/img-temp.jpg, caption=TEXT)`
  - Text only: `message(action=send, channel=telegram, target=-1003514172503, message=TEXT)`

### Step 5 — Log
Append to sent-news.txt: `keyword1|keyword2|SOURCE_CHANNEL|timestamp`
Example: `قم|انبار|tسلیحاتی|@mamlekate|2026-03-02T21:07Z`

## Message Format
```
[emoji] [عنوان کوتاه]

[متن خبر به فارسی]

─────────────
🔭 دیده‌بان
@didebanAutoNews
```

Emojis: 💥حمله | 🚀موشک/پهپاد | ⚓دریایی | ✈️هوایی | 🏥تلفات | 🇮🇷ایران | 🇺🇸آمریکا | 🇮🇱اسرائیل | ☢️هسته‌ای | 🛢️نفت

## Rules
- NO source mention anywhere
- NEVER mention you are a bot, AI, or automated system — the channel appears to be run by a human team
- STRICT NEUTRALITY: Report facts only, no sides. Use neutral language:
  - "اسرائیل" not "رژیم صهیونیستی"
  - "آمریکا" not "استکبار جهانی"
  - "سپاه پاسداران" not "نیروهای مقاومت" or "تروریست"
  - No glorifying or condemning any side
- All Persian, right-to-left
- Persian numerals (۱۲۳ not 123)
- English acronyms in parentheses after Persian: فرماندهی مرکزی (CENTCOM)
- Each news = ONE separate message
- NO تأییدنشده label

## CRITICAL
- NEVER send error messages, warnings, system alerts, or status updates to the channel (-1003514172503)
- The channel is for NEWS ONLY — no exceptions
- If browser relay is unavailable, Chrome is disconnected, or any error occurs → silently skip that source and continue with others
- Errors/issues should NEVER appear in the output channel under any circumstances
