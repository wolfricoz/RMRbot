"""Convert Discord message markdown into HTML the RoleplayMeets website accepts.

The site keeps only these tags: p, br, strong, em, u, s, a[href], ul, ol, li,
h1-h6, pre, code, sub, sup (plus a few style properties such as margin-left
and font-size). It also deletes blank lines ("\n\n") and "<br><br>", so the
output never relies on either.
"""

import html
import re
from datetime import datetime, timezone
from typing import Callable, Optional

Resolver = Optional[Callable[[str], Optional[str]]]

# Private-use characters mark placeholders for HTML that is already finished.
_PH_OPEN, _PH_CLOSE = "\ue000", "\ue001"
_PH_RE = re.compile(_PH_OPEN + r"(\d+)" + _PH_CLOSE)

_CODE_BLOCK_RE = re.compile(r"```(?:([\w+\-.#]+)?\n)?(.*?)```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"(``?)(.+?)\1")
_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|~>:<@])")
_MASKED_LINK_RE = re.compile(r"\[([^\[\]\n]+)\]\(<?(https?://[^\s)>]+)>?\)")
_ANGLE_LINK_RE = re.compile(r"<(https?://[^\s>]+)>")
_URL_RE = re.compile(r"https?://[^\s<]+[^\s<.,:;\"')\]!?]")
_USER_RE = re.compile(r"<@!?(\d+)>")
_ROLE_RE = re.compile(r"<@&(\d+)>")
_CHANNEL_RE = re.compile(r"<#(\d+)>")
_EMOJI_RE = re.compile(r"<a?:(\w+):\d+>")
_TIMESTAMP_RE = re.compile(r"<t:(-?\d+)(?::([tTdDfFR]))?>")

_HEADING_RE = re.compile(r"^(#{1,3}) +(.+)$")
_SUBTEXT_RE = re.compile(r"^-# +(.+)$")
_LIST_RE = re.compile(r"^( *)([-*]|\d+\.) +(.*)$")

# Inline formatting, applied in this order to already-escaped text.
_FORMATS = [
    (re.compile(r"\*\*\*(?!\s)(.+?)(?<!\s)\*\*\*"), r"<strong><em>\1</em></strong>"),
    (re.compile(r"\*\*(?!\s)(.+?)(?<!\s)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"__(?!\s)(.+?)(?<!\s)__"), r"<u>\1</u>"),
    (re.compile(r"\*(?![\s*])(.+?)(?<![\s*])\*"), r"<em>\1</em>"),
    (re.compile(r"(?<![A-Za-z0-9])_(?![\s_])(.+?)(?<![\s_])_(?![A-Za-z0-9])"), r"<em>\1</em>"),
    (re.compile(r"~~(?!\s)(.+?)(?<!\s)~~"), r"<s>\1</s>"),
    # Spoilers have no website equivalent: keep the text, drop the bars.
    (re.compile(r"\|\|(.+?)\|\|"), r"\1"),
]

_QUOTE_STYLE = "margin-left: 1.5em"
_TIMESTAMP_FORMATS = {
    "t": "%H:%M",
    "T": "%H:%M:%S",
    "d": "%d/%m/%Y",
    "D": "%B %d, %Y",
    "f": "%B %d, %Y %H:%M",
    "F": "%A, %B %d, %Y %H:%M",
    "R": "%B %d, %Y %H:%M",  # "in 2 hours" can't stay relative on a static page
}


def discord_to_html(
    text: str,
    resolve_user: Resolver = None,
    resolve_channel: Resolver = None,
    resolve_role: Resolver = None,
    heading_offset: int = 1,
) -> str:
    """Turn a Discord message into website HTML.

    resolve_user / resolve_channel / resolve_role take a Discord id (string) and
    return a display name (or None) so mentions read "@Name" instead of "@user".
    Tip: discord.py's message.clean_content already has user/channel/role
    mentions replaced, so you can pass that and skip the resolvers.

    heading_offset shifts Discord headings down: with 1, "#" becomes <h2>, so a
    post never competes with the page's own <h1> title.
    """
    store: list[str] = []

    def keep(fragment: str) -> str:
        store.append(fragment)
        return f"{_PH_OPEN}{len(store) - 1}{_PH_CLOSE}"

    def restore(value: str) -> str:
        while _PH_RE.search(value):
            value = _PH_RE.sub(lambda m: store[int(m.group(1))], value)
        return value

    def mention(prefix: str, resolver: Resolver, fallback: str) -> Callable[[re.Match], str]:
        def replace(match: re.Match) -> str:
            name = resolver(match.group(1)) if resolver else None
            return keep(html.escape(prefix + (name or fallback)))
        return replace

    def timestamp(match: re.Match) -> str:
        moment = datetime.fromtimestamp(int(match.group(1)), tz=timezone.utc)
        style = match.group(2) or "f"
        return keep(html.escape(moment.strftime(_TIMESTAMP_FORMATS[style]) + " UTC"))

    def link(url: str, label: Optional[str] = None) -> str:
        href = html.escape(url, quote=True)
        return keep(f'<a href="{href}">{label if label is not None else html.escape(url)}</a>')

    def inline(line: str) -> str:
        line = _INLINE_CODE_RE.sub(lambda m: keep(f"<code>{html.escape(m.group(2).strip())}</code>"), line)
        line = _ESCAPE_RE.sub(lambda m: keep(html.escape(m.group(1))), line)
        line = _USER_RE.sub(mention("@", resolve_user, "user"), line)
        line = _ROLE_RE.sub(mention("@", resolve_role, "role"), line)
        line = _CHANNEL_RE.sub(mention("#", resolve_channel, "channel"), line)
        line = _EMOJI_RE.sub(lambda m: keep(html.escape(f":{m.group(1)}:")), line)
        line = _TIMESTAMP_RE.sub(timestamp, line)
        # Link text keeps its formatting, so only the tags become placeholders.
        line = _MASKED_LINK_RE.sub(
            lambda m: keep(f'<a href="{html.escape(m.group(2), quote=True)}">') + m.group(1) + keep("</a>"),
            line,
        )
        line = _ANGLE_LINK_RE.sub(lambda m: link(m.group(1)), line)
        line = _URL_RE.sub(lambda m: link(m.group(0)), line)
        line = html.escape(line, quote=False)
        for pattern, replacement in _FORMATS:
            line = pattern.sub(replacement, line)
        return line

    def styled(tag: str, body: str, style: Optional[str]) -> str:
        attr = f' style="{style}"' if style else ""
        return f"<{tag}{attr}>{body}</{tag}>"

    def render_list(items: list[tuple[int, str, str]], style: Optional[str]) -> str:
        """items: (indent, marker, text). Deeper indents nest inside the item above."""
        out: list[str] = []
        stack: list[tuple[int, str]] = []  # (indent, "ul"|"ol")
        for indent, marker, body in items:
            tag = "ol" if marker[0].isdigit() else "ul"
            while stack and indent < stack[-1][0]:
                out.append(f"</li></{stack.pop()[1]}>")
            if stack and indent == stack[-1][0] and tag != stack[-1][1]:
                out.append(f"</li></{stack.pop()[1]}>")
            if stack and indent == stack[-1][0]:
                out.append("</li>")
            else:
                attr = f' style="{style}"' if style and not stack else ""
                out.append(f"<{tag}{attr}>")
                stack.append((indent, tag))
            out.append(f"<li>{inline(body)}")
        while stack:
            out.append(f"</li></{stack.pop()[1]}>")
        return "".join(out)

    def render_blocks(lines: list[str], style: Optional[str] = None) -> str:
        out: list[str] = []
        paragraph: list[str] = []
        items: list[tuple[int, str, str]] = []

        def flush() -> None:
            if paragraph:
                out.append(styled("p", "<br>".join(inline(l) for l in paragraph), style))
                paragraph.clear()
            if items:
                out.append(render_list(items, style))
                items.clear()

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith(">>> ") or stripped == ">>>":
                # Everything after ">>>" is quoted, to the end of the message.
                flush()
                rest = [stripped[4:]] + lines[i + 1:]
                out.append(render_blocks(rest, _QUOTE_STYLE))
                break
            if stripped.startswith("> ") or stripped == ">":
                flush()
                quoted = []
                while i < len(lines) and (lines[i].strip().startswith("> ") or lines[i].strip() == ">"):
                    quoted.append(lines[i].strip()[2:])
                    i += 1
                out.append(render_blocks(quoted, _QUOTE_STYLE))
                continue

            if not stripped:
                flush()
            elif heading := _HEADING_RE.match(stripped):
                flush()
                level = min(len(heading.group(1)) + heading_offset, 6)
                out.append(styled(f"h{level}", inline(heading.group(2)), style))
            elif subtext := _SUBTEXT_RE.match(stripped):
                flush()
                sub_style = "font-size: small" + (f"; {style}" if style else "")
                out.append(styled("p", inline(subtext.group(1)), sub_style))
            elif item := _LIST_RE.match(line):
                if paragraph:
                    flush()
                items.append((len(item.group(1)), item.group(2), item.group(3)))
            elif items and line.startswith(" "):
                # An indented line under a list item continues that item.
                indent, marker, body = items[-1]
                items[-1] = (indent, marker, f"{body} {stripped}")
            else:
                if items:
                    flush()
                paragraph.append(stripped)
            i += 1

        flush()
        return "".join(out)

    def code_block(match: re.Match) -> str:
        code = match.group(2).strip("\n")
        # The site deletes "\n\n", so keep blank lines in code alive with a space.
        code = re.sub(r"\n(?=\n)", "\n ", html.escape(code, quote=False))
        return f"<pre><code>{code}</code></pre>"

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    parts: list[str] = []
    position = 0
    for match in _CODE_BLOCK_RE.finditer(text):
        parts.append(render_blocks(text[position:match.start()].split("\n")))
        parts.append(code_block(match))
        position = match.end()
    parts.append(render_blocks(text[position:].split("\n")))

    return restore("".join(parts))