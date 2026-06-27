---
name: markdown-to-html
description: Convert Markdown text or .md files into HTML fragments or full HTML documents. Use when the user asks to transform Markdown into HTML, preserve headings/lists/links/code blocks, or generate browser-ready HTML from Markdown. 日本語で「マークダウンをHTMLに変換して」と頼まれたときにも使う。
license: MIT
---

# Markdown to HTML

Markdown を HTML に変換するためのスキル。

## When to use

- ユーザーが Markdown を HTML に変換したい
- `.md` ファイルから HTML ファイルを作りたい
- 本文だけの HTML 断片、またはブラウザで開ける完全な HTML 文書が必要

## Workflow

1. 入力がファイルなら中身を確認する。文字列ならそのまま扱う。
2. 変換は `scripts/md_to_html.py` を優先して使う。
3. デフォルトでは完全な HTML 文書を出力する。
4. HTML 断片が必要な場合は `--fragment` を付ける。
5. タイトル指定があれば `--title` を使う。なければ入力ファイル名か既定値を使う。
6. 出力後に見出し、箇条書き、コードブロック、リンクが崩れていないか軽く確認する。

## Commands

ファイルを HTML 文書へ変換:

```bash
python3 scripts/md_to_html.py input.md -o output.html --title "Document Title"
```

標準入力から HTML 断片を生成:

```bash
printf '# Hello\n\n- one\n- two\n' | python3 scripts/md_to_html.py --stdin --fragment
```

## Notes

- 外部ライブラリなしで動く軽量実装。
- 対応する主な記法: 見出し、段落、箇条書き、番号付きリスト、引用、コードフェンス、インラインコード、強調、リンク、画像、水平線、Markdown テーブル。
- 複雑な Markdown 拡張記法や厳密な CommonMark 完全互換が必要な場合は、その制約をユーザーに共有したうえで対応範囲を明示する。
