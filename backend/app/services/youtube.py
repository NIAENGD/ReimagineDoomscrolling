from datetime import datetime, timedelta
from urllib.parse import urlparse


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


def discover_videos(_source) -> list[dict]:
    raise NotImplementedError(
        "discover_videos is a required integration point and still a placeholder. "
        "Implement real YouTube channel discovery before using refresh flows."
    )
