#!/usr/bin/env python3
"""
Build script for the N5 Vocabulary Practice app.

Regenerates index.html (a single, self-contained, offline-capable HTML file)
by embedding the current vocabulary list into template.html.

Usage:
    python3 build.py --xlsx japanese_n5_vocabulary_updated.xlsx
    python3 build.py --json vocab_data.json
    python3 build.py                # defaults to japanese_n5_vocabulary_updated.xlsx if present,
                                     # otherwise vocab_data.json

Requires: openpyxl (only if building from an .xlsx file)
    pip install openpyxl --break-system-packages
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "template.html")
OUTPUT_PATH = os.path.join(HERE, "index.html")
DEFAULT_XLSX = os.path.join(HERE, "japanese_n5_vocabulary_updated.xlsx")
DEFAULT_JSON = os.path.join(HERE, "vocab_data.json")

EXPECTED_HEADER = ["Kanji", "Hiragana", "Romaji", "English", "Category", "Word Type", "Learned", "Notes", "Last Used"]


def load_from_xlsx(path):
    try:
        import openpyxl
    except ImportError:
        sys.exit("openpyxl is required to read .xlsx files. Install with:\n"
                  "  pip install openpyxl --break-system-packages")

    wb = openpyxl.load_workbook(path, data_only=True)
    if "N5 Vocabulary" not in wb.sheetnames:
        sys.exit(f"Sheet 'N5 Vocabulary' not found in {path}. Sheets present: {wb.sheetnames}")
    ws = wb["N5 Vocabulary"]

    rows = list(ws.iter_rows(min_row=1, values_only=True))
    header = [str(h).strip() if h else "" for h in rows[0]]
    if header[:len(EXPECTED_HEADER)] != EXPECTED_HEADER:
        print("Warning: header row doesn't match the expected layout.", file=sys.stderr)
        print(f"  Expected: {EXPECTED_HEADER}", file=sys.stderr)
        print(f"  Found:    {header}", file=sys.stderr)

    words = []
    skipped = 0
    for i, r in enumerate(rows[1:]):
        if not r or not any(r):
            continue
        kanji, hiragana, romaji, english, category, wtype, learned = (list(r) + [None] * 9)[:7]
        if not hiragana and not kanji:
            skipped += 1
            continue
        if not english:
            skipped += 1
            continue
        words.append({
            "id": len(words),
            "k": (kanji or "").strip(),
            "h": (hiragana or "").strip(),
            "r": (romaji or "").strip(),
            "e": (english or "").strip(),
            "cat": (category or "General").strip(),
            "type": (wtype or "").strip(),
            "learned": (str(learned).strip().upper() == "YES"),
        })
    if skipped:
        print(f"Note: skipped {skipped} row(s) missing required fields.", file=sys.stderr)
    return words


def load_from_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for i, w in enumerate(data):
        w["id"] = i
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", help="Path to the vocabulary .xlsx file")
    ap.add_argument("--json", help="Path to a vocab_data.json file (already-extracted format)")
    ap.add_argument("--out", default=OUTPUT_PATH, help="Output HTML path (default: index.html)")
    ap.add_argument("--save-json", action="store_true",
                     help="When building from .xlsx, also write vocab_data.json alongside it")
    args = ap.parse_args()

    if args.xlsx:
        words = load_from_xlsx(args.xlsx)
        src = args.xlsx
    elif args.json:
        words = load_from_json(args.json)
        src = args.json
    elif os.path.exists(DEFAULT_XLSX):
        words = load_from_xlsx(DEFAULT_XLSX)
        src = DEFAULT_XLSX
    elif os.path.exists(DEFAULT_JSON):
        words = load_from_json(DEFAULT_JSON)
        src = DEFAULT_JSON
    else:
        sys.exit("No vocabulary source found. Pass --xlsx or --json, or place "
                  f"{os.path.basename(DEFAULT_XLSX)} in this folder.")

    if not words:
        sys.exit(f"No words loaded from {src} — nothing to build.")

    if args.save_json and args.xlsx:
        with open(DEFAULT_JSON, "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False, indent=1)
        print(f"Wrote {DEFAULT_JSON} ({len(words)} words)")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    vocab_json = json.dumps(words, ensure_ascii=False)
    build_info = json.dumps({
        "builtAt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "count": len(words),
    })

    out = template.replace(
        "/*__VOCAB_JSON__*/[]/*__END_VOCAB_JSON__*/",
        f"/*__VOCAB_JSON__*/{vocab_json}/*__END_VOCAB_JSON__*/",
    )
    out = out.replace(
        '/*__BUILD_INFO__*/{"builtAt":"unknown","count":0}/*__END_BUILD_INFO__*/',
        f"/*__BUILD_INFO__*/{build_info}/*__END_BUILD_INFO__*/",
    )

    if "/*__VOCAB_JSON__*/" not in template or vocab_json not in out:
        sys.exit("Failed to inject vocabulary data — template placeholder may have been edited/removed.")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)

    size_kb = os.path.getsize(args.out) / 1024
    print(f"Built {args.out} — {len(words)} words from {src} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
