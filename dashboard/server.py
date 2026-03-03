from typing import List, Dict, Optional
"""
server.py — FastAPI backend for the Dideban live war news dashboard.
"""

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import fetcher
from geocoder import extract_and_geocode

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EVENTS_FILE = DATA_DIR / "events.json"
LOCATIONS_FILE = DATA_DIR / "locations.json"
INDEX_FILE = BASE_DIR / "index.html"

DATA_DIR.mkdir(exist_ok=True)

# ── In-memory state ──────────────────────────────────────────────────────────

def _load_json(path: Path, default):
    try:
        text = path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else default
    except Exception:
        return default


def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


events: List[Dict] = _load_json(EVENTS_FILE, [])
locations: List[Dict] = _load_json(LOCATIONS_FILE, [])

# Set of SSE subscriber queues
_subscribers: set = set()

MAX_EVENTS = 500  # cap stored events


async def _broadcast(event_type: str, data: dict):
    payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
    dead = set()
    for q in _subscribers:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.add(q)
    _subscribers.difference_update(dead)


# ── Background fetch loop ────────────────────────────────────────────────────

async def _fetch_and_update():
    global events, locations

    logger.info("Background fetch: starting")
    new_events_count = 0

    existing_ids = {e["id"] for e in events}

    try:
        tg_items = await fetcher.fetch_telegram_news()
        for item in tg_items:
            if item["id"] not in existing_ids:
                existing_ids.add(item["id"])
                events.insert(0, item)
                new_events_count += 1
                await _broadcast("news", item)
                # Geocode in background (non-blocking feel)
                await _geocode_and_add(item)
    except Exception as e:
        logger.error(f"Telegram fetch error: {e}")

    try:
        tw_items = await fetcher.fetch_twitter_news()
        for item in tw_items:
            if item["id"] not in existing_ids:
                existing_ids.add(item["id"])
                events.insert(0, item)
                new_events_count += 1
                await _broadcast("news", item)
    except Exception as e:
        logger.error(f"Twitter fetch error: {e}")

    # Trim events list
    if len(events) > MAX_EVENTS:
        events = events[:MAX_EVENTS]

    _save_json(EVENTS_FILE, events)
    _save_json(LOCATIONS_FILE, locations)
    logger.info(f"Background fetch: done — {new_events_count} new events")


async def _geocode_and_add(item: dict):
    """Extract locations from a news item and add them to the map."""
    global locations
    try:
        # Run blocking geocoder in thread pool
        loop = asyncio.get_event_loop()
        locs = await loop.run_in_executor(None, extract_and_geocode, item["text"])
        existing_names = {loc["name"] for loc in locations}
        for loc in locs:
            if loc["name"] not in existing_names:
                existing_names.add(loc["name"])
                entry = {
                    "id": str(uuid.uuid4()),
                    "name": loc["name"],
                    "lat": loc["lat"],
                    "lon": loc["lon"],
                    "text_snippet": loc["text_snippet"],
                    "timestamp": item.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "source_id": item["id"],
                }
                locations.append(entry)
                await _broadcast("location_add", entry)
    except Exception as e:
        logger.warning(f"Geocoding error: {e}")


async def _background_loop():
    while True:
        try:
            await _fetch_and_update()
        except Exception as e:
            logger.error(f"Unhandled error in background loop: {e}")
        await asyncio.sleep(120)  # every 2 minutes


# ── App lifecycle ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_background_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Dideban Dashboard", lifespan=lifespan)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse(INDEX_FILE, media_type="text/html")


@app.get("/events")
async def sse_events(request: Request):
    """Server-Sent Events endpoint."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.add(queue)

    async def event_generator() -> AsyncGenerator[str, None]:
        # Send current state on connect
        snapshot = {
            "events": events[:100],
            "locations": locations,
        }
        yield f"data: {json.dumps({'type': 'snapshot', 'data': snapshot}, ensure_ascii=False)}\n\n"

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"  # keep-alive comment
        finally:
            _subscribers.discard(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/events")
async def get_events(limit: int = 100):
    return events[:limit]


@app.get("/api/locations")
async def get_locations():
    return locations


class LocationCreate(BaseModel):
    name: str
    lat: float
    lon: float
    text_snippet: str = ""


@app.post("/api/locations", status_code=201)
async def add_location(body: LocationCreate):
    entry = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "lat": body.lat,
        "lon": body.lon,
        "text_snippet": body.text_snippet,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_id": None,
    }
    locations.append(entry)
    _save_json(LOCATIONS_FILE, locations)
    await _broadcast("location_add", entry)
    return entry


class TwitterItem(BaseModel):
    text: str
    user: str
    time: str = ""
    images: List[str] = []
    videos: List[str] = []
    videoPosters: List[str] = []

@app.post("/api/twitter/inject", status_code=200)
async def inject_twitter(items: List[TwitterItem]):
    """Inject tweets from browser scrape into the live feed."""
    import hashlib
    injected = 0
    existing_ids = {e.get("id") for e in events}
    for item in items:
        item_id = "tw_" + hashlib.md5((item.user + item.text).encode()).hexdigest()[:10]
        if item_id in existing_ids:
            continue
        # Build videos list with poster thumbnails
        videos_list = []
        for i, src in enumerate(item.videos):
            poster = item.videoPosters[i] if i < len(item.videoPosters) else ""
            videos_list.append({"src": src, "thumb": poster})
        entry = {
            "id": item_id,
            "source": "twitter",
            "channel": item.user,
            "text": item.text,
            "images": item.images,
            "videos": videos_list,
            "timestamp": item.time or datetime.now(timezone.utc).isoformat(),
            "official": any(w in item.text.lower() for w in ["official","confirms","minister","president","pentagon","ministry","secretary","general"]),
        }
        events.insert(0, entry)
        existing_ids.add(item_id)
        await _broadcast("news", entry)
        injected += 1
    if injected:
        _save_json(EVENTS_FILE, events[:2000])
    return {"injected": injected}


@app.get("/api/proxy-img")
async def proxy_image(url: str = ""):
    """Proxy external images to bypass CORS."""
    if not url:
        raise HTTPException(400, "No URL")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            content_type = r.headers.get("content-type", "image/jpeg")
            from fastapi.responses import Response
            return Response(content=r.content, media_type=content_type)
    except Exception as e:
        raise HTTPException(502, str(e))


@app.get("/api/translate")
async def translate_text(text: str = ""):
    """Translate text to Persian."""
    if not text:
        return {"result": text}
    try:
        from geocoder import translate_to_persian
        import asyncio
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(None, translate_to_persian, text)
        return {"result": translated}
    except Exception as e:
        return {"result": text}


@app.delete("/api/locations/{loc_id}", status_code=204)
async def delete_location(loc_id: str):
    global locations
    before = len(locations)
    locations = [loc for loc in locations if loc["id"] != loc_id]
    if len(locations) == before:
        raise HTTPException(status_code=404, detail="Location not found")
    _save_json(LOCATIONS_FILE, locations)
    await _broadcast("location_remove", {"id": loc_id})
    return None


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=False)
