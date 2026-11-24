#!/usr/bin/env python3
"""THE DAILY WORLD — one-page newspaper for Monday 23 November 2026.

make.fun bounty news-image-20261123. Layout follows the house method set on
2026-11-22: masthead with pink rule, six-cell numbers strip, three hero
cards, a central Equal Earth map (Natural Earth 110m, embedded in
mapdata.py) with a region index and DATE CHECK beside it, then 18 small
cards in three rows of six, an ALSO strip and a sources footer.

All illustrations are flat-vector panels in panels/ (no text in them);
every word and number on the page is drawn here from the verified brief.
Deterministic: same inputs -> same bytes. No network.
"""
import base64
import math
import os
import zlib

from PIL import Image, ImageDraw, ImageFont

from mapdata import MAP_B64

HERE = os.path.dirname(os.path.abspath(__file__))
W = H = 1024
MARGIN = 10
GAP = 8
CW = W - 2 * MARGIN  # content width = 1004

CREAM = (247, 242, 228)
PAPER = (253, 251, 244)
INK = (22, 22, 22)
GREY = (90, 88, 80)
PINK = (232, 67, 147)
SEA = (191, 224, 234)
LAND = (143, 206, 126)
LAND_EDGE = (74, 124, 67)
WHITE = (255, 255, 255)

# region -> (bar colour, light tint used for chips)
REGIONS = {
    "AMERICAS": ((74, 127, 181), (215, 229, 242)),
    "EUROPE": ((91, 154, 94), (218, 236, 214)),
    "ASIA": ((224, 138, 60), (249, 227, 200)),
    "MIDDLE EAST": ((201, 162, 39), (243, 232, 191)),
    "GLOBAL": ((125, 115, 144), (224, 220, 232)),
    "AFRICA": ((198, 91, 63), (245, 213, 201)),
    "OCEANIA": ((61, 154, 148), (207, 234, 231)),
}

# (num, region, category, title, summary, lat, lon) — text from the brief,
# numbers exactly as verified. lat/lon None -> no map dot (story 8, global).
STORIES = [
    (1, "AMERICAS", "MARKETS", "WALL STREET SURGES",
     "S&P +4.73%, Nasdaq +6.51%, Dow +1,448 — best day since April 2025.",
     40.71, -74.01),
    (2, "AFRICA", "WAR", "UKRAINE SINKS RUSSIAN WARSHIP IN LIBYA",
     "Naval drones sink corvette Mercury in Benghazi; Kremlin vows "
     "'painful consequences'.", 32.12, 20.07),
    (3, "EUROPE", "WAR", "RUSSIAN STRIKES KILL 11 IN KYIV REGION",
     "Apartment block hit in Dymer; toll at least 11, later reported 15.",
     50.78, 30.30),
    (4, "AMERICAS", "TECH", "NVIDIA +31.4% AS HUANG RETURNS AS CEO",
     "Back 10 days after quitting; stock +31.4% to $165.05.",
     37.37, -121.96),
    (5, "ASIA", "MARKETS", "KOSPI SLIDES 3.31% AS AI ROUT SPREADS",
     "4,708.54 close; Samsung -3.1%, SK Hynix -2.5%.",
     37.57, 126.98),
    (6, "EUROPE", "MARKETS", "EUROPEAN STOCKS REBOUND NEARLY 2%",
     "STOXX +1.9%, best since May; ASML up nearly 10%.",
     50.11, 8.68),
    (7, "GLOBAL", "MARKETS", "OIL SLIDES, GOLD JUMPS",
     "Brent -2.8% to $89.99; gold +3.4% to $3,634.",
     40.71, -74.01),
    (8, "GLOBAL", "MARKETS", "BITCOIN HOLDS ABOVE $60,000",
     "Holds $61K after weekend's $55K plunge and rebound.",
     None, None),
    (9, "AMERICAS", "POLITICS", "DEMOCRATS REACH 258 HOUSE SEATS",
     "Most since 1992; Hubbard wins by ~330 votes.",
     38.90, -77.04),
    (10, "AMERICAS", "POLITICS", "TRUMP WARNS IRAN STRIKES MAY RESUME",
     "May resume Iran strikes after New Year if no deal.",
     38.90, -77.04),
    (11, "EUROPE", "CLIMATE", "COP31 COLLAPSES WITHOUT A DEAL",
     "No deal, first since 2009; silent on fossil fuels.", 36.88, 30.70),
    (12, "MIDDLE EAST", "WAR", "HOUTHIS CLAIM SAUDI REFINERY STRIKE",
     "Claims Rabigh refinery, radar hits; unconfirmed.", 22.80, 39.03),
    (13, "MIDDLE EAST", "WAR", "HORMUZ TANKER ATTACKS SURGE",
     "Attacks surge; Iran threatens action vs US blockade.", 26.57, 56.27),
    (14, "EUROPE", "WAR", "ZAPORIZHZHIA STRIKE KILLS 3",
     "Afternoon strike: 3 killed, 1 wounded, officials say.", 47.84, 35.17),
    (15, "ASIA", "HUMANITARIAN", "AFGHANISTAN DROUGHT DEEPENS CRISIS",
     "Millions without safe water, PBS reports from Bamyan.", 34.82, 67.83),
    (16, "ASIA", "BUSINESS", "BROOKFIELD BUYS PGP GLASS FOR $1.7BN",
     "To buy India's PGP Glass from Blackstone for $1.7bn.",
     19.08, 72.88),
    (17, "AMERICAS", "WEATHER", "STORMS THREATEN THANKSGIVING TRAVEL",
     "Storms both coasts; holiday flood warnings.", 37.77, -122.42),
    (18, "OCEANIA", "DISASTER", "M6.5 DEEP QUAKE NEAR VANUATU",
     "M6.5 at 598 km depth near Vanuatu, 02:40 UTC.", -13.58, 172.27),
    (19, "AMERICAS", "SCIENCE", "KILAUEA EPISODE 57 FOUNTAINS, PAUSES",
     "Episode 57 fountains Monday, then pauses.", 19.42, -155.29),
    (20, "EUROPE", "SPORTS", "BRENTFORD ROUT EVERTON 4-0",
     "Lewis-Potter brace in 3 mins; Brentford up to sixth.", 51.49, -0.30),
    (21, "EUROPE", "SPORTS", "MONZA BEAT FIORENTINA 3-0",
     "Varela twice — 11 in 11 — Monza exit drop zone.", 45.58, 9.27),
]

NUMBERS = [
    ("+4.73%", "S&P 500"),
    ("+6.51%", "NASDAQ"),
    ("+31.4%", "NVIDIA"),
    ("-3.31%", "KOSPI"),
    ("258", "HOUSE SEATS"),
    ("M6.5", "VANUATU QUAKE"),
]

SUBTITLE = ("Wall Street surges as Nvidia brings back Huang • Ukraine "
            "sinks Russian warship in Libya • COP31 collapses in Antalya")

DATE_CHECK = (
    "Happened Sun 22 Nov, first reported or confirmed Mon 23 Nov: the "
    "Libya warship strike (2), the Kyiv-region strikes (3), the COP31 "
    "collapse (11), the Democrats' 258th seat (9) and the Houthi "
    "refinery claim (12 — a claim only, unconfirmed). Weekend results "
    "carried as briefs only: F1 Las Vegas (22, Sat night) and the ATP "
    "final (23, Sun). Everything else happened on Mon 23 Nov.")

ALSO_LINE = ("ALSO — 22 F1: VERSTAPPEN WINS LAS VEGAS GP (SAT NIGHT "
             "LOCAL — WEEKEND RESULT) · 23 ATP FINALS: ALCARAZ BEATS "
             "ZVEREV 6-2, 7-6(7) IN TURIN (SUN — WEEKEND RESULT)")

SOURCES = ("Sources: Reuters · AP · AFP · CNBC · BBC · Al Jazeera · "
           "Gulf News · USGS. All stories from Monday 23 November 2026 "
           "unless noted in the DATE CHECK.")

_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        _fonts[key] = ImageFont.truetype(os.path.join(HERE, "fonts", name),
                                         size)
    return _fonts[key]


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrap_balanced(draw, text, fnt, max_w):
    """Two-line wrap that balances the two lines' widths.

    Picks the word split minimising the wider line, so neither line
    hugs one edge while the other sits nearly empty. Falls back to the
    greedy wrap when no two-line split fits.
    """
    words = text.split()
    if len(words) <= 1:
        return [text] if text else []
    greedy = wrap(draw, text, fnt, max_w)
    if len(greedy) <= 1:
        return greedy
    best = None
    for i in range(1, len(words)):
        a = " ".join(words[:i])
        b = " ".join(words[i:])
        wa = draw.textlength(a, font=fnt)
        wb = draw.textlength(b, font=fnt)
        if wa <= max_w and wb <= max_w:
            score = max(wa, wb)
            if best is None or score < best[0]:
                best = (score, [a, b])
    return best[1] if best else greedy


def ellipsize(draw, line, fnt, max_w):
    while line and draw.textlength(line + "…", font=fnt) > max_w:
        line = line[:-1]
    return line + "…"


def text_block(draw, xy, text, fnt, max_w, max_lines, lh, fill):
    """Wrap text into at most max_lines lines; ellipsis on overflow."""
    if max_lines == 2:
        lines = wrap_balanced(draw, text, fnt, max_w)
    else:
        lines = wrap(draw, text, fnt, max_w)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = ellipsize(draw, lines[-1], fnt, max_w)
    x, y = xy
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def paste_cover(canvas, path, box):
    """Paste image into box (x0,y0,x1,y1), centre-cropped to cover."""
    x0, y0, x1, y1 = box
    tw, th = x1 - x0, y1 - y0
    im = Image.open(path).convert("RGB")
    scale = max(tw / im.width, th / im.height)
    nw, nh = max(tw, round(im.width * scale)), max(th, round(im.height * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    ox, oy = (nw - tw) // 2, (nh - th) // 2
    canvas.paste(im.crop((ox, oy, ox + tw, oy + th)), (x0, y0))


def number_dot(draw, cx, cy, num):
    r = 7
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PINK,
                 outline=WHITE, width=2)
    fnt = font(9, bold=True)
    s = str(num)
    w = draw.textlength(s, font=fnt)
    draw.text((cx - w / 2, cy - 5.5), s, font=fnt, fill=WHITE)


def draw_card(canvas, draw, story, x, y, w, h, hero):
    num, region, cat, title, summary, _lat, _lon = story
    bar_c, _tint = REGIONS[region]
    draw.rectangle([x, y, x + w, y + h], fill=PAPER, outline=INK, width=2)
    bar_h = 15 if hero else 11
    draw.rectangle([x + 2, y + 2, x + w - 2, y + 2 + bar_h], fill=bar_c)
    bf = font(9 if hero else 8, bold=True)
    draw.text((x + 6, y + 2 + (1 if hero else 0)), "%s · %s" % (region, cat),
              font=bf, fill=WHITE)
    ill_y = y + 2 + bar_h
    ill_h = 102 if hero else 60
    panel = os.path.join(HERE, "panels", "p%02d.webp" % num)
    paste_cover(canvas, panel, (x + 2, ill_y, x + w - 2, ill_y + ill_h))
    number_dot(draw, x + w - 2 - 6 - 7, ill_y + 6 + 7, num)
    tx = x + 7
    tw = w - 14
    ty = ill_y + ill_h + 3
    tf = font(14 if hero else 10, bold=True)
    title_lh = 17 if hero else 12
    text_block(draw, (tx, ty), title, tf, tw, 2, title_lh, INK)
    # the title block always reserves two lines, so summaries in the
    # same row start at the same y whether the title took 1 or 2 lines
    sy = ty + 2 * title_lh + 1
    sf = font(11 if hero else 10)
    text_block(draw, (tx, sy), summary, sf, tw, 2, 14 if hero else 12,
               (40, 40, 40))


# ---- Equal Earth map -------------------------------------------------

_A1, _A2, _A3, _A4 = 1.340264, -0.081106, 0.000893, 0.003796


def equal_earth(lon_deg, lat_deg):
    lam = math.radians(lon_deg)
    phi = math.radians(lat_deg)
    theta = math.asin(min(1.0, max(-1.0, (math.sqrt(3) / 2) * math.sin(phi))))
    t2 = theta * theta
    t6 = t2 * t2 * t2
    denom = 3 * (9 * _A4 * t6 * t2 + 7 * _A3 * t6 + 3 * _A2 * t2 + _A1)
    x = (2 * math.sqrt(3) * lam * math.cos(theta)) / denom
    y = theta * (_A1 + _A2 * t2 + t6 * (_A3 + _A4 * t2))
    return x, y


def load_rings():
    raw = zlib.decompress(base64.b64decode(MAP_B64)).decode()
    vals = [int(v) for v in raw.split(",")]
    rings, i = [], 0
    while i < len(vals):
        n = vals[i]
        i += 1
        ring, x, y = [], 0, 0
        for _ in range(n):
            x += vals[i]
            y += vals[i + 1]
            i += 2
            ring.append((x / 3.0, y / 3.0))
        rings.append(ring)
    return rings


def draw_map(canvas, draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=PAPER, outline=INK, width=2)
    draw.rectangle([x0 + 2, y0 + 2, x1 - 2, y0 + 18], fill=INK)
    draw.text((x0 + 8, y0 + 4), "THE DAY ON THE MAP", font=font(10, bold=True),
              fill=WHITE)
    mx0, my0, mx1, my1 = x0 + 6, y0 + 22, x1 - 6, y1 - 6
    draw.rectangle([mx0, my0, mx1, my1], fill=SEA)
    # fit: x spans lon -180..180 at the equator; y spans lat -50..75
    ex, _ = equal_earth(180, 0)
    _, ytop = equal_earth(0, 75)
    _, ybot = equal_earth(0, -50)
    scale = min((mx1 - mx0) / (2 * ex), (my1 - my0) / (ytop - ybot))
    cx = (mx0 + mx1) / 2
    cy = my0 + (my1 - my0) / 2 + (ytop + ybot) / 2 * scale

    def proj(lon, lat):
        px, py = equal_earth(lon, lat)
        return cx + px * scale, cy - py * scale

    for ring in load_rings():
        pts = [proj(lon, lat) for lon, lat in ring]
        draw.polygon(pts, fill=LAND, outline=LAND_EDGE)
    # story dots; close neighbours get small nudges so the r=7 dots
    # never overlap: 1 & 7 share New York, 9 & 10 share Washington,
    # and 2/3/6/11/14/20/21 crowd into Europe and the Mediterranean
    nudges = {7: (16, -6), 10: (16, 6), 2: (-10, 6), 3: (-7, -10),
              6: (11, -7), 11: (5, 11), 14: (11, 7), 20: (-12, -5),
              21: (10, 9)}
    for story in STORIES:
        num, _r, _c, _t, _s, lat, lon = story
        if lat is None:
            continue
        dx, dy = nudges.get(num, (0, 0))
        px, py = proj(lon, lat)
        number_dot(draw, px + dx, py + dy, num)
    draw.rectangle([mx0, my0, mx1, my1], outline=INK, width=1)


def draw_side_column(draw, x, y, w):
    # region index
    draw.rectangle([x, y, x + w, y + 124], fill=PAPER, outline=INK, width=2)
    draw.text((x + 8, y + 5), "IN THIS ISSUE — BY REGION",
              font=font(11, bold=True), fill=INK)
    draw.line([x + 8, y + 22, x + w - 8, y + 22], fill=PINK, width=2)
    by_region = {}
    for story in STORIES:
        by_region.setdefault(story[1], []).append(story[0])
    ry = y + 28
    for region in ("AMERICAS", "EUROPE", "ASIA", "MIDDLE EAST", "AFRICA",
                   "OCEANIA", "GLOBAL"):
        bar_c, _t = REGIONS[region]
        draw.rectangle([x + 8, ry + 2, x + 20, ry + 12], fill=bar_c,
                       outline=INK, width=1)
        draw.text((x + 26, ry), region, font=font(10, bold=True), fill=INK)
        nums = " ".join(str(n) for n in by_region[region])
        draw.text((x + 128, ry), nums, font=font(10), fill=(40, 40, 40))
        if region == "GLOBAL":
            draw.text((x + 168, ry), "(8 has no dot)", font=font(9),
                      fill=GREY)
        ry += 14
    # date check
    dy = y + 132
    draw.rectangle([x, dy, x + w, dy + 108], fill=(255, 248, 235),
                   outline=PINK, width=2)
    draw.text((x + 10, dy + 5), "DATE CHECK", font=font(11, bold=True),
              fill=PINK)
    text_block(draw, (x + 10, dy + 23), DATE_CHECK, font(9), w - 20, 7, 12,
               (40, 40, 40))


def build():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # masthead
    draw.text((MARGIN, MARGIN), "THE DAILY WORLD", font=font(30, bold=True),
              fill=INK)
    date_s = "MONDAY 23 NOVEMBER 2026"
    df = font(15, bold=True)
    dw = draw.textlength(date_s, font=df)
    draw.text((W - MARGIN - dw, MARGIN + 2), date_s, font=df, fill=INK)
    tag = "ONE PAGE · EVERY STORY THAT MATTERED"
    tf = font(9)
    tw = draw.textlength(tag, font=tf)
    draw.text((W - MARGIN - tw, MARGIN + 24), tag, font=tf, fill=GREY)
    draw.text((MARGIN, MARGIN + 36), SUBTITLE, font=font(10), fill=(40, 40, 40))
    draw.rectangle([MARGIN, MARGIN + 52, W - MARGIN, MARGIN + 56], fill=PINK)

    # numbers strip
    ny = MARGIN + 64
    draw.rectangle([MARGIN, ny, W - MARGIN, ny + 44], fill=PAPER,
                   outline=INK, width=1)
    cell = CW / 6
    for i, (big, label) in enumerate(NUMBERS):
        cx0 = MARGIN + i * cell
        if i:
            draw.line([cx0, ny + 6, cx0, ny + 38], fill=(180, 175, 160),
                      width=1)
        bf = font(18, bold=True)
        bw = draw.textlength(big, font=bf)
        draw.text((cx0 + (cell - bw) / 2, ny + 4), big, font=bf, fill=PINK)
        lf = font(8, bold=True)
        lw = draw.textlength(label, font=lf)
        draw.text((cx0 + (cell - lw) / 2, ny + 29), label, font=lf, fill=INK)

    # heroes
    hy = ny + 52
    hero_w = (CW - 2 * GAP) // 3
    for i, story in enumerate(STORIES[:3]):
        draw_card(img, draw, story, MARGIN + i * (hero_w + GAP), hy,
                  hero_w, 192, hero=True)

    # map band
    my = hy + 200
    draw_map(img, draw, (MARGIN, my, MARGIN + 602, my + 240))
    draw_side_column(draw, MARGIN + 610, my, CW - 610)

    # small panels: 18 cards, three rows of six
    py = my + 248
    pw = (CW - 5 * GAP) // 6
    for idx, story in enumerate(STORIES[3:]):
        r, c = divmod(idx, 6)
        draw_card(img, draw, story, MARGIN + c * (pw + GAP),
                  py + r * (128 + GAP), pw, 128, hero=False)

    # ALSO + sources footer
    fy = py + 3 * 128 + 2 * GAP + 8
    draw.line([MARGIN, fy - 4, W - MARGIN, fy - 4], fill=INK, width=1)
    af = font(9, bold=True)
    line = ALSO_LINE
    while draw.textlength(line, font=af) > CW:
        line = line[:-1]
    draw.text((MARGIN, fy), line, font=af, fill=INK)
    draw.text((MARGIN, fy + 13), SOURCES, font=font(8), fill=GREY)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = build()
    path = os.path.join(out_dir, "entry.png")
    img.save(path, format="PNG", optimize=True)
    if os.path.getsize(path) > 1048576:
        img.convert("P", palette=Image.ADAPTIVE, colors=256).save(
            path, format="PNG", optimize=True)
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
