# 3ツール（gh skill / APM / skills.sh）の比較と落とし穴

Agent Skills は **1つの `SKILL.md` を3ツールが共通で読む**（変換不要）。ただし配置先・
バージョン固定・SKILL.md 改変・認証の扱いがツールごとに異なる。以下は実機検証で得た要点。

## 配置先と挙動の早見表

| 観点 | gh skill | APM | skills.sh |
| --- | --- | --- | --- |
| 提供元 | GitHub 公式（gh 同梱 v2.90.0〜） | Microsoft/apm（brew/pip） | vercel-labs（npx） |
| 既定の配置先 | `--agent` 指定先（例 `claude-code`→`.claude/skills/`） | `--target` 指定先（`claude`/`agent-skills` 等） | `.agents/skills/` + 各agentへ symlink |
| バージョン固定 | `--pin <ver>` | `#<ver>` / semver 範囲 `#^1.0.0` / lockに記録 | ❌ 記録しない（内容ハッシュのみ） |
| SKILL.md 改変 | あり（`metadata.github-*` を付与） | なし | なし |
| lockfile | なし（出所は SKILL.md に） | `apm.lock.yaml` | `skills-lock.json` |
| private 認証 | gh 認証をそのまま利用 | git 認証に委譲（`--ssh`） | git 認証（公式未文書化） |
| 更新 | `gh skill update [name]` | `apm update [pkg] -y` | `npx skills update [name] -y` |

## 最重要の落とし穴

### Claude Code は `.agents/skills/` を読まない
- Claude Code が自動スキャンするのは **`.claude/skills/`（project）と `~/.claude/skills/`（global）のみ**。
- `.agents/skills/`（cross-client パス）は **未対応**（[claude-code#31005](https://github.com/anthropics/claude-code/issues/31005)）。
- 影響:
  - **APM** は `--target agent-skills` だけだと Claude Code が拾えない → `--target claude,agent-skills` と併記。
  - **skills.sh** は Claude Code 用に `.claude/skills/` への symlink を張って回避している。
  - **gh skill** は `--agent claude-code` で `.claude/skills/` に直接置くのでOK。
- `.agents/skills/` を直接読むのは Copilot / Codex など。

### skills.sh: `--agent` 省略時は既存ディレクトリにしか入らない
- `--agent` を指定しないと、**すでに存在するエージェント用ディレクトリにしか symlink を張らない**。
  `.claude/` が無い repo では `.agents/skills/` だけ作られ、Claude Code から見えない。
- Claude Code で使うなら **`--agent claude-code` を明示**（`.claude/skills/` を新規作成）。`--agent '*'` で全エージェント。
- コミットして配るなら **`--copy`**（symlink でなく実ファイル）。symlink を commit する場合は参照先
  （`.agents/skills/`）も一緒に commit が必要、かつ Windows では symlink が復元されないことに注意。
- 導入時に Gen / Socket / Snyk のセキュリティ評価が走る。

### APM: バージョン固定には smart 転送が必須
- GitHub の `https`/`ssh` はOK。`file://`・`git://`・スキームなしのローカルパスは ref が解決されない
  （HEAD に化ける／ローカルコピー扱いで `ref` 無視）。dumb-HTTP も ref ネゴ非対応で HEAD に落ちる。
- ロングフォーム `git:` の URL は `host/owner/repo(.git)` 形式が必須。http は各依存に `allow_insecure: true`。
- `apm install <pkg>` が require 相当（`apm.yml` 自動生成・追記 + lockfile 更新まで一括）。
- repo 指定で全スキル、`skills/<name>` 指定で個別。ref 省略は `unpinned ... drift` 警告。

### gh skill: SKILL.md にメタを書き込む
- 導入時、利用側コピーの frontmatter に `metadata.github-*`（repo/ref/tree-sha/pinned）を付与する。
  **提供元 repo の `skills/<name>/SKILL.md` は無改変**。`gh skill update` はこのメタで更新判定。
- 非対話で複数入れるには `--all`（または個別名）。`--pin` 固定分は `gh skill update` の対象外（`--unpin` で解除）。

## 公開・発見の仕組み

- **公開作業はどのツールも「git に push するだけ」**（中央レジストリ申請は不要）。
- `gh skill search` の発見条件: repo トピック **`agent-skills`**（`gh skill publish` が付与）＋ GitHub Code Search で
  `SKILL.md` の name/description がヒット。レイアウトは `skills/<name>/SKILL.md`。
- **skills.sh のディレクトリ（skills.sh）は GitHub を自動クロール**して `SKILL.md` を索引（手動登録不要）。
  → **public** なら自動掲載。**private** は Code Search もクロールも対象外＝公開カタログに載らない（社内限定向き）。

## バージョニング規約

- セマンティックバージョニング。**タグに `v` を付けない**（`1.2.0`。`v1.2.0` にしない）。
- 機械可読の version フィールドがある場合（package.json 等）はそもそも `v` なし。git タグも本プロジェクトでは `v` なしで統一。
