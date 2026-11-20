"""Callout deterministik; koordinat, mask, dan urutan prediksi tetap."""
import colorsys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MODES = ("Mask + Bbox", "Mask", "Bbox")


def instance_color(number):
    hue = (.56 + (number - 1) * .38196601125) % 1
    return tuple(round(v * 255) for v in colorsys.hsv_to_rgb(hue, .78, .88))


def place_callouts(items, width, offset_x, font, probe):
    """Pisahkan jangkar berimpit dan kemas nomor monoton dengan celah tetap."""
    if not items:
        return [], 0
    bw = max(34, max(probe.textbbox((0, 0), str(p['display_number']), font=font)[2] + 16 for p in items))
    row_height = font.size + 16
    gap, pad = max(24, font.size), 10
    ordered = sorted(items, key=lambda p: ((p['bbox_xyxy'][0]+p['bbox_xyxy'][2])/2, p['display_number']))
    groups = []
    for item in ordered:
        center = (item['bbox_xyxy'][0]+item['bbox_xyxy'][2])/2
        if not groups or center - groups[-1][-1][0] > bw:
            groups.append([])
        groups[-1].append((center, item))
    anchors = []
    for group in groups:
        for rank, (_, item) in enumerate(group):
            x1, y1, x2, _ = item['bbox_xyxy']
            # Jangkar berada pada sisi atas bbox asli, termasuk bbox identik.
            x = x1 + (x2-x1) * (rank+1)/(len(group)+1)
            anchors.append((x, y1, item))
    anchors.sort(key=lambda a: (a[0], a[2]['display_number']))
    capacity = max(1, (width-2*pad+gap)//(bw+gap))
    callouts = []
    for row, start in enumerate(range(0, len(anchors), capacity)):
        batch = anchors[start:start+capacity]
        lefts = []
        for x, _, _ in batch:
            ideal = round(x+offset_x-bw/2)
            lefts.append(max(pad, ideal, lefts[-1]+bw+gap if lefts else pad))
        lefts[-1] = min(lefts[-1], width-pad-bw)
        for k in range(len(lefts)-2, -1, -1):
            lefts[k] = min(lefts[k], lefts[k+1]-bw-gap)
        for xleft, (x, y, item) in zip(lefts, batch):
            callouts.append({'display_number': item['display_number'], 'instance_id': item['instance_id'],
                             'badge_rect': [xleft, 8+row*row_height, xleft+bw, 8+(row+1)*row_height-6],
                             'anchor_input_xy': [x, y]})
    return callouts, (row+1)*row_height+22


def render_pair(rgb, items, mode="Mask + Bbox", opacity=.65, focus=None):
    assert mode in MODES or mode in ("Mask saja", "Bbox saja")
    assert 0 <= opacity <= 1
    h, w = rgb.shape[:2]
    width = max(w, 600)
    fontpath = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    font = ImageFont.truetype(str(fontpath), max(18, min(26, round(w/45)))) if fontpath.exists() else ImageFont.load_default(size=18)
    ox = (width-w)//2
    probe = ImageDraw.Draw(Image.fromarray(rgb))
    callouts, header = place_callouts(items, width, ox, font, probe)
    height = max(h+header+30, round(width*.50))
    oy = header+(height-header-h)//2
    for c in callouts:
        c['badge_rect'][1] += oy-header
        c['badge_rect'][3] += oy-header
        x1, y1, x2, y2 = c['badge_rect']
        ax, ay = c['anchor_input_xy']
        c['leader_points_canvas'] = [[(x1+x2)/2, y2], [ax+ox, ay+oy]]
    original = Image.new('RGB', (width, height), 'white')
    original.paste(Image.fromarray(rgb), (ox, oy))
    pixels = rgb.astype(np.float32).copy()
    # Hanya urutan pelapisan gambar; daftar prediksi/tabel tetap utuh.
    paint_items = sorted(items, key=lambda p: p['display_number'] == focus)
    if mode not in ('Bbox', 'Bbox saja'):
        from pycocotools import mask as mask_utils
        for item in paint_items:
            bitmap = mask_utils.decode(item['segmentation']).astype(bool)
            assert bitmap.shape == (h, w)
            alpha = opacity if focus in (None, item['display_number']) else opacity*.35
            pixels[bitmap] = (1-alpha)*pixels[bitmap]+alpha*np.asarray(instance_color(item['display_number']))
    overlay = Image.new('RGB', (width, height), 'white')
    overlay.paste(Image.fromarray(np.uint8(np.clip(pixels, 0, 255))), (ox, oy))
    draw = ImageDraw.Draw(overlay)
    # Bbox, garis, lalu nomor agar label selalu berada pada lapisan teratas.
    for item in paint_items:
        if mode not in ('Mask', 'Mask saja'):
            x1, y1, x2, y2 = item['bbox_xyxy']
            selected = item['display_number'] == focus
            draw.rectangle((x1+ox, y1+oy, x2+ox, y2+oy),
                           outline=instance_color(focus) if selected else '#AF3131', width=3 if selected else 2)
    for c in callouts:
        points = [tuple(p) for p in c['leader_points_canvas']]
        color = instance_color(c['display_number'])
        draw.line(points, fill='white', width=5)
        draw.line(points, fill=color, width=2)
        ax, ay = points[-1]
        draw.ellipse((ax-3, ay-3, ax+3, ay+3), fill=color, outline='white', width=1)
    for c in callouts:
        color = instance_color(c['display_number'])
        selected = c['display_number'] == focus
        rect = c['badge_rect']
        draw.rectangle(rect, fill=color if selected else 'white', outline=color, width=3 if selected else 2)
        text = str(c['display_number']);bounds = draw.textbbox((0, 0), text, font=font)
        draw.text(((rect[0]+rect[2]-bounds[2])/2, rect[1]+3-bounds[1]), text,
                  font=font, fill='white' if selected else color)
    return original, overlay, {'input_offset_xy': [ox, oy], 'canvas_wh': [width, height],
        'number_badge_rectangles': [c['badge_rect'] for c in callouts],
        'callouts': callouts, 'focused_display_number': focus}
