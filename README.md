# Deepwick

<p align="center"><img src="logo/deepwick.svg" width="160" alt="Deepwick logo"></p>

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

### Diff backgrounds

Solid blends of Green, Red, and Blue over Background, for diff lines and the
changed words inside them. Foreground stays at least 7:1 on each.

| Name | Hex | Role | Blend |
|---|---|---|---|
| diffAdded | `#152424` | added line background | 20% Green |
| diffRemoved | `#341123` | removed line background | 20% Red |
| diffChanged | `#142240` | changed line background | 20% Blue |
| diffAddedEmph | `#1D3528` | added words within a line | 30% Green |
| diffRemovedEmph | `#4C1828` | removed words within a line | 30% Red |
| diffText | `#1D3252` | changed words within a line | 30% Blue |

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

## 256-color palette

Some apps have no 24-bit color (Mutt, Taskwarrior, curses apps like ranger),
and some fall back to 256 colors (Vim without `termguicolors`). Their ports
use these hand-picked xterm-256 indices, from `xterm256` in `palette.json`.
Never compute an index in a port.

The picks start from the nearest-looking index, then keep colors with
different jobs apart (mint and sage), spread the dark backgrounds
(233 / 235 / 237) so panels and striped rows show, and tint the diff
backgrounds so add, remove and change stay distinct. Every text color is at
least 4.5:1 on 233, and Foreground is at least 4.5:1 on Selection and every
diff background, and no two colors share an index (`check-contrast`). Indices 0–15 are never used: terminals
theme them.

Ports that use the 16 ANSI slots on purpose (tig, nnn) stay on them, because
those follow the terminal's Deepwick theme exactly.

| Color | True color | Index | Index color |
|---|---|---|---|
| background | `#04041a` | 233 | `#121212` |
| surface | `#10192C` | 235 | `#262626` |
| overlay | `#1B2140` | 237 | `#3a3a3a` |
| selection | `#264F78` | 24 | `#005f87` |
| muted | `#6E7899` | 66 | `#5f8787` |
| comment | `#7A86A8` | 103 | `#8787af` |
| foreground | `#D4D4D4` | 188 | `#d7d7d7` |
| blue | `#569CD6` | 75 | `#5fafff` |
| lightBlue | `#9CDCFE` | 117 | `#87d7ff` |
| cyan | `#4FC1FF` | 39 | `#00afff` |
| teal | `#4EC9B0` | 43 | `#00d7af` |
| mint | `#B8D7A3` | 151 | `#afd7af` |
| yellow | `#DCDCAA` | 187 | `#d7d7af` |
| gold | `#D7BA7D` | 179 | `#d7af5f` |
| orange | `#CE9178` | 173 | `#d7875f` |
| rose | `#D16969` | 167 | `#d75f5f` |
| magenta | `#C586C0` | 176 | `#d787d7` |
| sage | `#B5CEA8` | 108 | `#87af87` |
| green | `#57A64A` | 71 | `#5faf5f` |
| red | `#F44747` | 203 | `#ff5f5f` |
| white | `#FFFFFF` | 231 | `#ffffff` |
| diffAdded | `#152424` | 23 | `#005f5f` |
| diffRemoved | `#341123` | 52 | `#5f0000` |
| diffChanged | `#142240` | 17 | `#00005f` |
| diffAddedEmph | `#1D3528` | 22 | `#005f00` |
| diffRemovedEmph | `#4C1828` | 88 | `#870000` |
| diffText | `#1D3252` | 18 | `#000087` |

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
syntax-highlighter ports follow this table. Scopes are listed in full because
the most specific matching scope wins: a port that only styles `punctuation`
will paint comment markers and string quotes Foreground.

| Role | TextMate scopes | Semantic tokens | Color | Style |
|---|---|---|---|---|
| comment | `comment`, `punctuation.definition.comment`, `string.quoted.docstring`, `keyword.other.documentation`, `storage.type.class.jsdoc`, `storage.type.class.doxygen` | `comment` | Comment | italic |
| keyword | `keyword`, `storage.type`, `storage.modifier`, `constant.language`, `constant.other`, `variable.language.this`, `keyword.other.using`, `keyword.other.namespace`, Python `self` / `cls` (`variable.parameter.function.language.special.self`, `variable.parameter.function.language.special.cls`) | `keyword` | Blue |  |
| control flow | `keyword.control`, `keyword.operator.new`, `keyword.operator.expression`, `keyword.operator.cast`, `keyword.operator.sizeof`, `keyword.control.import`, `keyword.control.export`, `keyword.control.from` | — | Magenta |  |
| operator / punctuation | `keyword.operator`, `punctuation` | `operator` | Foreground |  |
| type | `entity.name.type`, `entity.name.class`, `entity.name.namespace`, `entity.name.scope-resolution`, `support.class`, `support.type` | `namespace`, `type`, `class` | Teal |  |
| interface / enum / struct | `entity.name.type.interface`, `entity.name.type.enum`, `entity.name.type.enum-member`, `entity.name.type.struct`, `storage.type.struct` | `interface`, `enum`, `struct`, `typeParameter` | Mint |  |
| function | `entity.name.function`, `entity.name.function.member`, `support.function`, `meta.function-call`, `support.function.magic`, `entity.name.function.decorator` | `function`, `method` | Yellow |  |
| macro | `entity.name.function.macro`, `entity.name.function.preprocessor`, `entity.name.constant.preprocessor` | `macro` | Magenta |  |
| variable | `variable`, `entity.name.variable`, `variable.parameter`, `variable.other.property`, `variable.other.object.property`, `entity.other.attribute-name`, `support.type.property-name` (CSS, JSON) | `variable`, `parameter`, `property` | Light Blue |  |
| constant | `variable.other.constant` | `*.readonly`, `enumMember` | Cyan |  |
| string | `string`, `punctuation.definition.string`, `string.quoted.include`, `string.quoted.other.lt-gt.include`, `punctuation.definition.string.begin.include`, `punctuation.definition.string.end.include`, `support.constant.property-value` (CSS) | `string` | Orange |  |
| escape | `constant.character.escape`, `entity.other.attribute-name.class.css`, `entity.other.attribute-name.id.css`, `punctuation.definition.group.regexp`, `punctuation.definition.character-class.regexp` | — | Gold |  |
| regex | `string.regexp` | `regexp` | Rose |  |
| number | `constant.numeric` | `number` | Sage |  |
| tag | `entity.name.tag` | — | Blue |  |
| tag bracket | `punctuation.definition.tag` | — | Muted |  |
| preprocessor | `meta.preprocessor` | — | Muted | bold |
| preprocessor keyword | `keyword.control.directive`, `keyword.preprocessor` | — | Foreground | bold |
| label | `entity.name.label` | `label` | Foreground |  |
| heading | `markup.heading`, `entity.name.section.markdown` | — | Blue | bold |
| bold / italic | `markup.bold` / `markup.italic` | — | inherit | bold / italic |
| link / inline code | `markup.underline.link`, `markup.inline.raw`, `markup.fenced_code.block` | — | Orange |  |
| invalid | `invalid` | — | Red |  |
| deprecated | `invalid.deprecated` | `*.deprecated` | Foreground | strikethrough |

Source colors folded into the palette: struct `#86C691` → Mint; macro
`#BD63C5` → Magenta; preprocessor and tag bracket `#808080` → Muted; label
`#C8C8C8` → Foreground; include brackets `#E0B090` → Orange.

The machine-readable version of everything above is [`palette.json`](palette.json).

## File listing roles

For file managers and `ls`-style listings (dircolors, eza, yazi). Git status
columns use the UI roles above: added Green, modified Blue, removed Red,
untracked or new Teal.

| Role | Color | Style |
|---|---|---|
| `directory` | Blue | bold |
| `executable` | Green | bold |
| `symlink` | Cyan | |
| `brokenSymlink` | Red | |
| `special` | Gold | |
| `archive` | Rose | |
| `media` | Magenta | |
| `document` | Orange | |
| `source` | Yellow | |
| `temp` | Muted | |
| `permRead` | Yellow | |
| `permWrite` | Red | |
| `permExec` | Green | |
| `size` | Sage | |
| `user` | Light Blue | |
| `group` | Comment | |
| `date` | Comment | |

`special` covers sockets, FIFOs and devices; `media` covers images, audio and
video; `document` covers PDFs, office files and plain text; `source` covers
source code and build files; `temp` covers temporary, backup, swap and
compiled files.

## Engine limitations

Some roles cannot be expressed by every highlighting engine. Ports state the
ones that apply in their README Notes, using these descriptions:

- **Tree-sitter without semantic tokens** (Neovim without LSP, Helix, Zed): no
  capture distinguishes interfaces, enums, and structs from other types, so the
  Mint role appears only where a language server supplies semantic tokens.
  Function-like macro definitions are Magenta. Neovim also captures object-like
  macro names (`#define MAX 3`) as macros, but Helix and Zed give them only the
  generic all-caps constant capture, so they are Cyan there.
- **Tree-sitter without per-language overrides** (Helix): Python's `and`,
  `or`, `not`, `is` and membership `in` share the capture used for
  `typeof`/`new`, so they take the control-flow color; Python builtin types take
  the keyword color.
- **Zed's Python grammar** captures control-flow keywords (`if`, `for`,
  `return`, `import`, …) and `and`/`or`/`not`/`is`/`in` (including a for-loop's
  `in`) as plain keywords, so they
  take the keyword color (Blue); builtin types take the type color (Teal).
- **TextMate grammars** (bat): no scope marks macro uses (only definitions) or C/C++ builtin types
  separately from other identifiers and keywords.
- **Terminal-rendered formats**: zsh `region_highlight` has no italic, so
  zsh-syntax-highlighting comments are not italic; bat draws italics only with
  `--italic-text=always`; Ptyxis has no selection color.
- **KTextEditor** (Kate, KWrite, KDevelop): a C preprocessor line is one
  token, so macro names are not Magenta and directive keywords are not bold
  Foreground; C function, struct and macro-use names are plain. Python
  definition names and constants are not distinguished, and a for-loop's `in`
  shares the operator-keyword style. TypeScript has no interface/enum
  distinction (no Mint), and `new` is Blue.
- **GtkSourceView** (GNOME Text Editor, gedit, Builder, Meld): Python control
  flow is mostly Blue (version 4 gives every Python keyword one style; version 5
  makes `return`/`raise` Magenta but keeps `if`/`for` and the operator keywords
  `and`/`or`/`not`/`is`/`in` Blue), and
  JavaScript/TypeScript keywords share one style; Python docstrings are strings;
  JavaScript/TypeScript function and type names are plain; a C preprocessor
  line is one style; no Mint; Markdown fenced code is plain Orange.
- **Obsidian**: one keyword color and no control-flow token in either
  grammar, so control flow is Blue. In reading view (Prism), booleans and
  Python `None` share the number color (Sage) and Python `print` is a keyword
  (Blue); Live Preview (CodeMirror legacy modes) colors Python class names like
  functions (Yellow), calls like variables (Light Blue) and `None` like a
  keyword (Blue); its definition and meta tokens are Yellow (Python function
  names, decorators), which also makes JavaScript/TypeScript variable
  declarations and C preprocessor lines Yellow.
- **pi** (highlight.js through nine theme roles, colors only): comments are not
  italic; control flow is Blue; class names share the function color (Yellow);
  `True`/`None`/`undefined` share the number color (Sage); builtins (`print`,
  `console`) share the type color (Teal); docstrings and regex literals are
  Orange; decorators are Comment; diffs have no line backgrounds.

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
check-port [PATH]         # check a port repo: README credit + tested version, LICENSE, CI, screenshot, palette
check-contrast            # verify text colors meet 4.5:1 on Background
deepwick-swatches -o swatches.svg
```

`check-palette` recognizes `#rgb`, `#rrggbb`, `#rrggbbaa`, `0xRRGGBB`,
`rgb(R, G, B)` / `rgba(R, G, B, A)`, and a bare `R,G,B` when it is the whole
value of a `key=value` line (Konsole's `Color=4,4,26`). Alpha is ignored when
the base color is in the palette. Two optional
files at the root of a port tune it:

- `.palette-allow` — extra permitted colors, one per line, as hex or `R,G,B`.
  Comments start with `# ` (hash, space): `#000000  # pure black required by the format`
- `.palette-ignore` — glob patterns of paths to skip, e.g. `vendor/`

Port CI is a single job. It runs `check-port`, then the port's `tests/` with
pytest (plus `tests/requirements.txt` if present). Tests that need an app the
runner lacks skip themselves:

```yaml
name: check
on: [push, pull_request]
jobs:
  port:
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
