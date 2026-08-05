#!/usr/bin/env python3
"""
Minimal, self-contained Excalidraw -> PNG renderer using Pillow.

Supports the element types used by generate_diagrams.py: rectangle, ellipse,
diamond, text (standalone and container-bound), and arrow. This is not a
pixel-perfect Excalidraw clone (no hand-drawn "rough" style), but produces a
clean, accurate PNG from the scene JSON.

Usage:
    python render_excalidraw.py <input.excalidraw> <output.png> [scale]
"""
import json
import math
import sys
from PIL import Image, ImageDraw, ImageFont

SCALE = 2
MARGIN = 40


def find_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def norm_color(c, default="#1e1e1e"):
    if not c or c == "transparent":
        return None
    return c


def rounded_rect(draw, box, radius, fill, outline, width):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def diamond(draw, x, y, w, h, fill, outline, width):
    pts = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
    draw.polygon(pts, fill=fill, outline=outline)
    if outline:
        draw.line(pts + [pts[0]], fill=outline, width=width)


def draw_arrow(draw, x, y, points, color, width):
    abs_pts = [(x + px, y + py) for px, py in points]
    if len(abs_pts) >= 2:
        draw.line(abs_pts, fill=color, width=width, joint="curve")
        # arrowhead at the last segment
        (x0, y0), (x1, y1) = abs_pts[-2], abs_pts[-1]
        ang = math.atan2(y1 - y0, x1 - x0)
        size = 10 * SCALE
        for da in (math.radians(150), math.radians(-150)):
            hx = x1 + size * math.cos(ang + da)
            hy = y1 + size * math.sin(ang + da)
            draw.line([(x1, y1), (hx, hy)], fill=color, width=width)


def text_lines(draw, box, lines, font, color, align):
    x0, y0, x1, y1 = box
    total_h = sum((draw.textbbox((0, 0), ln, font=font)[3]) for ln in lines) + \
        (len(lines) - 1) * 4 * SCALE
    cy = y0 + ((y1 - y0) - total_h) / 2 if (y1 - y0) > 0 else y0
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=font)
        lw, lh = bb[2] - bb[0], bb[3] - bb[1]
        if align == "left":
            cx = x0
        elif align == "right":
            cx = x1 - lw
        else:
            cx = x0 + ((x1 - x0) - lw) / 2 if (x1 - x0) > 0 else x0
        draw.text((cx, cy), ln, font=font, fill=color)
        cy += lh + 4 * SCALE


def render(in_path, out_path, scale=SCALE):
    global SCALE
    SCALE = scale
    data = json.load(open(in_path))
    els = [e for e in data["elements"] if not e.get("isDeleted")]

    xs = [e["x"] for e in els]
    ys = [e["y"] for e in els]
    max_x = max(e["x"] + e.get("width", 0) for e in els)
    max_y = max(e["y"] + e.get("height", 0) for e in els)
    min_x, min_y = min(xs), min(ys)

    W = int((max_x - min_x) * SCALE + 2 * MARGIN)
    H = int((max_y - min_y) * SCALE + 2 * MARGIN)

    img = Image.new("RGB", (W, H), "#ffffff")
    draw = ImageDraw.Draw(img)

    def tx(v):
        return (v - min_x) * SCALE + MARGIN

    def ty(v):
        return (v - min_y) * SCALE + MARGIN

    el_map = {e["id"]: e for e in els}

    # shapes first
    for e in els:
        t = e["type"]
        if t in ("rectangle", "ellipse", "diamond"):
            x, y = tx(e["x"]), ty(e["y"])
            w, h = e.get("width", 0) * SCALE, e.get("height", 0) * SCALE
            fill = norm_color(e.get("backgroundColor"))
            stroke = norm_color(e.get("strokeColor"), "#1e1e1e")
            sw = max(1, int(e.get("strokeWidth", 2) * SCALE / 2))
            if t == "rectangle":
                rounded_rect(draw, [x, y, x + w, y + h], 8 * SCALE, fill, stroke, sw)
            elif t == "ellipse":
                draw.ellipse([x, y, x + w, y + h], fill=fill, outline=stroke, width=sw)
            else:
                diamond(draw, x, y, w, h, fill, stroke, sw)
        elif t == "arrow":
            color = norm_color(e.get("strokeColor"), "#1e1e1e")
            sw = max(1, int(e.get("strokeWidth", 2) * SCALE / 2))
            pts = [(px * SCALE, py * SCALE) for px, py in e.get("points", [])]
            draw_arrow(draw, tx(e["x"]), ty(e["y"]), pts, color, sw)

    # text on top
    for e in els:
        if e["type"] != "text":
            continue
        color = norm_color(e.get("strokeColor"), "#1e1e1e")
        size = int(e.get("fontSize", 16) * SCALE)
        bold = size >= 22 * SCALE / 2
        font = find_font(size, bold=bold)
        lines = e.get("text", "").split("\n")
        cid = e.get("containerId")
        if cid and cid in el_map:
            c = el_map[cid]
            box = [tx(c["x"]), ty(c["y"]),
                   tx(c["x"] + c.get("width", 0)), ty(c["y"] + c.get("height", 0))]
        else:
            box = [tx(e["x"]), ty(e["y"]),
                   tx(e["x"] + e.get("width", 0)), ty(e["y"] + e.get("height", 0))]
        text_lines(draw, box, lines, font, color, e.get("textAlign", "center"))

    img.save(out_path)
    print(f"Rendered {in_path} -> {out_path} ({W}x{H})")


if __name__ == "__main__":
    inp = sys.argv[1]
    outp = sys.argv[2]
    sc = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    render(inp, outp, sc)
