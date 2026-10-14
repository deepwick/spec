# Deepwick

A deep navy theme with Visual Studio 2022's familiar syntax colors, for every
tool you use. This repository is the **specification**: the palette, the rules
every port follows, and the tools that check them.

> Deepwick is an unofficial theme derived from
> [Polywick Blue](https://vscode.polywickstudio.net) by Polywick Studio (MIT).
> Not affiliated with Polywick Studio.

![Deepwick palette](swatches.svg)

## Palette

Contrast is the WCAG 2.x ratio against Background. Every color used for text is
at least 4.5:1.

| Name | Hex | Role | Contrast |
|---|---|---|---|
| Background | `#04041a` | main surface | — |
| Surface | `#10192C` | current line, panels, status bars | 1.15 |
| Overlay | `#1B2140` | borders, inactive UI | 1.29 |
| Selection | `#264F78` | selection, visual mode | 2.38 |
| Muted | `#6E7899` | line numbers, hints, tag brackets | 4.64 |
| Comment | `#7A86A8` | comments, *italic* | 5.59 |
| Foreground | `#D4D4D4` | default text, operators | 13.66 |
| Blue | `#569CD6` | keywords, language constants, tags, headings | 6.87 |
| Light Blue | `#9CDCFE` | variables, parameters, properties | 13.57 |
| Cyan | `#4FC1FF` | readonly variables, enum members | 10.03 |
| Teal | `#4EC9B0` | types, classes, namespaces | 9.93 |
| Mint | `#B8D7A3` | interfaces, enums, type parameters, structs | 12.81 |
| Yellow | `#DCDCAA` | functions, methods, decorators | 14.32 |
| Gold | `#D7BA7D` | string escapes, CSS selectors, regex groups | 10.80 |
| Orange | `#CE9178` | strings, links, inline code | 7.66 |
| Rose | `#D16969` | regular expressions | 5.72 |
| Magenta | `#C586C0` | control flow, import/export, macros | 7.27 |
| Sage | `#B5CEA8` | numbers | 11.91 |
| Green | `#57A64A` | success, git added | 6.71 |
| Red | `#F44747` | errors, invalid, git removed | 5.63 |
| White | `#FFFFFF` | ANSI bright white, emphasis | 20.24 |

## ANSI 16

| Color | Normal | Bright |
|---|---|---|
| black | `#1B2140` (Overlay) | `#6E7899` (Muted) |
| red | `#F44747` (Red) | `#FF7A7A` |
| green | `#57A64A` (Green) | `#7FC46E` |
| yellow | `#DCDCAA` (Yellow) | `#F2F2C4` |
| blue | `#569CD6` (Blue) | `#9CDCFE` (Light Blue) |
| magenta | `#C586C0` (Magenta) | `#E0A8DC` |
| cyan | `#4EC9B0` (Teal) | `#7FE5CF` |
| white | `#D4D4D4` (Foreground) | `#FFFFFF` (White) |

The bright-only values `#FF7A7A`, `#7FC46E`, `#F2F2C4`, `#E0A8DC`, and
`#7FE5CF` may be used only in ANSI slots.

Terminal extras: background Background, foreground Foreground, cursor
Foreground, cursor text Background, selection Selection with Foreground text,
bold text Foreground.

## UI roles

| Role | Color |
|---|---|
| error | Red |
| warning | Yellow |
| info | Cyan |
| hint | Muted |
| success, git added | Green |
| git removed | Red |
| git modified | Blue |
| git untracked, new file | Teal |
| focused border, accent | Blue |
| inactive border | Overlay |
| search match | Selection background |
| current search match | Gold text on Selection |

## Syntax roles

Derived from Polywick Blue's TextMate and semantic token rules. Editor and
syntax-highlighter ports follow this table.

| Role | TextMate scopes (representative) | Semantic tokens | Color | Style |
|---|---|---|---|---|
| comment | `comment`, docstrings, doc tags | `comment` | Comment | italic |
| keyword | `keyword`, `storage.type`, `storage.modifier`, `constant.language`, `this`, `self` | `keyword` | Blue | |
| control flow | `keyword.control`, `keyword.operator.new`, import/export | — | Magenta | |
| operator | `keyword.operator`, `punctuation` | `operator` | Foreground | |
| type | `entity.name.type`, `entity.name.class`, `support.class` | `namespace`, `type`, `class` | Teal | |
| interface, enum, struct | `entity.name.type.interface/enum/struct` | `interface`, `enum`, `struct`, `typeParameter` | Mint | |
| function | `entity.name.function`, `support.function`, decorators | `function`, `method` | Yellow | |
| macro | `entity.name.function.macro` | `macro` | Magenta | |
| variable | `variable`, `variable.parameter`, properties, attribute names | `variable`, `parameter`, `property` | Light Blue | |
| constant | `variable.other.constant` | `*.readonly`, `enumMember` | Cyan | |
| string | `string`, include paths, CSS values | `string` | Orange | |
| escape | `constant.character.escape`, CSS selectors, regex groups | — | Gold | |
| regex | `string.regexp` | `regexp` | Rose | |
| number | `constant.numeric` | `number` | Sage | |
| tag | `entity.name.tag` | — | Blue | |
| tag bracket | `punctuation.definition.tag` | — | Muted | |
| preprocessor | `meta.preprocessor` | — | Muted | bold |
| preprocessor keyword | `keyword.control.directive` | — | Foreground | |
| label | `entity.name.label` | `label` | Foreground | |
| heading | `markup.heading` | — | Blue | bold |
| bold, italic | `markup.bold`, `markup.italic` | — | inherit | bold, italic |
| link, inline code | `markup.underline.link`, `markup.inline.raw` | — | Orange | |
| invalid | `invalid` | — | Red | |
| deprecated | `invalid.deprecated` | `*.deprecated` | Foreground | strikethrough |

The machine-readable version of everything above is [`palette.json`](palette.json).

## Rules for ports

Each port lives in its own repository, `deepwick/<app>`.

1. **Palette only.** Every hex color in a port must be in `palette.json`.
   `check-palette` enforces this.
2. **Same roles, same colors.** Map to the UI and syntax roles above. Document
   app-specific choices in the port's README; propose general ones here.
3. **Italic comments** wherever the format supports it.
4. **Copy-pasteable install,** tested on the latest stable app version, which
   the README states.
5. **Credit line** in every README (see the top of this file).
6. **Screenshots** use the standard content in [`samples/`](samples):
   `sample.py`, `sample.ts`, `sample.c`, and `sample.md` for editors and
   highlighters; `terminal.sh` for terminals.

A port repository looks like:

```
deepwick/<app>/
├── <theme file(s)>
├── README.md
├── screenshot.png
├── .github/workflows/check.yml
├── .palette-allow          # only if needed
└── LICENSE
```

## Tools

Python 3.11+, no dependencies.

```sh
pip install "deepwick-spec @ git+https://github.com/deepwick/spec@main"

check-palette [PATH]      # report colors not in the palette (exit 1 if any)
check-contrast            # verify text colors meet 4.5:1 on Background
deepwick-swatches -o swatches.svg
```

`check-palette` recognizes `#rgb`, `#rrggbb`, `#rrggbbaa`, and `0xRRGGBB`.
Alpha suffixes are fine when the base color is in the palette. Two optional
files at the root of a port tune it:

- `.palette-allow` — extra permitted colors, one per line. Comments start with
  `# ` (hash, space): `#000000  # pure black required by the format`
- `.palette-ignore` — glob patterns of paths to skip, e.g. `vendor/`

Port CI is a single job:

```yaml
name: check
on: [push, pull_request]
jobs:
  palette:
    uses: deepwick/spec/.github/workflows/check.yml@main
```

## Development

```sh
uv run pytest
uv run check-contrast
uv run deepwick-swatches -o swatches.svg   # after editing palette.json
```

## License

MIT. See [LICENSE](LICENSE).
