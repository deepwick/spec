import json
import re
from dataclasses import dataclass
from pathlib import Path

from deepwick_spec.color import normalize_hex

ANSI_SLOTS = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
ANSI_KEYS = ANSI_SLOTS + tuple("bright" + s.capitalize() for s in ANSI_SLOTS)
REQUIRED_COLORS = ("background", "foreground", "overlay")
STYLES = frozenset({"bold", "italic", "strikethrough", "underline"})
_STRICT_HEX = re.compile(r"#[0-9a-fA-F]{6}")


class PaletteError(ValueError):
    pass


@dataclass(frozen=True)
class SyntaxStyle:
    color: str | None
    style: tuple[str, ...] = ()


@dataclass(frozen=True)
class Palette:
    name: str
    colors: dict[str, str]
    ansi: dict[str, str]
    terminal: dict[str, str]
    ui: dict[str, str]
    syntax: dict[str, SyntaxStyle]
    text_colors: tuple[str, ...]

    def allowed_hex(self) -> frozenset[str]:
        return frozenset(normalize_hex(v) for v in (*self.colors.values(), *self.ansi.values()))


def default_palette_path() -> Path:
    bundled = Path(__file__).with_name("palette.json")
    if bundled.is_file():
        return bundled
    return Path(__file__).resolve().parent.parent / "palette.json"


def load_palette(path: Path | None = None) -> Palette:
    path = path or default_palette_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PaletteError(f"palette file not found: {path}") from None
    except json.JSONDecodeError as e:
        raise PaletteError(f"{path}: invalid JSON: {e}") from None
    return parse_palette(data)


def _check_hex(where: str, value: object) -> None:
    if not isinstance(value, str) or not _STRICT_HEX.fullmatch(value):
        raise PaletteError(f"{where}: expected #rrggbb, got {value!r}")


def parse_palette(data: dict) -> Palette:
    try:
        name = data["name"]
        colors = data["colors"]
        ansi = data["ansi"]
        terminal = data["terminal"]
        ui = data["ui"]
        syntax_raw = data["syntax"]
        text_colors = data["textColors"]
    except KeyError as e:
        raise PaletteError(f"missing top-level key: {e.args[0]}") from None

    for key, value in colors.items():
        _check_hex(f"colors.{key}", value)
    for required in REQUIRED_COLORS:
        if required not in colors:
            raise PaletteError(f"colors: required color {required!r} is missing")

    if set(ansi) != set(ANSI_KEYS):
        missing = sorted(set(ANSI_KEYS) - set(ansi))
        extra = sorted(set(ansi) - set(ANSI_KEYS))
        raise PaletteError(f"ansi: missing {missing}, unexpected {extra}")
    for key, value in ansi.items():
        _check_hex(f"ansi.{key}", value)

    def check_ref(where: str, color_name: str) -> None:
        if color_name not in colors:
            raise PaletteError(f"{where}: unknown color name {color_name!r}")

    for key, value in terminal.items():
        check_ref(f"terminal.{key}", value)
    for key, value in ui.items():
        check_ref(f"ui.{key}", value)

    syntax = {}
    for key, value in syntax_raw.items():
        color = value.get("color")
        if color is not None:
            check_ref(f"syntax.{key}.color", color)
        style = tuple(value.get("style", ()))
        unknown = set(style) - STYLES
        if unknown:
            raise PaletteError(f"syntax.{key}.style: unknown style(s) {sorted(unknown)}")
        syntax[key] = SyntaxStyle(color, style)

    for color_name in text_colors:
        check_ref("textColors", color_name)

    return Palette(name, dict(colors), dict(ansi), dict(terminal), dict(ui), syntax, tuple(text_colors))
