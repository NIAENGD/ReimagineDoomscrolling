# ReimagineDoomscrolling

A concept for curating high-quality YouTube content.

This repository contains notes and design documents for a proposed browser extension and local helper server. The goal is to automatically fetch videos from a user's feed, analyse transcripts with language models and present rewritten articles for distraction-free reading.

See [docs/overview.md](docs/overview.md) for the current high level design, including the strict scoring rubric used when analysing each transcript.

## Quick start

Install dependencies and run the helper server. It only provides a local endpoint for Whisper transcription so no API keys are required:

```bash
pip install -r requirements.txt
python server.py
```

Windows users can run `run_app.bat` for a small menu that installs
dependencies or launches the server.

The server exposes a small API for fetching subtitles and running Whisper when
needed. The Chrome extension in the `extension/` folder handles scoring and the
results page internally. Load the folder as an unpacked extension and click the
toolbar icon to open the main page. From there press **Launch** to begin
collecting links. Each link is sent to the server only when a transcript is
required.
