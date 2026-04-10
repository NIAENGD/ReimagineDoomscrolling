
def select_transcript_strategy(source) -> str:
    return source.transcript_strategy


def should_fallback_to_transcription(strategy: str, transcript_found: bool, fallback_enabled: bool) -> bool:
    if strategy == "force_local_transcription":
        return True
    if strategy == "disable_fallback":
        return False
    return not transcript_found and fallback_enabled


def fetch_transcript(_video_url: str, _languages: list[str]) -> tuple[str, str]:
    raise NotImplementedError(
        "fetch_transcript is a required integration point and still a placeholder. "
        "Implement transcript retrieval from your selected provider."
    )


def transcribe_audio_locally(_video_url: str) -> str:
    raise NotImplementedError(
        "transcribe_audio_locally is a required integration point and still a placeholder. "
        "Implement local transcription wiring before enabling fallback."
    )
