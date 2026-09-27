# N5 単語 Practice

An installable, offline JLPT N5 vocabulary practice app — flash cards,
multiple choice, text entry, and a mastery-driven "new vocab" drill mode.
Hosted here as a Progressive Web App (PWA) so it installs to your phone's
Home Screen and works with no connection at all (airplane mode included).

**Live app:** enable GitHub Pages on this repo (Settings → Pages → Deploy
from branch → `main` / `/ (root)`) and it'll be served at
`https://stuman8424-claude.github.io/n5-vocab-app/`

## Installing on iOS (the part that actually works)

Local files opened via the Files app or Shortcuts get blocked by iOS from
opening as a real, JS-capable page — that's why this is hosted instead.
Once GitHub Pages is live:

1. Open the live URL above **in Safari** (has to be Safari, not Chrome or
   an in-app browser — only Safari can add to the Home Screen)
2. Tap the **Share** button (square with an arrow, bottom of the screen)
3. Tap **Add to Home Screen**, confirm the name, tap **Add**
4. Open it from the Home Screen icon like any other app

The first load needs a real connection (to fetch the page once and let the
service worker cache it). After that, it works fully offline — turn on
airplane mode before or after that first load, doesn't matter, as long as
the first load has already happened once.

## Why a separate public repo

GitHub Pages (free tier) only serves from public repos. The actual
studying — session history, the tutoring workflow, `tutor_prompt.txt` —
stays in the private `japanese-n5-tutor` repo. This repo only holds the
generated practice app itself: vocabulary data, no personal notes or
session history.

## Updating the vocab list

When the vocabulary spreadsheet in the private tutoring repo changes,
rebuild and re-push here:

```bash
pip install openpyxl --break-system-packages   # first time only
python3 build.py --xlsx japanese_n5_vocabulary_updated.xlsx --save-json
```

This regenerates `index.html` from `template.html` + the spreadsheet. Then
commit and push `index.html` (and `vocab_data.json` / the `.xlsx` snapshot
if you want them to stay in sync here too). GitHub Pages redeploys
automatically on push — the next time your phone has a connection and
opens the app, it'll pull the update; if you're offline, you'll keep using
whatever was cached at last connection.

## Modes

1. **Flash cards** — tap to reveal, mark ✓ Got it / ✕ Missed it. The prompt
   never shows the reading — the flip reveals everything the prompt didn't
   already give away.
2. **Multiple choice** — pick from 4 options.
3. **Text entry** — type the answer and check it.
4. **New vocab** — drills up to 5 "not yet learned" words at once. A word
   is mastered once you pass it in flash cards, multiple choice, AND text
   entry — back to back, any miss resets that word's streak. Mastered
   words are tracked locally on the device (separate from the spreadsheet)
   so they won't resurface as "new" here again. Ends with a downloadable
   `.txt` report of what you mastered, formatted for pasting into
   `new_words.txt` in a future tutoring session.

## Entry mode

**English** or **Japanese** — sets which language you answer in for **text
entry only** (the only mode where you're actually typing, so it's the only
one where the script matters for your keyboard). Flash cards and multiple
choice always mix freely across English↔Japanese and, for words with a
kanji form, kanji↔kana reading questions too, regardless of this setting.

## Missed-word recycling (flash / MC / text)

A missed word is reinserted into the queue twice — once ~8–14 words later,
once ~24–38 words later — so misses get reinforced within the same session.

## Files

| File | Purpose |
|---|---|
| `index.html` | The app. This is what Pages serves and what the service worker caches. |
| `manifest.json` | Web app manifest — name, icons, standalone display mode. |
| `service-worker.js` | Caches the app for offline use after the first load. |
| `apple-touch-icon.png`, `icon-192.png`, `icon-512.png`, `icon-512-maskable.png`, `favicon-32.png` | App icons. |
| `template.html` | HTML/CSS/JS shell with a data placeholder — source for `build.py`. |
| `build.py` | Regenerates `index.html` from a spreadsheet or JSON export. |
| `vocab_data.json` | Plain JSON export of the vocab list at last build time. |
| `japanese_n5_vocabulary_updated.xlsx` | Snapshot of the vocab spreadsheet used for this build. |

## Notes / limitations

- Per-word stats (including New Vocab mastery) are keyed by row position in
  the vocabulary list. Reordering or deleting rows in the spreadsheet
  between rebuilds can realign saved stats to different words — appending
  new words at the end is safe.
- The 🔊 speaker button uses the device's built-in text-to-speech; works
  offline on iOS once a Japanese voice has been used once.
- Typing kanji in text entry (Japanese entry mode, kana→kanji questions)
  needs a Japanese keyboard/IME. Flash cards and multiple choice don't
  need one.
- All progress is stored in that browser's local storage on that device
  only — nothing syncs anywhere, and clearing Safari's site data for this
  app will reset it.
