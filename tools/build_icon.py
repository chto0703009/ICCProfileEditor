# Copyright (c) 2026 Christer Törnkvist.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render the Editor icon from geometry. Requires Pillow and macOS iconutil."""
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

RESOURCES = Path(__file__).resolve().parents[1] / 'resources'
SIZE = 1024


def bezier(start, segments):
    points = [start]
    for a, b, end in segments:
        x0, y0 = points[-1]
        for i in range(1, 81):
            t = i / 80
            u = 1 - t
            points.append((u**3*x0 + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*end[0],
                           u**3*y0 + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*end[1]))
    return points


def blend(a, b, amount):
    return tuple(round(x+(y-x)*amount) for x, y in zip(a, b))


def icon():
    art = Image.new('RGBA', (SIZE, SIZE))
    draw = ImageDraw.Draw(art)
    draw.rounded_rectangle((48, 48, 976, 976), radius=218, fill='#14243c')
    background = Image.new('RGBA', art.size)
    grad = ImageDraw.Draw(background)
    for y in range(SIZE):
        grad.line((0,y,SIZE,y), fill=blend((29, 50, 77), (14, 23, 42), y/SIZE))
    art.paste(background, mask=art.getchannel('A'))
    draw = ImageDraw.Draw(art)
    draw.rounded_rectangle((53, 53, 970, 970), radius=212, outline='#3d536e', width=5)
    # Three grid lines suggest the same coordinate plane used in the app.
    for x in (307, 513, 719):
        draw.line((x, 243, x, 789), fill='#354961', width=4)
    for y in (298, 508, 718):
        draw.line((230, y, 795, y), fill='#354961', width=4)
    outline = bezier((239, 651), [
        ((184, 529), (310, 466), (363, 377)),
        ((430, 262), (504, 195), (616, 265)),
        ((678, 305), (768, 267), (799, 365)),
        ((836, 481), (764, 553), (679, 618)),
        ((578, 697), (539, 776), (413, 767)),
        ((331, 764), (264, 719), (239, 651)),
    ])
    mask = Image.new('L', art.size)
    ImageDraw.Draw(mask).polygon(outline, fill=255)
    spectrum = Image.new('RGBA', art.size)
    pixels = spectrum.load()
    for y in range(200, 780):
        v = max(0, min(1, (y-250)/520))
        for x in range(175, 850):
            u = max(0, min(1, (x-220)/580))
            top = blend((87, 239, 166), (250, 191, 103), u)
            bottom = blend((36, 176, 219), (209, 87, 207), u)
            pixels[x,y] = blend(top,bottom,v) + (255,)
    art.paste(spectrum, mask=mask)
    draw = ImageDraw.Draw(art)
    draw.line(outline, fill='#b6f2ed', width=7)
    # Pencil, from nib at lower left to eraser at upper right.
    pencil = Image.new('RGBA', (630,170))
    pen = ImageDraw.Draw(pencil)
    pen.polygon([(26,85), (123,21), (565,21), (600,48), (600,122),
                 (565,149), (123,149)], fill='#17273e', outline='#1c314c', width=10)
    pen.polygon([(45,85),(128,32),(128,138)], fill='#f8c779')
    pen.polygon([(45,85),(79,63),(79,107)], fill='#192c42')
    pen.rounded_rectangle((122,32,579,138), radius=22, fill='#fff5e0')
    pen.rectangle((130,84,531,128), fill='#edd8b4')
    pen.rounded_rectangle((526,32,589,138), radius=18, fill='#ec8daf')
    pen.rectangle((518,32,543,138), fill='#93acc6')
    pencil = pencil.rotate(40, resample=Image.Resampling.BICUBIC, expand=True)
    art.alpha_composite(pencil, (500-pencil.width//2, 520-pencil.height//2))
    return art


def main():
    art = icon()
    art.resize((96,96), Image.Resampling.LANCZOS).save(RESOURCES/'editor-header.png')
    with TemporaryDirectory() as folder:
        iconset = Path(folder)/'Editor.iconset'
        iconset.mkdir()
        for base in (16,32,128,256,512):
            for factor in (1,2):
                size = base*factor
                suffix = '@2x' if factor == 2 else ''
                art.resize((size,size), Image.Resampling.LANCZOS).save(iconset/f'icon_{base}x{base}{suffix}.png')
        subprocess.run(['iconutil','-c','icns',str(iconset),'-o',str(RESOURCES/'Editor.icns')], check=True)


if __name__ == '__main__':
    main()
