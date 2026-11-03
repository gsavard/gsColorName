"""Conversions de couleurs, analyse de codes et recherche de noms (sans dépendance)."""
from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass


def resource_path(*parts: str) -> str:
    """Chemin d'une ressource, en mode source comme en exécutable PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

# ---------------------------------------------------------------- noms CSS
CSS_NAMES = {
    "aliceblue": "f0f8ff", "antiquewhite": "faebd7", "aqua": "00ffff", "aquamarine": "7fffd4",
    "azure": "f0ffff", "beige": "f5f5dc", "bisque": "ffe4c4", "black": "000000",
    "blanchedalmond": "ffebcd", "blue": "0000ff", "blueviolet": "8a2be2", "brown": "a52a2a",
    "burlywood": "deb887", "cadetblue": "5f9ea0", "chartreuse": "7fff00", "chocolate": "d2691e",
    "coral": "ff7f50", "cornflowerblue": "6495ed", "cornsilk": "fff8dc", "crimson": "dc143c",
    "cyan": "00ffff", "darkblue": "00008b", "darkcyan": "008b8b", "darkgoldenrod": "b8860b",
    "darkgray": "a9a9a9", "darkgreen": "006400", "darkkhaki": "bdb76b", "darkmagenta": "8b008b",
    "darkolivegreen": "556b2f", "darkorange": "ff8c00", "darkorchid": "9932cc", "darkred": "8b0000",
    "darksalmon": "e9967a", "darkseagreen": "8fbc8f", "darkslateblue": "483d8b",
    "darkslategray": "2f4f4f", "darkturquoise": "00ced1", "darkviolet": "9400d3",
    "deeppink": "ff1493", "deepskyblue": "00bfff", "dimgray": "696969", "dodgerblue": "1e90ff",
    "firebrick": "b22222", "floralwhite": "fffaf0", "forestgreen": "228b22", "fuchsia": "ff00ff",
    "gainsboro": "dcdcdc", "ghostwhite": "f8f8ff", "gold": "ffd700", "goldenrod": "daa520",
    "gray": "808080", "green": "008000", "greenyellow": "adff2f", "honeydew": "f0fff0",
    "hotpink": "ff69b4", "indianred": "cd5c5c", "indigo": "4b0082", "ivory": "fffff0",
    "khaki": "f0e68c", "lavender": "e6e6fa", "lavenderblush": "fff0f5", "lawngreen": "7cfc00",
    "lemonchiffon": "fffacd", "lightblue": "add8e6", "lightcoral": "f08080", "lightcyan": "e0ffff",
    "lightgoldenrodyellow": "fafad2", "lightgray": "d3d3d3", "lightgreen": "90ee90",
    "lightpink": "ffb6c1", "lightsalmon": "ffa07a", "lightseagreen": "20b2aa",
    "lightskyblue": "87cefa", "lightslategray": "778899", "lightsteelblue": "b0c4de",
    "lightyellow": "ffffe0", "lime": "00ff00", "limegreen": "32cd32", "linen": "faf0e6",
    "magenta": "ff00ff", "maroon": "800000", "mediumaquamarine": "66cdaa", "mediumblue": "0000cd",
    "mediumorchid": "ba55d3", "mediumpurple": "9370db", "mediumseagreen": "3cb371",
    "mediumslateblue": "7b68ee", "mediumspringgreen": "00fa9a", "mediumturquoise": "48d1cc",
    "mediumvioletred": "c71585", "midnightblue": "191970", "mintcream": "f5fffa",
    "mistyrose": "ffe4e1", "moccasin": "ffe4b5", "navajowhite": "ffdead", "navy": "000080",
    "oldlace": "fdf5e6", "olive": "808000", "olivedrab": "6b8e23", "orange": "ffa500",
    "orangered": "ff4500", "orchid": "da70d6", "palegoldenrod": "eee8aa", "palegreen": "98fb98",
    "paleturquoise": "afeeee", "palevioletred": "db7093", "papayawhip": "ffefd5",
    "peachpuff": "ffdab9", "peru": "cd853f", "pink": "ffc0cb", "plum": "dda0dd",
    "powderblue": "b0e0e6", "purple": "800080", "rebeccapurple": "663399", "red": "ff0000",
    "rosybrown": "bc8f8f", "royalblue": "4169e1", "saddlebrown": "8b4513", "salmon": "fa8072",
    "sandybrown": "f4a460", "seagreen": "2e8b57", "seashell": "fff5ee", "sienna": "a0522d",
    "silver": "c0c0c0", "skyblue": "87ceeb", "slateblue": "6a5acd", "slategray": "708090",
    "snow": "fffafa", "springgreen": "00ff7f", "steelblue": "4682b4", "tan": "d2b48c",
    "teal": "008080", "thistle": "d8bfd8", "tomato": "ff6347", "turquoise": "40e0d0",
    "violet": "ee82ee", "wheat": "f5deb3", "white": "ffffff", "whitesmoke": "f5f5f5",
    "yellow": "ffff00", "yellowgreen": "9acd32",
}

# Quelques noms français courants (pour la saisie et un nom FR de base)
FR_NAMES = {
    "noir": "000000", "blanc": "ffffff", "rouge": "ff0000", "vert": "008000", "bleu": "0000ff",
    "jaune": "ffff00", "orange": "ffa500", "violet": "8000ff", "rose": "ffc0cb", "gris": "808080",
    "marron": "8b4513", "brun": "8b4513", "beige": "f5f5dc", "turquoise": "40e0d0",
    "cyan": "00ffff", "magenta": "ff00ff", "or": "ffd700", "argent": "c0c0c0",
    "bordeaux": "6d071a", "marine": "000080", "bleu marine": "000080", "bleu ciel": "87ceeb",
    "bleu roi": "4169e1", "bleu nuit": "191970", "vert olive": "808000", "olive": "808000",
    "vert pomme": "34c924", "vert sapin": "095228", "vert émeraude": "01d758",
    "émeraude": "01d758", "kaki": "94812b", "corail": "ff7f50", "saumon": "fa8072",
    "framboise": "c72c48", "fuchsia": "fd3f92", "lavande": "e6e6fa", "lilas": "b666d2",
    "mauve": "d473d4", "pourpre": "9e0e40", "indigo": "4b0082", "ocre": "dfaf2c",
    "moutarde": "c7a02d", "sable": "e0cda9", "crème": "fdf1b8", "ivoire": "fffff0",
    "chocolat": "5a3a22", "caramel": "7e5835", "taupe": "463f32", "anthracite": "303030",
    "ardoise": "5a5e6b", "écru": "fef3e2", "céladon": "83a697", "vermillon": "db1702",
    "carmin": "960018", "cerise": "bb0b0b", "grenat": "6e0b14", "améthyste": "884da7",
    "aubergine": "370028", "prune": "811453", "pêche": "fdbfb7", "abricot": "e67e30",
    "citron": "f7ff3c", "safran": "f3d617", "cuivre": "b36700", "bronze": "614e1a",
    "acier": "4682b4", "azur": "007fff", "cobalt": "22427c", "turquin": "425b8a",
    "bleu canard": "048b9a", "sarcelle": "008080", "menthe": "16b84e", "jade": "87e990",
}


# ---------------------------------------------------------------- conversions
def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    c = _clamp(c)
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


_D65 = (0.95047, 1.0, 1.08883)


def rgb_to_xyz(r, g, b):
    r, g, b = (srgb_to_linear(x / 255) for x in (r, g, b))
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    return x, y, z


def xyz_to_rgb(x, y, z):
    r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b = x * 0.0556434 + y * -0.2040259 + z * 1.0572252
    return tuple(round(linear_to_srgb(c) * 255) for c in (r, g, b))


def xyz_to_lab(x, y, z):
    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x / _D65[0]), f(y / _D65[1]), f(z / _D65[2])
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def lab_to_xyz(L, a, b):
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    def finv(t):
        return t ** 3 if t ** 3 > 216 / 24389 else (116 * t - 16) / (24389 / 27)
    return finv(fx) * _D65[0], finv(fy) * _D65[1], finv(fz) * _D65[2]


def rgb_to_lab(r, g, b):
    return xyz_to_lab(*rgb_to_xyz(r, g, b))


def lab_to_lch(L, a, b):
    c = math.hypot(a, b)
    h = math.degrees(math.atan2(b, a)) % 360
    return L, c, h


def rgb_to_hsl(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    d = mx - mn
    if d == 0:
        return 0.0, 0.0, l * 100
    s = d / (1 - abs(2 * l - 1))
    h = _hue(r, g, b, mx, d)
    return h, s * 100, l * 100


def rgb_to_hsv(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    s = 0 if mx == 0 else d / mx
    h = 0.0 if d == 0 else _hue(r, g, b, mx, d)
    return h, s * 100, mx * 100


def _hue(r, g, b, mx, d):
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return (h * 60) % 360


def hsl_to_rgb(h, s, l):
    s, l = s / 100, l / 100
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    r, g, b = _sector(h, c, x)
    return tuple(round((v + m) * 255) for v in (r, g, b))


def hsv_to_rgb(h, s, v):
    s, v = s / 100, v / 100
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    r, g, b = _sector(h, c, x)
    return tuple(round((q + m) * 255) for q in (r, g, b))


def _sector(h, c, x):
    h %= 360
    if h < 60:
        return c, x, 0
    if h < 120:
        return x, c, 0
    if h < 180:
        return 0, c, x
    if h < 240:
        return 0, x, c
    if h < 300:
        return x, 0, c
    return c, 0, x


def rgb_to_cmyk(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    k = 1 - max(r, g, b)
    if k >= 1:
        return 0.0, 0.0, 0.0, 100.0
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return c * 100, m * 100, y * 100, k * 100


def cmyk_to_rgb(c, m, y, k):
    c, m, y, k = (v / 100 for v in (c, m, y, k))
    return tuple(round(255 * (1 - v) * (1 - k)) for v in (c, m, y))


def rgb_to_hwb(r, g, b):
    h, _, _ = rgb_to_hsv(r, g, b)
    w = min(r, g, b) / 255 * 100
    bl = (1 - max(r, g, b) / 255) * 100
    return h, w, bl


def luminance(r, g, b):
    return 0.2126 * srgb_to_linear(r / 255) + 0.7152 * srgb_to_linear(g / 255) + 0.0722 * srgb_to_linear(b / 255)


def contrast_ratio(rgb1, rgb2):
    l1, l2 = sorted((luminance(*rgb1), luminance(*rgb2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


# ---------------------------------------------------------------- ΔE
def delta_e76(lab1, lab2):
    return math.dist(lab1, lab2)


def delta_e2000(lab1, lab2):
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6)) - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dtheta = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dtheta)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


# ---------------------------------------------------------------- couleur
@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    @classmethod
    def from_hex(cls, h: str) -> "Color":
        h = h.lstrip("#")
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        return cls(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    @property
    def rgb(self):
        return (self.r, self.g, self.b)

    @property
    def hex(self):
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    @property
    def lab(self):
        return rgb_to_lab(*self.rgb)

    def formats(self) -> list[tuple[str, str]]:
        r, g, b = self.rgb
        h, s, l = rgb_to_hsl(r, g, b)
        hv, sv, vv = rgb_to_hsv(r, g, b)
        c, m, y, k = rgb_to_cmyk(r, g, b)
        hw, ww, bw = rgb_to_hwb(r, g, b)
        x, yy, z = rgb_to_xyz(r, g, b)
        L, A, B = self.lab
        _, C, H = lab_to_lch(L, A, B)
        dec = (r << 16) | (g << 8) | b
        colorref = (b << 16) | (g << 8) | r
        rgb565 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        return [
            ("HEX", self.hex),
            ("HEX (court)", self.short_hex() or "—"),
            ("RGB", f"rgb({r}, {g}, {b})"),
            ("RGB %", f"rgb({r/2.55:.1f}%, {g/2.55:.1f}%, {b/2.55:.1f}%)"),
            ("RGB normalisé (0–1)", f"{r/255:.4f}, {g/255:.4f}, {b/255:.4f}"),
            ("HSL / TSL", f"hsl({h:.0f}, {s:.1f}%, {l:.1f}%)"),
            ("HSV / HSB / TSV", f"hsv({hv:.0f}, {sv:.1f}%, {vv:.1f}%)"),
            ("HWB", f"hwb({hw:.0f} {ww:.1f}% {bw:.1f}%)"),
            ("CMYK / CMJN", f"cmyk({c:.0f}%, {m:.0f}%, {y:.0f}%, {k:.0f}%)"),
            ("CIE Lab (D65)", f"lab({L:.2f} {A:.2f} {B:.2f})"),
            ("CIE LCh (D65)", f"lch({L:.2f} {C:.2f} {H:.1f})"),
            ("CIE XYZ", f"{x*100:.3f}, {yy*100:.3f}, {z*100:.3f}"),
            ("Décimal (0xRRGGBB)", str(dec)),
            ("Hexadécimal 0x", f"0x{dec:06X}"),
            ("Décimal BGR (Win32/VBA COLORREF)", str(colorref)),
            ("ARGB (Android/.NET)", f"#FF{self.hex[1:]}"),
            ("RGB565 (16 bits)", f"0x{rgb565:04X}  ({rgb565})"),
            ("Binaire", f"{r:08b} {g:08b} {b:08b}"),
            ("Qt / QColor", f"QColor({r}, {g}, {b})"),
            ("Swift / UIColor", f"UIColor(red: {r/255:.3f}, green: {g/255:.3f}, blue: {b/255:.3f}, alpha: 1)"),
            ("Luminance relative", f"{luminance(r, g, b):.4f}"),
            ("Contraste blanc / noir", f"{contrast_ratio(self.rgb, (255,255,255)):.2f}:1  /  "
                                        f"{contrast_ratio(self.rgb, (0,0,0)):.2f}:1"),
        ]

    def short_hex(self):
        h = self.hex[1:]
        if h[0] == h[1] and h[2] == h[3] and h[4] == h[5]:
            return "#" + h[0] + h[2] + h[4]
        return None

    def harmonies(self):
        h, s, l = rgb_to_hsl(*self.rgb)
        def at(dh, dl=0):
            return Color(*hsl_to_rgb((h + dh) % 360, s, _clamp(l + dl, 0, 100)))
        return {
            "Complémentaire": [self, at(180)],
            "Analogues": [at(-30), self, at(30)],
            "Triade": [self, at(120), at(240)],
            "Complémentaires adjacentes": [self, at(150), at(210)],
            "Tétrade": [self, at(90), at(180), at(270)],
            "Nuances (clair → foncé)": [at(0, d) for d in (30, 15, 0, -15, -30)],
        }


# ---------------------------------------------------------------- analyse saisie
_NUM = r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?"


def _nums(s):
    return [float(x) for x in re.findall(_NUM, s)]


def _pct_or(v: str, scale: float):
    """'50%' -> 0.5*scale ; '0.5' (<=1) ambiguous handled by caller."""
    v = v.strip()
    if v.endswith("%"):
        return float(v[:-1]) / 100 * scale
    return float(v)


def parse_color(text: str, names: "NameDB | None" = None) -> Color:
    s = text.strip()
    if not s:
        raise ValueError("Saisie vide")
    low = s.lower()

    # préfixes explicites pour lever l'ambiguïté
    m = re.fullmatch(r"(?:dec|déc|d)\s*[:=]\s*(\d+)", low)
    if m:
        v = int(m.group(1))
        if v > 0xFFFFFF:
            raise ValueError("Valeur décimale trop grande (max 16777215)")
        return Color((v >> 16) & 255, (v >> 8) & 255, v & 255)
    m = re.fullmatch(r"bgr\s*[:=]\s*(\d+)", low)
    if m:
        v = int(m.group(1))
        return Color(v & 255, (v >> 8) & 255, (v >> 16) & 255)

    # hex
    m = re.fullmatch(r"(?:#|0x)?([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})", low)
    if m and (low.startswith(("#", "0x")) or re.search(r"[a-f]", low) or len(m.group(1)) == 6):
        h = m.group(1)
        if len(h) == 8:  # suppose RRGGBBAA (CSS) ; ignore alpha
            h = h[:6]
        return Color.from_hex(h)

    func = re.match(r"^([a-z]+)\s*\((.*)\)\s*$", low)
    if func:
        kind, body = func.group(1), func.group(2)
        parts = [p for p in re.split(r"[,\s/]+", body.strip()) if p]
        if kind in ("rgb", "rgba"):
            vals = [_pct_or(p, 255) for p in parts[:3]]
            return Color(*(round(_clamp(v, 0, 255)) for v in vals))
        if kind in ("hsl", "hsla", "tsl"):
            h = float(parts[0].replace("deg", ""))
            sv, lv = (float(p.rstrip("%")) for p in parts[1:3])
            if sv <= 1 and lv <= 1 and "%" not in body:
                sv, lv = sv * 100, lv * 100
            return Color(*hsl_to_rgb(h, sv, lv))
        if kind in ("hsv", "hsb", "tsv"):
            h = float(parts[0].replace("deg", ""))
            sv, vv = (float(p.rstrip("%")) for p in parts[1:3])
            if sv <= 1 and vv <= 1 and "%" not in body:
                sv, vv = sv * 100, vv * 100
            return Color(*hsv_to_rgb(h, sv, vv))
        if kind in ("cmyk", "cmjn", "device-cmyk"):
            vals = [float(p.rstrip("%")) for p in parts[:4]]
            if all(v <= 1 for v in vals) and "%" not in body:
                vals = [v * 100 for v in vals]
            return Color(*cmyk_to_rgb(*vals))
        if kind == "lab":
            L, a, b = (float(p.rstrip("%")) for p in parts[:3])
            return Color(*xyz_to_rgb(*lab_to_xyz(L, a, b)))
        if kind == "lch":
            L, C, H = (float(p.rstrip("%").replace("deg", "")) for p in parts[:3])
            a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
            return Color(*xyz_to_rgb(*lab_to_xyz(L, a, b)))
        if kind in ("hwb",):
            h = float(parts[0].replace("deg", ""))
            w, bl = (float(p.rstrip("%")) / 100 for p in parts[1:3])
            if w + bl >= 1:
                g = round(w / (w + bl) * 255)
                return Color(g, g, g)
            base = hsv_to_rgb(h, 100, 100)
            return Color(*(round((c / 255 * (1 - w - bl) + w) * 255) for c in base))
        if kind in ("qcolor", "color"):
            n = _nums(body)
            return Color(*(round(_clamp(v, 0, 255)) for v in n[:3]))
        raise ValueError(f"Fonction de couleur inconnue : {kind}()")

    # liste de 3 ou 4 nombres : RGB ou CMYK
    if re.fullmatch(r"[\d.\s,;%]+", low) and len(_nums(low)) in (3, 4):
        n = _nums(low)
        if len(n) == 3:
            if all(v <= 1 for v in n) and "." in low:
                n = [v * 255 for v in n]
            return Color(*(round(_clamp(v, 0, 255)) for v in n))
        if all(v <= 1 for v in n) and "." in low:
            n = [v * 100 for v in n]
        return Color(*cmyk_to_rgb(*n))

    # entier décimal
    if re.fullmatch(r"\d+", low):
        v = int(low)
        if v > 0xFFFFFF:
            raise ValueError("Valeur décimale trop grande (max 16777215)")
        return Color((v >> 16) & 255, (v >> 8) & 255, v & 255)

    # noms
    key = re.sub(r"[\s_-]+", "", low)
    if key in CSS_NAMES:
        return Color.from_hex(CSS_NAMES[key])
    if low in FR_NAMES:
        return Color.from_hex(FR_NAMES[low])
    if names:
        hx = names.lookup(s)
        if hx:
            return Color.from_hex(hx)
    raise ValueError(f"Impossible d'interpréter « {text} »")


# ---------------------------------------------------------------- base de noms
class NameDB:
    """Base d'environ 30 000 noms (color-name-list, MIT) + CSS + FR."""

    def __init__(self, path: str | None = None):
        self.entries: list[tuple[str, str, tuple]] = []  # (nom, hex, lab)
        self.by_name: dict[str, str] = {}
        path = path or resource_path("data", "colornames.json")
        data = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        for hx, name in data.items():
            self._add(name, hx)
        self.css = [(n, h, rgb_to_lab(*Color.from_hex(h).rgb)) for n, h in CSS_NAMES.items()]
        self.fr = [(n, h, rgb_to_lab(*Color.from_hex(h).rgb)) for n, h in FR_NAMES.items()]
        for n, h in CSS_NAMES.items():
            self.by_name.setdefault(n, h)

    def _add(self, name, hx):
        hx = hx.lstrip("#").lower()
        self.entries.append((name, hx, rgb_to_lab(*Color.from_hex(hx).rgb)))
        self.by_name.setdefault(name.lower(), hx)

    def __len__(self):
        return len(self.entries)

    def lookup(self, name: str):
        return self.by_name.get(name.strip().lower())

    @staticmethod
    def _nearest(pool, lab, n):
        pre = sorted(pool, key=lambda e: delta_e76(lab, e[2]))[: max(n * 6, 30)]
        scored = [(delta_e2000(lab, e[2]), e[0], e[1]) for e in pre]
        scored.sort()
        return scored[:n]

    def nearest(self, color: Color, n=10):
        return self._nearest(self.entries or self.css, color.lab, n)

    def nearest_css(self, color: Color, n=1):
        return self._nearest(self.css, color.lab, n)

    def nearest_fr(self, color: Color, n=1):
        return self._nearest(self.fr, color.lab, n)


def delta_label(de: float) -> str:
    if de < 1:
        return "identique à l'œil"
    if de < 2:
        return "quasi identique"
    if de < 5:
        return "très proche"
    if de < 10:
        return "proche"
    return "approximatif"
