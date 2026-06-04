#!/usr/bin/env python3
"""
Extract utterance segments from downloaded source audio.

Reads timing information from each language's metadata.csv, locates the
corresponding source file in downloads/{lang}/, and writes 16 kHz mono WAV
files into the dataset directory structure alongside the existing transcripts.

Run download_audio.py first to populate the downloads/ directory.

Usage:
  python segment_audio.py                          # all languages
  python segment_audio.py -l Cornish               # one language
  python segment_audio.py -l Cornish Hawaiian      # multiple languages
  python segment_audio.py --language Manx Mohawk   # long form
  python segment_audio.py --workers 4              # limit parallel jobs

Requirements:
  pip install soundfile numpy
  ffmpeg: https://ffmpeg.org/download.html
"""

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import soundfile as sf

LANGUAGES = ['Cornish', 'Hawaiian', 'Jejueo', 'Manx', 'Mohawk']
REPO_ROOT = Path(__file__).parent
DOWNLOADS_DIR = REPO_ROOT / 'downloads'
SAMPLE_RATE = 16000


def get_output_path(lang: str, row: dict) -> Path:
    uid = row['id']
    subset = row['subset']
    base = REPO_ROOT / lang / subset
    if '-' in uid:
        clean = uid.removeprefix('lbi-')
        rec_id, idx = clean.rsplit('-', 1)
        return base / rec_id / f'lbi-{rec_id}-{idx}.wav'
    return base / uid / f'{uid}.wav'


def find_source(lang_dir: Path, rec_id: str) -> Path | None:
    matches = list(lang_dir.glob(f'{rec_id}.*'))
    return matches[0] if matches else None


def decode_audio(src: Path) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp = Path(f.name)
    try:
        subprocess.run(
            ['ffmpeg', '-y', '-i', str(src), '-ar', str(SAMPLE_RATE), '-ac', '1', str(tmp)],
            capture_output=True, check=True,
        )
        data, _ = sf.read(str(tmp), dtype='int16')
        return data
    finally:
        tmp.unlink(missing_ok=True)


def process_source(lang: str, src: Path, rows: list[dict]) -> tuple[int, int, list[str]]:
    done = errors = 0
    error_ids = []
    try:
        audio = decode_audio(src)
    except Exception as e:
        print(f'    decode failed {src.name}: {type(e).__name__}: {e}', file=sys.stderr)
        return 0, len(rows), [row['id'] for row in rows]

    for row in rows:
        out_path = get_output_path(lang, row)
        if out_path.exists():
            done += 1
            continue
        try:
            start = int(float(row['start_sec']) * SAMPLE_RATE)
            end = int(float(row['end_sec']) * SAMPLE_RATE)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(out_path), audio[start:end], SAMPLE_RATE, subtype='PCM_16')
            done += 1
        except Exception as e:
            print(f'    segment failed {row["id"]}: {type(e).__name__}: {e}', file=sys.stderr)
            error_ids.append(row['id'])
            errors += 1

    rec_id = rows[0]['id'].removeprefix('lbi-').split('-')[0]
    status = f'{done} segments'
    if errors:
        status += f', {errors} failed'
    print(f'  {rec_id} — {status}', flush=True)

    return done, errors, error_ids


def process_language(lang: str, workers: int) -> None:
    print(f'\n=== {lang} ===', flush=True)
    lang_dir = DOWNLOADS_DIR / lang

    with open(REPO_ROOT / lang / 'metadata.csv', newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    source_groups: dict[Path, list[dict]] = defaultdict(list)
    skipped = 0

    for row in rows:
        rec_id = row['id'].removeprefix('lbi-').split('-')[0]
        src = find_source(lang_dir, rec_id)
        if src is None:
            skipped += 1
        else:
            source_groups[src].append(row)

    done = errors = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_source, lang, src, src_rows): src
            for src, src_rows in source_groups.items()
        }
        for future in as_completed(futures):
            d, e, eids = future.result()
            done += d
            errors += e
            for uid in eids:
                print(f'    failed: {uid}', file=sys.stderr)

    print(f'  Complete: {done}/{len(rows)} utterances', end='')
    if skipped:
        print(f' ({skipped} skipped — source not in downloads/)', end='')
    if errors:
        print(f' ({errors} errors)', end='')
    print()


def check_dependencies() -> None:
    if shutil.which('ffmpeg') is None:
        print('Missing dependency: ffmpeg', file=sys.stderr)
        print('  https://ffmpeg.org/download.html', file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Extract utterance segments from downloaded source audio.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'Available languages: {", ".join(LANGUAGES)}',
    )
    parser.add_argument(
        '-l', '--language',
        nargs='+',
        choices=LANGUAGES,
        default=LANGUAGES,
        dest='languages',
        metavar='LANG',
        help=f'Language(s) to process. Choices: {", ".join(LANGUAGES)}. Default: all.',
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=os.cpu_count(),
        metavar='N',
        help=f'Parallel decode jobs (default: {os.cpu_count()}).',
    )
    args = parser.parse_args()

    check_dependencies()

    for lang in args.languages:
        process_language(lang, args.workers)

    print('\nDone.')


if __name__ == '__main__':
    main()
