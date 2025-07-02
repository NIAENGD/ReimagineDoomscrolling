# ReimagineDoomscrolling

A concept for curating high-quality YouTube content.

This repository contains notes and design documents for a proposed browser extension and local helper server. The goal is to automatically fetch videos from a user's feed, analyse transcripts with language models and present rewritten articles for distraction-free reading.

See [docs/overview.md](docs/overview.md) for the current high level design, including the strict scoring rubric used when analysing each transcript.

## Quick start

Install dependencies and run the helper server. It only provides a local endpoint for Whisper transcription so no API keys are required. The server expects the `yt-dlp` and `whisper` commands (from `openai-whisper`) plus `ffmpeg` to be on your `PATH`:

```bash
pip install -r requirements.txt
# also ensure the helper CLIs are installed
pip install yt-dlp openai-whisper
# optional flags let you choose the Whisper model and language
python server.py [--whisper-model medium] [--whisper-language ja]
```

Windows users can run `run_app.bat` for a small menu that installs or
uninstalls the requirements. The menu also includes an option to update the
repository from GitHub before launching the server. A separate
`package.py` script creates a distributable zip containing the server
and Chrome extension:

```bash
python package.py
```
The archive is written to the `dist/` folder.

The server exposes a small API for fetching subtitles and running Whisper when
needed. Results are now persisted in a local SQLite database (`articles.db`).
The Chrome extension in the `extension/` folder shows a basic reader UI that
loads articles from the server. Load the folder as an unpacked extension and use
the popup to start collecting links. Each link is sent to the server only when a
transcript is required.

The popup now lets you customise the scoring and rewriting prompts. Choose the
desired ChatGPT model manually within the ChatGPT tab—the extension simply sends
your prompts to whatever model is active.
Use the new **Open tabs** button to launch hidden YouTube and ChatGPT tabs. Once
they load, click **Start** to begin processing. The extension no longer blocks
you if login cookies are missing. When finished it automatically closes the
hidden tabs.

## Development status

This project remains experimental. Recent updates added a simple reader UI,
database-backed storage and a packaging script for easier distribution.

See [TODO.md](TODO.md) for additional notes.
