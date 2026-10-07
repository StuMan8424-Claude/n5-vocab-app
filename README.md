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

Every build **pulls the live sheet** from the private `japanese-n5-tutor`
repo first, so it can't be made from a stale snapshot. The token is read from
the `GITHUB_TOKEN` environment variable (it's never stored in this public
repo):

```bash
pip install openpyxl --break-system-packages   # first time only
GITHUB_TOKEN=<token> python3 build.py          # pull latest sheet, rebuild
```

The build prints what changed since the previous one — new/removed words,
words newly marked learned, edited meanings — and the settings-screen footer
shows when the sheet was last synced (`786 words · sheet synced 2026-10-05`).
Then commit and push `index.html`, `vocab_data.json` and the `.xlsx` snapshot
to this repo.

Without a token, `build.py` falls back to the local `.xlsx` and warns that it
may be stale (`--no-pull` does that on purpose; `--xlsx` / `--json` build
from a specific file). The token is in the tutoring repo's `github_access.md`.

GitHub Pages redeploys automatically on push — the next time your phone has
a connection and opens the app, it'll pull the update; if you're offline,
you'll keep using whatever was cached at last connection.

## Kanji ↔ reading questions (multiple choice only)

The aim is to learn what each kanji **means and how it's read**. Flash cards
and text entry are unchanged; in multiple choice, words written with kanji
also come up two extra ways. A kanji is never in the question and the answers
at the same time.

**Kanji → reading.** The prompt is **one continuous kanji string** from a
word, with all kana stripped (so there's no okurigana to match against): 食
from 食べる, 食 *or* 物 from 食べ物 (never 食物 — kana separates them), 大学
from 大学. The options are **bare readings, not words**: the answer is the
reading of that string in this word (食 → た, 物 → もの, 大学 → だいがく).
Wrong options are readings of other kanji in words you've seen, of similar
length, and:

- never another valid reading of the prompt — answer し for 四 and よん, よっ,
  よ are kept out (and the reverse); 食 never offers しょく or じき beside た;
- never from a word that shares a kanji with the prompt;
- never the same string twice. Words with two readings in one entry (四 =
  し/よん) pick one at random as the answer.

**Kana → kanji.** The prompt is the word in kana; the options are kanji forms
that keep the answer's kana beginning and ending. Order of preference:
1. real words you've seen with the same kana frame (見える → 教える, 答える);
2. real words sharing just the ending (or beginning);
3. only if that's not enough, a **made-up form**: one kanji swapped, the kana
   kept (食べる → 飲べる, 良べる), preferring look-alike kanji
   (`lookalikes.txt`) then other kanji from your list. A made-up form is never
   a word in your list, and a real word that reads like the prompt (a second
   correct answer) is never offered. After you answer, made-up options are
   tagged "not a word" — with what a look-alike kanji actually means ("飲 =
   drink") — so they don't pass for vocabulary.
Pure-kanji words (no kana to match) keep the ordinary real-word options.

**After every kanji question** the card shows the word, its meaning, and the
kanji's meaning and kun/on readings (`食 — eat, food · た(べる), く(う) ·
ショク, ジキ`); a multi-kanji word whose reading can't be built from its kanji
(今日 きょう, 大人 おとな, 明日…) says "irregular reading: learn it as one
word". The speaker button is hidden until you've answered a kanji → reading
question, since saying the word would give the reading away.

If a word can't be asked safely (no table entry for its kanji, or too few
suitable wrong readings) the card quietly asks the meaning instead.

### The kanji tables (`kanji_info.txt`, `lookalikes.txt`)

`kanji_info.txt` has a line per kanji in the list — `kanji|meaning|kun
readings (okurigana in brackets)|on readings` — written from general knowledge
and **checked against the sheet on every build**: every reading the sheet shows
for a single kanji must be in the table, every multi-kanji run is tested to
see whether it can be built from the kanji's readings, and 591 words' kanji are
lined up with their readings (`rn` in `vocab_data.json`; 23 irregular runs
flagged). Sound changes (び for ひ, がっ for がく…) are added automatically.
The build prints `!!` lines for anything missing or inconsistent — add the
kanji or fix the reading and rebuild. When a newly learned word brings in a new
kanji, the build tells you to add it.

`lookalikes.txt` (`kanji|look-alike,look-alike`) is optional polish: 38 kanji
so far, covering the words whose kana frame has too few real partners. Kanji
without an entry fall back to other kanji from your list; the build notes which
learned words that affects. Both files are plain text — edit freely.

### English sanitising

Some English meanings in the sheet carry Japanese — grammar hints like
`It would be better to ~ (た/ない form + ほうがいい)` or a list of example
readings (`General counter (1-10 things): ひとつ、ふたつ、みっつ...`). As a
prompt or a multiple-choice option that hands over the answer, so `build.py`
cleans them: the English keeps everything except the Japanese
(`It would be better to ~`), and what was removed is stored as a note (`n`).
The note appears only where it helps and can't spoil — under the answer after
you flip a flash card, on the answer reveal of a self-graded text card, and in
Browse list. The sheet itself is never modified, the build prints each change,
and it refuses to ship if any English meaning still contains Japanese (11
entries are affected today: the grammar patterns, 知る and 〜つ). Cleaning is
idempotent, and nested brackets like `は(particle)` are handled.

### Why word ids are stable keys

Progress saved on a device (per-word stats, New vocab mastery) is keyed by a
**stable word key**: `kanji|reading`, with the English meaning appended only
where two entries share both (the two 魚 entries). It used to be keyed by row
number, which breaks as soon as the sheet changes: marking words learned
re-sorts it and one inserted word shifted 784 of 786 rows, which would have
silently re-pointed saved progress at the wrong words. Stable keys make
refreshing every build safe, including re-sorts.

`legacy_ids.json` is the old row-number order. It's embedded in the app so
progress saved under the old numeric ids is converted once on first load of
the new build. Keep the file; don't regenerate it. If a word's kanji or
reading is edited in the sheet, that one word's saved progress starts fresh.

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
2. **Multiple choice** — four answers in a 2×2 grid that fills the screen
   below the prompt card. **All four answers share one font size**: the
   largest at which every answer fits its cell (kanji up to ~120px; a card
   with a long phrase shrinks all four together). A label with no spaces —
   kana, kanji, or a single English word — stays on **one line** unless that
   would push it below 20px, i.e. a very long word (about 8+ characters on a
   phone; in the current list only なければならない, ありがとうございます,
   いってらっしゃい, ごちそうさまでした and テープレコーダー wrap). Labels with
   spaces wrap at the spaces, and English labels may also break after `/`,
   `;` or `,`. The Next button's space is always reserved so the grid never
   jumps when it appears. The first answer stands — later taps on that card
   do nothing. If a reading hint is available for the prompt, it's hidden
   behind a "Tap to show reading" line. The Katakana drill uses the same
   grid. Kanji words are also asked two kanji↔reading ways — see below.
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

## Multiple choice distractors

Wrong options are chosen to look like the answer, so a card can't be solved
by form alone (the one い-ending word among verbs, the one "To …" among
nouns). Candidates are scored and the best picked, with some randomness:

- same part of speech +100, same broad family (adjective / verb / noun /
  adverb / function word) +40
- inside your current filters +25
- Japanese-side options: same last character +30 (る with る, い with い) and
  same script style, kanji vs kana-only, +20
- minus a small penalty for label-length difference
- **only words you've seen** are ever used as wrong options: marked learned
  in the sheet, mastered in New vocab, or shown to you in flash cards /
  multiple choice. An unfamiliar word as a distractor just confuses. (A
  last-resort fallback to unseen words exists only so a card never has fewer
  than four options; it can't trigger with a normal sheet.)
- never an option with the same label as the answer (homophones on kana
  questions), nor an English meaning that shares an accepted form with it

Part of speech comes from the sheet's `type` column, normalised (い-adjective
/ i-Adj, な-adjective / na-Adj, the many "Verb (G1-…)" spellings, etc.).
About 20 adverbs (あまり, いつも, とても…) are tagged "Verb" in the sheet; the
app treats a "Verb" whose meaning doesn't start with "To " as an adverb. The
sheet itself is untouched, but fixing those tags would make it cleaner.

Measured over every learned word and direction: same-part-of-speech
distractors went from roughly 26–40% to ~99%; an い-adjective being the only
い-ending option fell from 58% to 2.5%; a verb being the only one with its
ending, 87% to 3%; and the "only one starting with To" tell went from 8% to 0.

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
| `build.py` | Pulls the live sheet from the tutoring repo (needs `GITHUB_TOKEN`) and regenerates `index.html`; prints what changed. |
| `kanji_tools.py` | Lines each kanji run up with its reading and validates the kanji tables against the sheet; used by `build.py`. |
| `kanji_info.txt` | Meaning, kun and on readings for every kanji in the list (the "Kanji ↔ reading" questions). |
| `lookalikes.txt` | Visually similar kanji used for made-up options in kana → kanji questions. |
| `legacy_ids.json` | Old row-number order of the sheet, for the one-time conversion of saved progress to stable word keys. Keep it. |
| `vocab_data.json` | Plain JSON export of the vocab list at last build time. |
| `japanese_n5_vocabulary_updated.xlsx` | Snapshot of the vocab spreadsheet used for this build. |

## Notes / limitations

- Per-word stats (including New Vocab mastery) are keyed by stable word key
  (`kanji|reading`), so re-sorting or adding rows is safe; editing a word's
  kanji or reading in the sheet resets that word's saved progress.
- The 🔊 speaker button uses the device's built-in text-to-speech; works
  offline on iOS once a Japanese voice has been used once.
- Typing kanji in text entry (Japanese entry mode, kana→kanji questions)
  needs a Japanese keyboard/IME. Flash cards and multiple choice don't
  need one.
- All progress is stored in that browser's local storage on that device
  only — nothing syncs anywhere, and clearing Safari's site data for this
  app will reset it.
