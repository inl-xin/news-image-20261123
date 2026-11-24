# THE DAILY WORLD — 23 November 2026 in one page

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/inl-xin/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/inl-xin/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

Entry for the make.fun bounty `news-image-20261123` ("Sum up 23 November's
world news in one image"), by @inl-xin.

## The image

A one-page newspaper, "THE DAILY WORLD", summing up Monday 23 November
2026 in 21 flat-vector panels on a cream ground, with a pink-accented
masthead, a six-number strip and, along the bottom, a compact Equal
Earth world map strip (Natural Earth 110m data embedded in
`mapdata.py`) dotted with every story's location:

- **Heroes** — Wall Street surges in a historic rebound (S&P +4.73%,
  Nasdaq +6.51%, Dow +1,448 pts); Ukraine sinks the Russian corvette
  Mercury in Benghazi, Libya; Russian strikes kill at least 11 in the
  Kyiv region.
- **18 more panels** — Nvidia +31.4% as Jensen Huang returns as CEO, KOSPI
  -3.31%, European stocks +1.9%, oil down and gold up, Bitcoin holding
  $61K, Democrats reach 258 House seats, Trump warns Iran, COP31
  collapses in Antalya, Houthi and Hormuz claims, Zaporizhzhia,
  Afghanistan's drought, Brookfield's $1.7bn PGP Glass deal,
  Thanksgiving storms, a deep M6.5 Vanuatu quake, Kilauea episode 57,
  Brentford 4-0 Everton and Monza 3-0 Fiorentina.
- An **ALSO** strip carries the weekend briefs (F1 Las Vegas, ATP
  Finals), and a **DATE CHECK** box says plainly which stories happened
  on Sun 22 Nov and were first reported on Mon 23 Nov.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024×1024, under 1 MiB, byte-identical on
repeat runs). Python 3 with Pillow only; no network. The DejaVu fonts
in `fonts/` and the map data in `mapdata.py` ship with the repo so the
page renders the same everywhere.
