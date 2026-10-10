# Framing the Road to War: Social Media and Iranian Public Opinion

Repository name: `iran-prewar-framing`

Repository description: Studying how Iranian social media framed the lead-up to the Iran–US war, using Entman's framing framework to examine narratives relevant to prewar public opinion.

This project studies posts from 20 popular Persian-language Telegram channels serving Iranian audiences during the three months leading up to the Iran–US war, using February 28, 2026 as the study's war-start boundary. The aim is to understand how these channels presented the prospect of conflict and how their communication may have contributed to the formation of public opinion before the war.

The research examines which issues channels emphasized, how they explained rising tensions, whom they held responsible, how they evaluated possible conflict, and which responses they promoted. Comparisons across channels and over time can reveal recurring and competing interpretations of diplomacy, military action, security, civilian harm, and political responsibility.

The current collection contains **157,604 posts across 20 selected channels**, collected on October 9, 2026. It covers **November 28, 2025 at 00:00 UTC, inclusive, through February 28, 2026 at 00:00 UTC, exclusive**. The post collection is complete; systematic framing analysis of the full collection is planned.

## Framing framework

The theoretical foundation is Robert M. Entman's seminal article, **“Framing: Toward Clarification of a Fractured Paradigm”** (1993), *Journal of Communication*, 43(4), 51–58. The four framing functions below guide the planned study.

Entman's framework treats framing as the selection and emphasis of aspects of an issue that guide its interpretation. The planned coding will examine four functions:

| Framing function | Question for a Telegram post |
| --- | --- |
| Problem definition | What situation is presented as a problem, threat, opportunity, or cost? |
| Causal interpretation | Who or what is presented as responsible, and what explanation is offered? |
| Moral evaluation | What judgments are expressed about actors, actions, or consequences? |
| Treatment recommendation | What response or remedy is proposed, supported, or rejected? |

A post may express several functions, only one, or none. Coding should distinguish the channel's own framing from an attributed quotation, forwarded message, or guest's interpretation. Retain supporting Persian excerpts and links to the parent post. Code absence and uncertainty explicitly rather than forcing every post into all four functions.

The existing scripts include pilot unitization, Persian seed-codebook generation, heuristic coding, and Gemini-assisted coding developed for Iran International. These are starting tools for a broader study, rather than a validated coding scheme for all 20 channels. The next steps are to refine the codebook on a diverse pilot sample, review coding with human coders, assess agreement, and then compare frame prevalence and change across channels and dates. Any model-assisted labels should retain their provenance and receive human validation.

Text analysis identifies frames available to audiences. Establishing that these frames changed public opinion will require additional audience evidence, such as surveys, interviews, or a suitable causal design. Engagement counters provide context but do not directly measure attitudes or endorsement.

## Shared repository contents

This repository currently shares the research description, Telegram downloader and login utility, non-secret configuration, and actual posts from the 20 selected channels. Framing-analysis scripts, older datasets, local credentials, and login sessions remain in the private working project.

```text
code/                                      Downloader, login, and shared paths
configs/approved_channels.csv              The 20 selected channels and identity notes
configs/project.json                       Study dates and data paths
configs/env.example                        Blank credential template
data/raw/prewar_2025-11-28_2026-02-28/
  csv/                                     20 complete per-channel CSV.gz files
  metadata/                                Counts, date coverage, and checksums
requirements.txt                           Downloader dependency
```

## Dataset

The [post files](data/raw/prewar_2025-11-28_2026-02-28/csv/) contain all **157,604 messages** from the 20 selected channels. The [per-channel inventory](data/raw/prewar_2025-11-28_2026-02-28/metadata/collection_inventory.csv) lists counts, date ranges, channel IDs, and identity caveats. No rows or fields were removed for publication.

Each `.csv.gz` is a losslessly compressed CSV. Compression is used because several original CSVs exceed [GitHub's regular file-size limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). Decompression reproduces the original CSV byte-for-byte; original file hashes are recorded in `metadata/compression_manifest.json`.

Decompress all files with Python (no additional packages needed):

```python
from pathlib import Path
import gzip
import shutil

folder = Path("data/raw/prewar_2025-11-28_2026-02-28/csv")
for path in folder.glob("*.csv.gz"):
    with gzip.open(path, "rb") as source, path.with_suffix("").open("wb") as output:
        shutil.copyfileobj(source, output)
```

Or read a compressed CSV directly with Python:

```python
import csv
import gzip
import sys

csv.field_size_limit(sys.maxsize)
path = "data/raw/prewar_2025-11-28_2026-02-28/csv/IranintlTV_2025-11-28_2026-02-28.csv.gz"
with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as source:
    for post in csv.DictReader(source):
        print(post["date"], post["text"])
```

Each row is one Telegram message, including media-only messages. Album messages are linked through `grouped_id`. CSVs retain Persian text and multiline captions; message and channel IDs; publication, edit, and collection times; post links; views, forwards, and reply counts; authors/senders; reactions; forwarding origins; reply relationships; text entities; buttons; media/file properties; and complete raw message metadata where available. Complex fields are JSON strings. Files use UTF-8 with BOM and chronological ordering.

The collection was validated for date boundaries, duplicate IDs within each channel, chronological order, and consistency with the original structured records. The repository distributes CSVs containing raw message metadata; separate duplicate JSONL exports are retained in the local project.

### Selection and limitations

The channels were selected from the researcher's approved-channel list primarily by post reach, with subscriber counts providing secondary context. This is a purposive sample, not a representative sample of all Iranians or all social media use. The [manifest](configs/approved_channels.csv) preserves PDF ranks, titles, audience counts, selected handles, candidate handles, and identity status.

Usernames can change or be reassigned. The former `FO_RK` channel was traced to `KH_B2` using stable channel ID `1350986218`; AVATODAY is `javanmardi77`. Where the صابرین name was ambiguous, the larger candidate, `saberin_ir`, was selected at the researcher's request. **PDF entry 20 uses `tkhbr` as a larger similar-name substitute; its identity as the original entry remains unconfirmed.** Retain this caveat in analysis and publication.

Deleted posts cannot be recovered. Text edits and engagement counters reflect collection time, not necessarily their prewar values. Media metadata is included, but media binaries and separate comment threads were not downloaded. Forwarded or repeated content across channels is retained.

## Downloading posts

Use Python 3.10 or newer. From the repository root, create a virtual environment and install the dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp configs/env.example configs/.env
```

Fill `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` in `configs/.env` with your own Telegram API credentials. `TELEGRAM_SESSION` is a local session basename stored under `configs/sessions/`. Credentials and sessions are excluded from Git. Optional model-API entries in the template belong to future analysis work and are not needed by the downloader.

Log in interactively:

```bash
python code/telegram_login.py
```

Download to a new directory to preserve the published collection:

```bash
python code/download_telegram_posts.py \
  --start 2025-11-28 --end 2026-02-28 \
  --channels-file configs/approved_channels.csv --csv \
  --out-dir data/raw/prewar_refresh_2025-11-28_2026-02-28
```

`--start` is inclusive and `--end` is exclusive, in UTC. The manifest is the default channel list; repeated `--channel HANDLE` arguments can select individual channels. The downloader creates plain CSVs in `csv/`, JSONL files in `jsonl/`, and progress reports in `metadata/`. Dataset paths are resolved from the repository root, so scripts can also be invoked from another working directory using an absolute script path.
