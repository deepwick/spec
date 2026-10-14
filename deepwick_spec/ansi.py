import re

SGR = re.compile(r"\x1b\[([0-9;:]*)m")


def _blank() -> dict:
    return {"fg": None, "bg": None, "bold": False, "italic": False, "underline": False, "reverse": False}


def _apply_group(style: dict, group: str) -> None:
    sub = [int(p) if p else 0 for p in group.split(":")]
    code = sub[0]
    if code in (38, 48) and len(sub) >= 5 and sub[1] == 2:
        r, g, b = sub[-3:]
        style["fg" if code == 38 else "bg"] = f"#{r:02x}{g:02x}{b:02x}"
    elif code == 4:
        style["underline"] = sub[1] != 0 if len(sub) > 1 else True


def runs(text: str) -> list[tuple[str, dict]]:
    style, out, pos = _blank(), [], 0
    for m in SGR.finditer(text):
        if m.start() > pos:
            out.append((text[pos : m.start()], dict(style)))
        groups = m.group(1).split(";") if m.group(1) else ["0"]
        i = 0
        while i < len(groups):
            group = groups[i]
            if ":" in group:
                _apply_group(style, group)
                i += 1
                continue
            p = int(group) if group else 0
            if p == 0:
                style = _blank()
            elif p == 1:
                style["bold"] = True
            elif p == 3:
                style["italic"] = True
            elif p == 4:
                style["underline"] = True
            elif p == 7:
                style["reverse"] = True
            elif p == 22:
                style["bold"] = False
            elif p == 23:
                style["italic"] = False
            elif p == 24:
                style["underline"] = False
            elif p == 27:
                style["reverse"] = False
            elif 30 <= p <= 37:
                style["fg"] = f"ansi:{p - 30}"
            elif 40 <= p <= 47:
                style["bg"] = f"ansi:{p - 40}"
            elif 90 <= p <= 97:
                style["fg"] = f"ansi:{p - 82}"
            elif 100 <= p <= 107:
                style["bg"] = f"ansi:{p - 92}"
            elif p == 39:
                style["fg"] = None
            elif p == 49:
                style["bg"] = None
            elif p in (38, 48):
                key = "fg" if p == 38 else "bg"
                mode = groups[i + 1] if i + 1 < len(groups) else ""
                if mode == "2":
                    r, g, b = (int(x) for x in groups[i + 2 : i + 5])
                    style[key] = f"#{r:02x}{g:02x}{b:02x}"
                    i += 4
                elif mode == "5":
                    style[key] = f"ansi256:{int(groups[i + 2])}"
                    i += 2
            i += 1
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], dict(style)))
    return out


def plain(text: str) -> str:
    return SGR.sub("", text)


def style_of(text: str, token: str) -> dict:
    found = runs(text)
    for chunk, style in found:
        if chunk.strip() == token:
            return style
    near = [chunk for chunk, _ in found if token[:3] in chunk][:10]
    raise AssertionError(f"no run equal to {token!r}; runs containing {token[:3]!r}: {near}")


def line_with(text: str, needle: str) -> str:
    for line in text.splitlines():
        if needle in plain(line):
            return line
    raise AssertionError(f"no line contains {needle!r}")
