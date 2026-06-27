---
name: skill-release
description: Agent Skills を共有する GitHub リポジトリ（skills/<name>/SKILL.md 形式）へ、新しいスキルを追加または既存スキルを更新し、gh skill publish で公開（リリース）するときの手順。「スキルを追加」「スキルを追加したのでリリース」「新しいスキルを作って公開」「スキルを更新したので公開」「スキルをリリースして」「skill をパブリッシュ」などと言われたら参照する。SKILL.md の配置規約・frontmatter ルール（name/description/license、description のコロンクォート、LF 改行）・README 追記・残存コピー掃除・gh skill publish による検証とリリース（v なし semver）までを repo 非依存で収録する。
license: MIT
---

# スキルの追加・リリース手順（汎用）

Agent Skills を共有する GitHub リポジトリに、スキルを追加／更新して公開するための手順。

## 前提: 3つのツールで利用される

公開したスキルは、利用側で次の **3ツールのいずれからも導入される**ことを前提とする。
いずれも同一の `skills/<name>/SKILL.md` を読むため、ツール別のバリアントは作らない。

- **gh skill**（GitHub CLI 公式）— 本手順のリリースに使う主軸。`gh skill install <OWNER>/<REPO> ...`
- **APM**（Microsoft/apm）— `apm install <OWNER>/<REPO>/skills/<name>#<tag>`
- **skills.sh**（vercel-labs/skills）— `npx skills add <OWNER>/<REPO> --skill <name>`

そのため SKILL.md は、3ツールが共通で要求する規約（`skills/<name>/SKILL.md` 構成、
frontmatter の `name`/`description`、agentskills.io 命名規則）を満たすように作る。

各ツールの配置先・バージョン固定・認証の違いや落とし穴（Claude Code は `.agents/skills/` を
読まない、skills.sh の `--agent`/symlink 挙動、APM の smart 転送必須、gh skill の provenance 付与、
公開・発見の仕組みなど）は **[references/three-tools.md](references/three-tools.md)** を参照。

> 以下、対象リポジトリを `<OWNER>/<REPO>` と表記する（実行前に実際の値へ置き換える）。

## 1. スキルファイルの配置

- 実体は `skills/<name>/SKILL.md`。
- `<name>` は **ディレクトリ名と frontmatter の `name` を一致**させる（kebab-case、agentskills.io の命名規則）。
- 改行コードは **LF**。CRLF が混じると `gh skill publish` の検証で frontmatter を誤認することがある。

## 2. frontmatter のルール

```yaml
---
name: <ディレクトリ名と同じ>
description: <自動起動用にトリガー語を豊富に。長くてよい>
license: <SPDX 識別子。例 MIT>
---
```

- `name` / `description` / `license` を入れる（`license` が無いと publish で warning）。
- ⚠️ **`description` に `: `（コロン + 半角スペース）が含まれると YAML が壊れる**。
  値全体をシングルクォートで囲み、内部の `'` は `''` にエスケープする。
  例: `Cannot set a node's parent` → `'... Cannot set a node''s parent ...'`
- `description` が 1024 字超の warning は **無視してよい**（トリガー精度のため意図的に長くするのは可）。
- 相互参照するスキルがあれば description 本文で名前を挙げる（例: 「テスト手順は xxx を参照」）。

## 3. README を更新

- リポジトリの README にスキル一覧があれば、新スキルの行（名前リンク + 概要）を追加する。

## 4. 検証（公開前に必ず）

```bash
# 外部由来のインストールキャッシュ・lockfile だけ掃除（git 未追跡の残存物）
rm -rf apm_modules apm.yml apm.lock.yaml skills-lock.json

# frontmatter / 仕様チェック（公開はしない）
gh skill publish --dry-run
```

- ⚠️ `apm_modules/` などインストールキャッシュ（git 未追跡）が残っていると、
  `gh skill publish` が古い内容を拾って**誤った warning/error** を出す。先に消す。
- ℹ️ **`.agents/`（と `.claude/skills/`）は、このリポジトリ内で利用するドッグフード用スキルであり、
  共有対象（`skills/<name>/`）ではない。** `gh skill publish` 実行時、`.agents/` に他のスキルが入っていると
  それらも走査されて warning が出ることがあるが、**共有するスキルではないので無視してよい**（退避・削除は不要）。
  - 例外: `.agents/` `.claude/skills/` の中身が外部 repo からの古いテストインストールコピー（git 未追跡）の場合は、
    誤検知防止のため消す。リポジトリが意図的にコミットしているドッグフード用コピーはそのまま残す。
- `error` がゼロなら OK。`warning`（description 字数 / secret scanning / tag protection / `.agents/` 内ドッグフードスキル）は
  すべて非ブロッカーなので、そのまま公開してよい。

## 5. コミット & プッシュ

```bash
git add skills/<name> README.md
git commit -m "Add <name> skill"   # 更新時は "Update <name> skill"
git push origin main
```

## 6. リリース（公開）

```bash
gh skill publish --tag <X.Y.Z>
```

- **バージョンは v を付けない semver**（`1.2.0`。`v1.2.0` にしない）。
- 付け方の目安: **新スキル追加 = minor アップ**（例 1.1.0 → 1.2.0）、
  **既存スキルの内容修正 = patch アップ**（例 1.1.2 → 1.1.3）。
- 直前のタグを `gh release list -R <OWNER>/<REPO>` で確認してから次を決める。
- `gh skill publish` は spec 検証・`agent-skills` トピック付与・リリース作成をまとめて行う。

## 7. 確認

```bash
gh release list -R <OWNER>/<REPO>
```

- 追加したバージョンが `Latest` になっていれば完了。

## 補足

- `gh skill` で導入したスキルの SKILL.md には provenance メタ（`metadata.github-*`）が付くが、
  これは利用側コピーのみ。提供元リポジトリの `skills/<name>/SKILL.md` は無改変。
- `license` の SPDX とリポジトリの `LICENSE` ファイルの著作権者表記は、対象プロジェクトの方針に合わせる。
