import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import colorcore as cc  # noqa: E402

DB = cc.NameDB()


@pytest.mark.parametrize("text,expected", [
    ("#1e90ff", "#1E90FF"), ("1E90FF", "#1E90FF"), ("#abc", "#AABBCC"),
    ("rgb(30,144,255)", "#1E90FF"), ("rgb(50%,0%,100%)", "#8000FF"), ("255 128 0", "#FF8000"),
    ("cmyk(0,100,100,0)", "#FF0000"), ("cmjn(0%,0%,0%,100%)", "#000000"), ("0,100,100,0", "#FF0000"),
    ("2003199", "#1E90FF"), ("dec:255", "#0000FF"), ("bgr:255", "#FF0000"),
    ("hsl(0,100%,50%)", "#FF0000"), ("hsv(120,100%,100%)", "#00FF00"),
    ("dodgerblue", "#1E90FF"), ("bleu roi", "#4169E1"), ("lab(53.24 80.09 67.20)", "#FF0000"),
])
def test_parse(text, expected):
    assert cc.parse_color(text, DB).hex == expected


def test_invalid():
    with pytest.raises(ValueError):
        cc.parse_color("pas une couleur", DB)


def test_cmyk_roundtrip():
    c = cc.Color(30, 144, 255)
    assert cc.Color(*cc.cmyk_to_rgb(*cc.rgb_to_cmyk(*c.rgb))) == c


def test_delta_e2000_reference():
    # paire de référence de Sharma et al. (2005)
    assert cc.delta_e2000((50, 2.6772, -79.7751), (50, 0, -82.7485)) == pytest.approx(2.0425, abs=1e-4)


def test_nearest_exact():
    d, name, hx = DB.nearest_css(cc.Color.from_hex("1e90ff"))[0]
    assert name == "dodgerblue" and d < 0.01


def test_db_loaded():
    assert len(DB) > 30000
