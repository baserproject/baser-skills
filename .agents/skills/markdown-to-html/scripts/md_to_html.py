#!/usr/bin/env python3
"""Convert a subset of Markdown into HTML without external dependencies."""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


INLINE_CODE_RE = re.compile(r"`([^`]+)`")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
STRONG_RE = re.compile(r"(\*\*|__)(.+?)\1")
EM_RE = re.compile(r"(\*|_)([^*_]+?)\1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Markdown text or files into HTML."
    )
    parser.add_argument("input", nargs="?", help="Input Markdown file path")
    parser.add_argument("-o", "--output", help="Output HTML file path")
    parser.add_argument("--stdin", action="store_true", help="Read Markdown from stdin")
    parser.add_argument(
        "--fragment",
        action="store_true",
        help="Emit an HTML fragment instead of a full HTML document",
    )
    parser.add_argument("--title", help="Document title for full HTML output")
    return parser.parse_args()


def read_input(args: argparse.Namespace) -> tuple[str, str]:
    if args.stdin:
        return sys.stdin.read(), "document"
    if not args.input:
        raise SystemExit("Provide an input file or use --stdin.")
    path = Path(args.input)
    return path.read_text(encoding="utf-8"), path.stem


def render_inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = INLINE_CODE_RE.sub(lambda m: f"<code>{html.escape(m.group(1))}</code>", escaped)
    escaped = IMAGE_RE.sub(
        lambda m: (
            f'<img src="{html.escape(m.group(2), quote=True)}" '
            f'alt="{html.escape(m.group(1), quote=True)}">'
        ),
        escaped,
    )
    escaped = LINK_RE.sub(
        lambda m: (
            f'<a href="{html.escape(m.group(2), quote=True)}">'
            f"{m.group(1)}</a>"
        ),
        escaped,
    )
    escaped = STRONG_RE.sub(lambda m: f"<strong>{m.group(2)}</strong>", escaped)
    escaped = EM_RE.sub(lambda m: f"<em>{m.group(2)}</em>", escaped)
    return escaped


def is_hr(line: str) -> bool:
    compact = line.replace(" ", "")
    return compact in {"---", "***", "___"}


def is_fence(line: str) -> bool:
    return line.startswith("```")


def is_ul_item(line: str) -> bool:
    return bool(re.match(r"^[-*+] ", line))


def is_ol_item(line: str) -> bool:
    return bool(re.match(r"^\d+\. ", line))


def is_table_delimiter(line: str) -> bool:
    stripped = line.strip()
    if "|" not in stripped:
        return False
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    return "|" in stripped and not is_table_delimiter(stripped)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def strip_list_marker(line: str) -> str:
    return re.sub(r"^([-*+] |\d+\. )", "", line, count=1)


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []
    list_stack: list[str] = []
    i = 0

    def flush_paragraph() -> None:
        if paragraph:
            content = " ".join(part.strip() for part in paragraph if part.strip())
            out.append(f"<p>{render_inline(content)}</p>")
            paragraph.clear()

    def close_lists() -> None:
        while list_stack:
            out.append(f"</{list_stack.pop()}>")

    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if in_code:
            if is_fence(stripped):
                out.append("<pre><code>{}</code></pre>".format(html.escape("\n".join(code_lines))))
                code_lines.clear()
                in_code = False
            else:
                code_lines.append(raw_line)
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            close_lists()
            i += 1
            continue

        if is_fence(stripped):
            flush_paragraph()
            close_lists()
            in_code = True
            i += 1
            continue

        if is_hr(stripped):
            flush_paragraph()
            close_lists()
            out.append("<hr>")
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            close_lists()
            level = len(heading.group(1))
            out.append(f"<h{level}>{render_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            close_lists()
            out.append(f"<blockquote>{render_inline(stripped[2:].strip())}</blockquote>")
            i += 1
            continue

        if is_ul_item(stripped):
            flush_paragraph()
            if not list_stack or list_stack[-1] != "ul":
                close_lists()
                out.append("<ul>")
                list_stack.append("ul")
            out.append(f"<li>{render_inline(strip_list_marker(stripped))}</li>")
            i += 1
            continue

        if is_ol_item(stripped):
            flush_paragraph()
            if not list_stack or list_stack[-1] != "ol":
                close_lists()
                out.append("<ol>")
                list_stack.append("ol")
            out.append(f"<li>{render_inline(strip_list_marker(stripped))}</li>")
            i += 1
            continue

        if (
            i + 1 < len(lines)
            and is_table_row(stripped)
            and is_table_delimiter(lines[i + 1].strip())
        ):
            flush_paragraph()
            close_lists()
            header_cells = split_table_row(stripped)
            out.append("<table>")
            out.append("  <thead>")
            out.append(
                "    <tr>{}</tr>".format(
                    "".join(f"<th>{render_inline(cell)}</th>" for cell in header_cells)
                )
            )
            out.append("  </thead>")
            out.append("  <tbody>")
            i += 2

            while i < len(lines):
                body_line = lines[i].strip()
                if not body_line or not is_table_row(body_line):
                    break
                body_cells = split_table_row(body_line)
                out.append(
                    "    <tr>{}</tr>".format(
                        "".join(f"<td>{render_inline(cell)}</td>" for cell in body_cells)
                    )
                )
                i += 1

            out.append("  </tbody>")
            out.append("</table>")
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    close_lists()

    if in_code:
        out.append("<pre><code>{}</code></pre>".format(html.escape("\n".join(code_lines))))

    return "\n".join(out)


def wrap_document(body: str, title: str) -> str:
    safe_title = html.escape(title, quote=False)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{
      color-scheme: light;
    }}
    body {{
      margin: 2rem auto;
      max-width: 760px;
      padding: 0 1rem 3rem;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.7;
      color: #1f2937;
    }}
    pre {{
      overflow-x: auto;
      padding: 1rem;
      background: #111827;
      color: #f9fafb;
      border-radius: 12px;
    }}
    code {{
      font-family: "SFMono-Regular", Consolas, monospace;
    }}
    img {{
      max-width: 100%;
      height: auto;
    }}
    blockquote {{
      margin-left: 0;
      padding-left: 1rem;
      border-left: 4px solid #d1d5db;
      color: #4b5563;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.5rem 0;
    }}
    th, td {{
      border: 1px solid #d1d5db;
      padding: 0.75rem;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f3f4f6;
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    markdown, default_title = read_input(args)
    body = markdown_to_html(markdown)
    output = body if args.fragment else wrap_document(body, args.title or default_title)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
