from typing import List, Dict, Optional
"""
geocoder.py — Extract location names from Persian text and geocode them via Nominatim.
"""

import re
import time
import logging
import requests

logger = logging.getLogger(__name__)

# ── Translation helper ────────────────────────────────────────────────────────
_translator = None

def translate_to_persian(text: str) -> str:
    """Translate English text to Persian using Google Translate (free)."""
    if not text or not text.strip():
        return text
    # If already mostly Persian/Arabic chars, skip
    persian_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    if persian_chars > len(text) * 0.3:
        return text
    try:
        global _translator
        if _translator is None:
            from googletrans import Translator
            _translator = Translator()
        result = _translator.translate(text, dest='fa', src='en')
        return result.text if result and result.text else text
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return text

logger = logging.getLogger(__name__)

# Known Persian location names → English search term for Nominatim
LOCATION_MAP = {
    "ایران": "Iran",
    "اسرائیل": "Israel",
    "اردن": "Jordan",
    "تهران": "Tehran",
    "تل‌آویو": "Tel Aviv",
    "تل آویو": "Tel Aviv",
    "بغداد": "Baghdad",
    "دمشق": "Damascus",
    "بیروت": "Beirut",
    "یمن": "Yemen",
    "صنعا": "Sanaa",
    "غزه": "Gaza",
    "رفح": "Rafah",
    "عراق": "Iraq",
    "سوریه": "Syria",
    "لبنان": "Lebanon",
    "عربستان": "Saudi Arabia",
    "ریاض": "Riyadh",
    "مسقط": "Muscat",
    "عمان": "Oman",
    "کویت": "Kuwait",
    "امارات": "UAE",
    "دبی": "Dubai",
    "ابوظبی": "Abu Dhabi",
    "قطر": "Qatar",
    "دوحه": "Doha",
    "اصفهان": "Isfahan",
    "مشهد": "Mashhad",
    "شیراز": "Shiraz",
    "اهواز": "Ahvaz",
    "تبریز": "Tabriz",
    "نتانز": "Natanz",
    "فردو": "Fordow",
    "اراک": "Arak, Iran",
    "بندرعباس": "Bandar Abbas",
    "خارک": "Kharg Island",
    "خوزستان": "Khuzestan",
    "الحدیده": "Hudaydah",
    "عدن": "Aden",
    "مأرب": "Marib",
    "نجف": "Najaf",
    "کربلا": "Karbala",
    "موصل": "Mosul",
    "بصره": "Basra",
    "کرکوک": "Kirkuk",
    "حلب": "Aleppo",
    "حمص": "Homs",
    "درعا": "Daraa",
    "حماه": "Hama",
    "ادلب": "Idlib",
    "جنوب لبنان": "South Lebanon",
    "جولان": "Golan Heights",
    "کرانه باختری": "West Bank",
    "رام‌الله": "Ramallah",
    "نابلس": "Nablus",
    "جنین": "Jenin",
    "خان‌یونس": "Khan Yunis",
    "خان یونس": "Khan Yunis",
    "بیت‌المقدس": "Jerusalem",
    "قدس": "Jerusalem",
    "حیفا": "Haifa",
    "تل‌الربیع": "Tel Aviv",
    "اشکلون": "Ashkelon",
    "عسقلان": "Ashkelon",
    "دیمونا": "Dimona",
    "نقب": "Negev",
    "ایلات": "Eilat",
}

_geocode_cache: Dict[str, Optional[Dict]] = {}

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "DidebanDashboard/1.0"}


def _nominatim_geocode(query: str) -> Optional[Dict]:
    if query in _geocode_cache:
        return _geocode_cache[query]
    try:
        time.sleep(1)  # Nominatim rate limit: 1 req/sec
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            result = {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
            _geocode_cache[query] = result
            return result
    except Exception as e:
        logger.warning(f"Nominatim geocode failed for '{query}': {e}")
    _geocode_cache[query] = None
    return None


def extract_and_geocode(text: str) -> List[Dict]:
    """
    Find Persian location names in text, geocode each, return list of dicts:
    {name, lat, lon, text_snippet}
    """
    found: List[Dict] = []
    seen_names: set[str] = set()

    for persian_name, english_name in LOCATION_MAP.items():
        if persian_name in text and english_name not in seen_names:
            coords = _nominatim_geocode(english_name)
            if coords:
                seen_names.add(english_name)
                # Grab a snippet around the match
                idx = text.find(persian_name)
                start = max(0, idx - 30)
                end = min(len(text), idx + len(persian_name) + 30)
                snippet = text[start:end].strip()
                found.append(
                    {
                        "name": persian_name,
                        "lat": coords["lat"],
                        "lon": coords["lon"],
                        "text_snippet": snippet,
                    }
                )

    return found
