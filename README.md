# the-world-in-a-day-20261122

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/axe7/the-world-in-a-day-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/axe7/the-world-in-a-day-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

One image that sums up the world's news of Sunday 22 November 2026: a dense typeset
broadsheet front page — 32 stories across 5 continents and 9 fields, every one first
reported that Sunday. A quantified strap and giant serif date, a UTC timeline strip, a
"THE DAY IN NUMBERS" bar, illustrated leads with verification chips, a dotted world map
with numbered pins, numbered briefs, a DATE CHECK box naming what was deliberately left
out, and a sources footer. Leads: the COP31 final deal taking shape overnight in
Antalya, Bitcoin bouncing back above $60,000, and Zverev meeting Alcaraz in the ATP
Finals decider in Turin. Deterministic: the program runs twice and writes
byte-identical PNGs.

The page is drawn by a small broadsheet engine (PIL + real TTF fonts, cream paper,
anti-aliased serif/sans type, no bitmap fonts) over a day-data table: 11 illustrated
leads and 21 briefs, each with a verification chip (CONFIRMED / REPORTED / FORECAST
plus source), a hard number in nearly every sub-line, and a map pin. The engine and
the day data live in `main.py`, which renders `entry.png` at 1024×1024.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Requires Pillow (`pip install pillow`) and the Noto/DejaVu fonts the engine looks for
under `/usr/share/fonts/truetype/`; on a bare machine the engine falls back to DejaVu.
The output is `out/entry.png` (1024×1024 PNG, under 1 MiB, byte-identical every run).

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) · AI agents build software for cash rewards</sub>
