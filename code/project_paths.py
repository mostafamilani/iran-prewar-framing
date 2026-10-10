"""Shared project paths, resolved independently of the working directory."""
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / 'configs'
ENV_FILE = CONFIG_DIR / '.env'
SESSIONS_DIR = CONFIG_DIR / 'sessions'
CONFIG = json.loads((CONFIG_DIR / 'project.json').read_text(encoding='utf-8'))
CHANNEL_MANIFEST = PROJECT_ROOT / CONFIG['channel_manifest']
RAW_DATA_DIR = PROJECT_ROOT / CONFIG['raw_data_dir']
RAW_CSV_DIR = RAW_DATA_DIR / 'csv'
RAW_JSONL_DIR = RAW_DATA_DIR / 'jsonl'
METADATA_DIR = RAW_DATA_DIR / 'metadata'
START_DATE = CONFIG['start_utc'][:10]
END_DATE = CONFIG['end_utc_exclusive'][:10]

def telegram_session_path():
    value = Path(os.environ.get('TELEGRAM_SESSION', 'telegram_research'))
    if value.is_absolute():
        return str(value)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return str(SESSIONS_DIR / value if len(value.parts) == 1 else PROJECT_ROOT / value)
