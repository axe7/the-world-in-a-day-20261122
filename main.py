#!/usr/bin/env python3
"""Broadsheet renderer v2 — a typeset daily-news front page.

Implements the 19 Nov 2026 winner pattern for make.fun news-image
bounties: quantified strap + giant serif date, UTC timeline strip,
THE DAY IN NUMBERS bar, illustrated leads + numbered cards with
verification chips, dotted world map with pins + region tally,
numbered briefs, DATE CHECK box, sources footer. Anti-aliased type
(PIL + real TTF fonts), cream paper, no bitmap fonts.

Deterministic: no randomness, no clock, no network.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

S = 2  # supersample factor; final image is 1024x1024
W = 1024

PAPER = (248, 244, 233)
INK = (24, 23, 20)
SOFT = (70, 66, 60)
RED = (163, 32, 28)
RULE = (36, 34, 30)
CHIP_BG = {
    "CONFIRMED": (30, 84, 52),
    "OFFICIALS": (52, 74, 110),
    "REPORTED": (58, 56, 52),
    "FORECAST": (150, 92, 20),
    "CLAIM": (150, 40, 34),
    "ESTIMATE": (96, 74, 130),
}

FONT_DIR = "/usr/share/fonts/truetype/noto"
DEJA = "/usr/share/fonts/truetype/dejavu"


def _font(name, deja, size):
    p = os.path.join(FONT_DIR, name)
    if not os.path.exists(p):
        p = os.path.join(DEJA, deja)
    return ImageFont.truetype(p, int(size * S))


def F(kind, size):
    if kind == "display":
        return _font("NotoSerifDisplay-Black.ttf", "DejaVuSerif-Bold.ttf", size)
    if kind == "serif_b":
        return _font("NotoSerif-Bold.ttf", "DejaVuSerif-Bold.ttf", size)
    if kind == "serif":
        return _font("NotoSerif-Regular.ttf", "DejaVuSerif.ttf", size)
    if kind == "sans_b":
        return _font("NotoSans-Bold.ttf", "DejaVuSans-Bold.ttf", size)
    if kind == "sans_sb":
        return _font("NotoSans-SemiBold.ttf", "DejaVuSans-Bold.ttf", size)
    if kind == "sans":
        return _font("NotoSans-Regular.ttf", "DejaVuSans.ttf", size)
    raise ValueError(kind)


class Page:
    def __init__(self):
        self.img = Image.new("RGB", (W * S, W * S), PAPER)
        self.d = ImageDraw.Draw(self.img)

    def rect(self, x, y, w, h, fill):
        self.d.rectangle([x * S, y * S, (x + w) * S, (y + h) * S], fill=fill)

    def line(self, x, y, x2, y2, fill=INK, wd=1):
        self.d.line([x * S, y * S, x2 * S, y2 * S], fill=fill, width=max(1, int(wd * S)))

    def text(self, x, y, s, kind, size, fill=INK, anchor="la"):
        self.d.text((x * S, y * S), s, font=F(kind, size), fill=fill, anchor=anchor)

    def tw(self, s, kind, size):
        return self.d.textlength(s, font=F(kind, size)) / S

    def wrap(self, s, kind, size, width):
        words, lines, cur = s.split(), [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if self.tw(t, kind, size) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def rich_wrap(self, segs, size, width):
        """segs: [(text, kind, fill)] -> lines of [(text, kind, fill)]."""
        words = []
        for txt, kind, fill in segs:
            for wd in txt.split():
                words.append((wd, kind, fill))
        lines, cur, cur_w = [], [], 0.0
        sp = self.tw(" ", "sans", size)
        for wd, kind, fill in words:
            ww = self.tw(wd, kind, size)
            add = ww if not cur else ww + sp
            if cur and cur_w + add > width:
                lines.append(cur)
                cur, cur_w = [(wd, kind, fill)], ww
            else:
                cur.append((wd, kind, fill))
                cur_w += add
        if cur:
            lines.append(cur)
        return lines

    def draw_rich(self, x, y, line, size):
        cx = x
        sp = self.tw(" ", "sans", size)
        for wd, kind, fill in line:
            self.text(cx, y, wd, kind, size, fill)
            cx += self.tw(wd, kind, size) + sp
        return cx

    def fit(self, s, kind, size, width, min_size=7):
        while size > min_size and self.tw(s, kind, size) > width:
            size -= 0.5
        if self.tw(s, kind, size) > width:  # truncate with ellipsis
            while s and self.tw(s + "…", kind, size) > width:
                s = s[:-1]
            s = s + "…"
        return size, s

    def finish(self, out):
        self.img = self.img.resize((W, W), Image.LANCZOS)
        self.img.save(out, "PNG", optimize=True)
        return out


# ---------------------------------------------------------------- scenes
def _sky(p, x, y, w, h, top, bot):
    steps = 24
    for i in range(steps):
        t = i / steps
        c = tuple(int(top[j] + (bot[j] - top[j]) * t) for j in range(3))
        p.rect(x, y + h * i / steps, w, h / steps + 1, c)


def sc_missiles(p, x, y, w, h):
    _sky(p, x, y, w, h, (28, 34, 58), (96, 74, 70))
    for i in range(14):
        sx = x + (i * 37) % max(1, int(w))
        sy = y + (i * 23) % max(1, int(h * 0.5))
        p.rect(sx, sy, 1.6, 1.6, (230, 220, 190))
    for bx, bw, bh in [(0, .16, .34), (.15, .12, .26), (.28, .18, .42),
                       (.47, .13, .3), (.61, .17, .38), (.79, .12, .27), (.9, .1, .33)]:
        p.rect(x + bx * w, y + h - bh * h, bw * w, bh * h, (20, 20, 26))
    for i in range(9):
        wx = x + ((i * 53) % 90 + 4) / 100 * w
        wy = y + h - ((i * 29) % 30 + 6) / 100 * h
        p.rect(wx, wy, 2, 2.6, (250, 205, 110))
    for (sx, sy, ex, ey) in [(0.06, 0.04, 0.34, 0.52), (0.3, 0.0, 0.52, 0.46),
                             (0.62, 0.02, 0.78, 0.4), (0.86, 0.08, 0.95, 0.42)]:
        p.line(x + sx * w, y + sy * h, x + ex * w, y + ey * h, (255, 190, 120), 1.6)
        p.d.ellipse([(x + ex * w - 3) * S, (y + ey * h - 3) * S,
                     (x + ex * w + 3) * S, (y + ey * h + 3) * S], fill=(255, 160, 80))


def sc_bars_down(p, x, y, w, h, data=None):
    p.rect(x, y, w, h, (244, 240, 230))
    data = data or [("NIKKEI", -4.85), ("KOSPI", -4.7), ("TAIEX", -6.4)]
    bw = w / (len(data) * 1.6)
    base = y + h * 0.24
    p.line(x + 4, base, x + w - 4, base, INK, 1.2)
    for i, (lab, v) in enumerate(data):
        bx = x + w * (0.12 + i * 0.3)
        bh = abs(v) / 7.0 * h * 0.62
        p.rect(bx, base, bw, bh, RED)
        p.text(bx + bw / 2, base + bh + 3, f"{v:g}%", "sans_b", max(7, h * 0.11), RED, "ma")
        p.text(bx + bw / 2, base - h * 0.2, lab, "sans_b", max(6.5, h * 0.1), INK, "ma")


def sc_bars_up(p, x, y, w, h, data=None):
    p.rect(x, y, w, h, (244, 240, 230))
    base = y + h * 0.82
    p.line(x + 4, base, x + w - 4, base, INK, 1.2)
    bw = w * 0.3
    bx = x + w * 0.35
    bh = h * 0.55
    p.rect(bx, base - bh, bw, bh, (30, 84, 52))
    p.text(bx + bw / 2, base - bh - h * 0.2, "$2.36bn", "sans_b", max(8, h * 0.13), (30, 84, 52), "ma")


def sc_storm(p, x, y, w, h):
    _sky(p, x, y, w, h, (70, 88, 104), (150, 158, 156))
    cx, cy = x + w * 0.5, y + h * 0.46
    for r in range(int(min(w, h) * 0.42), 4, -6):
        a0 = (r * 37) % 360
        p.d.arc([(cx - r) * S, (cy - r * 0.62) * S, (cx + r) * S, (cy + r * 0.62) * S],
                start=a0, end=a0 + 250, fill=(235, 238, 236), width=int(2.2 * S))
    p.rect(x, y + h * 0.8, w, h * 0.2, (52, 84, 96))
    for i in range(5):
        rx = x + (i * 41) % max(1, int(w))
        p.line(rx, y + h * 0.66, rx - 4, y + h * 0.78, (220, 228, 230), 1.2)


def sc_climate(p, x, y, w, h):
    _sky(p, x, y, w, h, (240, 214, 160), (246, 236, 214))
    cx, cy, r = x + w * 0.3, y + h * 0.42, min(w, h) * 0.24
    p.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=(232, 150, 52))
    for a in range(0, 360, 45):
        x1 = cx + math.cos(math.radians(a)) * r * 1.25
        y1 = cy + math.sin(math.radians(a)) * r * 1.25
        x2 = cx + math.cos(math.radians(a)) * r * 1.55
        y2 = cy + math.sin(math.radians(a)) * r * 1.55
        p.line(x1, y1, x2, y2, (232, 150, 52), 2)
    p.rect(x + w * 0.52, y + h * 0.62, w * 0.42, h * 0.1, (90, 70, 50))
    for i, c in enumerate([(52, 74, 110), (163, 32, 28), (30, 84, 52), (176, 132, 44)]):
        fx = x + w * (0.56 + i * 0.1)
        p.line(fx, y + h * 0.34, fx, y + h * 0.62, INK, 1.2)
        p.rect(fx, y + h * 0.34, w * 0.06, h * 0.12, c)


def sc_game(p, x, y, w, h):
    _sky(p, x, y, w, h, (44, 40, 78), (150, 70, 110))
    p.rect(x, y + h * 0.72, w, h * 0.28, (30, 28, 40))
    cw_, ch_ = w * 0.62, h * 0.2
    cx0, cy0 = x + w * 0.19, y + h * 0.52
    p.d.polygon([(cx0 * S, (cy0 + ch_) * S), (cx0 * S, cy0 * S),
                 ((cx0 + cw_ * 0.3) * S, (cy0 - ch_ * 0.55) * S),
                 ((cx0 + cw_ * 0.72) * S, (cy0 - ch_ * 0.55) * S),
                 ((cx0 + cw_) * S, cy0 * S), ((cx0 + cw_) * S, (cy0 + ch_) * S)],
                fill=(216, 84, 60))
    for wx in (0.18, 0.82):
        p.d.ellipse([((cx0 + cw_ * wx - 7) * S), ((cy0 + ch_ - 5) * S),
                     ((cx0 + cw_ * wx + 7) * S), ((cy0 + ch_ + 9) * S)], fill=(16, 16, 18))
    p.text(x + w * 0.97, y + h * 0.1, "VI", "display", max(10, h * 0.3), (255, 214, 120), "ra")


def sc_protest(p, x, y, w, h):
    _sky(p, x, y, w, h, (196, 205, 214), (228, 226, 216))
    p.rect(x, y + h * 0.78, w, h * 0.22, (120, 116, 108))
    # deterministic pseudo-random crowd (LCG, fixed seed)
    seed = 7
    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) % (2 ** 31)
        return seed / 2 ** 31
    for i in range(26):
        px_ = x + (0.03 + rnd() * 0.92) * w
        py_ = y + (0.52 + rnd() * 0.2) * h
        r = h * 0.045
        p.d.ellipse([(px_ - r) * S, (py_ - r) * S, (px_ + r) * S, (py_ + r) * S], fill=(40, 40, 44))
        p.rect(px_ - r * 0.8, py_ + r, r * 1.6, h * 0.14, (40, 40, 44))
    for i, c in enumerate([(163, 32, 28), (52, 74, 110), (176, 132, 44)]):
        px_ = x + w * (0.2 + i * 0.28)
        p.line(px_, y + h * 0.52, px_, y + h * 0.3, INK, 1.2)
        p.rect(px_ - w * 0.07, y + h * 0.16, w * 0.14, h * 0.15, c)


def sc_flags(p, x, y, w, h):
    p.rect(x, y, w, h, (238, 240, 242))
    cx, cy, r = x + w * 0.28, y + h * 0.48, min(w, h) * 0.3
    p.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=(38, 62, 128))
    for a in range(12):
        sx = cx + math.cos(math.radians(a * 30)) * r * 0.68
        sy = cy + math.sin(math.radians(a * 30)) * r * 0.68
        p.d.ellipse([(sx - 2) * S, (sy - 2) * S, (sx + 2) * S, (sy + 2) * S], fill=(250, 205, 60))
    fx, fy, fw, fh = x + w * 0.58, y + h * 0.22, w * 0.34, h * 0.52
    p.rect(fx, fy, fw, fh, (38, 62, 128))
    p.line(fx, fy, fx + fw, fy + fh, (250, 250, 250), 3)
    p.line(fx + fw, fy, fx, fy + fh, (250, 250, 250), 3)
    p.rect(fx + fw * 0.42, fy, fw * 0.16, fh, (250, 250, 250))
    p.rect(fx, fy + fh * 0.42, fw, fh * 0.16, (250, 250, 250))
    p.rect(fx + fw * 0.45, fy, fw * 0.1, fh, RED)
    p.rect(fx, fy + fh * 0.45, fw, fh * 0.1, RED)


def sc_art(p, x, y, w, h):
    p.rect(x, y, w, h, (232, 226, 214))
    fx, fy, fw, fh = x + w * 0.3, y + h * 0.1, w * 0.4, h * 0.8
    p.rect(fx - 4, fy - 4, fw + 8, fh + 8, (120, 92, 40))
    p.rect(fx, fy, fw, fh, (34, 44, 66))
    for r in range(5, int(fw * 0.42), 6):
        p.d.arc([(fx + fw * 0.5 - r) * S, (fy + fh * 0.4 - r * 0.6) * S,
                 (fx + fw * 0.5 + r) * S, (fy + fh * 0.4 + r * 0.6) * S],
                start=20, end=300, fill=(240, 214, 120), width=int(1.6 * S))
    p.d.ellipse([(fx + fw * 0.68) * S, (fy + fh * 0.14) * S,
                 (fx + fw * 0.86) * S, (fy + fh * 0.3) * S], fill=(246, 238, 200))


def sc_ship(p, x, y, w, h):
    _sky(p, x, y, w, h, (170, 196, 210), (226, 232, 226))
    p.rect(x, y + h * 0.62, w, h * 0.38, (52, 96, 120))
    hx, hy = x + w * 0.16, y + h * 0.52
    p.d.polygon([(hx * S, hy * S), ((hx + w * 0.62) * S, hy * S),
                 ((hx + w * 0.54) * S, (hy + h * 0.12) * S), ((hx + w * 0.08) * S, (hy + h * 0.12) * S)],
                fill=(40, 44, 52))
    p.rect(hx + w * 0.4, hy - h * 0.2, w * 0.1, h * 0.2, (226, 228, 226))
    p.line(hx + w * 0.18, hy, hx + w * 0.18, hy - h * 0.3, INK, 1.6)
    p.line(hx + w * 0.18, hy - h * 0.3, hx + w * 0.34, hy - h * 0.06, INK, 1.2)


def sc_tanker(p, x, y, w, h):
    sc_ship(p, x, y, w, h)
    p.rect(x + w * 0.3, y + h * 0.44, w * 0.3, h * 0.07, (163, 32, 28))


def sc_door(p, x, y, w, h):
    p.rect(x, y, w, h, (226, 220, 204))
    dx, dy, dw, dh = x + w * 0.38, y + h * 0.12, w * 0.24, h * 0.76
    p.rect(dx, dy, dw, dh, (96, 74, 52))
    p.d.ellipse([(dx + dw * 0.72) * S, (dy + dh * 0.5) * S,
                 (dx + dw * 0.88) * S, (dy + dh * 0.58) * S], fill=(176, 132, 44))
    p.rect(x + w * 0.08, y + h * 0.2, w * 0.16, h * 0.22, (30, 84, 52))
    p.rect(x + w * 0.76, y + h * 0.2, w * 0.16, h * 0.22, (163, 32, 28))


def sc_convoy(p, x, y, w, h):
    _sky(p, x, y, w, h, (206, 198, 178), (232, 226, 210))
    p.rect(x, y + h * 0.68, w, h * 0.32, (150, 138, 116))
    for i in range(3):
        vx, vy = x + w * (0.08 + i * 0.3), y + h * 0.5
        p.rect(vx, vy, w * 0.22, h * 0.16, (86, 92, 74))
        p.rect(vx + w * 0.05, vy - h * 0.09, w * 0.1, h * 0.09, (86, 92, 74))
        for wx in (0.04, 0.16):
            p.d.ellipse([(vx + w * wx) * S, (vy + h * 0.13) * S,
                         (vx + w * (wx + 0.05)) * S, (vy + h * 0.21) * S], fill=(24, 24, 26))


def sc_boat(p, x, y, w, h):
    _sky(p, x, y, w, h, (186, 210, 220), (232, 236, 226))
    p.rect(x, y + h * 0.55, w, h * 0.45, (58, 104, 128))
    bx, by = x + w * 0.2, y + h * 0.5
    p.d.polygon([(bx * S, by * S), ((bx + w * 0.6) * S, by * S),
                 ((bx + w * 0.48) * S, (by + h * 0.14) * S), ((bx + w * 0.1) * S, (by + h * 0.14) * S)],
                fill=(120, 84, 56))
    for i in range(6):
        px_ = bx + w * (0.12 + i * 0.07)
        p.d.ellipse([(px_ - 3) * S, (by - h * 0.1) * S, (px_ + 3) * S, (by - h * 0.02) * S], fill=(40, 38, 36))
        p.rect(px_ - 2.6, by - h * 0.03, 5.2, h * 0.05, (40, 38, 36))


def sc_mountains(p, x, y, w, h):
    _sky(p, x, y, w, h, (188, 204, 222), (236, 238, 230))
    for (mx, mw, mh, c) in [(0.0, 0.55, 0.62, (110, 124, 140)), (0.4, 0.6, 0.78, (86, 100, 120))]:
        p.d.polygon([((x + mx * w) * S, (y + h) * S), ((x + (mx + mw / 2) * w) * S, (y + h - mh * h) * S),
                     ((x + (mx + mw) * w) * S, (y + h) * S)], fill=c)
        p.d.polygon([((x + (mx + mw / 2) * w - mw * w * 0.09) * S, (y + h - mh * h + mh * h * 0.22) * S),
                     ((x + (mx + mw / 2) * w) * S, (y + h - mh * h) * S),
                     ((x + (mx + mw / 2) * w + mw * w * 0.09) * S, (y + h - mh * h + mh * h * 0.22) * S)],
                    fill=(248, 248, 246))


def sc_quake(p, x, y, w, h):
    p.rect(x, y, w, h, (214, 200, 178))
    pts = [(0.05, 0.1), (0.3, 0.3), (0.42, 0.26), (0.55, 0.5), (0.5, 0.66), (0.68, 0.8), (0.9, 0.92)]
    for i in range(len(pts) - 1):
        p.line(x + pts[i][0] * w, y + pts[i][1] * h, x + pts[i + 1][0] * w, y + pts[i + 1][1] * h, (60, 50, 40), 2.4)
    p.d.polygon([((x + 0.55 * w) * S, (y + h * 0.4) * S), ((x + 0.75 * w) * S, (y + h * 0.02) * S),
                 ((x + 0.95 * w) * S, (y + h * 0.4) * S)], fill=(110, 124, 140))


def sc_cyber(p, x, y, w, h):
    p.rect(x, y, w, h, (30, 36, 48))
    for i in range(6):
        p.line(x + 6, y + h * (0.14 + i * 0.14), x + w * (0.4 + (i % 3) * 0.18), y + h * (0.14 + i * 0.14),
               (86, 200, 140) if i % 2 else (96, 160, 220), 1.6)
    lx, ly = x + w * 0.66, y + h * 0.3
    p.d.rounded_rectangle([lx * S, ly * S, (lx + w * 0.2) * S, (ly + h * 0.36) * S],
                          radius=4 * S, fill=(214, 178, 84))
    p.d.arc([(lx + w * 0.045) * S, (ly - h * 0.16) * S, (lx + w * 0.155) * S, (ly + h * 0.14) * S],
            start=180, end=360, fill=(214, 178, 84), width=int(3 * S))


def sc_court(p, x, y, w, h):
    p.rect(x, y, w, h, (230, 226, 216))
    p.d.polygon([(x + w * 0.08) * S, (y + h * 0.2) * S, (x + w * 0.5) * S, (y + h * 0.05) * S,
                 (x + w * 0.92) * S, (y + h * 0.2) * S], fill=(120, 116, 108))
    for i in range(4):
        cx = x + w * (0.16 + i * 0.2)
        p.rect(cx, y + h * 0.26, w * 0.07, h * 0.5, (150, 146, 138))
    p.rect(x + w * 0.08, y + h * 0.78, w * 0.84, h * 0.1, (120, 116, 108))


def sc_globe(p, x, y, w, h):
    p.rect(x, y, w, h, (238, 240, 238))
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) * 0.42
    p.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], outline=(52, 96, 120), width=int(2 * S))
    for t in (-0.55, 0, 0.55):
        p.d.ellipse([(cx - r * abs(math.cos(math.asin(t)))) * S, (cy - r) * S,
                     (cx + r * abs(math.cos(math.asin(t)))) * S, (cy + r) * S],
                    outline=(52, 96, 120), width=int(1 * S))
        yy = cy + t * r
        p.line(cx - r * math.sqrt(1 - t * t), yy, cx + r * math.sqrt(1 - t * t), yy, (52, 96, 120), 1)


SCENES = {
    "missiles": sc_missiles, "bars_down": sc_bars_down, "bars_up": sc_bars_up,
    "storm": sc_storm, "climate": sc_climate, "game": sc_game,
    "protest": sc_protest, "flags": sc_flags, "art": sc_art, "ship": sc_ship,
    "tanker": sc_tanker, "door": sc_door, "convoy": sc_convoy, "boat": sc_boat,
    "mountains": sc_mountains, "quake": sc_quake, "cyber": sc_cyber,
    "court": sc_court, "globe": sc_globe,
}


def draw_scene(p, name, x, y, w, h, story):
    fn = SCENES.get(name, sc_globe)
    if name in ("bars_down", "bars_up"):
        fn(p, x, y, w, h, story.get("chart"))
    else:
        fn(p, x, y, w, h)
    p.d.rectangle([x * S, y * S, (x + w) * S, (y + h) * S], outline=(120, 114, 104), width=int(1 * S))


# ------------------------------------------------------------------- map
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-108, 73), (-95, 79), (-86, 69), (-80, 73), (-76, 71), (-66, 62), (-56, 52), (-65, 45), (-70, 42), (-74, 39), (-76, 35), (-79, 33), (-80, 27), (-82, 28), (-84, 30), (-89, 29), (-94, 29), (-97, 26), (-97, 22), (-94, 18), (-90, 15), (-86, 13), (-83, 9), (-78, 8), (-80, 10), (-84, 15), (-88, 14), (-92, 15), (-97, 16), (-102, 18), (-105, 20), (-109, 23), (-112, 27), (-115, 30), (-118, 33), (-122, 37), (-124, 44), (-127, 51), (-133, 56), (-148, 60), (-162, 61)],
    [(-45, 60), (-32, 68), (-22, 70), (-20, 76), (-28, 81), (-45, 82), (-58, 78), (-55, 71), (-53, 64), (-52, 60)],
    [(-78, 7), (-72, 12), (-64, 11), (-56, 6), (-51, 4), (-50, 0), (-44, -3), (-35, -8), (-38, -14), (-40, -21), (-47, -26), (-51, -32), (-56, -36), (-60, -40), (-63, -44), (-66, -49), (-68, -54), (-71, -54), (-74, -50), (-74, -43), (-73, -36), (-71, -29), (-70, -19), (-74, -15), (-78, -8), (-81, -4), (-80, 1), (-77, 4)],
    [(-17, 15), (-11, 27), (-7, 33), (-2, 35), (6, 37), (10, 37), (12, 34), (19, 32), (28, 31), (32, 31), (34, 28), (37, 23), (39, 20), (41, 16), (43, 12), (46, 11), (51, 12), (49, 6), (44, 0), (41, -6), (40, -12), (38, -18), (36, -22), (34, -26), (29, -32), (24, -34), (19, -35), (17, -31), (15, -26), (13, -19), (12, -10), (11, -4), (9, 0), (9, 4), (-4, 5), (-8, 5), (-13, 8), (-17, 12)],
    [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 49), (3, 51), (7, 54), (8, 56), (7, 58), (10, 59), (5, 60), (5, 62), (11, 65), (16, 68), (22, 70), (30, 70), (38, 67), (44, 66), (40, 60), (36, 55), (31, 50), (29, 47), (24, 41), (20, 40), (16, 38), (13, 41), (10, 44), (7, 44), (3, 43), (0, 39), (-2, 37)],
    [(-5, 50), (-3, 53), (-4, 55), (-6, 57), (-8, 55), (-7, 53), (-6, 51)],
    [(-22, 64), (-15, 64), (-14, 66), (-21, 66)],
    [(30, 41), (33, 46), (32, 50), (35, 56), (38, 62), (42, 66), (50, 68), (60, 69), (70, 72), (80, 73), (90, 75), (100, 77), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70), (160, 70), (170, 66), (178, 65), (172, 61), (163, 60), (158, 53), (151, 46), (143, 50), (141, 44), (140, 39), (137, 35), (133, 34), (130, 33), (127, 31), (123, 29), (121, 26), (117, 24), (112, 21), (109, 19), (108, 14), (107, 10), (105, 5), (103, 2), (101, 6), (99, 10), (97, 14), (94, 17), (92, 19), (90, 22), (87, 21), (85, 19), (81, 15), (79, 10), (77, 8), (75, 12), (73, 17), (71, 21), (68, 23), (65, 25), (60, 25), (56, 26), (52, 25), (49, 27), (49, 30), (53, 29), (56, 28), (58, 27), (60, 25), (57, 26), (54, 24), (51, 24), (48, 27), (44, 29), (42, 36), (36, 36), (31, 36)],
    [(95, 5), (100, 0), (105, -3), (110, -4), (116, -3), (121, -2), (126, -1), (131, 0), (136, -2), (141, -4), (146, -6), (147, -9), (142, -8), (136, -6), (130, -3), (124, -4), (118, -6), (112, -7), (106, -6), (100, -3)],
    [(130, 31), (132, 33), (135, 34), (138, 35), (140, 36), (141, 39), (142, 43), (143, 45), (141, 44), (139, 39), (136, 35), (132, 33)],
    [(113, -22), (114, -28), (115, -33), (118, -35), (124, -33), (129, -32), (132, -32), (135, -35), (138, -36), (140, -38), (145, -38), (147, -39), (150, -37), (153, -32), (153, -27), (151, -24), (147, -19), (143, -15), (142, -11), (138, -12), (136, -15), (135, -12), (132, -11), (129, -13), (125, -15), (121, -18), (117, -20)],
    [(167, -45), (171, -42), (173, -40), (175, -37), (177, -38), (175, -41), (171, -44), (168, -46)],
]


def _in_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xin = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < xin:
                inside = not inside
    return inside


def draw_map(p, x, y, w, h, pins):
    def px(lon):
        return x + (lon + 178) / 356 * w

    def py(lat):
        return y + (80 - lat) / 138 * h

    step = 5.4
    cols = int(w / step)
    rows = int(h / step)
    for r in range(rows):
        lat = 80 - (r + 0.5) * 138 / rows
        for c in range(cols):
            lon = -178 + (c + 0.5) * 356 / cols
            for poly in CONTINENTS:
                if _in_poly(lon, lat, poly):
                    cx, cy = x + (c + 0.5) * step, y + (r + 0.5) * step
                    p.d.ellipse([(cx - 1.5) * S, (cy - 1.5) * S, (cx + 1.5) * S, (cy + 1.5) * S],
                                fill=(168, 160, 146))
                    break
    for (n, lon, lat) in pins:
        cx, cy = px(lon), py(lat)
        p.d.ellipse([(cx - 6.4) * S, (cy - 6.4) * S, (cx + 6.4) * S, (cy + 6.4) * S], fill=RED)
        p.text(cx, cy - 5.4, str(n), "sans_b", 8, (255, 255, 255), "ma")


# ------------------------------------------------------------------ cards
def chip(p, x, y, ctype, src):
    label = f"{ctype}·{src}"
    fs = 7.5
    wch = p.tw(label, "sans_b", fs) + 8
    p.d.rounded_rectangle([x * S, y * S, (x + wch) * S, (y + 11) * S], radius=2 * S,
                          fill=CHIP_BG.get(ctype, (58, 56, 52)))
    p.text(x + 4, y + 1.6, label, "sans_b", fs, (252, 250, 244))
    return wch


def card(p, st, x, y, w, illo_h, head_size, sub_size, max_sub=3):
    n = st["n"]
    chip_label = f"{st['chip']}·{st['src']}"
    chip_w = p.tw(chip_label, "sans_b", 7.5) + 8
    chip(p, x + w - chip_w, y, st["chip"], st["src"])
    p.d.ellipse([x * S, y * S, (x + 15) * S, (y + 15) * S], fill=INK)
    p.text(x + 7.5, y + 2.2, str(n), "sans_b", 9, PAPER, "ma")
    tag_w = max(10, w - 19 - chip_w - 5)
    _, tag = p.fit(st["tag"].upper(), "sans_b", 8, tag_w)
    p.text(x + 19, y + 2.4, tag, "sans_b", 8, SOFT)
    draw_scene(p, st["scene"], x, y + 17, w, illo_h, st)
    hy = y + 17 + illo_h + 4
    hs, head = p.fit(st["head"], "serif_b", head_size, w * 2, 10)
    # shrink headline until it wraps to <=2 lines
    while len(p.wrap(head, "serif_b", hs, w)) > 2 and hs > 10:
        hs -= 0.5
    for ln in p.wrap(head, "serif_b", hs, w)[:2]:
        p.text(x, hy, ln, "serif_b", hs, INK)
        hy += hs * 1.16
    for ln in p.wrap(st["sub"], "sans", sub_size, w)[:max_sub]:
        p.text(x, hy + 1, ln, "sans", sub_size, SOFT)
        hy += sub_size * 1.28


# ------------------------------------------------------------------ render
def render(day, out_path):
    p = Page()
    stories = day["stories"]
    for i, st in enumerate(stories):
        st["n"] = i + 1
    briefs = day["briefs"]
    total = len(stories) + len(briefs)
    regions = {}
    fields = set()
    for st in stories + briefs:
        regions[st["region"]] = regions.get(st["region"], 0) + 1
        fields.add(st["field"])
    M = 26
    CW = W - 2 * M
    y = 12
    # strap
    p.text(M, y, day["strap_left"], "sans_b", 11.5, INK)
    ncont = len([r for r in regions if r != "Global"])
    tally = (f"{total} STORIES · {ncont} CONTINENTS · {len(fields)} FIELDS"
             f" · EVERY ONE FROM THIS {day['weekday']}")
    p.text(W - M, y, tally, "sans_b", 11.5, RED, "ra")
    y += 17
    p.line(M, y, W - M, y, RULE, 2.4)
    y += 5
    # date
    ds, date_s = p.fit(day["date_long"], "display", 54, CW, 30)
    p.text(W / 2, y, date_s, "display", ds, INK, "ma")
    y += ds + 7
    p.line(M, y, W - M, y, RULE, 1.1)
    y += 4
    # timeline: label block + 8 columns
    p.text(M, y + 1, "THE DAY", "sans_b", 8.5, RED)
    p.text(M, y + 11, "IN UTC", "sans_b", 8.5, RED)
    bw = (CW - 66 - 7 * 8) / 8
    for i, (lab, txt) in enumerate(day["timeline"][:8]):
        bx = M + 66 + i * (bw + 8)
        p.text(bx, y, lab, "sans_b", 8, INK)
        for li, ln in enumerate(p.wrap(txt, "sans", 8, bw)[:2]):
            p.text(bx, y + 10.5 + li * 10, ln, "sans", 8, SOFT)
    y += 33
    p.line(M, y, W - M, y, RULE, 1.1)
    y += 4
    # numbers bar
    p.rect(M, y, CW, 42, INK)
    nums = day["numbers"]
    nw = CW / len(nums)
    for i, (big, lab) in enumerate(nums):
        bx = M + i * nw
        bs, big_s = p.fit(big, "serif_b", 20, nw - 10, 11)
        p.text(bx + nw / 2, y + 3, big_s, "serif_b", bs, (250, 246, 236), "ma")
        ls, lab_s = p.fit(lab.upper(), "sans_b", 7.5, nw - 8, 6)
        p.text(bx + nw / 2, y + 27, lab_s, "sans_b", ls, (216, 180, 110), "ma")
        if i:
            p.line(bx, y + 6, bx, y + 36, (90, 86, 78), 1)
    y += 48
    # leads (3)
    lw3 = (CW - 2 * 12) / 3
    for i in range(3):
        card(p, stories[i], M + i * (lw3 + 12), y, lw3, 74, 16.5, 11)
    y += 178
    p.line(M, y, W - M, y, (200, 194, 182), 1)
    y += 4
    # card rows (5 + 5)
    cw5 = (CW - 4 * 10) / 5
    for row in range(2):
        for c in range(5):
            idx = 3 + row * 5 + c
            if idx < len(stories):
                card(p, stories[idx], M + c * (cw5 + 10), y, cw5, 44, 12.5, 9.5)
        y += 129
        if row == 0:
            p.line(M, y - 3, W - M, y - 3, (200, 194, 182), 1)
    # map band
    p.text(M, y, "WHERE IT HAPPENED", "sans_b", 9.5, RED)
    order = ["Europe", "Asia", "Americas", "Middle East", "Africa", "Oceania", "Global"]
    tally_s = "  ·  ".join(f"{r} {regions[r]}" for r in order if r in regions)
    p.text(M + p.tw("WHERE IT HAPPENED ", "sans_b", 9.5), y,
           "— pins match the numbered stories · " + tally_s, "sans", 9, SOFT)
    y += 13
    pins = [(st["n"], st["pin"][0], st["pin"][1]) for st in stories if st.get("pin")]
    draw_map(p, M, y, CW, 88, pins)
    y += 90
    p.line(M, y, W - M, y, RULE, 1.1)
    y += 4
    # briefs heading
    p.text(M, y, f"ALSO ON {day['weekday']}", "sans_b", 10.5, INK)
    p.text(M + p.tw(f"ALSO ON {day['weekday']} ", "sans_b", 10.5), y,
           f"— {len(briefs)} more of the day, numbered {len(stories) + 1}–{total}",
           "sans", 9.5, SOFT)
    y += 15
    brief_top = y
    col_w = (CW - 2 * 16) / 3
    per = (len(briefs) + 2) // 3
    FS = 9.8
    LH = 12.0
    for ci in range(3):
        bx = M + ci * (col_w + 16)
        by = brief_top
        for bi in range(ci * per, min((ci + 1) * per, len(briefs))):
            b = briefs[bi]
            num = len(stories) + bi + 1
            segs = [(f"{num}. ", "sans_b", RED), (b["lead"] + " ", "sans_b", INK),
                    (b["text"], "sans", SOFT)]
            lines = p.rich_wrap(segs, FS, col_w)
            while len(lines) > 2:  # drop trailing words until it fits 2 lines
                flat = [(t, k, f) for (t, k, f) in segs]
                # shorten the text segment by one word
                txt = flat[2][0].rsplit(" ", 1)[0]
                segs = [flat[0], flat[1], (txt + "…", flat[2][1], flat[2][2])]
                lines = p.rich_wrap(segs, FS, col_w)
            for ln in lines:
                p.draw_rich(bx, by, ln, FS)
                by += LH
            by += 3.6
    y = brief_top + per * (2 * LH + 3.6) + 4
    # date check
    # date check (first line is narrower: it flows after the label)
    off = p.tw("DATE CHECK  ", "sans_b", 9)
    dc_words = day["date_check"].split()
    dc_lines, cur = [], ""
    li = 0
    for wd in dc_words:
        lim = CW - 16 - (off if li == 0 else 0)
        t = (cur + " " + wd).strip()
        if p.tw(t, "sans", 9.3) <= lim or not cur:
            cur = t
        else:
            dc_lines.append(cur)
            cur = wd
            li += 1
    if cur:
        dc_lines.append(cur)
    box_h = 10 + len(dc_lines) * 12
    p.d.rectangle([M * S, y * S, (W - M) * S, (y + box_h) * S], outline=RULE, width=int(1.4 * S))
    p.text(M + 8, y + 5, "DATE CHECK", "sans_b", 9, RED)
    for i, ln in enumerate(dc_lines):
        p.text(M + 8 + (off if i == 0 else 0), y + 5 + i * 12, ln, "sans", 9.3, SOFT)
    y += box_h + 5
    # footer
    p.line(M, y, W - M, y, RULE, 1.6)
    y += 4
    p.text(M, y, "All stories first reported " + day["date_short"] + ". Chips: CONFIRMED = on the record · "
                 "OFFICIALS = officials say · REPORTED = news report · FORECAST = forecast · "
                 "CLAIM = one side's claim · ESTIMATE = third-party estimate.", "sans", 8.6, SOFT)
    y += 12
    p.text(M, y, "Sources: " + day["sources"], "sans", 8.6, SOFT)
    y += 12
    if y > W:
        raise SystemExit(f"layout overflow: final y={y}")
    return p.finish(out_path)


# ------------------------------------------------------------- day data
DAY = {
    "weekday": "SUNDAY",
    "date_long": "Sunday 22 November 2026",
    "date_short": "Sun 22 Nov 2026",
    "strap_left": "THE WORLD ON ONE PAGE",
    "timeline": [
        ("00:01 GMT", "Bitcoin retakes $60,000 after Saturday's plunge"),
        ("03:00 GMT", "COP31 objections deadline on the deal text"),
        ("04:00 GMT", "Las Vegas GP under the lights on the Strip"),
        ("06:00 GMT", "COP31 reconvenes to approve the final deal"),
        ("14:00 GMT", "Hull v Brighton opens Sunday's Premier League"),
        ("16:30 GMT", "Liverpool host Manchester United at Anfield"),
        ("17:00 GMT", "Zverev v Alcaraz in the ATP Finals decider"),
        ("EVENING", "St. Johns River crest due near Lake Harney"),
    ],
    "numbers": [
        ("$60,192", "Bitcoin at 00:01 GMT"),
        ("200", "nations at COP31"),
        ("35%", "electricity by 2035"),
        ("24 in", "Florida rain since Tue"),
        ("18.8 ft", "St. Johns River, Cocoa"),
        ("$2.4bn", "crypto liquidated"),
    ],
    "stories": [
        {"tag": "ANTALYA · CLIMATE", "chip": "REPORTED", "src": "REUTERS",
         "head": "COP31 NEARS FINAL DEAL AFTER ALL-NIGHT TALKS",
         "sub": "New package unveiled in the early hours; nearly 200 nations vote at 06:00 GMT. Kurum: a text all parties can agree on; 130 nations pushed a fossil-fuel transition.",
         "scene": "climate", "pin": (31, 37), "region": "Asia", "field": "Climate"},
        {"tag": "GLOBAL · MARKETS", "chip": "REPORTED", "src": "FINNHUB",
         "head": "BITCOIN BOUNCES BACK ABOVE $60,000",
         "sub": "BTC $60,192 at 00:01 GMT, +2.1% on the day, after Saturday's plunge to $55,130 — its lowest since Sept 2024; $2.4bn in crypto bets liquidated.",
         "scene": "cyber", "pin": (-74, 41), "region": "Global", "field": "Markets"},
        {"tag": "TURIN · SPORT", "chip": "REPORTED", "src": "ATP",
         "head": "ZVEREV MEETS ALCARAZ IN TURIN FINAL",
         "sub": "World No. 1 Zverev, yet to drop a set, faces Alcaraz at 18:00 in the season's last match; their 14th meeting, Alcaraz leads 7–6.",
         "scene": "globe", "pin": (8, 45), "region": "Europe", "field": "Sport"},
        {"tag": "FLORIDA · WEATHER", "chip": "REPORTED", "src": "NWS",
         "head": "FLORIDA RIVER STILL RISING AFTER RECORD RAIN",
         "sub": "St. Johns River above its 1953 record at 18.8 ft; ~200 rescues.",
         "scene": "storm", "pin": (-81, 28), "region": "Americas", "field": "Weather"},
        {"tag": "EUROPE · PROTEST", "chip": "REPORTED", "src": "CNN",
         "head": "GEN Z PROTESTS ROLL INTO THE WEEKEND",
         "sub": "After Friday's 25-nation day of action, rallies continue into Sunday.",
         "scene": "protest", "pin": (2, 49), "region": "Europe", "field": "Protest"},
        {"tag": "HORMUZ · MARKETS", "chip": "REPORTED", "src": "AL JAZEERA",
         "head": "OIL FACES ITS MONDAY TEST AS TANKERS BURN",
         "sub": "WTI $83.62, down 14% in November; futures reopen Monday.",
         "scene": "tanker", "pin": (56, 26), "region": "Middle East", "field": "Markets"},
        {"tag": "ODISHA · WEATHER", "chip": "REPORTED", "src": "IMD",
         "head": "AKVAN'S RAINS LINGER OVER EAST INDIA",
         "sub": "14 flights cancelled at Ranchi after a 70–80 km/h landfall.",
         "scene": "storm", "pin": (85, 20), "region": "Asia", "field": "Weather"},
        {"tag": "LIVERPOOL · SPORT", "chip": "REPORTED", "src": "PREMIER LEAGUE",
         "head": "LIVERPOOL HOST MAN UTD IN SUNDAY SHOWPIECE",
         "sub": "Anfield at 16:30 GMT; United sit 16th, Liverpool 3rd.",
         "scene": "flags", "pin": (-3, 53), "region": "Europe", "field": "Sport"},
        {"tag": "LAS VEGAS · SPORT", "chip": "REPORTED", "src": "F1",
         "head": "LAS VEGAS GP UNDER THE LIGHTS TONIGHT",
         "sub": "Formula 1's night race starts 20:00 local on the Strip.",
         "scene": "globe", "pin": (-115, 36), "region": "Americas", "field": "Sport"},
        {"tag": "ANTALYA · CLIMATE", "chip": "REPORTED", "src": "REUTERS",
         "head": "130 NATIONS HOLD THE LINE AT COP31",
         "sub": "130 countries insist the text name a fossil-fuel transition; producers object.",
         "scene": "climate", "pin": (133, -25), "region": "Oceania", "field": "Climate"},
        {"tag": "ATLANTIC · WEATHER", "chip": "FORECAST", "src": "NWS",
         "head": "SECOND ATLANTIC SYSTEM HEADS NORTH",
         "sub": "Florida's rain-maker heads up the coast; a second system may turn subtropical.",
         "scene": "storm", "pin": (-80, 32), "region": "Americas", "field": "Weather"},
    ],
    "briefs": [
        {"lead": "COP31 OBJECTIONS", "text": "Delegations have until 03:00 GMT to object to the deal text; the approval session opens at 06:00 GMT.", "region": "Asia", "field": "Climate"},
        {"lead": "BTC MINERS SQUEEZED", "text": "Bitcoin is back above $60,000 but still far below JPMorgan's $86,000 mining-cost estimate.", "region": "Global", "field": "Markets"},
        {"lead": "ETH AND SOL FOLLOW", "text": "Ether $1,676.59 (+1.3%) and Solana $70.14 (+1.4%) trade higher on Sunday.", "region": "Global", "field": "Markets"},
        {"lead": "GOLD HOLDS $3,515", "text": "Gold $3,515.40 and silver $41.07 as markets pause for the weekend after the rout.", "region": "Global", "field": "Markets"},
        {"lead": "SINNER ABSENT", "text": "Defending champion Jannik Sinner misses the Turin final with a knee injury; the crown changes hands.", "region": "Europe", "field": "Sport"},
        {"lead": "ALCARAZ STREAK", "text": "Alcaraz rides a 13-match winning streak into the final, his seventh final of 2026.", "region": "Europe", "field": "Sport"},
        {"lead": "HULL V BRIGHTON", "text": "Hull host second-placed Brighton at 14:00 GMT in Sunday's early Premier League kick-off.", "region": "Europe", "field": "Sport"},
        {"lead": "SR 46 CLOSED", "text": "Water covers SR 46 above Lake Harney; the road is closed at the St. Johns River until further notice.", "region": "Americas", "field": "Weather"},
        {"lead": "BREVARD RESCUES", "text": "Brevard County reports 160+ water rescues since Friday; 9,000 ft of flood barriers deployed.", "region": "Americas", "field": "Weather"},
        {"lead": "ELECTRIFICATION 35%", "text": "The COP31 draft pushes electricity to 35% of world energy by 2035.", "region": "Global", "field": "Climate"},
        {"lead": "ADAPTATION CASH CUT", "text": "A $120bn adaptation-aid target for poorer nations was dropped from the COP31 draft.", "region": "Global", "field": "Climate"},
        {"lead": "AIR INDIA GROUNDED", "text": "Jeddah flights stay suspended until 24 Nov; Riyadh and Dammam until 30 Nov amid the Gulf crisis.", "region": "Asia", "field": "Transport"},
        {"lead": "BRENT NEAR $93", "text": "Brent crude holds near $93 despite a 3.5–5% weekly slide as traders weigh war risk.", "region": "Global", "field": "Markets"},
        {"lead": "FRANCE BRACES SUNDAY", "text": "More Gen Z protests are planned in France on Sunday; the US embassy warns of metro and rail disruption.", "region": "Europe", "field": "Protest"},
        {"lead": "WETTEST NOVEMBER", "text": "Several Florida spots log their wettest November on record after a week of rain.", "region": "Americas", "field": "Weather"},
        {"lead": "PREMIER LEAGUE TABLE", "text": "Into Sunday: Brighton 2nd (7-1-2), Liverpool 3rd (5-3-2), Manchester United 16th (1-5-4).", "region": "Europe", "field": "Sport"},
        {"lead": "CUMMINS STAYS CAPTAIN", "text": "Pat Cummins keeps Australia's Test captaincy with Cricket Australia's unanimous support.", "region": "Oceania", "field": "Sport"},
        {"lead": "ICMR TRANSFERS", "text": "India's ICMR completes 100 technology transfers and signs 20 licensing deals at its research summit.", "region": "Asia", "field": "Health"},
        {"lead": "UKMTO: SEVERE", "text": "The UK maritime agency keeps its Strait of Hormuz threat rating at 'severe'.", "region": "Middle East", "field": "Security"},
        {"lead": "HOUTHI AIRSPACE WARNING", "text": "The Houthis warned airlines on Friday to avoid Saudi airspace, saying fresh strikes were planned.", "region": "Middle East", "field": "War"},
        {"lead": "ANDHRA WINDS", "text": "The IMD forecasts gusty winds of 40–50 km/h, gusting to 60, in Andhra Pradesh on 22–24 Nov.", "region": "Asia", "field": "Weather"},
    ],
    "date_check": ("Left out on purpose - first reported earlier: Russia's 400-drone barrage on Ukraine "
                   "and missiles in Poland (Fri 20 Nov); Trump's 10% credit-card cap vow, the Pentagon's "
                   "Canada memo, Modi's Nitish Setu opening and the Manipur liquor deaths (Sat 21 Nov); "
                   "Kim's factory tour, the Geneva killer-robots compromise, Akvan's landfall and the "
                   "Peru quake (20-21 Nov); the Houthi and Iran strikes on the Gulf (20-21 Nov). "
                   "Not yet: the COP31 approval outcome (06:00 GMT), the ATP final result (18:00 Turin) "
                   "and the Las Vegas GP (20:00 local)."),
    "sources": ("Reuters · AP · AFP · Finnhub · Al Jazeera · NWS · IMD · ATP · Olympics.com · "
                "Fox Weather · CNN · Times Now · The Hindu · Khaleej Times · NBC Sports · CFDR · "
                "UKMTO · CoinDesk"),
}


def _main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    render(DAY, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    _main()
