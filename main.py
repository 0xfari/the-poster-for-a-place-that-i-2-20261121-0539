#!/usr/bin/env python3
"""VELDARA — a travel poster for a place that does not exist.

A canyon town of rose-gold sandstone where a turquoise river runs between
the cliffs, and paper lanterns drift on the water at dusk. The landmark is
the Lantern Bridge, a stone arch strung with lanterns. Drawn procedurally
with PIL: no network, no external assets, deterministic. The only font is
bundled in this repository (fonts/DejaVuSans-Bold.ttf, loaded by relative
path); it never touches a host font directory.
"""

import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, "fonts", "DejaVuSans-Bold.ttf")

# --- palette ---
INDIGO = (26, 34, 66)
VIOLET = (84, 66, 110)
AMBER = (232, 163, 76)
GOLD = (255, 196, 107)
CREAM = (247, 234, 211)
CLIFF = (185, 106, 68)
CLIFF_DARK = (150, 82, 52)
CLIFF_LIGHT = (206, 128, 84)
RIVER = (38, 122, 122)
RIVER_LIGHT = (74, 168, 160)
RIVER_DEEP = (24, 84, 88)
BANK = (74, 52, 56)
STONE = (96, 84, 92)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(size, stops):
    """stops: list of (position 0..1, color)."""
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    w, h = size
    for y in range(h):
        t = y / max(h - 1, 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                d.line([(0, y), (w, y)], fill=lerp(c0, c1, f))
                break
        else:
            d.line([(0, y), (w, y)], fill=stops[-1][1])
    return img


def glow(layer, cx, cy, r, color, blur):
    """Soft radial glow: concentric circles, alpha falling off."""
    tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    steps = 14
    for i in range(steps, 0, -1):
        rr = r * i / steps
        a = int(color[3] * (1 - i / steps) ** 1.6)
        td.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                   fill=(color[0], color[1], color[2], a))
    tmp = tmp.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(tmp)


def soft_disc(layer, box, fill, blur):
    tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(tmp).ellipse(box, fill=fill)
    tmp = tmp.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(tmp)


def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def draw_tracked(draw, cx, y, text, font, fill, tracking, shadow=None):
    """Draw text centered on cx, letter by letter, with tracking."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        if shadow is not None:
            draw.text((x + 3, y + 4), ch, font=font, fill=shadow)
        draw.text((x, y), ch, font=font, fill=fill)
        x += wch + tracking


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(20261121)

    # --- sky: indigo dusk melting into amber at the horizon ---
    img = vertical_gradient((W, H), [
        (0.00, INDIGO),
        (0.30, (52, 48, 88)),
        (0.48, VIOLET),
        (0.56, (196, 120, 84)),
        (0.62, AMBER),
        (1.00, (120, 74, 66)),
    ])
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)

    # --- stars in the upper sky ---
    for _ in range(90):
        x = rng.uniform(0, W)
        y = rng.uniform(0, 330)
        r = rng.uniform(0.6, 1.8)
        a = rng.randint(90, 210)
        ld.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 210, a))

    # --- the low sun, setting into the ridge, and its glow ---
    sun_cx, sun_cy = 640, 530
    glow(layer, sun_cx, sun_cy, 280, (255, 180, 90, 170), 40)
    glow(layer, sun_cx, sun_cy, 130, (255, 210, 130, 210), 18)
    ld.ellipse([sun_cx - 52, sun_cy - 52, sun_cx + 52, sun_cy + 52],
               fill=(255, 206, 120, 255))
    ld.ellipse([sun_cx - 34, sun_cy - 34, sun_cx + 34, sun_cy + 34],
               fill=(255, 238, 190, 255))

    # --- distant ridge silhouettes across the horizon ---
    ridge = [(0, 560), (140, 520), (300, 552), (470, 516), (640, 548),
             (800, 520), (940, 550), (1024, 528), (1024, 620), (0, 620)]
    ld.polygon(ridge, fill=(74, 52, 84, 255))
    ridge2 = [(0, 600), (180, 566), (360, 596), (560, 570), (760, 598),
              (920, 572), (1024, 594), (1024, 660), (0, 660)]
    ld.polygon(ridge2, fill=(96, 62, 78, 255))

    # --- canyon cliffs, left and right, framing the valley ---
    left_cliff = [(0, 330), (120, 380), (210, 470), (250, 580), (280, 700),
                  (300, 1024), (0, 1024)]
    ld.polygon(left_cliff, fill=CLIFF + (255,))
    right_cliff = [(1024, 350), (920, 400), (830, 490), (790, 590),
                   (760, 700), (740, 1024), (1024, 1024)]
    ld.polygon(right_cliff, fill=CLIFF + (255,))
    # strata bands on the cliffs, clipped to the cliff polygons
    strata = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(strata)
    for y0, col in ((420, CLIFF_DARK), (520, CLIFF_LIGHT), (640, CLIFF_DARK),
                    (760, CLIFF_LIGHT), (880, CLIFF_DARK)):
        sd.line([(0, y0), (320, y0 + 60)], fill=col + (255,), width=7)
        sd.line([(1024, y0 + 20), (720, y0 + 80)], fill=col + (255,), width=7)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(left_cliff, fill=255)
    md.polygon(right_cliff, fill=255)
    layer.paste(strata, (0, 0), mask)
    # cliff-top rim light
    ld.line([(0, 330), (120, 380), (210, 470)], fill=(240, 170, 110, 255), width=5)
    ld.line([(1024, 350), (920, 400), (830, 490)], fill=(240, 170, 110, 255), width=5)

    # --- town windows glowing on the cliff faces ---
    for _ in range(26):
        side = rng.choice(("L", "R"))
        if side == "L":
            x = rng.uniform(20, 210)
            y = rng.uniform(400, 900)
        else:
            x = rng.uniform(820, 1000)
            y = rng.uniform(420, 900)
        w = rng.uniform(7, 12)
        h = rng.uniform(9, 15)
        ld.rectangle([x, y, x + w, y + h], fill=(255, 200, 110, 255))

    # --- the river: turquoise, widening from the horizon to the viewer ---
    river = [(470, 620), (560, 620), (620, 760), (680, 900), (720, 1024),
             (300, 1024), (350, 900), (400, 760)]
    ld.polygon(river, fill=RIVER + (255,))
    # sun path on the water: a narrow warm streak down the middle
    ld.polygon([(508, 620), (538, 620), (570, 760), (598, 900), (612, 1024),
                (452, 1024), (476, 900), (492, 760)], fill=(198, 140, 88, 255))
    ld.polygon([(520, 620), (532, 620), (548, 760), (566, 900), (576, 1024),
                (488, 1024), (502, 900), (512, 760)], fill=(228, 178, 118, 255))
    # dark banks along the river
    ld.polygon([(300, 1024), (350, 900), (400, 760), (470, 620),
                (430, 620), (360, 760), (310, 900), (250, 1024)],
               fill=BANK + (255,))
    ld.polygon([(720, 1024), (680, 900), (620, 760), (560, 620),
                (600, 620), (660, 760), (720, 900), (770, 1024)],
               fill=BANK + (255,))

    # --- the Lantern Bridge: stone arch over the river, mid-ground ---
    # arch band
    ld.arc([330, 600, 700, 820], start=180, end=360, fill=STONE + (255,), width=30)
    ld.arc([330, 600, 700, 820], start=180, end=360, fill=(140, 124, 132, 255), width=6)
    # bridge deck
    ld.rectangle([318, 690, 712, 712], fill=STONE + (255,))
    ld.rectangle([318, 690, 712, 696], fill=(150, 134, 142, 255))
    # (no arch windows under the deck: they read as dark blobs over the
    # sun-path on the water; the arch and deck alone carry the bridge)
    # lanterns hanging from the bridge
    for cx in range(350, 690, 42):
        ld.line([(cx, 700), (cx, 726)], fill=(60, 48, 52, 255), width=3)
        glow(layer, cx, 742, 26, (255, 190, 90, 190), 8)
        ld.ellipse([cx - 11, 730, cx + 11, 754], fill=(255, 196, 107, 255))
        ld.ellipse([cx - 5, 734, cx + 5, 750], fill=(255, 232, 175, 255))

    # warm reflection of the bridge lanterns on the water below it
    for cx in range(400, 620, 44):
        ld.line([(cx, 758), (cx, 800)], fill=(255, 190, 100, 110), width=4)

    # --- lanterns drifting on the river, with reflections ---
    for _ in range(16):
        t = rng.random()
        y = 780 + t * 220
        # river narrows with distance: x range shrinks toward the horizon
        half = 60 + t * 150
        cx = 510 + rng.uniform(-half, half)
        r = 7 + t * 6
        glow(layer, cx, y, int(r * 3), (255, 190, 90, 170), 6)
        ld.ellipse([cx - r, y - r, cx + r, y + r], fill=(255, 196, 107, 255))
        ld.ellipse([cx - r * 0.45, y - r * 0.45, cx + r * 0.45, y + r * 0.45],
                   fill=(255, 232, 175, 255))
        # reflection streak below the lantern
        ld.line([(cx, y + r + 4), (cx, y + r + 26 + t * 30)],
                fill=(255, 190, 100, 140), width=3)

    # --- foreground rocks, dark, framing the bottom corners ---
    ld.polygon([(0, 1024), (0, 940), (120, 980), (230, 1024)], fill=(34, 26, 30, 255))
    ld.polygon([(1024, 1024), (1024, 950), (900, 990), (790, 1024)],
               fill=(34, 26, 30, 255))

    # --- birds crossing the dusk sky ---
    for bx, by, s in ((300, 300, 14), (350, 320, 11), (760, 280, 13),
                      (820, 310, 10), (430, 260, 9)):
        ld.arc([bx - s, by - s // 2, bx, by + s // 2], start=200, end=340,
               fill=(40, 32, 56, 255), width=3)
        ld.arc([bx, by - s // 2, bx + s, by + s // 2], start=200, end=340,
               fill=(40, 32, 56, 255), width=3)

    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    d = ImageDraw.Draw(img)

    # --- the name: large, tracked, cream, set into the sky ---
    font = load_font(118)
    draw_tracked(d, W // 2, 118, "VELDARA", font, CREAM, 22,
                 shadow=(30, 20, 44))

    img.save(os.path.join(out_dir, "entry.png"), optimize=True)


if __name__ == "__main__":
    main()
