from typing import List, Dict, Optional
"""
fetcher.py — Fetch news from Telegram channels and Twitter/X (via Nitter).
"""

import hashlib
import logging
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Official statement detection ─────────────────────────────────────────────

OFFICIAL_KEYWORDS = [
    # Persian titles / institutions
    "وزیر", "وزارت", "رئیس‌جمهور", "رئیس جمهور", "فرمانده", "سخنگو",
    "نخست‌وزیر", "نخست وزیر", "ارتش", "سپاه", "نیروی هوایی", "نیروی دریایی",
    "ستاد کل", "وزارت دفاع", "وزارت خارجه", "وزارت اطلاعات",
    "دولت", "پارلمان", "مجلس", "شورای امنیت", "رهبری", "رهبر",
    "سفیر", "کنسول", "دیپلمات",
    # English institutions often transliterated / mixed
    "پنتاگون", "کاخ سفید", "ناتو", "سازمان ملل", "شورای اروپا",
    "بیانیه", "اطلاعیه", "اعلام کرد", "تأکید کرد", "تصریح کرد",
    "گفت‌وگو", "مصاحبه", "اظهار داشت", "اعلام داشت",
    # Specific senior roles
    "رئیس ستاد", "فرمانده کل", "وزیر امور خارجه", "وزیر دفاع",
    "رئیس سازمان", "دبیرکل",
]


NEUTRAL_REPLACEMENTS = {
    "سرزمین‌های اشغالی": "اسرائیل",
    "سرزمین های اشغالی": "اسرائیل",
    "اراضی اشغالی": "اسرائیل",
    "فلسطین اشغالی": "اسرائیل",
    "رژیم صهیونیستی": "اسرائیل",
    "رژیم اشغالگر": "اسرائیل",
    "بلندی‌های جولان اشغالی": "بلندی‌های جولان",
    "بلندی های جولان اشغالی": "بلندی‌های جولان",
    "جولان اشغالی": "بلندی‌های جولان",
}

def neutralize_text(text: str) -> str:
    """Replace politically biased terms with neutral equivalents."""
    for biased, neutral in NEUTRAL_REPLACEMENTS.items():
        text = text.replace(biased, neutral)
    return text

def is_official_statement(text: str) -> bool:
    """Return True if the text contains keywords indicating an official statement."""
    return any(kw in text for kw in OFFICIAL_KEYWORDS)

TELEGRAM_CHANNELS = [
    "SaberinFa",
    "ManotoTV",
    "overlordechokilo",
    "tehran_timse",
    "defender_iran",
    "final_battle313",
    "gordanesam313",
    "sarbazane_g",
    "mamlekate",
    "VahidOnline",
    "Parvazdaroj",
    "irannotam",
]

NITTER_LIST_URL = "https://nitter.net/i/lists/2028404706926813366"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fa,en;q=0.9",
}


def _make_id(source: str, text: str) -> str:
    return hashlib.md5(f"{source}:{text[:100]}".encode()).hexdigest()[:16]


def _parse_tg_time(el) -> str:
    """Try to extract ISO timestamp from a Telegram message element."""
    time_el = el.find("time") if el else None
    if time_el and time_el.get("datetime"):
        return time_el["datetime"]
    return datetime.now(timezone.utc).isoformat()


async def fetch_telegram_news() -> List[Dict]:
    results = []
    async with httpx.AsyncClient(
        headers=HEADERS, timeout=20, follow_redirects=True
    ) as client:
        for channel in TELEGRAM_CHANNELS:
            url = f"https://t.me/s/{channel}"
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Telegram {channel}: HTTP {resp.status_code}")
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                messages = soup.select(".tgme_widget_message_wrap")
                if not messages:
                    # Fallback selector
                    messages = soup.select(".tgme_widget_message")
                for msg in messages[-20:]:  # last 20 per channel — dashboard shows EVERYTHING
                    text_el = msg.select_one(".tgme_widget_message_text")
                    text = neutralize_text(text_el.get_text(separator="\n").strip()) if text_el else ""

                    # Extract image URLs from message photos
                    images = []
                    # Method 1: background-image style on photo divs
                    for photo_el in msg.select(".tgme_widget_message_photo_wrap, .tgme_widget_message_photo"):
                        style = photo_el.get("style", "")
                        match = re.search(r"url\(['\"]?(https?://[^'\")\s]+)['\"]?\)", style)
                        if match:
                            images.append(match.group(1))
                    # Method 2: <img> tags inside message
                    for img_el in msg.select(".tgme_widget_message_photo img, .media_photo img"):
                        src = img_el.get("src", "")
                        if src.startswith("http"):
                            images.append(src)

                    # Extract videos — deduplicate by src URL
                    videos = []
                    seen_video_srcs = set()
                    for video_el in msg.select("video"):
                        src = video_el.get("src", "")
                        if not src.startswith("http") or src in seen_video_srcs:
                            continue
                        seen_video_srcs.add(src)
                        # Get thumbnail from video_thumb div
                        thumb = ""
                        thumb_el = msg.select_one(".tgme_widget_message_video_thumb")
                        if thumb_el:
                            style = thumb_el.get("style", "")
                            m = re.search(r"url\(['\"]?(https?://[^'\")\s]+)['\"]?\)", style)
                            if m:
                                thumb = m.group(1)
                        videos.append({"src": src, "thumb": thumb})

                    # Dashboard shows EVERYTHING — only skip truly empty messages
                    if not text and not images and not videos:
                        continue

                    timestamp = _parse_tg_time(msg)
                    results.append(
                        {
                            "id": _make_id(channel, text or str(images)),
                            "source": "telegram",
                            "channel": channel,
                            "text": text,
                            "images": images,
                            "videos": videos,
                            "timestamp": timestamp,
                            "official": is_official_statement(text),
                        }
                    )
            except Exception as e:
                logger.warning(f"Telegram fetch error for @{channel}: {e}")
    return results


async def fetch_twitter_news() -> List[Dict]:
    results = []
    # Try multiple Nitter instances in case one is down
    nitter_instances = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
    ]
    list_path = "/i/lists/2028404706926813366"

    async with httpx.AsyncClient(
        headers=HEADERS, timeout=20, follow_redirects=True
    ) as client:
        for base in nitter_instances:
            url = f"{base}{list_path}"
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Nitter {base}: HTTP {resp.status_code}")
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                tweets = soup.select(".timeline-item")
                if not tweets:
                    tweets = soup.select(".tweet-body")
                for tweet in tweets[:30]:
                    # Username
                    user_el = tweet.select_one(".username") or tweet.select_one(
                        ".fullname"
                    )
                    user = user_el.get_text().strip() if user_el else "unknown"
                    # Text
                    content_el = tweet.select_one(
                        ".tweet-content"
                    ) or tweet.select_one(".tweet-text")
                    if not content_el:
                        continue
                    text = neutralize_text(content_el.get_text(separator="\n").strip())
                    if not text:
                        continue
                    # Timestamp
                    time_el = tweet.select_one("span.tweet-date a") or tweet.select_one(
                        "time"
                    )
                    if time_el and time_el.get("title"):
                        timestamp = time_el["title"]
                    elif time_el and time_el.get("datetime"):
                        timestamp = time_el["datetime"]
                    else:
                        timestamp = datetime.now(timezone.utc).isoformat()
                    results.append(
                        {
                            "id": _make_id(user, text),
                            "source": "twitter",
                            "channel": user,
                            "text": text,
                            "timestamp": timestamp,
                            "official": is_official_statement(text),
                        }
                    )
                if results:
                    break  # Got data, stop trying instances
            except Exception as e:
                logger.warning(f"Nitter fetch error {base}: {e}")
    return results
