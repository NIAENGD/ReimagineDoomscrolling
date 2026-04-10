
def select_transcript_strategy(source) -> str:
    return source.transcript_strategy


def should_fallback_to_transcription(strategy: str, transcript_found: bool, fallback_enabled: bool) -> bool:
    if strategy == "force_local_transcription":
        return True
    if strategy == "disable_fallback":
        return False
    return not transcript_found and fallback_enabled


def fetch_transcript(_video_url: str, _languages: list[str]) -> tuple[str, str]:
    return "Sample transcript text", "manual"


def transcribe_audio_locally(_video_url: str) -> str:
    return "Local transcription text"
