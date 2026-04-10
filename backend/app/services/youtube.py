from __future__ import annotations

from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlparse

import httpx


YOUTUBE_FEED_BASE = "https://www.youtube.com/feeds/videos.xml"


def normalize_source_url(url: str) -> str:
    url = url.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        raise ValueError("Only YouTube URLs are supported")
    if "@" in url:
        return url.split("?")[0]
    parsed = urlparse(url)
    if parsed.path.startswith("/channel/"):
        return f"https://www.youtube.com{parsed.path}"
    return url


def evaluate_video_policy(video: dict, source) -> tuple[bool, str]:
    if source.skip_shorts and video.get("duration", 0) < 60:
        return False, "short"
    if video.get("duration", 0) < source.min_duration_seconds:
        return False, "min_duration"
    if source.skip_livestreams and video.get("is_live"):
        return False, "livestream"
    if source.discovery_mode == "rolling_window":
        published = video.get("published_at")
        if published and published < datetime.utcnow() - timedelta(hours=source.rolling_window_hours):
            return False, "outside_window"
    return True, "ok"


def _feed_url_from_source_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    path = parsed.path.rstrip("/")

    if path.startswith("/channel/"):
        channel_id = path.split("/", 2)[2]
        return f"{YOUTUBE_FEED_BASE}?channel_id={channel_id}"
    if path.startswith("/@"):
        handle = path.split("/@", 1)[1]
        return f"{YOUTUBE_FEED_BASE}?user={handle}"

    query = parse_qs(parsed.query)
    if "channel_id" in query and query["channel_id"]:
        return f"{YOUTUBE_FEED_BASE}?channel_id={query['channel_id'][0]}"

    raise ValueError("Unsupported YouTube source URL format for discovery")


def _parse_atom_entries(feed_xml: str) -> list[dict]:
    import xml.etree.ElementTree as ET

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    root = ET.fromstring(feed_xml)
    entries: list[dict] = []

    for entry in root.findall("atom:entry", ns):
        video_id = entry.findtext("yt:videoId", default="", namespaces=ns)
        if not video_id:
            continue
        title = entry.findtext("atom:title", default="", namespaces=ns)
        published_raw = entry.findtext("atom:published", default="", namespaces=ns)
        published_at = None
        if published_raw:
            try:
                published_at = parsedate_to_datetime(published_raw).replace(tzinfo=None)
            except (TypeError, ValueError):
                published_at = None

        entries.append(
            {
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": title or video_id,
                "published_at": published_at,
                "duration": 0,
                "is_live": False,
            }
        )

    return entries


def discover_videos(source) -> list[dict]:
    try:
        feed_url = _feed_url_from_source_url(source.url)
    except ValueError:
        return []

    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(feed_url)
            response.raise_for_status()
        videos = _parse_atom_entries(response.text)
    except Exception:
        return []

    limit = max(int(getattr(source, "max_videos", 10) or 10), 0)
    return videos[:limit]
