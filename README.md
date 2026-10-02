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

Full workflow — pull the current spreadsheet from the private tutoring
repo, rebuild, then push here:

```bash
# 1. Pull the current spreadsheet from the private japanese-n5-tutor repo
#    (token is in that repo's github_access.md)
curl -s -H "Authorization: token <GITHUB_TOKEN>" \
  -H "Accept: application/vnd.github.raw" \
  -o japanese_n5_vocabulary_updated.xlsx \
  https://api.github.com/repos/StuMan8424-Claude/japanese-n5-tutor/contents/japanese_n5_vocabulary_updated.xlsx

# 2. Rebuild index.html (and refresh the JSON export) from it
pip install openpyxl --break-system-packages   # first time only
python3 build.py --xlsx japanese_n5_vocabulary_updated.xlsx --save-json

# 3. Commit and push index.html, vocab_data.json, and the .xlsx snapshot to this repo
```

GitHub Pages redeploys automatically on push — the next time your phone has
a connection and opens the app, it'll pull the update; if you're offline,
you'll keep using whatever was cached at last connection.

## Troubleshooting: app looks out of date

The service worker fetches fresh content whenever it can reach the network
and only falls back to the cached copy when offline — so an out-of-date
app almost always means it hasn't had a chance to refresh yet, not that
something's broken.

1. Make sure you actually have a connection (not airplane mode) when you
   open it.
2. Force-quit and reopen: swipe up to the App Switcher, swipe the app's
   card off the top, then relaunch from its Home Screen icon. This mostly
   matters because iOS can otherwise resume a backgrounded page instead of
   loading it fresh.
3. If it's still stale, the guaranteed manual reset (this clears saved
   progress/stats too, since they share the same storage as the cache):
   - **Settings app → Safari → Advanced → Website Data**, find the site,
     swipe to **Delete**
   - Delete the Home Screen icon (long-press → Remove App)
   - Revisit the URL fresh in Safari, confirm it looks current, then
     **Share → Add to Home Screen** again

If none of that works, check that the service worker's fetch handler is
actually bypassing the HTTP cache (`{ cache: 'no-store' }` on the `fetch()`
call in `service-worker.js`) — without it, "network-first" can silently
serve a stale cached response instead of really checking the server, which
force-quitting can't fix since the staleness lives one layer below the app.

## Modes

1. **Flash cards** — tap to reveal, mark ✓ Got it / ✕ Missed it. The prompt
   never shows the reading — the flip reveals everything the prompt didn't
   already give away.
2. **Multiple choice** — pick from 4 options. If a reading hint is
   available for the prompt, it's hidden behind a "Tap to show reading"
   line rather than shown outright.
3. **Text entry** — type the answer and check it. Same tap-to-reveal
   reading hint as multiple choice.
4. **New vocab** — drills up to 5 "not yet learned" words at once. A word
   is mastered once you pass it in flash cards, multiple choice, AND text
   entry — back to back, any miss resets that word's streak. Mastered
   words are tracked locally on the device (separate from the spreadsheet)
   so they won't resurface as "new" here again. Ends with a downloadable
   `.txt` report of what you mastered, formatted for pasting into
   `new_words.txt` in a future tutoring session.
5. **Browse list** — not a quiz. Just lists every word matching the
   current Word set + Category filters, grouped by category, with reading
   and a ✓ for anything already marked learned. Useful for sanity-checking
   what's actually in a filter before starting a session with it. A ⏱
   marks words you tend to answer slowly (see Response-time tracking).
6. **Katakana** — a character drill, separate from the vocabulary modes
   (the 46 base katakana are built into the app, not read from the
   spreadsheet, so the Word set / Category / Entry mode / Session length
   settings don't apply). Multiple choice: see a katakana character, pick
   its reading. Distractors come from look-alike groups first — シ/ツ/ソ/ン
   is the main one, plus ノ/メ/ヌ, ウ/ワ/フ, ク/ケ, コ/ユ/ヨ, サ/セ, チ/テ,
   ニ/ハ/ヒ, ホ/ネ, マ/ム, ル/レ/ロ, リ/ル — with random characters only
   filling gaps. Characters you've missed before are asked more often.
   First answer stands. No mnemonics or hints: contrast drilling only.
   Round size is 10 / 20 / 30 / all 46 — growing it over time is the pace
   indicator. Per-character results are kept locally, separate from the
   vocabulary stats.

## Word set

Filters which words are eligible before starting a flash card / multiple
choice / text entry / browse session: **Learned only** (default), **Not
yet learned**, **Weak words** (missed before, or answered slowly — see
below), or **All words**. Doesn't apply to New Vocab mode, which always pulls from
not-yet-learned words regardless of this setting.

## Favor weak & newer words

For flash cards, multiple choice and text entry sessions (not New vocab,
Browse or Katakana), a **Favor weak & newer words** setting — **On** by
default — biases which words get picked and the order they come in. It's a
soft bias, not a filter: everything in your Word set / Category filters can
still appear, and **Off (even draw)** restores a plain shuffle.

Each word gets a weight starting at 1 (capped at 7):

- up to +4.5 for being missed more than answered right (fades as you get it
  right)
- +1.5 if it's slower than your own average on multiple choice
- +2.25 / +1.5 / +0.75 if it's never been seen / seen once / seen twice
- +0.5 if the sheet doesn't mark it learned

Selection is weighted without replacement and the order is kept, so weak
words also tend to come earlier — which means the setting still matters when
a session covers the whole filter. On a realistic history, a word missed
several times was about 4× as likely to land in a 50-card session as a solid
word, and slow or barely-seen words about 2×.

Evidence comes only from flash cards and multiple choice (text entry never
writes to the per-word record), so a device with no history treats every
word as new and the bias is mild. Constants live in `wordWeight()` in
`template.html`.

## Response-time tracking

Only **multiple choice** (and its leg of New vocab) is timed, as a
confidence signal. It runs silently — nothing ticks on screen.

- The timed moment is the choice tap. Flash cards are **not** timed —
  time-to-reveal can't tell "knew it" from "stared at it". Flash correctness
  (your own Got it / Missed it) is still recorded.
- Only **correct** answers are timed.
- **Text entry is not tracked at all** — no correctness, no timing in the
  persistent per-word record. Exact-match typing is too noisy to trust
  (phrase-style meanings, romaji spelling variants, keyboard autocorrect).
  It still gives on-screen feedback and drives the current session. The
  English matcher accepts the full string, each `/` or `;` alternative, and
  each with a parenthetical dropped ("Old (objects)" → "old"); about 25
  counter/phrase entries still have no sensible typeable form.
- Anything over **20 seconds** is discarded as "stepped away and came
  back" rather than counted as slow (`DISTRACTION_CAP_MS` in `template.html`).
- Each word keeps a rolling window of its last 6 times
  (`TIMES_PER_WORD_CAP`), so one bad day doesn't haunt it forever.
- A word counts as **slow** when its average is more than 1.6× your own
  overall average (relative to *you*, not a fixed number of seconds).
  Slow words are included in the **Weak words** filter even if you've never
  missed them, and get a ⏱ in Browse list.
- Katakana rounds also record correct-answer times (same cap) per
  character; nothing displays them yet.

Stats are stored per device in local storage and don't sync.

## Text entry: self-graded phrase cards

About 25 entries have English meanings that can't be typed fairly
("Small animals counter: cats, dogs, fish, rabbits"). In text entry, when
the answer is English and none of the accepted forms is short and free of
list punctuation, the card becomes self-graded: **Show answer**, then
**Got it / Missed it**, just like a flash card. This also applies to the
text leg of New vocab, so those words can still be mastered. Japanese entry
mode isn't affected (there's no English to type).

## Passing New vocab back to the spreadsheet

The app can't write to the spreadsheet or the tutoring repo (by design — no
token lives in a public app). Instead, the settings screen has a **New vocab
to pass back to the sheet** panel listing every word mastered in New vocab
on this device that the sheet still shows as not learned. **Copy list** or
**Download .txt**, then give it to Claude in a tutoring session, which
updates the spreadsheet and `new_words.txt`. The list is self-cleaning:
after the sheet is updated and the app rebuilt (see above), those words show
as learned and drop off it. (Each New vocab session summary also has its own
per-session report.) "Mastered" here means the app's rule — a clean pass in
flash, multiple choice and text — not the tutoring rule of two independent
production sentences, so treat it as "drilled", not "learned".

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
