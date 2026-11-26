#!/usr/bin/env python3
"""News Image 25 November 2026 — v5 entry generator.

Builds out/entry.png (1024x1024, <=1 MiB) from the verified facts embedded
below. Deterministic: no network, no timestamps, no randomness. Python 3
stdlib + Pillow only. DejaVu Sans / DejaVu Sans Bold.

Layout (1024x1024, paper #FAF8F2, white panels, #D9D4C8 borders):
  header 0-96 | hero XL row 100-272 (3 cols) | hero rows 276-620 (3x3)
  bottom 624-896 (list left, map right) | timeline 900-928 | footer 932-1024
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "entry.png")

W, H = 1024, 1024
PAPER = "#FAF8F2"
PANEL = "#FFFFFF"
BORDER = "#D9D4C8"
NAVY = "#0E2A47"
INK = "#1A1A1A"
MUTED = "#6B7280"
KPI_BLUE = "#BFD3E6"
TIMELINE_BG = "#EFEAE0"
ROW_TINT = "#F2EEE3"

REGION = {
    "NA": "#2563EB",
    "LatAm": "#16A34A",
    "Europe": "#7C3AED",
    "MidEast": "#EA580C",
    "Africa": "#B45309",
    "Asia-Pacific": "#0891B2",
}
REGION_ORDER = ["NA", "LatAm", "Europe", "MidEast", "Africa", "Asia-Pacific"]
REGION_LABEL = {
    "NA": "N. America", "LatAm": "LatAm", "Europe": "Europe",
    "MidEast": "MidEast", "Africa": "Africa", "Asia-Pacific": "Asia-Pacific",
}
TAG_BG = {
    "CONFIRMED": "#15803D",
    "OFFICIAL": "#1D4ED8",
    "REPORTED": "#B45309",
    "CLAIM": "#B91C1C",
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

_fonts = {}


def F(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    return _fonts[key]


def tw(d, text, font):
    """Text width in px."""
    return d.textbbox((0, 0), text, font=font)[2]


def wrap(d, text, font, max_w):
    """Greedy word wrap; returns list of lines, each <= max_w if possible."""
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if tw(d, trial, font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def fit_size(d, text, start, max_w, bold=False, minimum=8):
    """Largest font size <= start whose text fits max_w."""
    size = start
    while size > minimum and tw(d, text, F(size, bold)) > max_w:
        size -= 1
    return size


def trunc(d, text, font, max_w):
    """Truncate with ellipsis to fit max_w."""
    if tw(d, text, font) <= max_w:
        return text
    ell = "\u2026"
    while text and tw(d, text + ell, font) > max_w:
        text = text[:-1]
    return text + ell


# ---------------------------------------------------------------- data
# Hero: (num, region, field, tag, [headline lines], context, source, lat, lon,
#        illustration kind, band label)
HEROES = [
    (1, "Asia-Pacific", "Space", "CONFIRMED",
     ["CHINA LAUNCHES", "SHENZHOU-24"],
     "Pakistan's first astronaut reaches Tiangong; docks 03:56 UTC",
     "CMSA/Xinhua", 40.96, 100.29, "rocket", "LONG MARCH 2F"),
    (2, "NA", "Trade", "REPORTED",
     ["US PROPOSES TARIFFS", "ON 14 ECONOMIES"],
     "USTR proposes duties up to 35% after 8-month probe; hearing 25 Jan 2027",
     "AP/Reuters", 38.91, -77.04, "ship", "SECTION 301"),
    (3, "Europe", "Conflict", "CONFIRMED",
     ["RUSSIA KNOCKS OUT", "DTEK POWER PLANT"],
     "112 drones overnight; 9 killed, 59 hurt across Ukraine",
     "Reuters/DTEK", 50.45, 30.52, "plant", "DTEK PLANT"),
    (4, "NA", "Markets", "CONFIRMED",
     ["DOW RECOVERS", "1,100-POINT PLUNGE"],
     "Erases intraday plunge; closes +0.33% at 50,182.95",
     "AP", 40.71, -74.01, "chart_up", "DOW 50,182.95"),
    (5, "Asia-Pacific", "Markets", "CONFIRMED",
     ["KOSPI CRASHES 6.2%"],
     "KOSPI \u22126.16% to 4,697.51; Samsung, SK Hynix ~\u221210%",
     "Yonhap", 37.57, 126.98, "chart_down", "\u22126.16%"),
    (6, "MidEast", "Conflict", "CONFIRMED",
     ["ISRAELI STRIKE KILLS", "HAMAS SECURITY CHIEF"],
     "Abu al-Awf, wife + 2 daughters killed in Gaza City",
     "Al Jazeera/IDF", 31.50, 34.47, "city", "GAZA CITY"),
    (7, "Europe", "Conflict", "CLAIM",
     ["UKRAINE HITS 5 JETS"],
     "Strikes confirmed; 3 MiG-31 + 2 Su-34 per Kyiv \u2014 count unverified",
     "Gen Staff/Reuters", 55.90, 43.00, "jets", "SAVASLEYKA"),
    (8, "Africa", "Health", "OFFICIAL",
     ["EBOLA TOLL NEARS", "5,800 DEATHS"],
     "DRC: 11,762 cases, 5,775 deaths \u2014 WHO risk assessment v5",
     "WHO/DRC ministry", 1.57, 30.25, "virus", "DRC \u00b7 BUNDIBUGYO"),
    (9, "MidEast", "Conflict", "CLAIM",
     ["HOUTHIS CLAIM", "RAS TANURA STRIKE"],
     "Smoke over Saudi Arabia's largest refinery; damage unconfirmed",
     "Reuters/NASA", 26.60, 50.20, "refinery", "RAS TANURA"),
    (10, "Asia-Pacific", "Tech", "CONFIRMED",
     ["AUSTRALIA PASSES", "DIGITAL DUTY OF CARE"],
     "Fines up to 5% of global turnover; users can switch off feeds",
     "ALP/AP", -35.28, 149.13, "phone", "5% FINES"),
    (11, "NA", "Culture", "CONFIRMED",
     ["MACY'S POSTPONES", "100TH PARADE"],
     "Nor'easter gusts 50\u201360 mph; first weather postponement ever",
     "AP/Macy's", 40.71, -74.01, "balloon", "100TH PARADE"),
    (12, "Europe", "Economy", "CONFIRMED",
     ["POUNDLAND COLLAPSES"],
     "~600 stores; ~11,000 jobs at risk weeks before Christmas",
     "Retail Gazette/Reuters", 51.51, -0.13, "shop", "600 STORES"),
]

# List: (num, region, field, tag, headline, context, source, lat, lon)
LIST = [
    (13, "NA", "Economy", "OFFICIAL", "US GDP revised to 4.3%",
     "Q3 growth revised 3.4%\u21924.3%; PCE inflation 3.8%", "BEA",
     38.91, -77.04),
    (14, "Africa", "Energy", "CONFIRMED", "Cairo tanker fire kills 31",
     "Fuel tanker overturns on Ring Road, El Warraq; 31 killed, 21 hurt",
     "AP/Health Ministry", 30.04, 31.24),
    (15, "Asia-Pacific", "Weather", "CONFIRMED", "Java mine: 9 dead, 17 trapped",
     "Ciseureuh River floods Pongkor mine shaft, Bogor; Wed recovery toll",
     "AP", -6.60, 106.80),
    (16, "Asia-Pacific", "Economy", "CONFIRMED", "Dhaka garment wage +36%",
     "Minimum wage 12,500\u219217,000 taka after 12h talks",
     "AP/Dhaka Tribune", 23.81, 90.41),
    (17, "Asia-Pacific", "Diplomacy", "CONFIRMED", "Solomon signs security treaty",
     "Honiara bars foreign bases; Australia commits A$740m over 10 years",
     "DFAT/Reuters", -9.43, 159.95),
    (18, "Africa", "Law", "CONFIRMED", "Court clears Ramaphosa",
     "Phala Phala impeachment report set aside", "Reuters",
     -33.92, 18.42),
    (19, "MidEast", "Conflict", "CONFIRMED", "Coalition strikes Hodeidah",
     "Strikes on Hodeidah port, Saada, Amran, Sanaa after Riyadh attack",
     "Coalition/Al Jazeera", 14.80, 42.95),
    (20, "MidEast", "Conflict", "CLAIM", "Two tankers hit mines in Hormuz",
     "IRGC claim; no independent confirmation; third tanker reported",
     "IRNA/Reuters", 26.60, 56.30),
    (21, "LatAm", "Law", "CONFIRMED", "All hostages freed in Cartagena",
     "~20 rescued from supermarket siege after ~15-hour standoff",
     "AP", 10.39, -75.51),
    (22, "Europe", "Defence", "REPORTED", "Ukraine laser downs jet drone",
     "Blysk laser kill claimed a world first; system still in testing",
     "BBC/Al Jazeera", 50.45, 30.52),
    (23, "Europe", "Defence", "CONFIRMED", "Poland plans eastern no-fly zone",
     "After Russian missiles landed on Polish soil 20 Nov",
     "Reuters", 52.23, 21.01),
    (24, "Europe", "Tech", "OFFICIAL", "EU unveils Quantum Act, \u20ac50bn",
     "Sovereign tech fund to lead quantum by 2030",
     "European Commission", 50.85, 4.35),
    (25, "MidEast", "Law", "CONFIRMED", "Judges urge dropping bribery case",
     "Netanyahu Case 4000 presents 'considerable difficulties'",
     "Reuters", 31.77, 35.21),
    (26, "Europe", "Energy", "OFFICIAL", "UK energy cap up 26% from Jan",
     "Typical bill \u00a31,723 \u2192 \u00a32,166; \u00a3100 payment for bands A\u2013D",
     "Ofgem", 51.51, -0.13),
    (27, "NA", "Cyber", "REPORTED", "FinCEN offline after breach",
     "Limited subset accessed; filing deadlines extended to 30 Dec",
     "Reuters", 38.91, -77.04),
    (28, "NA", "Defence", "CONFIRMED", "Army detonates bomb chemicals",
     "9,500 lb degraded lead azide blown up in Iowa", "AP/Army",
     40.83, -91.26),
    (29, "NA", "Weather", "CONFIRMED", "Nor'easter snarls holiday travel",
     "4,200+ flights delayed; New Jersey declares emergency",
     "FlightAware/AP", 40.71, -74.01),
    (30, "NA", "Weather", "CONFIRMED", "King tides destroy Pacifica pier",
     "20\u201330 ft waves tear off end of 1,140 ft pier", "AP",
     37.61, -122.49),
    (31, "LatAm", "Politics", "OFFICIAL", "Bolsonaro still in ICU",
     "Intestine resuming function; no discharge date", "DF Star/Globo",
     -15.79, -47.88),
    (32, "Europe", "Diplomacy", "OFFICIAL", "EU\u2013Balkans back enlargement",
     "\u20ac338m for reform leaders Albania, Montenegro, N. Macedonia",
     "European Council", 50.85, 4.35),
    (33, "Europe", "Politics", "CONFIRMED", "Parliament reopens nature laws",
     "EP votes 367\u2013268; assessments capped at 300 days",
     "EP/Politico", 48.58, 7.75),
    (34, "Europe", "Economy", "CONFIRMED", "Germany's economy nearly stalls",
     "Q3 growth revised down to 0.1%", "Destatis", 52.52, 13.40),
    (35, "Africa", "Conflict", "CONFIRMED", "RSF drone attacks kill 19",
     "Damazin + Roseires, Blue Nile; 20+ wounded", "Al Jazeera",
     11.80, 34.40),
    (36, "MidEast", "Diplomacy", "CONFIRMED", "Syria praised over Captagon haul",
     "2.3m pills seized in Tartous; CENTCOM praises Damascus",
     "SANA/CENTCOM", 33.51, 36.29),
    (37, "Asia-Pacific", "Economy", "OFFICIAL", "Australia inflation jumps to 4.9%",
     "Housing + power drive rise; trimmed mean 3.8%", "ABS",
     -35.28, 149.13),
    (38, "Asia-Pacific", "Diplomacy", "CONFIRMED", "North Korea expels Swiss diplomat",
     "Pyongyang office ordered shut within 48 hours", "KCNA/Reuters",
     39.02, 125.75),
    (39, "Asia-Pacific", "Defence", "CONFIRMED", "South Korea widens naval reach",
     "Cheonghae zone expands; no combat troops, no war \u2014 Lee",
     "Yonhap", 37.57, 126.98),
    (40, "Asia-Pacific", "Space", "CONFIRMED", "Japan unveils LUPEX moon rover",
     "To hunt water at lunar south pole; launch 2028", "JAXA/AFP",
     35.68, 139.69),
    (41, "Asia-Pacific", "Economy", "CONFIRMED", "Sensex jumps 1,502 points",
     "+1.82% to 83,938; Flipkart CEO steps down", "PTI",
     19.08, 72.88),
    (42, "Africa", "Diplomacy", "OFFICIAL", "Sudan rejects peace-talks offer",
     "Ethiopia 'did not meet conditions for a neutral mediator'",
     "Sudan govt", 15.60, 32.53),
]

ALL_STORIES = HEROES + LIST

# ---------------------------------------------------------------- checks
# Every text draw is recorded with its allowed box; verified at the end.
RECORDS = []


def record(kind, box, allowed, text):
    RECORDS.append((kind, box, allowed, text))


def text(d, xy, s, font, fill, allowed, anchor="la", kind="text"):
    """Draw text and record its bbox against an allowed rect."""
    d.text(xy, s, font=font, fill=fill, anchor=anchor)
    bb = d.textbbox(xy, s, font=font, anchor=anchor)
    record(kind, bb, allowed, s)
    return bb


def panel(d, box, fill=PANEL, outline=BORDER, width=1):
    d.rectangle(box, fill=fill, outline=outline, width=width)


def num_chip(d, cx, cy, n, color, r=9, font_size=10):
    """Numbered circle; returns its bbox (recorded against its panel)."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline="#FFFFFF",
              width=1)
    f = F(font_size, True)
    s = str(n)
    bb = d.textbbox((cx, cy), s, font=f, anchor="mm")
    d.text((cx, cy), s, font=f, fill="#FFFFFF", anchor="mm")
    return bb


def tag_chip(d, x, y, tag, font_size=9):
    """Tag pill at (x, y); returns width."""
    f = F(font_size, True)
    w = tw(d, tag, f) + 12
    h = font_size + 8
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2,
                        fill=TAG_BG[tag])
    d.text((x + 6, y + h // 2), tag, font=f, fill="#FFFFFF", anchor="lm")
    return w, h

# ---------------------------------------------------------------- illustrations
# Simple flat vector scenes drawn from primitives. Each takes the band/strip
# box (x0,y0,x1,y1). Label pill is drawn by the caller, never over art that
# matters; number chips live outside the band (XL: chip sits top-left of the
# band but the pill/label is right-aligned, far away).

BAND_BG = {
    "rocket": "#101E33", "ship": "#0F3A4D", "plant": "#2B2B2B",
    "chart_up": "#E7F3E7", "chart_down": "#FBEAEA", "city": "#3A2E2A",
    "jets": "#274B73", "virus": "#3D2C4D", "refinery": "#4A2C14",
    "phone": "#123B5C", "balloon": "#2F5D8A", "shop": "#5C3A1E",
}


def _stars(d, box, pts):
    x0, y0, x1, y1 = box
    for (fx, fy, r) in pts:
        cx, cy = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#FFFFFF")


def draw_illustration(d, kind, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d.rectangle(box, fill=BAND_BG[kind])
    if kind == "rocket":
        _stars(d, box, [(0.08, 0.2, 1.5), (0.2, 0.55, 1), (0.85, 0.25, 1.5),
                        (0.7, 0.6, 1), (0.45, 0.15, 1), (0.95, 0.7, 1)])
        cx = x0 + w * 0.30
        d.polygon([(cx, y0 + 6), (cx - 9, y0 + 22), (cx + 9, y0 + 22)],
                  fill="#E25822")
        d.rectangle([cx - 9, y0 + 22, cx + 9, y1 - 12], fill="#F2F2F2")
        d.rectangle([cx - 9, y0 + 34, cx + 9, y0 + 38], fill="#2563EB")
        d.polygon([(cx - 9, y1 - 12), (cx - 15, y1 - 4), (cx - 9, y1 - 6)],
                  fill="#B91C1C")
        d.polygon([(cx + 9, y1 - 12), (cx + 15, y1 - 4), (cx + 9, y1 - 6)],
                  fill="#B91C1C")
        d.polygon([(cx - 6, y1 - 12), (cx + 6, y1 - 12), (cx, y1 - 1)],
                  fill="#F59E0B")
        d.rectangle([x0, y1 - 4, x1, y1], fill="#1E3A2F")
    elif kind == "ship":
        d.rectangle([x0, y1 - 16, x1, y1], fill="#0B6B8A")
        d.rectangle([x0 + w * 0.12, y1 - 34, x0 + w * 0.88, y1 - 16],
                    fill="#1F2937")
        cols = ["#EA580C", "#2563EB", "#16A34A", "#B45309", "#7C3AED"]
        for i, c in enumerate(cols):
            cx = x0 + w * 0.16 + i * w * 0.14
            d.rectangle([cx, y1 - 52, cx + w * 0.11, y1 - 34], fill=c)
        d.rectangle([x0 + w * 0.82, y1 - 56, x0 + w * 0.90, y1 - 34],
                    fill="#F2F2F2")
        f = F(16, True)
        d.text((x0 + w * 0.62, y0 + 4), "%", font=f, fill="#FDE68A")
    elif kind == "plant":
        d.polygon([(x0 + w * 0.18, y1 - 6), (x0 + w * 0.26, y0 + 12),
                   (x0 + w * 0.44, y0 + 12), (x0 + w * 0.52, y1 - 6)],
                  fill="#6B7280")
        d.rectangle([x0 + w * 0.24, y0 + 8, x0 + w * 0.46, y0 + 14],
                    fill="#9CA3AF")
        d.rectangle([x0 + w * 0.60, y1 - 34, x0 + w * 0.66, y1 - 6],
                    fill="#4B5563")
        d.rectangle([x0 + w * 0.70, y1 - 24, x0 + w * 0.76, y1 - 6],
                    fill="#4B5563")
        bolt = [(x0 + w * 0.86, y0 + 8), (x0 + w * 0.78, y0 + 30),
                (x0 + w * 0.84, y0 + 30), (x0 + w * 0.76, y0 + 52),
                (x0 + w * 0.90, y0 + 26), (x0 + w * 0.84, y0 + 26)]
        d.polygon(bolt, fill="#FACC15")
    elif kind in ("chart_up", "chart_down"):
        grid = "#CBD5E1" if kind == "chart_up" else "#E5C5C5"
        for gy in (0.3, 0.55, 0.8):
            d.line([x0 + 6, y0 + h * gy, x1 - 6, y0 + h * gy], fill=grid)
        col = "#15803D" if kind == "chart_up" else "#B91C1C"
        if kind == "chart_up":
            pts = [(x0 + 8, y0 + h * 0.78), (x0 + w * 0.3, y0 + h * 0.66),
                   (x0 + w * 0.5, y0 + h * 0.70), (x0 + w * 0.72, y0 + h * 0.38),
                   (x0 + w * 0.92, y0 + h * 0.18)]
        else:
            pts = [(x0 + 8, y0 + h * 0.20), (x0 + w * 0.3, y0 + h * 0.30),
                   (x0 + w * 0.5, y0 + h * 0.28), (x0 + w * 0.72, y0 + h * 0.62),
                   (x0 + w * 0.92, y0 + h * 0.82)]
        d.line(pts, fill=col, width=3, joint="curve")
        ex, ey = pts[-1]
        d.polygon([(ex, ey - 7), (ex + 9, ey + 2), (ex - 1, ey + 6)],
                  fill=col)
        for (fx, fy) in [(0.15, 0.45), (0.4, 0.5), (0.6, 0.3)]:
            d.ellipse([x0 + w * fx - 2, y0 + h * fy - 2,
                       x0 + w * fx + 2, y0 + h * fy + 2], fill=col)
    elif kind == "city":
        d.rectangle([x0, y1 - 8, x1, y1], fill="#1F2937")
        for i, (fx, fw, fh) in enumerate([(0.06, 0.14, 0.55), (0.24, 0.12, 0.75),
                                          (0.40, 0.16, 0.5), (0.60, 0.13, 0.68),
                                          (0.78, 0.15, 0.45)]):
            bx = x0 + w * fx
            d.rectangle([bx, y1 - 8 - h * fh, bx + w * fw, y1 - 8],
                        fill="#111827" if i % 2 else "#1F2937")
            for wy in range(2):
                for wx in range(2):
                    d.rectangle([bx + 3 + wx * (w * fw - 6) / 2,
                                 y1 - 8 - h * fh + 5 + wy * 12,
                                 bx + 6 + wx * (w * fw - 6) / 2,
                                 y1 - 8 - h * fh + 9 + wy * 12],
                                fill="#FACC15")
        d.ellipse([x0 + w * 0.85, y0 + 6, x0 + w * 0.85 + 14, y0 + 20],
                  fill="#FDE68A")
    elif kind == "jets":
        for (fx, fy, s) in [(0.25, 0.55, 1.0), (0.65, 0.30, 0.8)]:
            cx, cy = x0 + w * fx, y0 + h * fy
            L = 34 * s
            d.polygon([(cx - L, cy), (cx + L * 0.7, cy - 5 * s),
                       (cx + L, cy), (cx + L * 0.7, cy + 5 * s)],
                      fill="#E5E7EB")
            d.polygon([(cx - L * 0.2, cy - 4 * s), (cx + L * 0.1, cy - 16 * s),
                       (cx + L * 0.25, cy - 4 * s)], fill="#9CA3AF")
            d.polygon([(cx - L * 0.2, cy + 4 * s), (cx + L * 0.1, cy + 14 * s),
                       (cx + L * 0.25, cy + 4 * s)], fill="#9CA3AF")
        d.line([x0 + 6, y1 - 8, x1 - 6, y1 - 8], fill="#60A5FA", width=2)
    elif kind == "virus":
        cx, cy, r = x0 + w * 0.30, y0 + h * 0.52, min(w, h) * 0.26
        for k in range(10):
            import math
            a = k * 36 * math.pi / 180
            x2, y2 = cx + (r + 8) * math.cos(a), cy + (r + 8) * math.sin(a)
            d.line([cx + r * 0.8 * math.cos(a), cy + r * 0.8 * math.sin(a),
                    x2, y2], fill="#A78BFA", width=2)
            d.ellipse([x2 - 2.5, y2 - 2.5, x2 + 2.5, y2 + 2.5],
                      fill="#A78BFA")
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#7C3AED")
        for (ox, oy, rr) in [(-0.3, -0.25, 0.28), (0.35, 0.1, 0.2),
                             (-0.05, 0.35, 0.22)]:
            d.ellipse([cx + r * ox - r * rr, cy + r * oy - r * rr,
                       cx + r * ox + r * rr, cy + r * oy + r * rr],
                      fill="#5B21B6")
    elif kind == "refinery":
        d.rectangle([x0, y1 - 6, x1, y1], fill="#1F2937")
        for fx in (0.15, 0.32, 0.55):
            bx = x0 + w * fx
            d.rectangle([bx, y0 + h * 0.35, bx + 10, y1 - 6], fill="#78716C")
            d.rectangle([bx - 3, y0 + h * 0.35 - 4, bx + 13, y0 + h * 0.35],
                        fill="#57534E")
        d.ellipse([x0 + w * 0.72, y0 + h * 0.42, x0 + w * 0.72 + 16,
                   y0 + h * 0.42 + 16], fill="#D6D3D1")
        d.ellipse([x0 + w * 0.78, y0 + h * 0.28, x0 + w * 0.78 + 20,
                   y0 + h * 0.28 + 20], fill="#A8A29E")
        d.ellipse([x0 + w * 0.70, y0 + h * 0.12, x0 + w * 0.70 + 14,
                   y0 + h * 0.12 + 14], fill="#78716C")
    elif kind == "phone":
        px, py = x0 + w * 0.28, y0 + h * 0.12
        pw, ph = w * 0.30, h * 0.76
        d.rounded_rectangle([px, py, px + pw, py + ph], radius=5,
                            fill="#0F172A", outline="#64748B")
        d.rectangle([px + 3, py + 8, px + pw - 3, py + ph - 8], fill="#38BDF8")
        d.line([px + 5, py + ph * 0.45, px + pw - 5, py + ph * 0.30],
               fill="#FFFFFF", width=2)
        d.line([px + 5, py + ph * 0.45, px + pw - 5, py + ph * 0.60],
               fill="#FFFFFF", width=2)
        sx, sy = x0 + w * 0.68, y0 + h * 0.30
        d.polygon([(sx, sy - 12), (sx + 12, sy - 4), (sx + 12, sy + 8),
                   (sx, sy + 16), (sx - 12, sy + 8), (sx - 12, sy - 4)],
                  fill="#FACC15", outline="#B45309")
        d.text((sx, sy + 2), "\u2713", font=F(11, True), fill="#92400E",
               anchor="mm")
    elif kind == "balloon":
        cx, cy = x0 + w * 0.38, y0 + h * 0.42
        r = min(w, h) * 0.32
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#DC2626")
        d.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r],
                  fill="#F87171")
        d.line([cx - r * 0.7, cy + r * 0.7, cx - 8, y1 - 14], fill="#78350F",
               width=2)
        d.line([cx + r * 0.7, cy + r * 0.7, cx + 8, y1 - 14], fill="#78350F",
               width=2)
        d.rectangle([cx - 9, y1 - 14, cx + 9, y1 - 4], fill="#92400E")
        _stars(d, box, [(0.85, 0.15, 1), (0.9, 0.5, 1.2), (0.1, 0.2, 1)])
    elif kind == "shop":
        d.rectangle([x0, y1 - 6, x1, y1], fill="#44403C")
        d.rectangle([x0 + w * 0.12, y0 + h * 0.30, x0 + w * 0.88, y1 - 6],
                    fill="#F5F5F4")
        for i in range(5):
            sx = x0 + w * 0.12 + i * w * 0.152
            col = "#DC2626" if i % 2 == 0 else "#F5F5F4"
            d.polygon([(sx, y0 + h * 0.30), (sx + w * 0.152, y0 + h * 0.30),
                       (sx + w * 0.152, y0 + h * 0.44), (sx, y0 + h * 0.44)],
                      fill=col)
        d.rectangle([x0 + w * 0.30, y0 + h * 0.58, x0 + w * 0.70, y1 - 6],
                    fill="#A8A29E")
        d.line([x0 + w * 0.50, y0 + h * 0.58, x0 + w * 0.50, y1 - 6],
               fill="#57534E", width=2)

# ---------------------------------------------------------------- heroes
def draw_label_pill(d, box, label, font_size=9):
    """Right-aligned dark pill with white label text, inside band/strip box."""
    x0, y0, x1, y1 = box
    f = F(font_size, True)
    tw_ = tw(d, label, f)
    pw, ph = tw_ + 12, font_size + 8
    px = x1 - pw - 6
    py = y0 + 6
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph // 2,
                        fill="#0E2A47")
    d.text((px + 6, py + ph // 2), label, font=f, fill="#FFFFFF",
           anchor="lm")
    return (px, py, px + pw, py + ph)


def draw_hero_xl(d, hero, box):
    num, region, _field, tag, lines, ctx, src, _lat, _lon, kind, label = hero
    x0, y0, x1, y1 = box
    panel(d, box)
    band = (x0, y0, x1, y0 + 62)
    draw_illustration(d, kind, band)
    # number chip: top-left INSIDE band; label pill: top-right of band.
    chip = num_chip(d, x0 + 16, y0 + 16, num, REGION[region], r=11,
                    font_size=11)
    record("chip", chip, band, str(num))
    pill = draw_label_pill(d, band, label, 9)
    record("label", pill, band, label)
    # headline: 2 lines, 24px bold, auto-fit down if needed
    tx = x0 + 12
    tw_ = x1 - x0 - 24
    size = 24
    while size > 19 and any(tw(d, ln, F(size, True)) > tw_ for ln in lines):
        size -= 1
    y = y0 + 70
    for ln in lines:
        text(d, (tx, y), ln, F(size, True), INK, (x0, y0, x1, y1),
             kind="headline")
        y += size + 5
    # context: 2 lines, 11px
    for ln in wrap(d, ctx, F(11), tw_)[:2]:
        text(d, (tx, y), ln, F(11), "#374151", (x0, y0, x1, y1))
        y += 15
    # bottom row: tag chip + source
    by = y1 - 22
    w_, h_ = tag_chip(d, tx, by, tag, 9)
    record("tag", (tx, by, tx + w_, by + h_), (x0, y0, x1, y1), tag)
    text(d, (tx + w_ + 8, by + h_ // 2), src, F(10), MUTED,
         (x0, y0, x1, y1), anchor="lm")


def draw_hero(d, hero, box):
    num, region, _field, tag, lines, ctx, src, _lat, _lon, kind, label = hero
    x0, y0, x1, y1 = box
    panel(d, box)
    strip = (x1 - 96, y0, x1, y1)
    draw_illustration(d, kind, strip)
    # label pill at BOTTOM of strip (never near the number chip);
    # shrink font so the pill always fits the 96px strip.
    fsize = 8
    while fsize > 6 and tw(d, label, F(fsize, True)) + 10 > 86:
        fsize -= 1
    f = F(fsize, True)
    shown_label = trunc(d, label, f, 86 - 10) if tw(d, label, f) + 10 > 86 \
        else label
    tw_ = tw(d, shown_label, f)
    pw, ph = tw_ + 10, fsize + 7
    px = x1 - pw - 5
    py = y1 - ph - 5
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph // 2,
                        fill="#0E2A47")
    d.text((px + 5, py + ph // 2), shown_label, font=f, fill="#FFFFFF", anchor="lm")
    record("label", (px, py, px + pw, py + ph), strip, shown_label)
    # text area left of strip
    tx = x0 + 10
    tw_ = (x1 - 96) - tx - 6
    # headline 2 lines 18-19px bold; the FIRST line is indented by the
    # number chip's width so the chip never covers a letter (v4-style
    # defect: chip over headline). Other lines start at tx.
    size = 19
    while size > 16 and (
            tw(d, lines[0], F(size, True)) > tw_ - 22 or
            any(tw(d, ln, F(size, True)) > tw_ for ln in lines[1:])):
        size -= 1
    y = y0 + 8
    # number chip centred on the first headline line, left of the text
    chip = num_chip(d, tx + 9, y + size // 2 + 1, num, REGION[region], r=9,
                    font_size=10)
    record("chip", chip, (x0, y0, x1, y1), str(num))
    for li, ln in enumerate(lines):
        lx = tx + 22 if li == 0 else tx
        text(d, (lx, y), ln, F(size, True), INK, (x0, y0, x1, y1),
             kind="headline")
        y += size + 4
    for ln in wrap(d, ctx, F(10), tw_)[:2]:
        text(d, (tx, y), ln, F(10), "#374151", (x0, y0, x1, y1))
        y += 13
    by = y1 - 20
    w_, h_ = tag_chip(d, tx, by, tag, 9)
    record("tag", (tx, by, tx + w_, by + h_), (x0, y0, x1, y1), tag)
    text(d, (tx + w_ + 6, by + h_ // 2), src, F(9), MUTED,
         (x0, y0, x1, y1), anchor="lm")


# ---------------------------------------------------------------- list + map
def draw_list(d, box):
    x0, y0, x1, y1 = box
    panel(d, box)
    text(d, (x0 + 10, y0 + 8), "MORE FROM 25 NOVEMBER", F(13, True), NAVY,
         box)
    cols = [x0 + 2, x0 + 204, x0 + 406]
    col_w = 194
    row_h = 24
    top = y0 + 30
    for i, item in enumerate(LIST):
        num, region = item[0], item[1]
        headline = item[4]
        col = i % 3
        row = i // 3
        rx = cols[col]
        ry = top + row * row_h
        if row % 2 == 1:
            d.rectangle([x0 + 1, ry, x1 - 1, ry + row_h], fill=ROW_TINT)
        chip = num_chip(d, rx + 10, ry + row_h // 2, num, REGION[region],
                        r=8, font_size=9)
        record("chip", chip, box, str(num))
        # NOTE: spec says 11px, but 11px DejaVu Bold needs ~217px for the
        # longest 32-char headline while a column only leaves 172px after
        # the number chip (21/30 would truncate). 9px bold fits 28/30 in
        # full; the other two truncate by one word with an ellipsis.
        f = F(9, True)
        shown = trunc(d, headline, f, col_w - 22)
        text(d, (rx + 22, ry + row_h // 2), shown, f, INK, box, anchor="lm")


# Equirectangular map: lon -170..190, lat 83..-56, aspect kept 2:1.
def project(lon, lat, mbox):
    mx0, my0, mx1, my1 = mbox
    mw, mh = mx1 - mx0, my1 - my0
    scale = mw / 360.0
    map_h = 139 * scale
    ox, oy = mx0, my0 + (mh - map_h) / 2
    return (ox + (lon + 170) * scale, oy + (83 - lat) * scale)


CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 73), (-65, 60), (-55, 52), (-60, 47), (-70, 42), (-75, 35),
     (-80, 32), (-85, 30), (-90, 21), (-97, 16), (-105, 20), (-115, 28),
     (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    # Greenland
    [(-58, 64), (-45, 60), (-30, 68), (-20, 70), (-35, 76), (-55, 76),
     (-60, 74)],
    # South America
    [(-80, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-70, -52),
     (-65, -55), (-68, -50), (-62, -42), (-57, -38), (-48, -28),
     (-41, -23), (-35, -9), (-35, -6), (-44, 0), (-50, 4), (-55, 6),
     (-60, 8), (-70, 11), (-75, 10)],
    # Africa
    [(-17, 15), (-17, 21), (-10, 31), (-5, 35), (10, 37), (20, 32),
     (32, 31), (35, 28), (43, 12), (51, 11), (48, 2), (41, -2),
     (40, -10), (35, -18), (32, -26), (28, -33), (20, -35), (15, -27),
     (12, -18), (13, -10), (9, -1), (9, 4), (-8, 5), (-13, 8), (-17, 12)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (-4, 50), (0, 51), (3, 53), (8, 57),
     (10, 59), (5, 60), (12, 62), (18, 69), (25, 71), (30, 70), (40, 68),
     (45, 66), (40, 60), (35, 55), (30, 55), (28, 50), (24, 45),
     (20, 40), (15, 38), (12, 44), (8, 44), (3, 43), (-2, 37), (-6, 36)],
    # Asia (incl. Middle East, India, SE Asia)
    [(30, 70), (40, 68), (50, 69), (60, 69), (70, 72), (80, 73),
     (90, 75), (100, 77), (110, 74), (120, 73), (130, 72), (140, 72),
     (150, 70), (160, 66), (162, 60), (158, 52), (142, 50), (140, 42),
     (135, 35), (130, 33), (127, 35), (122, 38), (120, 32), (122, 28),
     (115, 22), (110, 20), (108, 12), (105, 9), (100, 8), (98, 12),
     (95, 16), (92, 21), (89, 22), (86, 20), (80, 13), (77, 8),
     (75, 20), (72, 20), (66, 25), (62, 25), (58, 26), (56, 26),
     (52, 28), (50, 30), (48, 30), (44, 29), (43, 12), (40, 15),
     (39, 21), (35, 28), (36, 36), (30, 36), (28, 40), (27, 41),
     (30, 45), (28, 50), (30, 55)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
    # UK
    [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53), (1, 51)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 36), (140, 38),
     (141, 40), (142, 42), (143, 44), (141, 45), (140, 40), (139, 37),
     (137, 35), (135, 33), (132, 32)],
    # Indonesia
    [(95, 5), (98, 3), (102, -2), (106, -6), (110, -7), (114, -8),
     (118, -9), (120, -10), (119, -5), (115, -2), (110, 0), (105, 3),
     (100, 4)],
    # New Zealand
    [(167, -45), (170, -42), (174, -39), (176, -38), (178, -38),
     (175, -41), (172, -43), (168, -46)],
]


def draw_map(d, box):
    x0, y0, x1, y1 = box
    panel(d, box)
    text(d, (x0 + 10, y0 + 8), "WHERE IT HAPPENED", F(13, True), NAVY, box)
    mbox = (x0 + 4, y0 + 30, x1 - 4, y1 - 40)
    d.rectangle(mbox, fill="#E8EEF2")
    for poly in CONTINENTS:
        pts = [project(lon, lat, mbox) for lon, lat in poly]
        d.polygon(pts, fill="#D5DBDF", outline="#AEB8C0")
    # pins with jitter for duplicates (same lat/lon seen in order)
    seen = {}
    positions = []
    for s in ALL_STORIES:
        num, region, lat, lon = s[0], s[1], s[7], s[8]
        key = (lat, lon)
        k = seen.get(key, 0)
        seen[key] = k + 1
        dx, dy = [(0, 0), (9, -7), (-9, 7), (0, 9), (9, 7), (-9, -7)][k % 6]
        px, py = project(lon, lat, mbox)
        positions.append((num, region, px + dx, py + dy))
    for num, region, px, py in positions:
        d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=REGION[region],
                  outline="#FFFFFF", width=2)
    # pin numbers only where uncrowded
    for i, (num, region, px, py) in enumerate(positions):
        crowded = any(
            j != i and abs(px - qx) < 17 and abs(py - qy) < 13
            for j, (_n, _r, qx, qy) in enumerate(positions))
        if not crowded:
            text(d, (px + 8, py), str(num), F(7, True), "#374151", box,
                 anchor="lm")
    # caption + colour key
    cy = y1 - 34
    text(d, (x0 + 10, cy), "42 stories pinned \u2014 pin colour = region",
         F(10), MUTED, box)
    kx = x0 + 10
    ky = y1 - 18
    for r in REGION_ORDER:
        d.ellipse([kx, ky, kx + 8, ky + 8], fill=REGION[r])
        text(d, (kx + 11, ky + 4), REGION_LABEL[r], F(9), "#374151", box,
             anchor="lm")
        kx += 11 + tw(d, REGION_LABEL[r], F(9)) + 12


# ---------------------------------------------------------------- page
def draw_header(d):
    d.rectangle([0, 0, W, 96], fill=NAVY)
    text(d, (12, 10), "WEDNESDAY 25 NOVEMBER 2026", F(34, True), "#FFFFFF",
         (0, 0, W, 96))
    text(d, (12, 50), "42 STORIES \u00b7 6 REGIONS \u00b7 15 FIELDS",
         F(13, True), "#FFFFFF", (0, 0, W, 96))
    kpi = ("Dow 50,182.95 (+0.33%) \u00b7 S&P 7,182.78 (\u22120.25%) \u00b7 "
           "KOSPI \u22126.16% \u00b7 Nikkei \u22122.8% \u00b7 Brent $94.61 (+3.5%) "
           "\u00b7 US GDP 4.3% \u00b7 PCE 3.8% \u00b7 Australia CPI 4.9%")
    size = fit_size(d, kpi, 11, W - 24, minimum=9)
    text(d, (12, 72), kpi, F(size), KPI_BLUE, (0, 0, W, 96))


def draw_timeline(d):
    d.rectangle([0, 900, W, 928], fill=TIMELINE_BG)
    tl = ("TIMELINE (UTC)   00:18 Shenzhou launches \u00b7 02:12 Ukraine hits "
          "Savasleyka \u00b7 06:35 Space handshake \u00b7 09:46 Hormuz mines "
          "\u00b7 13:30 GDP 4.3% \u00b7 21:00 Dow closes +0.33% \u00b7 23:08 "
          "Macy's postponed")
    size = fit_size(d, tl, 11, W - 24, bold=True, minimum=9)
    text(d, (12, 914), tl, F(size, True), NAVY, (0, 900, W, 928),
         anchor="la")


def draw_footer(d):
    lines = [
        ("DATE CHECK \u2014 Left out (not 25 Nov): ",
         "Huawei verdict 24 Nov \u00b7 COP31 ended 22 Nov \u00b7 Riyadh tower "
         "strike 24 Nov \u00b7 Peru quake 20 Nov \u00b7 CIA/ODNI breach 24 Nov "
         "\u00b7 IRGC 4th tanker 24 Nov"),
        ("NOT YET: ",
         "Tariffs hearing 25 Jan 2027 \u00b7 Fed decision 9 Dec \u00b7 Macy's "
         "parade Sat 28 Nov \u00b7 EU budget summit 26\u201327 Nov \u00b7 "
         "Poundland buyers sought \u00b7 Ras Tanura damage unconfirmed"),
        ("Sources: ",
         "AP \u00b7 Reuters \u00b7 BEA \u00b7 WHO \u00b7 DRC Health Ministry "
         "\u00b7 CMSA/Xinhua \u00b7 European Commission \u00b7 IDF \u00b7 "
         "Al Jazeera \u00b7 DFAT \u00b7 SANA/CENTCOM \u00b7 JAXA \u00b7 Yonhap "
         "\u00b7 Retail Gazette \u00b7 Ofgem \u00b7 Dhaka Tribune"),
        ("HOW SURE ",
         "\u25cf CONFIRMED (2+ outlets) \u25cf OFFICIAL (govt/institution) "
         "\u25cf REPORTED (1 outlet) \u25cf CLAIM (one party) \u2014 Every "
         "story here happened, or was first reported, on 25 November 2026."),
    ]
    y = 938
    for label, rest in lines:
        size = 10
        while size > 8 and (tw(d, label, F(size, True)) +
                            tw(d, rest, F(size))) > W - 24:
            size -= 1
        x = 12
        text(d, (x, y), label, F(size, True), NAVY, (0, 932, W, H))
        x += tw(d, label, F(size, True))
        text(d, (x, y), rest, F(size), "#374151", (0, 932, W, H))
        y += 21


def build():
    RECORDS.clear()
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_header(d)
    xs = [12, 348, 684]
    for i, hero in enumerate(HEROES[:3]):
        draw_hero_xl(d, hero, (xs[i], 100, xs[i] + 328, 272))
    rows = [(276, 388), (392, 504), (508, 620)]
    for r, (ry0, ry1) in enumerate(rows):
        for c in range(3):
            hero = HEROES[3 + r * 3 + c]
            draw_hero(d, hero, (xs[c], ry0, xs[c] + 328, ry1))
    draw_list(d, (12, 624, 612, 896))
    draw_map(d, (624, 624, 1012, 896))
    draw_timeline(d)
    draw_footer(d)
    return img


def verify_layout():
    """Every recorded text/chip bbox must lie inside its allowed panel."""
    bad = []
    for kind, bb, allowed, s in RECORDS:
        ax0, ay0, ax1, ay1 = allowed
        if bb[0] < ax0 - 0.5 or bb[1] < ay0 - 0.5 or bb[2] > ax1 + 0.5 \
                or bb[3] > ay1 + 0.5:
            bad.append((kind, s, bb, allowed))
    return bad


def main():
    img = build()
    bad = verify_layout()
    print(f"layout records: {len(RECORDS)}  overflow: {len(bad)}")
    for kind, s, bb, allowed in bad[:20]:
        print(f"  OVERFLOW {kind} {s!r} box={bb} allowed={allowed}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, format="PNG")
    size = os.path.getsize(OUT)
    print(f"saved {OUT}  {img.size[0]}x{img.size[1]}  {size} bytes")
    # spec invariants
    assert img.size == (1024, 1024), "size must be 1024x1024"
    assert size <= 1024 * 1024, "PNG must be <= 1 MiB"
    assert len(ALL_STORIES) == 42, "must be 42 stories"
    # "1,100" appears only in the Dow headline, never in small text
    small = [s for (k, _b, _a, s) in RECORDS if k == "text"]
    assert not any("1,100" in s for s in small), "1,100 leaked to small text"
    assert not bad, "layout overflow found"
    return 0


if __name__ == "__main__":
    sys.exit(main())
