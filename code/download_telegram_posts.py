#!/usr/bin/env python3
"""Download public Telegram channel posts for a date window."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from project_paths import ENV_FILE, CHANNEL_MANIFEST, RAW_DATA_DIR, telegram_session_path
from typing import Iterable

from telethon import TelegramClient


def load_dotenv(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_utc_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD, for example 2024-01-31") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download posts from public Telegram channels into JSONL."
    )
    parser.add_argument("--start", required=True, type=parse_utc_date, help="Start date, inclusive, UTC: YYYY-MM-DD")
    parser.add_argument("--end", required=True, type=parse_utc_date, help="End date, exclusive, UTC: YYYY-MM-DD")
    parser.add_argument(
        "--channel",
        action="append",
        dest="channels",
        help="Channel handle without @. Can be passed multiple times. Defaults to the 20 approved-channel selections.",
    )
    parser.add_argument("--out-dir", default=str(RAW_DATA_DIR), help="Output directory")
    parser.add_argument("--channels-file", help="CSV channel manifest with a handle column; blank handles are skipped")
    parser.add_argument("--csv", action="store_true", help="Also export one UTF-8 CSV per channel")
    return parser


def message_to_row(channel: str, msg) -> dict:
    replies = msg.replies.replies if msg.replies else None
    row = {
        "channel": channel,
        "id": msg.id,
        "date": msg.date.isoformat() if msg.date else None,
        "text": msg.message,
        "views": msg.views,
        "forwards": msg.forwards,
        "reply_count": replies,
        "has_media": msg.media is not None,
        "grouped_id": msg.grouped_id,
        "post_author": msg.post_author,
        "url": f"https://t.me/{channel}/{msg.id}",
    }
    row['collected_at_utc'] = datetime.now(timezone.utc).isoformat()
    row['media_type'] = type(msg.media).__name__ if msg.media else None
    for key in ['edit_date', 'sender_id', 'pinned', 'post', 'silent', 'noforwards', 'via_bot_id', 'ttl_period']:
        value = getattr(msg, key, None)
        row[key] = value.isoformat() if isinstance(value, datetime) else value
    for key in ['fwd_from', 'reply_to', 'reactions', 'entities', 'reply_markup', 'replies', 'media']:
        value = getattr(msg, key, None)
        row[key + '_json'] = json.dumps(value, ensure_ascii=False, default=json_default) if value is not None else None
    file = msg.file
    for key in ['name', 'mime_type', 'size', 'width', 'height', 'duration', 'title', 'performer']:
        row['file_' + key] = getattr(file, key, None) if file else None
    row['raw_message_json'] = json.dumps(msg.to_dict(), ensure_ascii=False, default=json_default)
    return row


def json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        import base64
        return base64.b64encode(value).decode('ascii')
    if hasattr(value, 'to_dict'):
        return value.to_dict()
    raise TypeError(f'Unsupported metadata type: {type(value)}')


async def download_channel(
    client: TelegramClient,
    channel: str,
    start: datetime,
    end: datetime,
    out_dir: Path,
    export_csv: bool = False,
) -> int:
    jsonl_dir = out_dir / "jsonl"
    csv_dir = out_dir / "csv"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)
    out_path = jsonl_dir / f"{channel}_{start.date()}_{end.date()}.jsonl"
    count = 0
    rows = []
    entity = await client.get_entity(channel)

    async for msg in client.iter_messages(entity, offset_date=end):
        if msg.date is None:
            continue
        if msg.date < start:
            break
        if msg.date >= end:
            continue

        row = message_to_row(channel, msg)
        row.update(channel_id=entity.id, channel_title=entity.title, channel_username=entity.username)
        rows.append(row)
        count += 1
        if count % 1000 == 0:
            print(f"{channel}: collected {count} posts...")

    rows.reverse()
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"{channel}: wrote {count} posts to {out_path}")
    if export_csv:
        csv_path = csv_dir / out_path.with_suffix('.csv').name
        fields = list(rows[0]) if rows else ['channel', 'id', 'date', 'text', 'url']
        with csv_path.open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{channel}: wrote CSV to {csv_path}", flush=True)
    return count

async def run(channels: Iterable[str], start: datetime, end: datetime, out_dir: Path, export_csv: bool = False) -> None:
    load_dotenv()

    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    session = telegram_session_path()

    if not api_id or not api_hash:
        raise SystemExit("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH. Put them in configs/.env.")
    if start >= end:
        raise SystemExit("--start must be earlier than --end")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metadata").mkdir(parents=True, exist_ok=True)

    client = TelegramClient(session, int(api_id), api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise SystemExit('Saved Telegram session is not authorized. Run code/telegram_login.py to renew it.')
    summary = []
    try:
        for channel in channels:
            channel = channel.lstrip('@')
            try:
                count = await download_channel(client, channel, start, end, out_dir, export_csv)
                summary.append(dict(channel=channel, status='complete', posts=count))
            except Exception as exc:
                summary.append(dict(channel=channel, status='failed', error=str(exc)))
                print(f'{channel}: FAILED: {exc}', flush=True)
            (out_dir / 'metadata/download_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    finally:
        await client.disconnect()


def main() -> None:
    args = build_parser().parse_args()
    channels = args.channels
    if args.channels_file or not channels:
        with open(args.channels_file or CHANNEL_MANIFEST, encoding='utf-8-sig', newline='') as handle:
            channels = [row['handle'] for row in csv.DictReader(handle) if row['handle'].strip()]
    asyncio.run(run(channels, args.start, args.end, Path(args.out_dir), args.csv))


if __name__ == "__main__":
    main()
