from __future__ import annotations

import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlparse

import httpx


YOUTUBE_FEED_BASE = "https://www.youtube.com/feeds/videos.xml"
CHANNEL_ID_PATTERN = re.compile(r'"externalId":"(UC[0-9A-Za-z_-]{20,})"')
CHANNEL_ID_PATTERNS = (
    CHANNEL_ID_PATTERN,
    re.compile(r'"channelId":"(UC[0-9A-Za-z_-]{20,})"'),
    re.compile(r'channelId=("(UC[0-9A-Za-z_-]{20,})"|\'(UC[0-9A-Za-z_-]{20,})\')'),
    re.compile(r"https://www\.youtube\.com/channel/(UC[0-9A-Za-z_-]{20,})"),
    re.compile(r"feeds/videos\.xml\?channel_id=(UC[0-9A-Za-z_-]{20,})"),
)


def _normalize_channel_id(raw_channel_id: str) -> str:
    channel_id = (raw_channel_id or "").strip().strip("'\"")
    if not channel_id:
        return ""
    if channel_id.startswith("UC") and re.fullmatch(r"UC[0-9A-Za-z_-]{20,}", channel_id):
        return channel_id
    if re.fullmatch(r"[0-9A-Za-z_-]{22,}", channel_id):
        return f"UC{channel_id}"
    return channel_id


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
    redirected_path = urlparse(str(response.url)).path.rstrip("/")
    if redirected_path.startswith("/channel/"):
        redirected_parts = redirected_path.split("/")
        if len(redirected_parts) >= 3:
            redirected_channel_id = _normalize_channel_id(redirected_parts[2])
            if redirected_channel_id.startswith("UC"):
                return redirected_channel_id

    for pattern in CHANNEL_ID_PATTERNS:
        match = pattern.search(response.text)
        if not match:
            continue
        groups = [group for group in match.groups() if group]
        if groups:
            return _normalize_channel_id(groups[0])
        matched = _normalize_channel_id(match.group(0))
        if matched.startswith("UC"):
            return matched
    return ""


def _candidate_feed_urls(source_url: str, channel_id: str = "") -> list[str]:
    candidates: list[str] = []
    normalized_channel_id = _normalize_channel_id(channel_id)
    if normalized_channel_id:
        return [f"{YOUTUBE_FEED_BASE}?channel_id={normalized_channel_id}"]

    parsed = urlparse(source_url)
    path = parsed.path.rstrip("/")

    if path.startswith("/channel/"):
        source_channel_id = _normalize_channel_id(path.split("/", 2)[2])
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
        query_channel_id = _normalize_channel_id(query["channel_id"][0])
        return [f"{YOUTUBE_FEED_BASE}?channel_id={query_channel_id}"]

    raise ValueError("Unsupported YouTube source URL format for discovery")


def _fetch_feed(source_url: str, channel_id: str = "") -> tuple[list[dict], dict]:
    candidate_urls = _candidate_feed_urls(source_url, channel_id)
    last_error: Exception | None = None
    for feed_url in candidate_urls:
        try:
            with _http_client() as client:
                response = client.get(feed_url)
                response.raise_for_status()
            videos, metadata = _parse_atom_feed(response.text)
            if videos:
                return videos, metadata
            if feed_url.endswith("videos.xml") or "channel_id=" in feed_url:
                return videos, metadata
            last_error = ValueError(f"Empty feed response from {feed_url}")
        except Exception as exc:
            last_error = exc
            continue
    if last_error:
        raise ValueError(f"Unable to fetch feed for source URL: {last_error}") from last_error
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
    channel_id = _normalize_channel_id(root.findtext("yt:channelId", default="", namespaces=ns))

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
                try:
                    published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00")).replace(tzinfo=None)
                except ValueError:
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
    videos, _ = _fetch_feed(source.canonical_url or source.url, source.channel_id or "")

    if getattr(source, "discovery_mode", "latest_n") == "since_last_success" and getattr(source, "last_success_at", None):
        videos = [
            video
            for video in videos
            if video.get("published_at") and video["published_at"] > source.last_success_at
        ]

    limit = max(int(getattr(source, "max_videos", 10) or 10), 0)
    return videos[:limit]
