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
    if parsed.path.startswith("/c/") or parsed.path.startswith("/user/"):
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
    if path.startswith("/user/"):
        username = path.split("/user/", 1)[1]
        return f"{YOUTUBE_FEED_BASE}?user={username}"

    query = parse_qs(parsed.query)
    if "channel_id" in query and query["channel_id"]:
        return f"{YOUTUBE_FEED_BASE}?channel_id={query['channel_id'][0]}"

    raise ValueError("Unsupported YouTube source URL format for discovery")


def _parse_atom_feed(feed_xml: str) -> tuple[list[dict], dict]:
    import xml.etree.ElementTree as ET

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    root = ET.fromstring(feed_xml)
    entries: list[dict] = []
    channel_title = root.findtext("atom:title", default="", namespaces=ns)
    channel_id = root.findtext("yt:channelId", default="", namespaces=ns)

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

    return entries, {"title": channel_title, "channel_id": channel_id}


def resolve_source_identity(source_url: str) -> dict:
    normalized = normalize_source_url(source_url)
    feed_url = _feed_url_from_source_url(normalized)

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        response = client.get(feed_url)
        response.raise_for_status()
    entries, metadata = _parse_atom_feed(response.text)

    channel_id = metadata.get("channel_id", "")
    canonical_url = f"https://www.youtube.com/channel/{channel_id}" if channel_id else normalized
    return {
        "normalized_url": normalized,
        "canonical_url": canonical_url,
        "channel_id": channel_id,
        "title": metadata.get("title", ""),
        "last_discovered_count": len(entries),
    }


def discover_videos(source) -> list[dict]:
    try:
        feed_url = _feed_url_from_source_url(source.url)
    except ValueError:
        return []

    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(feed_url)
            response.raise_for_status()
        videos, _ = _parse_atom_feed(response.text)
    except Exception:
        return []

    if getattr(source, "discovery_mode", "latest_n") == "since_last_success" and getattr(source, "last_success_at", None):
        videos = [
            video
            for video in videos
            if video.get("published_at") and video["published_at"] > source.last_success_at
        ]

    limit = max(int(getattr(source, "max_videos", 10) or 10), 0)
    return videos[:limit]
