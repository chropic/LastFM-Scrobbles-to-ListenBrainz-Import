#!/usr/bin/env python3
"""
Convert a Last.fm scrobbles export (JSON) into a ListenBrainz JSONL import file,
then package it into a ZIP archive suitable for ListenBrainz import.

Behavior intentionally matches the original script:
- Reads INPUT_FILE (default: scrobbles.json)
- Writes OUTPUT_JSONL (default: listenbrainz_listens.jsonl)
- Creates OUTPUT_ZIP (default: listenbrainz_import.zip) containing "listens.jsonl"
- Skips "now playing" entries
- Skips entries without date.uts
"""

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

INPUT_FILE = "scrobbles.json"
OUTPUT_JSONL = "listenbrainz_listens.jsonl"
OUTPUT_ZIP = "listenbrainz_import.zip"


def get_text(value: Any) -> Optional[str]:
    """
    Extract text from Last.fm-style fields.

    - None -> None
    - str -> str
    - dict -> dict["#text"] if present
    - other -> str(value)
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        inner = value.get("#text")
        if inner is None or isinstance(inner, str):
            return inner
        return str(inner)
    return str(value)


def _ensure_list(value: Any) -> List[Any]:
    """Return `value` as a list (wrapping scalars), treating None as an empty list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def flatten_tracks(payload: Any) -> List[Dict[str, Any]]:
    """
    Flatten common Last.fm export shapes into a list of track dicts.

    Mirrors the original logic:
    - If payload is a list: flatten one level of nested lists
    - If payload is a dict:
        - prefer payload["recenttracks"]["track"]
        - else payload["track"]
        - else [payload]
    """
    items: List[Any] = []

    if isinstance(payload, list):
        for x in payload:
            if isinstance(x, list):
                items.extend(x)
            else:
                items.append(x)
    elif isinstance(payload, dict):
        if isinstance(payload.get("recenttracks"), dict):
            items = _ensure_list(payload["recenttracks"].get("track"))
        elif "track" in payload:
            items = _ensure_list(payload.get("track"))
        else:
            items = [payload]

    # Keep only dict entries; anything else would fail downstream anyway.
    return [x for x in items if isinstance(x, dict)]


def track_to_listen(track_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert a single Last.fm track object into a ListenBrainz listen dict.
    Returns None if the entry should be skipped.
    """
    attr = track_obj.get("@attr")
    if isinstance(attr, dict) and attr.get("nowplaying") == "true":
        return None

    date = track_obj.get("date")
    if not isinstance(date, dict) or "uts" not in date:
        return None

    try:
        listened_at = int(date["uts"])
    except (TypeError, ValueError):
        return None

    track_name = get_text(track_obj.get("name"))
    artist_name = get_text(track_obj.get("artist"))
    album_name = get_text(track_obj.get("album"))

    if not track_name or not artist_name:
        return None

    listen: Dict[str, Any] = {
        "listened_at": listened_at,
        "track_metadata": {
            "track_name": track_name,
            "artist_name": artist_name,
        },
    }

    if album_name:
        listen["track_metadata"]["release_name"] = album_name

    return listen


def write_listens_jsonl(input_path: Path, output_path: Path) -> int:
    """Read Last.fm JSON, convert, and write JSONL. Returns number of listens written."""
    with input_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    tracks = flatten_tracks(raw)

    written = 0
    with output_path.open("w", encoding="utf-8") as out:
        for t in tracks:
            listen = track_to_listen(t)
            if listen is None:
                continue

            out.write(json.dumps(listen, ensure_ascii=False) + "\n")
            written += 1

    return written


def make_import_zip(jsonl_path: Path, zip_path: Path) -> None:
    """Create the ListenBrainz import ZIP with the required internal filename."""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(jsonl_path, arcname="listens.jsonl")


def main() -> None:
    input_path = Path(INPUT_FILE)
    output_jsonl_path = Path(OUTPUT_JSONL)
    output_zip_path = Path(OUTPUT_ZIP)

    written = write_listens_jsonl(input_path, output_jsonl_path)
    print("Listens written:", written)

    make_import_zip(output_jsonl_path, output_zip_path)
    print("Created:", OUTPUT_ZIP)


if __name__ == "__main__":
    main()