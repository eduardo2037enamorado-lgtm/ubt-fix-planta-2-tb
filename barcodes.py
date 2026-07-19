import re
from io import BytesIO
from urllib.parse import unquote, urlparse

import barcode
import qrcode
from barcode.writer import ImageWriter

from ubt_units import UBT_UNITS, is_valid_ubt, normalize_ubt

BARCODE_PATTERN = re.compile(r"^UBT[-\s]?(\d{3}-\d+)$", re.IGNORECASE)
URL_UBT_PATTERNS = (
    re.compile(r"/u/(\d{3}-\d+)(?:\?|$|/)", re.IGNORECASE),
    re.compile(r"[?&]ubt=(\d{3}-\d+)", re.IGNORECASE),
)


def ubt_to_barcode(ubt: str) -> str:
    if not is_valid_ubt(ubt):
        raise ValueError(f"UBT inválida: {ubt}")
    return f"UBT{ubt}"


def ubt_scan_url(base_url: str, ubt: str) -> str:
    base = (base_url or "").rstrip("/")
    return f"{base}/u/{ubt}"


def barcode_to_ubt(code: str) -> str | None:
    cleaned = (code or "").strip().upper().replace(" ", "")
    match = BARCODE_PATTERN.match(cleaned)
    if not match:
        return None
    return normalize_ubt(match.group(1))


def parse_scan_input(code: str) -> str | None:
    cleaned = unquote((code or "").strip())
    if not cleaned:
        return None

    direct = barcode_to_ubt(cleaned)
    if direct is not None:
        return direct

    normalized = normalize_ubt(cleaned)
    if normalized is not None:
        return normalized

    for pattern in URL_UBT_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            ubt = normalize_ubt(match.group(1))
            if ubt is not None:
                return ubt

    parsed = urlparse(cleaned)
    if parsed.path:
        path_match = re.search(r"/u/(\d{3}-\d+)$", parsed.path, re.IGNORECASE)
        if path_match:
            return normalize_ubt(path_match.group(1))

    return None


def generate_barcode_png(ubt: str) -> bytes:
    value = ubt_to_barcode(ubt)
    barcode_class = barcode.get_barcode_class("code128")
    image = barcode_class(value, writer=ImageWriter())
    buffer = BytesIO()
    image.write(
        buffer,
        options={
            "module_width": 0.35,
            "module_height": 12,
            "font_size": 14,
            "text_distance": 4,
            "quiet_zone": 4,
        },
    )
    return buffer.getvalue()


def generate_qr_png(content: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(content)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
