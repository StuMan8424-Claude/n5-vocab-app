"""Kanji helpers shared by build.py: split each written word into kanji / kana runs,
line each kanji run up with its reading, and validate the hand-written tables
(kanji_info.txt, lookalikes.txt) against the vocabulary sheet."""
import json, re

KJ = r"\u3400-\u9fff々"
KN = r"\u3041-\u309f\u30a0-\u30ff"
VOICE = dict(zip("かきくけこさしすせそたちつてとはひふへほ", "がぎぐげござじずぜぞだぢづでどばびぶべぼ"))
SEMI = dict(zip("はひふへほ", "ぱぴぷぺぽ"))
SMALL = "ゃゅょ"


def kata2hira(s):
    return "".join(chr(ord(c) - 0x60) if "\u30a1" <= c <= "\u30f6" else c for c in s)


def variants(r):
    """A reading as written, plus its usual sound-change forms (rendaku, p-forms, gemination)."""
    out = {r}
    if r:
        f = r[0]
        if f in VOICE:
            out.add(VOICE[f] + r[1:])
        if f in SEMI:
            out.add(SEMI[f] + r[1:])
        if f == "ち" and len(r) > 1 and r[1] in SMALL:
            out.add("じ" + r[1:])
        for v in list(out):
            if v and v[-1] in "くきつちふ" and len(v) > 1:
                out.add(v[:-1] + "っ")
    return out


def stem(kun):
    return kun.split("(")[0]


def parse_table(path):
    table = {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#"):
            continue
        k, m, kun, on = ln.split("|")
        assert len(k) == 1 and k not in table, f"bad or duplicate kanji line: {ln!r}"
        table[k] = {"m": m, "kun": [x for x in kun.split(",") if x], "on": [x for x in on.split(",") if x]}
    return table


def parse_lookalikes(path):
    out = {}
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except FileNotFoundError:
        return out
    for ln in lines:
        if not ln or ln.startswith("#"):
            continue
        k, alts = ln.split("|")
        out[k] = [a for a in alts.split(",") if a and a != k]
    return out


def valid_set(entry):
    s = set()
    for k in entry["kun"]:
        s |= variants(stem(k))
    for o in entry["on"]:
        s |= variants(o)
    return s


def runs(k):
    return [
        ("K", m.group(1)) if m.group(1) else ("k", m.group(2)) if m.group(2) else ("o", m.group(3))
        for m in re.finditer(rf"([{KJ}]+)|([{KN}ー]+)|([^{KJ}{KN}ー]+)", k)
    ]


def align(k, reading):
    """[(kanji run, its reading), ...] by pinning the kana runs of the written form inside the reading."""
    reading = kata2hira(reading.replace("〜", ""))
    R = [(t, kata2hira(s) if t == "k" else s) for t, s in runs(k.replace("〜", ""))]
    pos, res, pending = 0, [], None
    for idx, (t, s) in enumerate(R):
        if t == "o":
            continue
        if t == "K":
            pending = (s, pos)
            continue
        last = all(x[0] == "o" for x in R[idx + 1:])
        if last:
            if not reading.endswith(s):
                return None
            j = len(reading) - len(s)
        else:
            j = reading.find(s, pos + (1 if pending else 0))
            if j < 0:
                return None
        if pending:
            seg = reading[pending[1]:j]
            if not seg:
                return None
            res.append((pending[0], seg))
            pending = None
        pos = j + len(s)
    if pending:
        seg = reading[pending[1]:]
        if not seg:
            return None
        res.append((pending[0], seg))
    return res


def decomposes(chars, reading, V):
    chars = [c for c in chars if c != "々"]
    memo = {}

    def go(i, j):
        if i == len(chars):
            return j == len(reading)
        if (i, j) in memo:
            return memo[(i, j)]
        ok = any(v and reading.startswith(v, j) and go(i + 1, j + len(v)) for v in V.get(chars[i], ()))
        memo[(i, j)] = ok
        return ok

    return go(0, 0)


def annotate_runs(words, table):
    """Give each word with kanji `rn`: its tokens, kanji runs carrying their reading(s).
    Returns a report dict. Words whose reading can't be lined up simply get no `rn`."""
    V = {k: valid_set(e) for k, e in table.items()}
    report = {"failed": [], "irregular": [], "single_not_in_table": [], "missing_kanji": set(), "single_ground_truth": {}}
    for w in words:
        w.pop("rn", None)
        if not (w["k"] and w["k"] != w["h"] and re.search(rf"[{KJ}]", w["k"])):
            continue
        per_variant = []
        for v in w["h"].split("/"):
            a = align(w["k"], v)
            if a is None:
                per_variant = None
                break
            per_variant.append(a)
        if not per_variant:
            report["failed"].append(w["k"])
            continue
        kanji_runs = [s for t, s in runs(w["k"]) if t == "K"]
        if any(len(a) != len(kanji_runs) for a in per_variant):
            report["failed"].append(w["k"])
            continue
        toks, ki = [], 0
        for t, s in runs(w["k"]):
            if t == "K":
                rs = []
                for a in per_variant:
                    if a[ki][1] not in rs:
                        rs.append(a[ki][1])
                tok = {"t": "k", "s": s, "r": rs}
                if len(s) > 1 and "々" not in s and not any(decomposes(list(s), r, V) for r in rs):
                    tok["i"] = 1   # irregular: can't be built from per-kanji readings (今日 きょう, 大人 おとな…)
                    report["irregular"].append(s)
                if len(s) == 1:
                    for r in rs:
                        report["single_ground_truth"].setdefault(s, set()).add(r)
                        if r not in V.get(s, ()):
                            report["single_not_in_table"].append((w["k"], s, r))
                for c in s:
                    if c != "々" and c not in table:
                        report["missing_kanji"].add(c)
                toks.append(tok)
                ki += 1
            else:
                toks.append({"t": "f", "s": s})
        w["rn"] = toks
    report["irregular"] = sorted(set(report["irregular"]))
    return report


def embed_table(words, table):
    """Only the kanji that occur in the list, with meaning, display readings and the full valid-reading set."""
    used = {c for w in words for c in w["k"] if re.match(rf"[{KJ}]", c)}
    gt = {}
    for w in words:
        for t in w.get("rn", []):
            if t["t"] == "k" and len(t["s"]) == 1:
                gt.setdefault(t["s"], set()).update(t["r"])
    out = {}
    for c in sorted(used):
        e = table.get(c)
        if not e:
            continue
        v = valid_set(e) | gt.get(c, set())
        out[c] = {"m": e["m"], "k": e["kun"], "o": e["on"], "v": sorted(v)}
    return out
