#!/usr/bin/env python3
"""THE DAILY WORLD — one-page newspaper for Monday 23 November 2026.

make.fun bounty news-image-20261123. Layout follows the house method set on
2026-11-22: masthead with pink rule, six-cell numbers strip, three hero
cards, then 18 small cards in rows of 5 / 5 / 5 / 3 (the last row stretched
to fill), and along the bottom a compact Equal Earth map strip (Natural
Earth 110m, embedded in mapdata.py, cropped tight to the day's stories)
with the region index and DATE CHECK beside it, an ALSO strip and a
sources footer. Type is set large throughout so headlines and card
titles stay legible when the page is scaled down.

Map markers sit at each story's exact projected lat/long as a small dot;
where the numbered circles would crowd, the circle is offset nearby and
tied to its dot with a thin leader line.

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


def wrap_balanced_n(draw, text, fnt, max_w, max_lines):
    """Balanced wrap into at most max_lines lines.

    Uses the greedy line count (capped at max_lines), then chooses the
    word splits that minimise the widest line, so no line is left with
    an orphan word while another sprawls. Falls back to the greedy
    wrap when no split fits.
    """
    words = text.split()
    if len(words) <= 1:
        return [text] if text else []
    greedy = wrap(draw, text, fnt, max_w)
    k = min(len(greedy), max_lines)
    if k <= 1:
        return greedy[:1]
    n = len(words)
    width = [draw.textlength(" ".join(words[i:j]), font=fnt)
             for i in range(n) for j in range(i + 1, n + 1)]

    def w(i, j):
        return width[i * n - i * (i - 1) // 2 + (j - i - 1)]

    # dp[j][m] = (widest line, split tuple) covering words[:j] in m lines
    INF = float("inf")
    dp = [[(INF, None)] * (k + 1) for _ in range(n + 1)]
    dp[0][0] = (0.0, ())
    for m in range(1, k + 1):
        for j in range(1, n + 1):
            for i in range(j):
                prev, split = dp[i][m - 1]
                if split is None or w(i, j) > max_w:
                    continue
                cand = max(prev, w(i, j))
                if cand < dp[j][m][0]:
                    dp[j][m] = (cand, split + (i,))
    best, split = dp[n][k]
    if split is None:
        return greedy
    bounds = list(split) + [n]
    return [" ".join(words[bounds[t]:bounds[t + 1]]) for t in range(k)]


def ellipsize(draw, line, fnt, max_w):
    while line and draw.textlength(line + "…", font=fnt) > max_w:
        line = line[:-1]
    return line + "…"


def text_block(draw, xy, text, fnt, max_w, max_lines, lh, fill):
    """Wrap text into at most max_lines lines; ellipsis on overflow."""
    if max_lines >= 2:
        lines = wrap_balanced_n(draw, text, fnt, max_w, max_lines)
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


def paste_cover(canvas, path, box, fx=0.5, fy=0.5):
    """Paste image into box (x0,y0,x1,y1), cover-cropped around the
    focus point (fx, fy as fractions of the source, clamped so the
    crop window never leaves the image)."""
    x0, y0, x1, y1 = box
    tw, th = x1 - x0, y1 - y0
    im = Image.open(path).convert("RGB")
    scale = max(tw / im.width, th / im.height)
    nw, nh = max(tw, round(im.width * scale)), max(th, round(im.height * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    ox = min(max(round(fx * nw - tw / 2), 0), nw - tw)
    oy = min(max(round(fy * nh - th / 2), 0), nh - th)
    canvas.paste(im.crop((ox, oy, ox + tw, oy + th)), (x0, y0))


def number_dot(draw, cx, cy, num):
    r = 7
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PINK,
                 outline=WHITE, width=2)
    fnt = font(9, bold=True)
    s = str(num)
    w = draw.textlength(s, font=fnt)
    draw.text((cx - w / 2, cy - 5.5), s, font=fnt, fill=WHITE)


# Crop focus per panel (fractions of the source image). Most panels
# are centre-composed; a few keep their subject off-centre (4's chip
# is high right, 6's euro sign low left, 14's clinic right, ...).
FOCUS = {
    1: (0.5, 0.48), 2: (0.5, 0.5), 3: (0.5, 0.45), 4: (0.66, 0.5),
    5: (0.5, 0.5), 6: (0.45, 0.5), 7: (0.45, 0.5), 8: (0.5, 0.5),
    9: (0.5, 0.5), 10: (0.55, 0.5), 11: (0.5, 0.5), 12: (0.45, 0.5),
    13: (0.5, 0.5), 14: (0.55, 0.5), 15: (0.45, 0.5), 16: (0.5, 0.5),
    17: (0.5, 0.5), 18: (0.5, 0.5), 19: (0.5, 0.5), 20: (0.5, 0.5),
    21: (0.5, 0.5),
}


def draw_card_hero(canvas, draw, story, x, y, w, h):
    """Hero card: region bar, wide illustration, title, summary."""
    num, region, cat, title, summary, _lat, _lon = story
    bar_c, _tint = REGIONS[region]
    draw.rectangle([x, y, x + w, y + h], fill=PAPER, outline=INK, width=2)
    draw.rectangle([x + 2, y + 2, x + w - 2, y + 17], fill=bar_c)
    draw.text((x + 6, y + 3), "%s · %s" % (region, cat),
              font=font(10, bold=True), fill=WHITE)
    fx, fy = FOCUS[num]
    panel = os.path.join(HERE, "panels", "p%02d.webp" % num)
    paste_cover(canvas, panel, (x + 2, y + 19, x + w - 2, y + 104), fx, fy)
    number_dot(draw, x + w - 2 - 6 - 7, y + 19 + 6 + 7, num)
    tx, tw = x + 7, w - 14
    tf = font(15, bold=True)
    text_block(draw, (tx, y + 108), title, tf, tw, 2, 18, INK)
    # title block always reserves two lines so summaries align
    text_block(draw, (tx, y + 108 + 2 * 18 + 1), summary, font(12), tw, 2,
               15, (40, 40, 40))


def draw_card_small(canvas, draw, story, x, y, w, h, wide=False):
    """Small card: region bar, square thumbnail with the title beside
    it, then the summary full-width below the thumbnail."""
    num, region, cat, title, summary, _lat, _lon = story
    bar_c, _tint = REGIONS[region]
    draw.rectangle([x, y, x + w, y + h], fill=PAPER, outline=INK, width=2)
    draw.rectangle([x + 2, y + 2, x + w - 2, y + 15], fill=bar_c)
    draw.text((x + 6, y + 3), "%s · %s" % (region, cat),
              font=font(9, bold=True), fill=WHITE)
    thumb = 70 if wide else 60
    fx, fy = FOCUS[num]
    panel = os.path.join(HERE, "panels", "p%02d.webp" % num)
    paste_cover(canvas, panel, (x + 2, y + 17, x + 2 + thumb,
                                y + 17 + thumb), fx, fy)
    number_dot(draw, x + 2 + thumb - 6 - 7, y + 17 + 6 + 7, num)
    tx = x + 8 + thumb
    text_block(draw, (tx, y + 19), title, font(12, bold=True),
               x + w - 5 - tx, 4 if not wide else 3, 13, INK)
    text_block(draw, (x + 7, y + 17 + thumb + 5), summary, font(11),
               w - 14, 2, 13, (40, 40, 40))


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


# The strip is cropped tight around the day's stories: longitude
# -160..180 (the far Pacific margins go) and latitude -15..54 (the
# empty southern ocean and the far north go), so land fills the frame.
MAP_LON0, MAP_LON1 = -160.0, 180.0
MAP_LAT0, MAP_LAT1 = -15.0, 54.0

# Preferred label offsets (dx, dy) from a story's exact point, used as
# the solver's starting fan in the crowded clusters: 1 & 7 share New
# York, 9 & 10 share Washington, 4 & 17 share the Bay Area, and
# 2/3/6/11/14/20/21 crowd into Europe and the Mediterranean. Isolated
# stories start (and stay) on their point.
LABEL_SEED = {
    1: (-17, -13), 7: (16, -14), 9: (-18, 11), 10: (16, 13),
    4: (-15, -11), 17: (14, 12),
    20: (-16, 4), 6: (7, 16), 21: (-17, 15), 3: (-12, 4),
    14: (13, 12), 11: (19, 13), 2: (-15, 12), 12: (15, 9),
    13: (16, 2), 15: (11, -11), 18: (-7, -16),
}


def map_projection(sw, sh):
    """Equal Earth fit of the crop window into an sw x sh layer.

    Returns proj(lon, lat) -> (px, py) in layer coordinates. The
    equator is the widest parallel, so the x span is measured there.
    """
    x_lo = equal_earth(MAP_LON0, 0)[0]
    x_hi = equal_earth(MAP_LON1, 0)[0]
    y_hi = equal_earth(0, MAP_LAT1)[1]
    y_lo = equal_earth(0, MAP_LAT0)[1]
    scale = min(sw / (x_hi - x_lo), sh / (y_hi - y_lo))
    x_mid = (x_lo + x_hi) / 2
    y_mid = (y_hi + y_lo) / 2

    def proj(lon, lat):
        px, py = equal_earth(lon, lat)
        return (sw / 2 + (px - x_mid) * scale,
                sh / 2 - (py - y_mid) * scale)

    return proj


def solve_labels(anchors, sw, sh):
    """Place the numbered circles so none overlaps another circle or
    covers another story's dot, keeping each as close to its own exact
    point as the crowding allows. Deterministic relaxation from the
    seeded fan: label-label repulsion (min centre distance 16.5),
    label-dot repulsion (min 11), a weak spring to the anchor, and a
    clamp that keeps every circle inside the sea rect."""
    labels = {}
    for num, (ax, ay) in anchors.items():
        dx, dy = LABEL_SEED.get(num, (0, 0))
        labels[num] = (ax + dx, ay + dy)
    inset = 8.5
    for _ in range(600):
        moved = False
        for a in sorted(labels):
            ax, ay = anchors[a]
            lx, ly = labels[a]
            fx = (ax - lx) * 0.02
            fy = (ay - ly) * 0.02
            for b, (ox, oy) in labels.items():
                if b == a:
                    continue
                dx, dy = lx - ox, ly - oy
                dist = math.hypot(dx, dy)
                if dist < 16.5:
                    if dist < 0.01:
                        dx, dy, dist = 1.0, 0.0, 1.0
                    push = (16.5 - dist) / 2 + 0.1
                    fx += dx / dist * push
                    fy += dy / dist * push
            for b, (ox, oy) in anchors.items():
                if b == a or (ox, oy) == (ax, ay):
                    continue
                dx, dy = lx - ox, ly - oy
                dist = math.hypot(dx, dy)
                if dist < 11.0:
                    if dist < 0.01:
                        dx, dy, dist = 0.0, -1.0, 1.0
                    fx += dx / dist * (11.0 - dist + 0.1)
                    fy += dy / dist * (11.0 - dist + 0.1)
            nx = min(max(lx + fx, inset), sw - inset)
            ny = min(max(ly + fy, inset), sh - inset)
            if abs(nx - lx) > 0.005 or abs(ny - ly) > 0.005:
                moved = True
            labels[a] = (nx, ny)
        if not moved:
            break
    return labels


def render_map_layer(sw, sh):
    """The sea, land and markers of the map strip, drawn on their own
    layer so the cropped projection is clipped at the sea rect."""
    layer = Image.new("RGB", (sw, sh), SEA)
    d = ImageDraw.Draw(layer)
    proj = map_projection(sw, sh)
    for ring in load_rings():
        pts = [proj(lon, lat) for lon, lat in ring]
        d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    anchors = {}
    for story in STORIES:
        num, _r, _c, _t, _s, lat, lon = story
        if lat is None:
            continue
        anchors[num] = proj(lon, lat)
    labels = solve_labels(anchors, sw, sh)
    for num, (ax, ay) in anchors.items():
        lx, ly = labels[num]
        if math.hypot(lx - ax, ly - ay) > 1.5:
            d.line([ax, ay, lx, ly], fill=INK, width=1)
    for num, (ax, ay) in anchors.items():
        d.ellipse([ax - 2.5, ay - 2.5, ax + 2.5, ay + 2.5], fill=INK,
                  outline=WHITE, width=1)
    for num, (lx, ly) in labels.items():
        number_dot(d, lx, ly, num)
    return layer


def draw_map(canvas, draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=PAPER, outline=INK, width=2)
    draw.rectangle([x0 + 2, y0 + 2, x1 - 2, y0 + 18], fill=INK)
    draw.text((x0 + 8, y0 + 4), "THE DAY ON THE MAP", font=font(11, bold=True),
              fill=WHITE)
    mx0, my0, mx1, my1 = x0 + 6, y0 + 22, x1 - 6, y1 - 6
    canvas.paste(render_map_layer(mx1 - mx0, my1 - my0), (mx0, my0))
    draw.rectangle([mx0, my0, mx1, my1], outline=INK, width=1)


def draw_legend(draw, x, y, w, h):
    # region index, one column of region rows
    draw.rectangle([x, y, x + w, y + h], fill=PAPER, outline=INK, width=2)
    draw.text((x + 8, y + 6), "IN THIS ISSUE — BY REGION",
              font=font(10, bold=True), fill=INK)
    draw.line([x + 8, y + 24, x + w - 8, y + 24], fill=PINK, width=2)
    by_region = {}
    for story in STORIES:
        by_region.setdefault(story[1], []).append(story[0])
    order = ["AMERICAS", "EUROPE", "ASIA", "MIDDLE EAST", "AFRICA",
             "OCEANIA", "GLOBAL"]
    for idx, region in enumerate(order):
        ry = y + 30 + idx * 15
        bar_c, _t = REGIONS[region]
        draw.rectangle([x + 8, ry + 1, x + 19, ry + 11], fill=bar_c,
                       outline=INK, width=1)
        nf = font(10, bold=True)
        draw.text((x + 24, ry), region, font=nf, fill=INK)
        nx = x + 24 + draw.textlength(region, font=nf) + 6
        nums = " ".join(str(n) for n in by_region[region])
        draw.text((nx, ry + 1), nums, font=font(9), fill=(40, 40, 40))
    draw.text((x + 8, y + h - 16), "(8 has no dot)", font=font(8),
              fill=GREY)


def draw_date_check(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 248, 235),
                   outline=PINK, width=2)
    draw.text((x + 10, y + 6), "DATE CHECK", font=font(11, bold=True),
              fill=PINK)
    text_block(draw, (x + 10, y + 24), DATE_CHECK, font(10), w - 20, 12,
               13, (40, 40, 40))


def build():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # masthead
    draw.text((MARGIN, MARGIN + 2), "THE DAILY WORLD",
              font=font(30, bold=True), fill=INK)
    date_s = "MONDAY 23 NOVEMBER 2026"
    df = font(15, bold=True)
    dw = draw.textlength(date_s, font=df)
    draw.text((W - MARGIN - dw, MARGIN + 4), date_s, font=df, fill=INK)
    tag = "ONE PAGE · EVERY STORY THAT MATTERED"
    tf = font(9)
    tw = draw.textlength(tag, font=tf)
    draw.text((W - MARGIN - tw, MARGIN + 26), tag, font=tf, fill=GREY)
    draw.text((MARGIN, MARGIN + 38), SUBTITLE, font=font(11),
              fill=(40, 40, 40))
    draw.rectangle([MARGIN, MARGIN + 53, W - MARGIN, MARGIN + 57], fill=PINK)

    # numbers strip
    ny = MARGIN + 65
    draw.rectangle([MARGIN, ny, W - MARGIN, ny + 44], fill=PAPER,
                   outline=INK, width=1)
    cell = CW / 6
    for i, (big, label) in enumerate(NUMBERS):
        cx0 = MARGIN + i * cell
        if i:
            draw.line([cx0, ny + 6, cx0, ny + 38], fill=(180, 175, 160),
                      width=1)
        bf = font(20, bold=True)
        bw = draw.textlength(big, font=bf)
        draw.text((cx0 + (cell - bw) / 2, ny + 3), big, font=bf, fill=PINK)
        lf = font(9, bold=True)
        lw = draw.textlength(label, font=lf)
        draw.text((cx0 + (cell - lw) / 2, ny + 28), label, font=lf, fill=INK)

    # heroes: three across, ~1.5x the small-card height (180 vs 119)
    hy = ny + 52
    hero_w = (CW - 2 * GAP) // 3
    for i, story in enumerate(STORIES[:3]):
        draw_card_hero(img, draw, story, MARGIN + i * (hero_w + GAP), hy,
                       hero_w, 180)

    # small panels: 18 cards, rows of 5 / 5 / 5 / 3; the last row's
    # three cards stretch to hero width so the row is filled
    py = hy + 188
    pw = (CW - 4 * GAP) // 5
    wide_w = (CW - 2 * GAP) // 3
    for idx, story in enumerate(STORIES[3:]):
        r, c = divmod(idx, 5)
        if r < 3:
            draw_card_small(img, draw, story, MARGIN + c * (pw + GAP),
                            py + r * (119 + GAP), pw, 119)
        else:
            draw_card_small(img, draw, story, MARGIN + c * (wide_w + GAP),
                            py + r * (119 + GAP), wide_w, 119, wide=True)

    # bottom band: the compact map strip (520 wide), then the region
    # index and the DATE CHECK box beside it, all 156 tall
    by = py + 4 * 119 + 3 * GAP + 8
    draw_map(img, draw, (MARGIN, by, MARGIN + 520, by + 156))
    draw_legend(draw, MARGIN + 528, by, 176, 156)
    draw_date_check(draw, MARGIN + 712, by, CW - 712, 156)

    # ALSO + sources footer
    fy = by + 166
    draw.line([MARGIN, fy - 4, W - MARGIN, fy - 4], fill=INK, width=1)
    af = font(9, bold=True)
    line = ALSO_LINE
    while draw.textlength(line, font=af) > CW:
        line = line[:-1]
    draw.text((MARGIN, fy), line, font=af, fill=INK)
    draw.text((MARGIN, fy + 13), SOURCES, font=font(9), fill=GREY)
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
