# ReimagineDoomscrolling

A concept for curating high-quality YouTube content.

This repository contains notes and design documents for a proposed browser extension and local helper server. The goal is to automatically fetch videos from a user's feed, analyse transcripts with language models and present rewritten articles for distraction-free reading.

See [docs/overview.md](docs/overview.md) for the current high level design.

## Quick start

Install dependencies and run the helper server:

```bash
pip install -r requirements.txt
python server.py
```

The server exposes a small API for transcription and processing. See
`server.py` for details.
