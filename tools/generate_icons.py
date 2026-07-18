"""Genera le icone PNG per la schermata Home di iPadOS."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static"


def create_icon(size: int) -> None:
    scale = size / 512
    image = Image.new("RGB", (size, size), "#1d6f5f")
    draw = ImageDraw.Draw(image)
    pad = round(90 * scale)
    draw.ellipse((pad, pad, size - pad, size - pad), fill="#f5f7f2")
    ring = round(114 * scale)
    draw.ellipse((ring, ring, size - ring, size - ring), outline="#d5a94e", width=max(3, round(12 * scale)))
    points_red = [(300, 198), (270, 272), (196, 302), (226, 228)]
    points_dark = [(270, 272), (226, 228), (300, 198)]
    draw.polygon([(round(x * scale), round(y * scale)) for x, y in points_red], fill="#b5483e")
    draw.polygon([(round(x * scale), round(y * scale)) for x, y in points_dark], fill="#18211f")
    r = round(15 * scale)
    center = round(256 * scale)
    draw.ellipse((center - r, center - r, center + r, center + r), fill="#d5a94e")
    image.save(OUT / f"icon-{size}.png", optimize=True)


if __name__ == "__main__":
    for icon_size in (180, 192, 512):
        create_icon(icon_size)
