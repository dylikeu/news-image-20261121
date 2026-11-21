#!/usr/bin/env python3
"""Render 'The World in One Day - Saturday 21 November 2026'.

One-page newspaper front page: 42 stories, 7 regions, 13 fields.
Masthead + UTC timeline + 3 hero stories with drawn scene illustrations
+ 12 medium stories each with a small drawn scene + stylised world map
with 12 numbered locations + numbered list of the rest + DATE CHECK box
+ Friday's market closes. Draws with Pillow only; output is a
1024x1024 PNG under 1 MiB.
Run:  python3 render.py [output.png]
"""
import math
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 242, 231)      # newsprint cream
INK = (26, 26, 26)           # near-black ink
RED = (176, 42, 32)          # headline red
BLUE = (31, 78, 121)         # deep blue
GREY = (110, 105, 95)        # muted grey
LIGHT = (233, 226, 212)      # light panel
RULE = (26, 26, 26)
MAP_LAND = (196, 205, 190)   # pale sage land
MAP_SEA = (226, 232, 228)    # pale sea
SKY = (38, 52, 74)           # night sky for scenes
OCHRE = (200, 160, 0)
GREEN = (46, 110, 62)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def wrap(draw, s, f, max_w):
    """Greedy word wrap, returns list of lines that fit max_w."""
    words, lines, cur = s.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if text_w(draw, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def centre(draw, x0, x1, y, s, f, fill=INK):
    w = text_w(draw, s, f)
    draw.text(((x0 + x1 - w) / 2, y), s, font=f, fill=fill)


def hline(draw, x0, x1, y, fill=RULE, width=2):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def vline(draw, x, y0, y1, fill=RULE, width=1):
    draw.line([(x, y0), (x, y1)], fill=fill, width=width)


def fit_font(draw, s, path, start, minimum, max_w):
    size = start
    while size > minimum and text_w(draw, s, font(path, size)) > max_w:
        size -= 1
    return font(path, size)


# ---------------------------------------------------------------- stories
# (number, region, headline, deck, tag, source) -- every story happened,
# or was first reported, on Saturday 21 November 2026.
# Regions: NA, LATAM, EUR, ME, AFR, APAC, WORLD.
HEROES = [
    (1, "EUR", "Russia's barrage hits Kyiv; missiles land in Poland",
     "400+ drones, 110 missiles kill at least 8 in Kyiv; missiles land "
     "in Poland too.",
     "CONFIRMED", "BBC"),
    (2, "EUR", "COP31 talks run past deadline in overtime",
     "Antalya misses its Friday deadline; France, Panama demand a "
     "fossil-fuel shift.",
     "REPORTED", "BBC"),
    (3, "EUR", "UK and EU sign three post-Brexit deals",
     "Burnham signs food, emissions and youth pacts in Brussels; "
     "rejoining 'on the table'.",
     "OFFICIAL", "France 24"),
]

# (number, region, headline, deck, tag, source, scene-kind)
MEDIUM = [
    (4, "NA", "Pill makes pancreatic tumours vanish in trial",
     "Daraxonrasib: tumours gone in 1 in 12; nearly all stopped growing.",
     "REPORTED", "Guardian", "pill"),
    (5, "WORLD", "BepiColombo enters Mercury orbit",
     "Europe-Japan craft circles Mercury after an 8-year trip.",
     "OFFICIAL", "UPI", "mercury"),
    (6, "NA", "FBI crime database and USDA 'hacked'",
     "Hackers entered the NCIC database and a USDA payment system.",
     "REPORTED", "BBC", "hack"),
    (7, "ME", "Hormuz tanker attacks continue",
     "Tankers hit near Khasab; six attacks in a week, US drone downed.",
     "REPORTED", "Al Jazeera", "tanker"),
    (8, "ME", "Three Houthi missiles downed over Riyadh",
     "Missiles aimed at Riyadh destroyed; alerts for a third night.",
     "REPORTED", "Al Jazeera", "riyadh"),
    (9, "NA", "Trump threatens tax on firms building data centres abroad",
     "'A tremendous tax' for US firms building AI centres overseas.",
     "REPORTED", "CNBC", "datacenter"),
    (10, "NA", "Claimed AI-assisted proof of Riemann",
     "Claimed proof of the 1859 prime puzzle; checking will take time.",
     "CLAIM", "BBC", "riemann"),
    (11, "WORLD", "GTA 6 earns $3.8bn on day one",
     "Rockstar: $3.8bn in first-day sales, the biggest launch ever.",
     "REPORTED", "Guardian", "gta"),
    (12, "EUR", "Cost-of-living protests sweep Europe",
     "Students in 25 countries walk out; Italy strikes; France marches.",
     "REPORTED", "BBC", "protest"),
    (13, "EUR", "Geneva agrees more work on AI-weapons rules",
     "128 nations back drafting a killer-robot accord by 2028.",
     "OFFICIAL", "NPR", "robot"),
    (14, "EUR", "Denmark expels Russian diplomat over 'plot'",
     "Two arrested; attaché expelled over plot to kill rapper Kyivstoner.",
     "OFFICIAL", "BBC", "plane"),
    (15, "ME", "Israeli fire kills nine in Gaza",
     "Nine dead, 55 hurt; settler attacks on olive farmers pass 400.",
     "REPORTED", "Al Jazeera", "gaza"),
]

# (number, region, headline, tag, source) -- numbered list.
BRIEFS = [
    (16, "NA", "Trump defends Putin ties", "REPORTED", "BBC"),
    (17, "NA", "Palisades fire arson conviction", "CONFIRMED", "BBC"),
    (18, "LATAM", "Salvadoran troops fight Haiti gangs", "REPORTED", "Guardian"),
    (19, "AFR", "Nigeria boat capsizes; 30 dead", "REPORTED", "Daily Trust"),
    (20, "NA", "Indian jailed 19 yrs in murder plot", "CONFIRMED", "BBC"),
    (21, "AFR", "Uganda limits events over Ebola", "OFFICIAL", "AllAfrica"),
    (22, "EUR", "Spain vote 29 Nov; banking tax eyed", "REPORTED", "ST"),
    (23, "APAC", "Japan sidelined by China", "REPORTED", "Japan Times"),
    (24, "AFR", "Mlambo-Ngcuka dies aged 71", "CONFIRMED", "ST"),
    (25, "LATAM", "Peru quake 6.7 shakes Junín", "REPORTED", "La Nación"),
    (26, "NA", "Trump: discussed Nvidia chief with Xi", "REPORTED", "CNBC"),
    (27, "ME", "Kata'ib Hezbollah agrees presence", "REPORTED", "Al Jazeera"),
    (28, "EUR", "Estonia closes 5 Russia crossings", "OFFICIAL", "Euronews"),
    (29, "LATAM", "Bolsonaro in hospital with obstruction", "CONFIRMED", "DW"),
    (30, "APAC", "Nepal PM to visit India 22–23 Nov", "OFFICIAL", "BBC"),
    (31, "EUR", "Police jailed over Zecler beating", "CONFIRMED", "BBC"),
    (32, "NA", "Mamdani: close Rikers Island by 2032", "OFFICIAL", "BBC"),
    (33, "APAC", "Seoul moves to impeach chief justice", "REPORTED", "Yonhap"),
    (34, "LATAM", "Argentina country risk tops 1,000", "REPORTED", "BA Times"),
    (35, "NA", "Judge approves $7.25bn Roundup deal", "CONFIRMED", "BBC"),
    (36, "AFR", "Lissu convicted of sedition", "CONFIRMED", "BBC"),
    (37, "AFR", "Kenya starts onshore oil drilling", "REPORTED", "AllAfrica"),
    (38, "EUR", "CERN finds ultra-rare decay", "REPORTED", "SciDaily"),
    (39, "ME", "Basra power station fire kills 4", "REPORTED", "Al Jazeera"),
    (40, "APAC", "Quake 6.8 off Timor", "REPORTED", "Yonhap"),
    (41, "AFR", "700,000 displaced in Ethiopia", "REPORTED", "Africanews"),
    (42, "EUR", "France probes Depardieu, Houellebecq", "REPORTED", "BBC"),
]

# (hour, label) -- the day in UTC, approximate times marked with ~.
TIMELINE = [
    ("00:00", "COP31 passes Friday deadline, no deal"),
    ("~03:00", "Russia's barrage hits Kyiv; missiles in Poland"),
    ("~07:00", "S&P 500 in correction after AI sell-off"),
    ("~11:00", "UK and EU sign three deals in Brussels"),
    ("~14:00", "Cancer-pill results; BepiColombo at Mercury"),
    ("~20:00", "COP31 in overtime; Geneva backs AI-weapons talks"),
]

# (lon, lat, number) -- places marked on the map.
DOTS = [
    (31.5, 50.5, 1),     # Kyiv
    (22.5, 50.0, 2),     # SE Poland
    (30.7, 36.9, 3),     # Antalya
    (4.4, 50.8, 4),      # Brussels
    (-0.1, 51.5, 5),     # London (displaced, see LEADERS)
    (46.7, 24.6, 6),     # Riyadh
    (56.5, 26.5, 7),     # Strait of Hormuz
    (34.5, 31.5, 8),     # Gaza (displaced, see LEADERS)
    (-77.0, 38.9, 9),    # Washington
    (-72.3, 18.5, 10),   # Port-au-Prince
    (6.0, 5.0, 11),      # Bayelsa, Nigeria
    (-75.0, -11.0, 12),  # Junín, Peru
]

# Display displacement for dots too close to a neighbour: number -> (lon, lat)
LEADERS = {5: (-6.0, 53.5), 8: (36.5, 26.5)}

MAP_LEGEND = [
    ("1", "Kyiv — barrage, 8 killed"),
    ("2", "Poland — missiles land"),
    ("3", "Antalya — COP31 overtime"),
    ("4", "Brussels — UK-EU deals"),
    ("5", "London — cancer-pill trial"),
    ("6", "Riyadh — missiles downed"),
    ("7", "Hormuz — tankers hit"),
    ("8", "Gaza — nine killed"),
    ("9", "Washington — FBI hack"),
    ("10", "Haiti — troops fight gangs"),
    ("11", "Bayelsa — boat capsizes"),
    ("12", "Junín — quake 6.7"),
]

# Rough continent outlines, (lon, lat). Stylised, not to scale.
NORTH_AMERICA = [(-168, 66), (-165, 60), (-158, 58), (-152, 60), (-140, 60),
                 (-135, 57), (-130, 54), (-125, 49), (-124, 42), (-120, 34),
                 (-114, 29), (-110, 24), (-105, 20), (-97, 16), (-94, 17),
                 (-90, 14), (-86, 12), (-83, 9), (-80, 8), (-79, 9),
                 (-82, 13), (-85, 16), (-88, 18), (-90, 21), (-91, 19),
                 (-96, 19), (-97, 26), (-93, 30), (-89, 30), (-84, 30),
                 (-81, 26), (-80, 32), (-76, 35), (-74, 40), (-70, 42),
                 (-68, 45), (-65, 44), (-60, 47), (-55, 52), (-60, 55),
                 (-64, 58), (-68, 55), (-72, 58), (-78, 62), (-85, 66),
                 (-92, 66), (-95, 69), (-110, 68), (-125, 70), (-140, 70),
                 (-155, 71), (-162, 70), (-168, 66)]
GREENLAND = [(-58, 64), (-52, 60), (-45, 60), (-40, 64), (-32, 68),
             (-25, 70), (-20, 74), (-25, 76), (-35, 77), (-50, 76),
             (-58, 74), (-60, 70), (-58, 64)]
SOUTH_AMERICA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
                 (-72, -18), (-70, -23), (-70, -30), (-72, -37), (-73, -44),
                 (-74, -50), (-70, -54), (-66, -55), (-68, -50), (-65, -45),
                 (-62, -41), (-57, -38), (-52, -33), (-48, -28), (-41, -23),
                 (-39, -17), (-35, -9), (-35, -6), (-40, -3), (-44, -2),
                 (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-68, 11),
                 (-72, 12), (-75, 10), (-79, 9)]
AFRICA = [(-17, 15), (-17, 21), (-15, 27), (-10, 31), (-5, 35), (0, 36),
          (10, 37), (11, 34), (15, 32), (20, 32), (25, 32), (30, 31),
          (32, 31), (34, 28), (35, 23), (37, 18), (39, 15), (41, 11),
          (43, 11), (46, 11), (51, 12), (51, 10), (48, 5), (45, 2),
          (41, -2), (40, -6), (39, -12), (36, -18), (33, -26), (30, -32),
          (26, -34), (20, -35), (17, -32), (15, -27), (13, -18), (12, -12),
          (13, -6), (9, -1), (9, 4), (4, 6), (-3, 5), (-8, 5), (-13, 8),
          (-17, 12), (-17, 15)]
EUROPE = [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-1, 46), (-4, 48),
          (-2, 50), (0, 51), (3, 53), (5, 53), (8, 55), (8, 57), (10, 58),
          (12, 56), (18, 56), (21, 55), (24, 58), (21, 59), (24, 60),
          (18, 60), (12, 60), (5, 60), (5, 62), (10, 64), (14, 67),
          (18, 69), (25, 71), (30, 70), (32, 68), (35, 66), (40, 64),
          (44, 62), (48, 60), (50, 58), (48, 55), (44, 52), (40, 50),
          (38, 47), (35, 45), (30, 46), (28, 44), (24, 42), (23, 40),
          (22, 37), (26, 36), (28, 38), (30, 41), (33, 42), (36, 42),
          (39, 41), (41, 41), (38, 39), (36, 36), (33, 36), (30, 36),
          (27, 37), (23, 36), (20, 39), (19, 42), (16, 44), (14, 45),
          (12, 44), (8, 44), (3, 43), (0, 40), (-2, 37), (-6, 36),
          (-9, 37), (-10, 36)]
ASIA = [(30, 36), (36, 36), (42, 35), (44, 38), (48, 38), (50, 40),
        (54, 38), (56, 40), (60, 42), (63, 44), (66, 45), (70, 44),
        (74, 43), (78, 44), (82, 46), (86, 48), (90, 50), (94, 52),
        (98, 52), (102, 52), (106, 53), (110, 54), (114, 54), (118, 55),
        (122, 56), (126, 58), (130, 59), (134, 59), (138, 60), (142, 59),
        (146, 59), (150, 60), (155, 60), (158, 59), (162, 60), (162, 56),
        (158, 52), (156, 50), (152, 48), (148, 44), (144, 42), (142, 40),
        (140, 38), (138, 35), (135, 33), (132, 31), (130, 30), (127, 28),
        (124, 26), (122, 24), (120, 22), (118, 20), (116, 18), (114, 16),
        (112, 14), (110, 12), (108, 10), (106, 8), (104, 6), (102, 4),
        (100, 2), (98, 6), (96, 10), (94, 14), (92, 16), (90, 20),
        (88, 22), (86, 20), (84, 18), (82, 16), (80, 14), (78, 10),
        (76, 8), (74, 12), (72, 16), (70, 20), (68, 22), (66, 24),
        (64, 25), (62, 25), (60, 25), (58, 25), (56, 26), (54, 26),
        (52, 28), (50, 29), (48, 30), (46, 30), (44, 31), (42, 33),
        (40, 36), (38, 36), (36, 36)]
JAPAN = [(130, 31), (132, 33), (134, 34), (136, 35), (138, 35), (140, 36),
         (141, 39), (142, 42), (144, 44), (142, 44), (140, 42), (139, 38),
         (137, 35), (135, 33), (132, 32), (130, 31)]
BRITAIN = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
           (1, 51), (-3, 50), (-5, 50)]
AUSTRALIA = [(114, -22), (114, -30), (115, -35), (120, -34), (124, -33),
             (129, -32), (132, -32), (135, -35), (137, -38), (140, -38),
             (142, -39), (145, -38), (147, -39), (150, -37), (153, -32),
             (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
             (140, -17), (136, -15), (135, -12), (132, -11), (130, -13),
             (127, -14), (124, -15), (122, -17), (120, -20), (116, -21),
             (114, -22)]
NEW_ZEALAND = [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38),
               (174, -41), (171, -43), (168, -46), (167, -45)]
INDONESIA = [(95, 5), (98, 3), (101, 0), (104, -3), (106, -6), (110, -7),
             (114, -8), (114, -10), (110, -8), (106, -6), (102, -4),
             (99, 0), (96, 3), (95, 5)]
# Caribbean islands -- small but must be drawn, or the Haiti dot floats on sea.
# Hispaniola is drawn slightly enlarged so it still reads around its dot.
CARIBBEAN = [
    # Cuba
    [(-84.8, 22.8), (-83.0, 23.3), (-80.5, 23.0), (-78.0, 22.2),
     (-75.5, 21.0), (-74.2, 20.2), (-75.8, 20.4), (-78.5, 21.2),
     (-81.0, 22.2), (-83.5, 22.0), (-84.8, 21.8)],
    # Hispaniola (Haiti + Dominican Republic)
    [(-74.8, 20.2), (-73.0, 20.4), (-71.0, 19.9), (-69.0, 19.2),
     (-68.5, 18.2), (-69.5, 17.6), (-71.5, 17.8), (-73.0, 18.2),
     (-74.3, 18.6), (-74.8, 19.4)],
    # Jamaica
    [(-78.3, 18.4), (-77.0, 18.5), (-76.2, 18.0), (-77.0, 17.9),
     (-78.3, 18.0)],
    # Puerto Rico
    [(-67.2, 18.5), (-66.0, 18.5), (-65.6, 18.1), (-66.5, 17.9),
     (-67.2, 18.1)],
]

CONTINENTS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EUROPE,
              ASIA, JAPAN, BRITAIN, AUSTRALIA, NEW_ZEALAND, INDONESIA,
              *CARIBBEAN]



# ---------------------------------------------------------------- scenes
def explosion(draw, cx, cy, r, core=(255, 210, 60)):
    """Starburst: orange spikes, yellow core."""
    for i in range(8):
        ang = math.radians(i * 45 + 10)
        x2, y2 = cx + r * math.cos(ang), cy + r * math.sin(ang)
        x3, y3 = cx + r * 0.45 * math.cos(ang + 0.35), cy + r * 0.45 * math.sin(ang + 0.35)
        x4, y4 = cx + r * 0.45 * math.cos(ang - 0.35), cy + r * 0.45 * math.sin(ang - 0.35)
        draw.polygon([(cx, cy), (x2, y2), (x3, y3)], fill=(230, 120, 30))
        draw.polygon([(cx, cy), (x2, y2), (x4, y4)], fill=(240, 160, 40))
    draw.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45],
                 fill=core)


def bezier_arc(draw, x0, y0, x1, y1, lift, fill, width=2):
    """Quadratic bezier arc from (x0,y0) to (x1,y1), arcing up by lift."""
    mx, my = (x0 + x1) / 2, min(y0, y1) - lift
    pts = []
    for t in [i / 24.0 for i in range(25)]:
        bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t ** 2 * x1
        by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t ** 2 * y1
        pts.append((bx, by))
    draw.line(pts, fill=fill, width=width)
    # arrowhead at the end
    dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    draw.polygon([(x1, y1), (x1 - 7 * ux - 3 * uy, y1 - 7 * uy + 3 * ux),
                  (x1 - 7 * ux + 3 * uy, y1 - 7 * uy - 3 * ux)], fill=fill)


def flag_uk(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(0, 40, 90))
    draw.polygon([(x, y), (x + w * 0.18, y), (x + w, y + h),
                  (x + w * 0.82, y + h)], fill=(255, 255, 255))
    draw.polygon([(x + w, y), (x + w * 0.82, y), (x, y + h),
                  (x + w * 0.18, y + h)], fill=(255, 255, 255))
    draw.line([(x + w / 2, y), (x + w / 2, y + h)], fill=(255, 255, 255), width=max(2, int(h * 0.28)))
    draw.line([(x, y + h / 2), (x + w, y + h / 2)], fill=(255, 255, 255), width=max(2, int(h * 0.28)))
    draw.line([(x + w / 2, y), (x + w / 2, y + h)], fill=(200, 16, 46), width=max(1, int(h * 0.12)))
    draw.line([(x, y + h / 2), (x + w, y + h / 2)], fill=(200, 16, 46), width=max(1, int(h * 0.12)))


def flag_eu(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(0, 40, 90))
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) * 0.32
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        sx, sy = cx + r * math.cos(ang), cy + r * math.sin(ang)
        draw.ellipse([sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5], fill=(255, 210, 0))


def scene_kyiv(draw, x, y, w, h):
    """Night sky over a stylised Ukraine/Poland map, missile arcs, blasts."""
    draw.rectangle([x, y, x + w, y + h], fill=(24, 34, 56))
    # stars
    for sx, sy in [(18, 12), (60, 8), (120, 16), (200, 10), (260, 14),
                   (40, 26), (150, 6), (230, 24), (285, 8)]:
        draw.ellipse([x + sx - 1, y + sy - 1, x + sx + 1, y + sy + 1],
                     fill=(220, 220, 200))
    # landmass: Ukraine (big) + Poland (left)
    ukr = [(150, 40), (210, 34), (265, 42), (290, 55), (280, 75), (240, 84),
           (190, 84), (155, 72), (140, 55)]
    pol = [(95, 38), (140, 34), (155, 48), (145, 70), (110, 74), (92, 58)]
    draw.polygon([(x + px, y + py) for px, py in ukr], fill=(120, 130, 110))
    draw.polygon([(x + px, y + py) for px, py in pol], fill=(150, 158, 140))
    draw.text((x + 108, y + 75), "POLAND", font=font(SANS_B, 9), fill=(240, 240, 230))
    draw.text((x + 195, y + 75), "UKRAINE", font=font(SANS_B, 9), fill=(240, 240, 230))
    # Kyiv marker + blast
    draw.ellipse([x + 218, y + 52, x + 226, y + 60], fill=RED, outline=(255, 255, 255), width=1)
    explosion(draw, x + 222, y + 56, 13)
    explosion(draw, x + 276, y + 40, 9)
    explosion(draw, x + 178, y + 66, 8)
    # missile arcs coming from the east
    bezier_arc(draw, x + 300, y + 20, x + 222, y + 56, 26, (255, 120, 60), 3)
    bezier_arc(draw, x + 300, y + 34, x + 276, y + 40, 18, (255, 120, 60), 3)
    bezier_arc(draw, x + 150, y + 12, x + 118, y + 52, 14, (255, 160, 80), 3)
    draw.text((x + 230, y + 26), "KYIV", font=font(SANS_B, 9), fill=(255, 255, 255))
    # red impact dots in Poland
    for dx, dy in [(112, 52), (128, 62)]:
        draw.ellipse([x + dx - 3, y + dy - 3, x + dx + 3, y + dy + 3], fill=RED,
                     outline=(255, 255, 255), width=1)


def scene_cop(draw, x, y, w, h):
    """COP31 hall: flags, globe, setting sun, OVERTIME banner."""
    draw.rectangle([x, y, x + w, y + h], fill=(214, 196, 160))
    # setting sun (whole: ends at y+50, above the hall, so it is never clipped)
    draw.ellipse([x + w - 70, y + 6, x + w - 22, y + 50], fill=(230, 120, 40))
    draw.ellipse([x + w - 63, y + 13, x + w - 29, y + 43], fill=(245, 180, 60))
    # hall: roofline strip only (the banner covers the hall body below it)
    draw.rectangle([x + 12, y + 52, x + w - 12, y + h - 8], fill=(120, 96, 70))
    draw.rectangle([x + 12, y + 52, x + w - 12, y + 60], fill=(90, 70, 48))
    # globe on the podium
    gx, gy = x + 34, y + 16
    draw.ellipse([gx, gy, gx + 34, gy + 34], fill=(70, 130, 180),
                 outline=(255, 255, 255), width=2)
    draw.ellipse([gx + 8, gy + 6, gx + 20, gy + 16], fill=GREEN)
    draw.ellipse([gx + 18, gy + 20, gx + 28, gy + 30], fill=GREEN)
    draw.text((x + 76, y + 20), "COP31", font=font(SERIF_B, 20), fill=INK)
    draw.text((x + 76, y + 40), "ANTALYA", font=font(SANS_B, 10), fill=(90, 60, 40))
    # OVERTIME banner
    draw.rectangle([x + 12, y + h - 26, x + w - 12, y + h - 8], fill=RED)
    centre(draw, x + 12, x + w - 12, y + h - 23, "NO DEAL — IN OVERTIME",
           font(SANS_B, 12), fill=(255, 255, 255))


def scene_ukeu(draw, x, y, w, h):
    """Brussels: UK + EU flags, signed documents, three seals."""
    draw.rectangle([x, y, x + w, y + h], fill=(196, 208, 220))
    # skyline
    for bx, bw, bh in [(10, 26, 34), (44, 20, 48), (200, 30, 40), (238, 24, 30),
                       (270, 22, 44)]:
        draw.rectangle([x + bx, y + h - 18 - bh, x + bx + bw, y + h - 18],
                       fill=(90, 100, 118))
    draw.rectangle([x, y + h - 18, x + w, y + h], fill=(120, 128, 120))
    # flag poles
    draw.line([(x + 92, y + 10), (x + 92, y + h - 18)], fill=INK, width=2)
    draw.line([(x + 212, y + 10), (x + 212, y + h - 18)], fill=INK, width=2)
    flag_uk(draw, x + 96, y + 12, 52, 30)
    flag_eu(draw, x + 156, y + 12, 52, 30)
    # handshake: two sleeves meeting
    draw.polygon([(x + 118, y + 62), (x + 148, y + 52), (x + 148, y + 70),
                  (x + 118, y + 78)], fill=(30, 60, 110))
    draw.polygon([(x + 188, y + 62), (x + 158, y + 52), (x + 158, y + 70),
                  (x + 188, y + 78)], fill=(20, 40, 80))
    draw.ellipse([x + 142, y + 52, x + 164, y + 74], fill=(232, 190, 150),
                 outline=(180, 140, 110), width=1)
    # three signed documents with seals
    for i, dx in enumerate((118, 148, 178)):
        draw.rectangle([x + dx, y + h - 34, x + dx + 24, y + h - 22],
                       fill=(255, 255, 255), outline=INK, width=1)
        draw.line([(x + dx + 4, y + h - 30), (x + dx + 20, y + h - 30)],
                  fill=GREY, width=1)
        draw.ellipse([x + dx + 15, y + h - 27, x + dx + 21, y + h - 21],
                     fill=RED)
    centre(draw, x, x + w, y + h - 16, "3 DEALS SIGNED",
           font(SANS_B, 10), fill=INK)


# ---------------------------------------------------------------- mini scenes (62x62)
def mini_pill(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(238, 232, 220))
    # bottle
    draw.rectangle([x + 12, y + 16, x + 32, y + 52], fill=(255, 255, 255),
                   outline=INK, width=2)
    draw.rectangle([x + 14, y + 8, x + 30, y + 16], fill=RED)
    draw.text((x + 15, y + 30), "Rx", font=font(SANS_B, 10), fill=RED)
    # pills
    draw.ellipse([x + 38, y + 40, x + 52, y + 48], fill=(220, 60, 50))
    draw.ellipse([x + 42, y + 50, x + 56, y + 56], fill=(240, 200, 60))
    # shrinking tumour cell
    draw.ellipse([x + 40, y + 10, x + 56, y + 26], fill=(150, 60, 70))
    draw.line([(x + 56, y + 18), (x + 60, y + 18)], fill=INK, width=2)
    draw.polygon([(x + 60, y + 14), (x + 60, y + 22), (x + 54, y + 18)],
                 fill=INK)


def mini_mercury(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(16, 20, 34))
    for sx, sy in [(8, 8), (50, 6), (20, 14), (56, 30), (10, 40)]:
        draw.ellipse([x + sx - 1, y + sy - 1, x + sx + 1, y + sy + 1],
                     fill=(220, 220, 200))
    # Mercury
    draw.ellipse([x + 14, y + 18, x + 46, y + 50], fill=(170, 150, 130))
    for cx, cy, r in [(24, 28, 4), (36, 36, 5), (30, 42, 3)]:
        draw.ellipse([x + cx - r, y + cy - r, x + cx + r, y + cy + r],
                     fill=(130, 110, 95))
    # spacecraft + orbit arc
    draw.arc([x + 4, y + 8, x + 58, y + 58], 200, 340, fill=(200, 200, 200),
             width=1)
    draw.rectangle([x + 46, y + 8, x + 54, y + 14], fill=(220, 220, 220),
                   outline=INK, width=1)
    draw.rectangle([x + 40, y + 9, x + 46, y + 13], fill=(90, 140, 200))
    draw.rectangle([x + 54, y + 9, x + 60, y + 13], fill=(90, 140, 200))


def mini_hack(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(30, 34, 44))
    # server rack
    for i in range(3):
        ry = y + 8 + i * 14
        draw.rectangle([x + 8, ry, x + 34, ry + 11], fill=(70, 80, 96),
                       outline=(180, 180, 180), width=1)
        draw.ellipse([x + 11, ry + 4, x + 14, ry + 7], fill=(90, 220, 90))
        draw.line([(x + 18, ry + 5), (x + 30, ry + 5)], fill=(200, 200, 200),
                  width=1)
    # broken padlock
    draw.ellipse([x + 40, y + 30, x + 58, y + 48], fill=(220, 60, 50))
    draw.arc([x + 44, y + 18, x + 56, y + 34], 180, 330, fill=(220, 60, 50),
             width=3)
    draw.arc([x + 44, y + 18, x + 56, y + 34], 330, 360, fill=(220, 60, 50),
             width=3)
    draw.rectangle([x + 47, y + 36, x + 51, y + 44], fill=(255, 255, 255))
    # warning triangle
    draw.polygon([(x + 48, y + 6), (x + 58, y + 20), (x + 38, y + 20)],
                 fill=(240, 200, 40))
    draw.text((x + 46, y + 10), "!", font=font(SANS_B, 10), fill=INK)


def mini_tanker(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(150, 190, 210))
    draw.rectangle([x, y + 34, x + s, y + s], fill=(40, 90, 140))
    # tanker
    draw.polygon([(x + 6, y + 30), (x + 56, y + 30), (x + 50, y + 42),
                  (x + 12, y + 42)], fill=(40, 40, 44))
    draw.rectangle([x + 40, y + 18, x + 50, y + 30], fill=(220, 220, 220))
    draw.rectangle([x + 16, y + 22, x + 24, y + 30], fill=(180, 60, 40))
    # splash + projectile streak
    draw.line([(x + 50, y + 6), (x + 56, y + 26)], fill=(255, 120, 40), width=3)
    explosion(draw, x + 52, y + 32, 8)
    draw.arc([x + 8, y + 44, x + 24, y + 54], 0, 180, fill=(255, 255, 255),
             width=2)


def mini_riyadh(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(26, 30, 52))
    for sx, sy in [(8, 8), (30, 6), (52, 10), (18, 16)]:
        draw.ellipse([x + sx - 1, y + sy - 1, x + sx + 1, y + sy + 1],
                     fill=(220, 220, 200))
    # skyline
    for bx, bw, bh in [(6, 10, 26), (20, 8, 34), (32, 12, 22), (48, 8, 30)]:
        draw.rectangle([x + bx, y + 56 - bh, x + bx + bw, y + 56],
                       fill=(70, 80, 110))
    # tower with spire
    draw.rectangle([x + 20, y + 14, x + 28, y + 56], fill=(120, 130, 150))
    draw.polygon([(x + 24, y + 4), (x + 24, y + 14), (x + 28, y + 14)],
                 fill=(160, 170, 190))
    for wx in (22, 26):
        draw.rectangle([x + wx, y + 20, x + wx + 2, y + 50], fill=(255, 220, 90))
    # interceptor arcs
    bezier_arc(draw, x + 8, y + 52, x + 40, y + 16, 10, (255, 255, 255), 1)
    bezier_arc(draw, x + 56, y + 52, x + 44, y + 22, 8, (255, 200, 80), 1)
    explosion(draw, x + 42, y + 18, 6)


def mini_datacenter(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(222, 226, 230))
    # building
    draw.rectangle([x + 8, y + 14, x + 46, y + 54], fill=(90, 110, 140),
                   outline=INK, width=1)
    for row in range(3):
        for col in range(3):
            draw.rectangle([x + 13 + col * 11, y + 19 + row * 11,
                            x + 20 + col * 11, y + 26 + row * 11],
                           fill=(160, 220, 140))
    draw.rectangle([x + 46, y + 14, x + 54, y + 54], fill=(70, 88, 112))
    # big $ + tax stamp
    f = font(SERIF_B, 22)
    draw.text((x + 40, y + 30), "$", font=f, fill=(30, 90, 50))
    draw.ellipse([x + 36, y + 4, x + 58, y + 26], outline=RED, width=2)
    draw.text((x + 40, y + 10), "TAX", font=font(SANS_B, 8), fill=RED)


def mini_riemann(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(34, 64, 48))
    draw.rectangle([x + 4, y + 4, x + s - 4, y + s - 4], outline=(150, 120, 70),
                   width=2)
    draw.text((x + 8, y + 8), "ζ(s) = 0", font=font(SERIF_B, 12),
              fill=(255, 255, 255))
    draw.text((x + 8, y + 24), "Re(s) = ½", font=font(SERIF, 11),
              fill=(255, 255, 255))
    draw.text((x + 7, y + 40), "2 3 5 7 11", font=font(SANS_B, 10),
              fill=(255, 220, 90))


def mini_gta(draw, x, y, s=62):
    # dusk sky
    for i in range(31):
        draw.line([(x, y + i * 2), (x + s, y + i * 2)],
                  fill=(90 + i * 3, 50 + i * 2, 110 + i), width=2)
    draw.ellipse([x + 38, y + 6, x + 54, y + 22], fill=(255, 200, 90))
    # skyline + palms
    for bx, bw, bh in [(4, 12, 22), (20, 10, 30), (34, 12, 18), (48, 10, 26)]:
        draw.rectangle([x + bx, y + 56 - bh, x + bx + bw, y + 56],
                       fill=(30, 20, 50))
    draw.line([(x + 12, y + 56), (x + 12, y + 40)], fill=(20, 40, 20), width=2)
    draw.arc([x + 4, y + 34, x + 20, y + 46], 180, 360, fill=(20, 60, 25),
             width=2)
    draw.text((x + 6, y + 26), "$3.8bn", font=font(SANS_B, 13),
              fill=(255, 255, 255))


def mini_protest(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(232, 226, 210))
    # crowd
    for i, cx in enumerate((10, 24, 38, 52)):
        draw.ellipse([x + cx - 5, y + 34, x + cx + 5, y + 44], fill=(220, 180, 140))
        draw.rectangle([x + cx - 7, y + 44, x + cx + 7, y + 58],
                       fill=((60, 90, 140) if i % 2 == 0 else (140, 60, 60)))
    for i, cx in enumerate((16, 32, 48)):
        draw.ellipse([x + cx - 5, y + 24, x + cx + 5, y + 34], fill=(200, 160, 120))
        draw.rectangle([x + cx - 7, y + 34, x + cx + 7, y + 48],
                       fill=((90, 120, 70) if i % 2 == 0 else (120, 90, 50)))
    # placards
    draw.rectangle([x + 8, y + 6, x + 26, y + 20], fill=(255, 255, 255),
                   outline=RED, width=2)
    draw.line([(x + 17, y + 20), (x + 17, y + 34)], fill=INK, width=2)
    draw.text((x + 12, y + 9), "€", font=font(SANS_B, 11), fill=RED)
    draw.rectangle([x + 38, y + 4, x + 56, y + 16], fill=(255, 255, 255),
                   outline=INK, width=2)
    draw.line([(x + 47, y + 16), (x + 47, y + 30)], fill=INK, width=2)
    draw.line([(x + 41, y + 13), (x + 53, y + 7)], fill=RED, width=2)


def mini_robot(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(226, 232, 238))
    # UN flag
    draw.rectangle([x + 6, y + 6, x + 22, y + 18], fill=(60, 120, 200))
    draw.ellipse([x + 11, y + 9, x + 17, y + 15], outline=(255, 255, 255),
                 width=1)
    # robot
    draw.rectangle([x + 30, y + 16, x + 52, y + 42], fill=(150, 160, 170),
                   outline=INK, width=2)
    draw.ellipse([x + 36, y + 24, x + 41, y + 29], fill=RED)
    draw.ellipse([x + 45, y + 24, x + 50, y + 29], fill=RED)
    draw.line([(x + 41, y + 16), (x + 41, y + 10)], fill=INK, width=2)
    draw.ellipse([x + 39, y + 7, x + 43, y + 11], fill=(240, 200, 40))
    draw.rectangle([x + 34, y + 42, x + 40, y + 52], fill=(120, 130, 140))
    draw.rectangle([x + 42, y + 42, x + 48, y + 52], fill=(120, 130, 140))
    # gavel
    draw.rectangle([x + 8, y + 46, x + 22, y + 52], fill=(140, 100, 60))
    draw.line([(x + 15, y + 52), (x + 22, y + 58)], fill=(120, 80, 40), width=3)
    draw.text((x + 26, y + 48), "2028", font=font(SANS_B, 9), fill=INK)


def mini_plane(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(190, 210, 230))
    # runway + plane taking off
    draw.rectangle([x, y + 46, x + s, y + 50], fill=(90, 90, 90))
    draw.polygon([(x + 8, y + 30), (x + 52, y + 22), (x + 56, y + 26),
                  (x + 20, y + 36)], fill=(255, 255, 255))
    draw.polygon([(x + 30, y + 24), (x + 40, y + 12), (x + 44, y + 14),
                  (x + 36, y + 26)], fill=(220, 220, 220))
    draw.polygon([(x + 44, y + 20), (x + 52, y + 12), (x + 54, y + 15),
                  (x + 48, y + 22)], fill=(220, 220, 220))
    draw.rectangle([x + 52, y + 6, x + 58, y + 10], fill=(200, 40, 40))
    # EXPELLED stamp
    draw.rectangle([x + 6, y + 50, x + 56, y + 58], outline=RED, width=2)
    centre(draw, x + 6, x + 56, y + 51, "EXPELLED", font(SANS_B, 7), fill=RED)


def mini_gaza(draw, x, y, s=62):
    draw.rectangle([x, y, x + s, y + s], fill=(226, 232, 228))
    # coastline + strip outline (shortened so the bottom band stays clear)
    draw.rectangle([x, y + 8, x + 18, y + 44], fill=(120, 170, 200))
    draw.polygon([(x + 18, y + 10), (x + 30, y + 8), (x + 34, y + 44),
                  (x + 22, y + 48), (x + 18, y + 40)], fill=(196, 205, 190),
                 outline=INK)
    draw.text((x + 36, y + 10), "GAZA", font=font(SANS_B, 8), fill=INK)
    # hospital with cross
    draw.rectangle([x + 36, y + 26, x + 56, y + 48], fill=(255, 255, 255),
                   outline=INK, width=1)
    draw.rectangle([x + 43, y + 30, x + 49, y + 42], fill=RED)
    draw.rectangle([x + 39, y + 34, x + 53, y + 38], fill=RED)
    draw.text((x + 4, y + 52), "9 KILLED", font=font(SANS_B, 8), fill=RED)


MINI_SCENES = {
    "pill": mini_pill, "mercury": mini_mercury, "hack": mini_hack,
    "tanker": mini_tanker, "riyadh": mini_riyadh, "datacenter": mini_datacenter,
    "riemann": mini_riemann, "gta": mini_gta, "protest": mini_protest,
    "robot": mini_robot, "plane": mini_plane, "gaza": mini_gaza,
}
HERO_SCENES = {1: scene_kyiv, 2: scene_cop, 3: scene_ukeu}

# ---------------------------------------------------------------- layout
def draw_masthead(draw):
    x0, x1 = 24, 1000
    draw.text((x0, 6), "THE WORLD IN ONE DAY", font=font(SERIF_B, 26),
              fill=INK)
    right = "No. 326  •  PRICE: FREE"
    draw.text((x1 - text_w(draw, right, font(SANS_B, 11)), 14), right,
              font=font(SANS_B, 11), fill=GREY)
    centre(draw, x0, x1, 36, "Saturday, 21 November 2026",
           font(SERIF_B, 40), fill=RED)
    centre(draw, x0, x1, 84,
           "42 STORIES  •  7 REGIONS  •  13 FIELDS",
           font(SANS_B, 13))
    hline(draw, x0, x1, 102, width=3)
    hline(draw, x0, x1, 106, width=1)


def draw_timeline(draw):
    y0 = 110
    draw.text((24, y0), "THE DAY IN UTC", font=font(SANS_B, 11), fill=RED)
    tx0, tx1 = 24, 1000
    ty = y0 + 20
    draw.line([(tx0, ty), (tx1, ty)], fill=RULE, width=2)
    n = len(TIMELINE)
    tf = font(SANS_B, 10)
    lf = font(SANS, 9)
    for i, (hour, label) in enumerate(TIMELINE):
        cx = tx0 + (tx1 - tx0) * (i + 0.5) / n
        draw.ellipse([cx - 4, ty - 4, cx + 4, ty + 4], fill=RED,
                     outline=(255, 255, 255), width=1)
        hw = text_w(draw, hour, tf)
        draw.text((cx - hw / 2, ty + 6), hour, font=tf, fill=RED)
        for j, ln in enumerate(wrap(draw, label, lf, 156)[:2]):
            lw = text_w(draw, ln, lf)
            draw.text((cx - lw / 2, ty + 19 + j * 11), ln, font=lf,
                      fill=INK)
    hline(draw, 24, 1000, 170, width=1)


def draw_heroes(draw):
    y0 = 176
    scene_h = 86
    cols = [(24, 328), (360, 664), (696, 1000)]
    for (x0, x1), (num, region, head, deck, tag, src) in zip(cols, HEROES):
        w = x1 - x0
        draw.rectangle([x0, y0, x1, y0 + scene_h], outline=RULE, width=1)
        HERO_SCENES[num](draw, x0, y0, w, scene_h)
        y = y0 + scene_h + 6
        draw.text((x0, y), "%d  %s" % (num, region), font=font(SANS_B, 11),
                  fill=RED)
        y += 16
        hf = font(SERIF_B, 19)
        for ln in wrap(draw, head, hf, w)[:2]:
            draw.text((x0, y), ln, font=hf, fill=INK)
            y += 21
        y += 1
        df = font(SANS, 11)
        for ln in wrap(draw, deck, df, w)[:2]:
            draw.text((x0, y), ln, font=df, fill=(60, 58, 52))
            y += 13
        y += 1
        draw.text((x0, y), "%s  ·  %s" % (tag, src), font=font(SANS_B, 10),
                  fill=RED)
    vline(draw, 344, y0, 368, fill=GREY)
    vline(draw, 680, y0, 368, fill=GREY)
    hline(draw, 24, 1000, 368, width=2)


def draw_medium(draw):
    x0, x1 = 20, 1004
    gap = 8
    pw = (x1 - x0 - 3 * gap) // 4
    ph, vgap = 78, 6
    y0 = 374
    for i, (num, region, head, deck, tag, src, kind) in enumerate(MEDIUM):
        row, col = divmod(i, 4)
        px = x0 + col * (pw + gap)
        py = y0 + row * (ph + vgap)
        draw.rectangle([px, py, px + pw, py + ph], fill=LIGHT,
                       outline=(200, 193, 176), width=1)
        MINI_SCENES[kind](draw, px + 5, py + 8)
        tx = px + 74
        tw = px + pw - 6 - tx
        draw.text((tx, py + 5), "%d  %s" % (num, region),
                  font=font(SANS_B, 9), fill=RED)
        tf = font(SANS_B, 8)
        tagstr = "%s · %s" % (tag, src)
        draw.text((px + pw - 6 - text_w(draw, tagstr, tf), py + 5),
                  tagstr, font=tf, fill=RED)
        hf = font(SERIF_B, 12)
        yy = py + 18
        for ln in wrap(draw, head, hf, tw)[:2]:
            draw.text((tx, yy), ln, font=hf, fill=INK)
            yy += 14
        df = font(SANS, 9)
        for ln in wrap(draw, deck, df, tw)[:2]:
            draw.text((tx, yy), ln, font=df, fill=(60, 58, 52))
            yy += 11
    hline(draw, 20, 1004, 626, width=2)


def project(lon, lat, mx0, my0, sx, sy, lat_top=80.0):
    return (mx0 + (lon + 180.0) * sx, my0 + (lat_top - lat) * sy)


def draw_map(draw):
    mx0, my0, mw, mh = 24, 632, 668, 156
    mx1, my1 = mx0 + mw, my0 + mh
    draw.rectangle([mx0, my0, mx1, my1], fill=MAP_SEA, outline=RULE, width=1)
    sx = mw / 360.0
    sy = mh / 140.0  # lat 80 .. -60
    for poly in CONTINENTS:
        pts = [project(lon, lat, mx0, my0, sx, sy) for lon, lat in poly]
        draw.polygon(pts, fill=MAP_LAND, outline=(120, 128, 118))
    for lon in range(-150, 181, 30):
        x = mx0 + (lon + 180.0) * sx
        draw.line([(x, my0), (x, my1)], fill=(210, 217, 212), width=1)
    df = font(SANS_B, 10)
    for lon, lat, n in DOTS:
        if n in LEADERS:
            dlon, dlat = LEADERS[n]
            tx, ty = project(lon, lat, mx0, my0, sx, sy)
            cx, cy = project(dlon, dlat, mx0, my0, sx, sy)
            draw.line([(tx, ty), (cx, cy)], fill=RED, width=1)
            draw.ellipse([tx - 2, ty - 2, tx + 2, ty + 2], fill=RED)
        else:
            cx, cy = project(lon, lat, mx0, my0, sx, sy)
        r = 8
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED,
                     outline=(255, 255, 255), width=2)
        s = str(n)
        draw.text((cx - text_w(draw, s, df) / 2, cy - 7), s, font=df,
                  fill=(255, 255, 255))
    draw.text((mx0 + 6, my0 + 6), "WHERE IT HAPPENED — 12 PLACES",
              font=font(SANS_B, 9), fill=GREY)
    lx = 712
    draw.text((lx, 632), "ON THE MAP", font=font(SANS_B, 12), fill=RED)
    lf = font(SANS, 11)
    y = 650
    for n, label in MAP_LEGEND:
        draw.text((lx, y), n + ".", font=font(SANS_B, 11), fill=RED)
        draw.text((lx + 26, y), label, font=lf, fill=INK)
        y += 12
    hline(draw, 24, 1000, 794, width=2)


def draw_briefs(draw):
    draw.text((20, 800), "ALSO ON SATURDAY 21 NOVEMBER — THE REST OF THE DAY",
              font=font(SANS_B, 12), fill=RED)
    cols_x = [20, 352, 684]
    col_w = 318
    row_h = 12
    y0 = 816
    nf = font(SANS_B, 10)
    bf = font(SANS, 9)
    for idx, (num, region, head, tag, src) in enumerate(BRIEFS):
        col, row = divmod(idx, 9)
        x = cols_x[col]
        y = y0 + row * row_h
        suffix = " — %s · %s" % (tag, src)
        nx = x + (16 if num < 10 else 20)
        avail = col_w - (nx - x) - 4 - text_w(draw, suffix, bf)
        h = head
        while h and text_w(draw, h + "…", bf) > avail:
            h = h.rsplit(" ", 1)[0] if " " in h else h[:-1]
        rest = h + ("…" if h != head else "") + suffix
        draw.text((x, y), str(num), font=nf, fill=RED)
        draw.text((nx, y), rest, font=bf, fill=INK)
    hline(draw, 20, 1004, 928, width=2)


def draw_bottom(draw):
    # DATE CHECK box
    bx0, bx1 = 20, 640
    by0 = 932
    draw.rectangle([bx0, by0, bx1, 1004], outline=RED, width=2)
    draw.text((bx0 + 10, by0 + 5), "DATE CHECK",
              font=font(SANS_B, 12), fill=RED)
    df = font(SANS, 10)
    lines = [
        "Every story here happened, or was first reported, on Sat 21 Nov 2026.",
        "LEFT OUT (other dates): ICJ Myanmar ruling (19 Nov) · Shenzhen summit (19 Nov) ·",
        "Anthropic IPO debut (19 Nov) · measles status lost (19–20 Nov) · air-taxi demo (20 Nov).",
        "NOT YET: COP31 deal (in overtime) · Nepal PM's India visit (22–23 Nov) · Spain vote (29 Nov).",
    ]
    y = by0 + 21
    for ln in lines:
        draw.text((bx0 + 10, y), ln, font=df, fill=INK)
        y += 11
    # BY THE NUMBERS box
    nx0, nx1 = 656, 1004
    draw.rectangle([nx0, by0, nx1, 1004], fill=LIGHT, outline=RULE, width=1)
    draw.text((nx0 + 10, by0 + 5), "BY THE NUMBERS — FRI 20 NOV CLOSE",
              font=font(SANS_B, 12), fill=INK)
    nf = font(SANS_B, 10)
    nums = [
        "S&P 500 in correction · Nasdaq erases 2026 gains",
        "Nikkei −5.1% · SoftBank −16% (week)",
        "Brent ~$91 · Gold −4.2% (week) · US 10-yr above 5%",
        "Anthropic −10%+ at open, day after record debut",
    ]
    y = by0 + 21
    for ln in nums:
        draw.text((nx0 + 10, y), ln, font=nf, fill=INK)
        y += 12
    # footer
    ff = font(SANS, 9)
    foot = ("Sources: BBC, Reuters, AP, AFP, The Guardian, national outlets — "
            "full list in the repo SOURCES.md. Figures as reported 21 Nov 2026.")
    draw.text((20, 1009), foot, font=ff, fill=GREY)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "news.png"
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    draw_masthead(draw)
    draw_timeline(draw)
    draw_heroes(draw)
    draw_medium(draw)
    draw_map(draw)
    draw_briefs(draw)
    draw_bottom(draw)
    img.save(out, "PNG", optimize=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
