import re

_HEX = re.compile(r"(#|0[xX])([0-9a-fA-F]+)")


def normalize_hex(value: str) -> str:
    match = _HEX.fullmatch(value.strip())
    if not match:
        raise ValueError(f"not a hex color: {value!r}")
    prefix, digits = match.group(1), match.group(2).lower()
    allowed_lengths = {3, 6, 8} if prefix == "#" else {6}
    if len(digits) not in allowed_lengths:
        raise ValueError(f"not a hex color: {value!r}")
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    return "#" + digits[:6]


def relative_luminance(hex_color: str) -> float:
    h = normalize_hex(hex_color)
    channels = [int(h[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    high, low = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)
