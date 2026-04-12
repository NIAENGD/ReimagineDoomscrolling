from __future__ import annotations

import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlparse

import httpx


YOUTUBE_FEED_BASE = "https://www.youtube.com/feeds/videos.xml"
CHANNEL_ID_PATTERN = re.compile(r'"externalId":"(UC[0-9A-Za-z_-]{20,})"')


def _http_client() -> httpx.Client:
    return httpx.Client(
        timeout=20.0,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )


def normalize_source_url(url: str) -> str:
    url = url.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        raise ValueError("Only YouTube URLs are supported")
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path.startswith("/@"):
        return f"https://www.youtube.com{path}"
    if path.startswith("/channel/"):
        return f"https://www.youtube.com{path}"
    if path.startswith("/c/") or path.startswith("/user/"):
        return f"https://www.youtube.com{path}"
    return url


def evaluate_video_policy(video: dict, source) -> tuple[bool, str]:
    duration = video.get("duration")
    has_duration = duration is not None and duration > 0

    if source.skip_shorts and has_duration and duration < 60:
        return False, "short"
    if has_duration and duration < source.min_duration_seconds:
        return False, "min_duration"
    if source.skip_livestreams and video.get("is_live"):
        return False, "livestream"
    if source.discovery_mode == "rolling_window":
        published = video.get("published_at")
        if published and published < datetime.utcnow() - timedelta(hours=source.rolling_window_hours):
            return False, "outside_window"
    return True, "ok"


def _extract_channel_id_from_page(source_url: str) -> str:
    with _http_client() as client:
        response = client.get(source_url)
        response.raise_for_status()
    match = CHANNEL_ID_PATTERN.search(response.text)
    return match.group(1) if match else ""


def _candidate_feed_urls(source_url: str, channel_id: str = "") -> list[str]:
    candidates: list[str] = []
    if channel_id:
        return [f"{YOUTUBE_FEED_BASE}?channel_id={channel_id}"]

    parsed = urlparse(source_url)
    path = parsed.path.rstrip("/")

    if path.startswith("/channel/"):
        source_channel_id = path.split("/", 2)[2]
        return [f"{YOUTUBE_FEED_BASE}?channel_id={source_channel_id}"]
    if path.startswith("/@") or path.startswith("/c/") or path.startswith("/user/"):
        handle_or_name = path.split("/", 2)[1].lstrip("@")
        if handle_or_name:
            candidates.append(f"{YOUTUBE_FEED_BASE}?user={handle_or_name}")
        try:
            resolved_channel_id = _extract_channel_id_from_page(source_url)
            if resolved_channel_id:
                candidates.append(f"{YOUTUBE_FEED_BASE}?channel_id={resolved_channel_id}")
        except Exception:
            pass
        if candidates:
            return candidates

    query = parse_qs(parsed.query)
    if "channel_id" in query and query["channel_id"]:
        return [f"{YOUTUBE_FEED_BASE}?channel_id={query['channel_id'][0]}"]

    raise ValueError("Unsupported YouTube source URL format for discovery")


def _fetch_feed(source_url: str, channel_id: str = "") -> tuple[list[dict], dict]:
    for feed_url in _candidate_feed_urls(source_url, channel_id):
        try:
            with _http_client() as client:
                response = client.get(feed_url)
                response.raise_for_status()
            return _parse_atom_feed(response.text)
        except Exception:
            continue
    raise ValueError("Unable to fetch feed for source URL")


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
                "duration": None,
                "is_live": False,
            }
        )

    return entries, {"title": channel_title, "channel_id": channel_id}


def resolve_source_identity(source_url: str) -> dict:
    normalized = normalize_source_url(source_url)
    entries, metadata = _fetch_feed(normalized)

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
        videos, _ = _fetch_feed(source.canonical_url or source.url, source.channel_id or "")
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
