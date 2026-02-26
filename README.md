# Last.fm Scrobbles → ListenBrainz Import Converter

This script converts a Last.fm scrobbles export JSON file into a ListenBrainz import-ready **JSONL** file and packages it into a **ZIP** archive for upload.

It is designed to match ListenBrainz’ import format by writing one JSON object per line (JSONL), then placing it in a zip file as `listens.jsonl`.

## What it does

- Reads `scrobbles.json` (your Last.fm export)
- Skips entries marked as “now playing”
- Skips entries missing `date.uts` (Unix timestamp)
- Writes `listenbrainz_listens.jsonl`
- Creates `listenbrainz_import.zip` containing `listens.jsonl`

## Requirements

- Python 3.8+ (no third-party dependencies)
- A Last.fm scrobble export in .JSON format [from this website.](https://lastfm.ghan.nl/export/)

## Setup

1. Place this script in a folder.
2. Put your Last.fm export JSON file in the same folder and name it:

   - `scrobbles.json`

If your input file has a different name, edit the constant at the top of the script:

```py
INPUT_FILE = "scrobbles.json"
