"""Certificate image generator.

Replicates the old TDP flow (certification-image) using Pillow:
downloads the certificate PNG template from S3, draws certification
details on it, and returns the result as PNG bytes or PDF bytes.
"""
from __future__ import annotations

import io
import logging
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from app.utils.s3_storage import download_file

logger = logging.getLogger("eam.utils.cert_image")

TEMPLATE_S3_KEY = "pm/eam/Certificate"


@lru_cache(maxsize=1)
def _load_template() -> bytes:
    """Download & cache the template PNG from S3 (called once)."""
    return download_file(TEMPLATE_S3_KEY)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a TrueType font, fall back to default."""
    # Try common system fonts
    font_candidates = (
        ["/System/Library/Fonts/Helvetica.ttc",          # macOS
         "/System/Library/Fonts/SFNSMono.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "arial.ttf", "Arial.ttf"]
    )
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    # fallback
    return ImageFont.load_default()


def generate_cert_image(
    simple_id: str,
    certificate_type: str,
    user_name: str,
    issue_date: str,
    expiration_date: str,
) -> bytes:
    """Return PNG bytes of the rendered certificate."""
    template_bytes = _load_template()
    img = Image.open(io.BytesIO(template_bytes)).copy()
    draw = ImageDraw.Draw(img)

    w = img.width  # 1500

    # Fonts matching old system sizes (old system canvas was also 1500 wide)
    font_32 = _get_font(32)
    font_28 = _get_font(28)
    font_52_bold = _get_font(52, bold=True)
    font_38_bold = _get_font(38, bold=True)
    font_24 = _get_font(24)

    black = "#000000"
    dark = "#36393d"

    # Centered text helper
    def draw_centered(text: str, y: int, font, fill: str = black):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) / 2, y), text, font=font, fill=fill)

    # "This certifies that"
    draw_centered("This certifies that", 470, font_32, black)

    # User name (bold, larger)
    draw_centered(user_name or "", 550, font_52_bold, dark)

    # "has successfully passed all requirements for"
    draw_centered("has successfully passed all requirements for", 630, font_28, black)

    # Certificate type (bold)
    draw_centered(certificate_type or "", 710, font_38_bold, dark)

    # Detail labels (right-aligned at x=345, values left-aligned at x=350)
    details = [
        ("Certificate No.", simple_id or "", 840),
        ("Issue Date", (issue_date or "").split(" ")[0].split("T")[0], 895),
        ("Expiration Date", (expiration_date or "").split(" ")[0].split("T")[0], 950),
    ]
    for label, value, y in details:
        # Right-aligned label
        bbox = draw.textbbox((0, 0), label, font=font_24)
        lw = bbox[2] - bbox[0]
        draw.text((345 - lw, y), label, font=font_24, fill=black)
        # Left-aligned value with colon
        draw.text((350, y), f": {value}", font=font_24, fill=black)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_cert_pdf(
    simple_id: str,
    certificate_type: str,
    user_name: str,
    issue_date: str,
    expiration_date: str,
) -> bytes:
    """Return PDF bytes containing the rendered certificate image at 40% scale."""
    png_bytes = generate_cert_image(
        simple_id, certificate_type, user_name, issue_date, expiration_date,
    )
    img = Image.open(io.BytesIO(png_bytes))
    scale = 0.4
    page_w = img.width * scale
    page_h = img.height * scale

    # Use Pillow to create a simple PDF
    # Resize the image to 40% and save as PDF
    resized = img.resize((int(page_w), int(page_h)), Image.LANCZOS)
    if resized.mode == "RGBA":
        # PDF doesn't support RGBA, convert
        background = Image.new("RGB", resized.size, (255, 255, 255))
        background.paste(resized, mask=resized.split()[3])
        resized = background

    buf = io.BytesIO()
    resized.save(buf, format="PDF")
    return buf.getvalue()
