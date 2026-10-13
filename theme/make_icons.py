"""Generate the "ArctOS" icon theme: iOS 4-6 style glossy rounded tiles.

Original artwork (gradients + gloss drawn here, glyphs from Adwaita symbolic icons, CC BY-SA 3.0),
not Apple's icons. Usage: python make_icons.py <glyph_png_dir> <out_theme_dir>
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = 512          # master size
R = 96           # corner radius (iOS-ish)
SIZES = (512, 256, 192, 128, 96, 64, 48, 32)

GLYPHS = sys.argv[1]
OUT = sys.argv[2]


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mask():
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, S - 1, S - 1), R, fill=255)
    return m


MASK = mask()


def gradient(top, bottom):
    t, b = hexrgb(top), hexrgb(bottom)
    g = Image.new('RGB', (1, S))
    for y in range(S):
        f = y / (S - 1)
        g.putpixel((0, y), tuple(int(t[i] * (1 - f) + b[i] * f) for i in range(3)))
    return g.resize((S, S))


def gloss(img):
    """iOS 4 gloss: soft white overlay on the upper half, ending in a wide elliptical edge."""
    ov = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(ov)
    d.ellipse((-S * 0.45, -S * 0.62, S * 1.45, S * 0.50), fill=255)
    grad = Image.new('L', (1, S))
    for y in range(S):
        grad.putpixel((0, y), int(max(0.0, 0.42 - 0.34 * (y / (S * 0.5))) * 255) if y < S * 0.5 else 0)
    grad = grad.resize((S, S))
    alpha = ImageChops.multiply(ov, grad)
    white = Image.new('RGB', (S, S), (255, 255, 255))
    img.paste(white, (0, 0), alpha)
    return img


def tint(glyph, color):
    g = glyph.convert('RGBA')
    solid = Image.new('RGBA', g.size, hexrgb(color) + (255,))
    solid.putalpha(g.getchannel('A'))
    return solid


def place(img, glyph, scale=0.58, color='#ffffff', dy=0, shadow=True):
    g = glyph.resize((int(S * scale), int(S * scale)), Image.LANCZOS)
    g = tint(g, color)
    x = (S - g.width) // 2
    y = (S - g.height) // 2 + dy
    if shadow:
        sh = Image.new('RGBA', g.size, (0, 0, 0, 0))
        sh.putalpha(g.getchannel('A').point(lambda a: int(a * 0.35)))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        img.paste(sh, (x, y + 8), sh)
    img.paste(g, (x, y), g)


def finish(img, name):
    img = gloss(img)
    # thin top highlight / bottom shade rim
    rim = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(rim)
    d.rounded_rectangle((1, 1, S - 2, S - 2), R, outline=(255, 255, 255, 70), width=3)
    img = img.convert('RGBA')
    img.alpha_composite(rim)
    img.putalpha(MASK)
    for size in SIZES:
        d = os.path.join(OUT, '%dx%d' % (size, size), 'apps')
        os.makedirs(d, exist_ok=True)
        img.resize((size, size), Image.LANCZOS).save(os.path.join(d, name + '.png'), optimize=True)


def g(name):
    return Image.open(os.path.join(GLYPHS, name + '.png'))


def simple(icon, top, bottom, glyph, color='#ffffff', scale=0.58):
    img = gradient(top, bottom)
    place(img, g(glyph), scale, color)
    finish(img, icon)


# ---- custom drawn tiles ----

def clock_tile(icon):
    img = gradient('#3a3a3c', '#050505')
    d = ImageDraw.Draw(img)
    c, r = S / 2, S * 0.36
    d.ellipse((c - r, c - r, c + r, c + r), fill=(250, 250, 250))
    for i in range(12):
        a = math.radians(i * 30)
        d.line((c + math.sin(a) * r * 0.80, c - math.cos(a) * r * 0.80,
                c + math.sin(a) * r * 0.92, c - math.cos(a) * r * 0.92), fill=(40, 40, 40), width=8)
    d.line((c, c, c + math.sin(math.radians(-60)) * r * 0.5, c - math.cos(math.radians(-60)) * r * 0.5),
           fill=(20, 20, 20), width=16)
    d.line((c, c, c + math.sin(math.radians(60)) * r * 0.72, c - math.cos(math.radians(60)) * r * 0.72),
           fill=(20, 20, 20), width=11)
    d.line((c, c, c + math.sin(math.radians(170)) * r * 0.8, c - math.cos(math.radians(170)) * r * 0.8),
           fill=(230, 40, 40), width=5)
    d.ellipse((c - 12, c - 12, c + 12, c + 12), fill=(230, 40, 40))
    finish(img, icon)


def messages_tile(icon):
    img = gradient('#8af27a', '#20b13a')
    sh = Image.new('L', (S, S), 0)
    ds = ImageDraw.Draw(sh)
    ds.ellipse((S * 0.16, S * 0.22, S * 0.84, S * 0.70), fill=255)
    ds.polygon([(S * 0.30, S * 0.60), (S * 0.22, S * 0.80), (S * 0.44, S * 0.66)], fill=255)
    shadow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    shadow.putalpha(sh.point(lambda a: int(a * 0.3)).filter(ImageFilter.GaussianBlur(6)))
    img.paste(shadow, (0, 8), shadow)
    img.paste(Image.new('RGB', (S, S), (255, 255, 255)), (0, 0), sh)
    finish(img, icon)


def compass_tile(icon):
    img = gradient('#f4f6f8', '#c9ced6')
    d = ImageDraw.Draw(img)
    c, r = S / 2, S * 0.38
    d.ellipse((c - r, c - r, c + r, c + r), fill=(28, 116, 232))
    d.ellipse((c - r * 0.93, c - r * 0.93, c + r * 0.93, c + r * 0.93), fill=(72, 168, 250))
    for i in range(36):
        a = math.radians(i * 10)
        L = 0.84 if i % 9 else 0.74
        d.line((c + math.sin(a) * r * L, c - math.cos(a) * r * L, c + math.sin(a) * r * 0.92,
                c - math.cos(a) * r * 0.92), fill=(255, 255, 255), width=3)
    a = math.radians(45)
    tip = (c + math.sin(a) * r * 0.8, c - math.cos(a) * r * 0.8)
    tail = (c - math.sin(a) * r * 0.8, c + math.cos(a) * r * 0.8)
    side1 = (c + math.cos(a) * 22, c + math.sin(a) * 22)
    side2 = (c - math.cos(a) * 22, c - math.sin(a) * 22)
    d.polygon([tip, side1, side2], fill=(235, 52, 45))
    d.polygon([tail, side1, side2], fill=(250, 250, 250))
    finish(img, icon)


def maps_tile(icon):
    img = gradient('#d7f0c4', '#9fd28a')
    d = ImageDraw.Draw(img)
    d.polygon([(0, S * 0.62), (S, S * 0.30), (S, S * 0.42), (0, S * 0.74)], fill=(255, 255, 255))
    d.polygon([(S * 0.58, 0), (S * 0.70, 0), (S * 0.48, S), (S * 0.36, S)], fill=(250, 222, 120))
    d.rectangle((0, S * 0.78, S, S), fill=(120, 190, 240))
    place(img, g('mark-location'), 0.42, '#e8392f', dy=-30)
    finish(img, icon)


def notes_tile(icon):
    img = gradient('#fff7a8', '#f3d84c')
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, S, S * 0.20), fill=(196, 140, 72))
    for y in range(int(S * 0.34), S, 58):
        d.line((S * 0.10, y, S * 0.90, y), fill=(200, 170, 120), width=4)
    d.line((S * 0.20, S * 0.20, S * 0.20, S), fill=(230, 120, 120), width=4)
    finish(img, icon)


def settings_tile(icon, glyph='emblem-system', scale=0.62):
    img = gradient('#c9cdd3', '#7c828b')
    place(img, g(glyph), scale, '#4a4e55', shadow=False)
    finish(img, icon)


def calendar_tile(icon):
    img = gradient('#ffffff', '#e4e4e4')
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, S, S * 0.28), fill=(224, 52, 46))
    place(img, g('x-office-calendar'), 0.46, '#2b2b2b', dy=50, shadow=False)
    finish(img, icon)


def store_tile(icon):
    from PIL import ImageFont
    img = gradient('#62cdff', '#0a62f0')
    font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', int(S * 0.62))
    txt = Image.new('L', (S, S), 0)
    ImageDraw.Draw(txt).text((S / 2, S / 2 + 10), 'A', font=font, fill=255, anchor='mm')
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    sh.putalpha(txt.point(lambda a: int(a * 0.35)).filter(ImageFilter.GaussianBlur(6)))
    img.paste(sh, (0, 8), sh)
    img.paste(Image.new('RGB', (S, S), (255, 255, 255)), (0, 0), txt)
    finish(img, icon)


simple('org.gnome.Calls', '#8cf26b', '#1fa82a', 'call-start')
messages_tile('sm.puri.Chatty')
simple('org.gnome.Contacts', '#d8d3c4', '#9e9686', 'avatar-default', '#ffffff', 0.60)
# third-party apps keep their own icons (Firefox etc.)
simple('org.gnome.Calculator', '#5b5f66', '#202226', 'accessories-calculator')
calendar_tile('org.gnome.Calendar')
simple('org.gnome.Snapshot', '#a3a9b1', '#4b5058', 'camera-photo')
clock_tile('org.gnome.clocks')
simple('org.gnome.Console', '#3a3a3a', '#0b0b0b', 'utilities-terminal', '#4cd964')
simple('org.gnome.Papers', '#ff9a74', '#e0442b', 'x-office-document')
simple('eu.lucaweiss.lpa_gtk', '#b8bcc4', '#6f747c', 'auth-sim')
simple('org.gnome.Nautilus', '#73c6ff', '#1a6fe0', 'folder')
simple('org.gnome.Decibels', '#ff8fb1', '#e8305e', 'audio-x-generic')
simple('org.gnome.Loupe', '#ffe36b', '#f39a17', 'image-x-generic')
maps_tile('org.gnome.Maps')
settings_tile('org.gnome.Settings')
settings_tile('mobi.phosh.MobileSettings', 'phone', 0.52)
store_tile('org.gnome.Software')
notes_tile('org.gnome.TextEditor')
simple('org.gnome.Showtime', '#4a4a4a', '#0e0e0e', 'media-playback-start')
simple('org.gnome.Weather', '#6cc6ff', '#1e74db', 'weather-few-clouds')
simple('org.kop316.vvmplayer', '#5b8def', '#1d3fa8', 'audio-input-microphone')
simple('os.arctos.Wallpapers', '#b68cff', '#5a2fd6', 'image-x-generic')
simple('cups', '#c8ccd2', '#6d727a', 'printer')

with open(os.path.join(OUT, 'index.theme'), 'w') as f:
    f.write('[Icon Theme]\nName=ArctOS\nComment=iOS 4-6 style glossy tiles (original artwork)\n'
            'Inherits=Adwaita,hicolor\n')
    f.write('Directories=' + ','.join('%dx%d/apps' % (s, s) for s in SIZES) + '\n\n')
    for s in SIZES:
        f.write('[%dx%d/apps]\nSize=%d\nContext=Applications\nType=Fixed\n\n' % (s, s, s))
print('done')
