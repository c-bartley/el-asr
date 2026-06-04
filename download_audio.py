#!/usr/bin/env python3
"""
Download source audio for the endangered language ASR dataset.

Downloads one file per unique source recording into downloads/{lang}/.
Run segment_audio.py afterwards to extract utterance segments.

Usage:
  python download_audio.py                          # all languages
  python download_audio.py -l Cornish               # one language
  python download_audio.py -l Cornish Hawaiian      # multiple languages
  python download_audio.py --language Manx Mohawk   # long form

Requirements:
  pip install yt-dlp requests
  ffmpeg: https://ffmpeg.org/download.html (required by yt-dlp for audio extraction)
"""

import argparse
import csv
import shutil
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

import requests
import yt_dlp

LANGUAGES = ['Cornish', 'Hawaiian', 'Jejueo', 'Manx', 'Mohawk']
REPO_ROOT = Path(__file__).parent
DOWNLOADS_DIR = REPO_ROOT / 'downloads'

SKIP_SOURCES = {
    'forvo':       'Automated download is prohibited by Forvo Terms of Service.',
    'tts-bobc':    'No source URLs available.',
    'elar':        'Requires an access request at https://elararchive.org',
    'elar_doreco': 'Protected by Cloudflare; automated download not possible.',
    'youtube':     'YouTube access is unreliable for automated download; obtain manually.',
}

YTDLP_SOURCES = {'soundcloud', 'clilstore'}


def clean_url(url: str) -> str:
    # Clilstore URLs encode '&' as '{and}' to avoid CSV ambiguity.
    return url.replace('{and}', '&').strip()


def find_downloaded(lang_dir: Path, rec_id: str) -> Path | None:
    for f in lang_dir.glob(f'{rec_id}.*'):
        if f.suffix == '.part':
            continue
        with open(f, 'rb') as fh:
            header = fh.read(15)
        if header.startswith(b'<!DOCTYPE') or header.startswith(b'<html'):
            f.unlink()  # remove silently-failed download
            continue
        return f
    return None


def download_direct(url: str, dest: Path) -> bool:
    parsed = urllib.parse.urlparse(url)
    decoded_path = urllib.parse.unquote(parsed.path)
    encoded_url = parsed._replace(path=urllib.parse.quote(decoded_path, safe='/')).geturl()
    try:
        resp = requests.get(
            encoded_url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; academic research)'},
            timeout=60,
        )
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f'    download error: {e}', file=sys.stderr)
        return False


def download_ytdlp(url: str, output_template: str) -> bool:
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f'    yt-dlp error: {e}', file=sys.stderr)
        return False


def process_language(lang: str) -> None:
    print(f'\n=== {lang} ===')
    lang_dir = DOWNLOADS_DIR / lang
    lang_dir.mkdir(parents=True, exist_ok=True)

    with open(REPO_ROOT / lang / 'metadata.csv', newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    url_to_rows: dict[str, list[dict]] = defaultdict(list)
    skipped: dict[str, int] = defaultdict(int)

    for row in rows:
        src = row['source']
        url = row['audio_url'].strip()
        if src in SKIP_SOURCES or not url:
            skipped[src] += 1
            continue
        url_to_rows[url].append(row)

    if skipped:
        print('  Skipped (not automatically downloadable):')
        for src in skipped:
            print(f'    [{src}] {SKIP_SOURCES.get(src, "No URL available.")}')
        print(f'    Total skipped: {sum(skipped.values())} utterances')

    pending = {
        url: utt_rows for url, utt_rows in url_to_rows.items()
        if find_downloaded(lang_dir, utt_rows[0]['id'].removeprefix('lbi-').split('-')[0]) is None
    }
    already = len(url_to_rows) - len(pending)
    if already:
        print(f'  {already} already downloaded, {len(pending)} remaining.')

    done = already
    errors = 0

    for i, (url, utt_rows) in enumerate(pending.items(), 1):
        rec_id = utt_rows[0]['id'].removeprefix('lbi-').split('-')[0]
        source = utt_rows[0]['source']
        cleaned = clean_url(url)
        print(f'  [{i}/{len(pending)}] {cleaned[:72]}', end='', flush=True)

        if source in YTDLP_SOURCES:
            ok = download_ytdlp(cleaned, str(lang_dir / f'{rec_id}.%(ext)s'))
        else:
            ext = Path(urllib.parse.urlparse(cleaned).path).suffix or '.mp3'
            ok = download_direct(cleaned, lang_dir / f'{rec_id}{ext}')

        if ok:
            downloaded = find_downloaded(lang_dir, rec_id)
            if downloaded is None:
                print(f'    validation failed: file is HTML or missing', file=sys.stderr)
                ok = False

        print(' — ok' if ok else ' — FAILED')
        done += ok
        errors += not ok

    print(f'  Complete: {done}/{len(url_to_rows)} recordings', end='')
    if errors:
        print(f' ({errors} errors)', end='')
    print()


def check_dependencies() -> None:
    if shutil.which('yt-dlp') is None:
        print('Missing dependency: yt-dlp', file=sys.stderr)
        print('  pip install yt-dlp', file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Download source audio for the endangered language ASR dataset.',
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
    args = parser.parse_args()

    check_dependencies()

    for lang in args.languages:
        process_language(lang)

    print('\nDone.')


if __name__ == '__main__':
    main()
