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
    files: dict[str, SyntaxStyle]
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
    except UnicodeDecodeError as e:
        raise PaletteError(f"{path}: not UTF-8: {e}") from None
    except OSError as e:
        raise PaletteError(f"cannot read palette file {path}: {e.strerror}") from None
    return parse_palette(data)


def _check_hex(where: str, value: object) -> None:
    if not isinstance(value, str) or not _STRICT_HEX.fullmatch(value):
        raise PaletteError(f"{where}: expected #rrggbb, got {value!r}")


def _expect(where: str, value: object, kind: type, description: str) -> None:
    if not isinstance(value, kind):
        raise PaletteError(f"{where}: expected {description}, got {type(value).__name__}")


def parse_palette(data: dict) -> Palette:
    _expect("palette", data, dict, "an object")
    try:
        name = data["name"]
        colors = data["colors"]
        ansi = data["ansi"]
        terminal = data["terminal"]
        ui = data["ui"]
        syntax_raw = data["syntax"]
        files_raw = data["files"]
        text_colors = data["textColors"]
    except KeyError as e:
        raise PaletteError(f"missing top-level key: {e.args[0]}") from None
    for key, value in (("colors", colors), ("ansi", ansi), ("terminal", terminal), ("ui", ui), ("syntax", syntax_raw), ("files", files_raw)):
        _expect(key, value, dict, "an object")
    _expect("textColors", text_colors, list, "a list")
    if not text_colors:
        raise PaletteError("textColors: expected a non-empty list")

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

    def check_ref(where: str, color_name: object) -> None:
        _expect(where, color_name, str, "a color name")
        if color_name not in colors:
            raise PaletteError(f"{where}: unknown color name {color_name!r}")

    for key, value in terminal.items():
        check_ref(f"terminal.{key}", value)
    for key, value in ui.items():
        check_ref(f"ui.{key}", value)

    def parse_styles(section: str, raw: dict) -> dict[str, SyntaxStyle]:
        parsed = {}
        for key, value in raw.items():
            _expect(f"{section}.{key}", value, dict, "an object")
            color = value.get("color")
            if color is not None:
                check_ref(f"{section}.{key}.color", color)
            _expect(f"{section}.{key}.style", value.get("style", []), list, "a list")
            style = tuple(value.get("style", ()))
            unknown = set(style) - STYLES
            if unknown:
                raise PaletteError(f"{section}.{key}.style: unknown style(s) {sorted(unknown)}")
            parsed[key] = SyntaxStyle(color, style)
        return parsed

    syntax = parse_styles("syntax", syntax_raw)
    files = parse_styles("files", files_raw)

    for color_name in text_colors:
        check_ref("textColors", color_name)

    return Palette(name, dict(colors), dict(ansi), dict(terminal), dict(ui), syntax, files, tuple(text_colors))
