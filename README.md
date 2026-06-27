# baser-skills

baserCMS / CakePHP / PHP の開発・移行で使う **Agent Skills** を共有するリポジトリです。
スキルの実体は `skills/<name>/SKILL.md`。**1つの `SKILL.md` を Claude Code / GitHub Copilot / Codex などが共通で読みます**(変換・ツール別バリアントは不要)。

## 収録スキル

| スキル | 概要 |
| --- | --- |
| [`basercms4-development`](skills/basercms4-development/SKILL.md) | baserCMS 4系（CakePHP 2.10）＋ jQuery プロジェクトの開発ルール集（構成・命名・ログ・サーバ制約） |
| [`basercms5-development`](skills/basercms5-development/SKILL.md) | baserCMS 5系（CakePHP 5）＋ jQuery プロジェクトの開発ルール集（構成・命名・ログ・サーバ制約） |
| [`basercms4-to-5-upgrade`](skills/basercms4-to-5-upgrade/SKILL.md) | baserCMS 4 → 5（CakePHP 2 → 5）サイト全体のアップグレード／移行手順とルール集 |
| [`basercms-plugin-4-to-5-upgrade`](skills/basercms-plugin-4-to-5-upgrade/SKILL.md) | プラグイン内部コードの 4 → 5 書き換えパターン集（Controller/Table/Entity/View/Helper/フォーム/Vue・JS） |
| [`basercms-plugin-5x-update`](skills/basercms-plugin-5x-update/SKILL.md) | baserCMS プラグインを 5.2系 → 5.3系 へ移行する際の固有の破壊的変更・非推奨・テスト基盤対応レシピ集 |
| [`basercms-core-plugin-convert`](skills/basercms-core-plugin-convert/SKILL.md) | 通常プラグイン（単体配布）を monorepo の「コアプラグイン」へ昇格させる手順（命名規約変更・テスト基盤統合・各種登録・split 確認まで） |
| [`basercms-unittest`](skills/basercms-unittest/SKILL.md) | baserCMS（CakePHP5 / PHPUnit）のユニットテストをローカル Docker で実行・調査する手順 |
| [`cakephp-migration`](skills/cakephp-migration/SKILL.md) | CakePHP バージョンアップ（5.0 → 5.1 → 5.2 〜）の非推奨・破壊的変更パターン集と修正レシピ |
| [`php-migration`](skills/php-migration/SKILL.md) | PHP バージョンアップ（8.2 / 8.4 / 8.5 〜）の非推奨・破壊的変更対応レシピ |

> これらのスキルは説明文の中で相互参照しているため、**まとめて導入する**ことを推奨します。

---

## 導入方法

skills.sh、apm、gh skill での導入方法をご紹介します。
　　

### 1. skills.sh（npx）

[vercel-labs/skills](https://github.com/vercel-labs/skills)。`npx` だけで導入できる最も手軽な方式（追加インストール不要）。

**導入**:

```bash
# 全体
npx -y skills@latest add baserproject/baser-skills --skill '*' -y

# 個別
npx -y skills@latest add baserproject/baser-skills --skill php-migration -y
```

**アップデート**:

```bash
# 全体
npx -y skills@latest update -y

# 個別
npx -y skills@latest update php-migration -y
```

- **常に最新**を取得します（バージョン固定の仕組みはありません）。`add ... -l` で導入可能なスキルを一覧できます。`--skill` は複数をカンマ区切りで指定可。
- 実体を `.agents/skills/` に置き、各エージェント用ディレクトリ（`.claude/skills/` 等）へ **シンボリックリンク**を張ります。
- ⚠️ `--agent` を省くと、**既に存在するエージェント用ディレクトリにしか symlink を張りません**（`.claude/` が無い repo では `.agents/skills/` のみ作成され、Claude Code から見えない）。Claude Code で使うなら **`--agent claude-code` を明示**してください（`.claude/skills/` を新規作成します）。`--agent '*'` で全エージェント対象。
- 導入時に Gen / Socket / Snyk によるセキュリティ評価が実行されます。`skills-lock.json` を生成し、SKILL.md は無改変。

**注意事項**
- ⚠️ **バージョン（tag/commit）を記録しません**（`skills-lock.json` は内容ハッシュのみ）。厳密な版固定が必要な用途には不向き。
- private repo 対応は公式に未文書化（git 認証があれば動く想定）。
　
　

### 2. APM（Agent Package Manager）

[Microsoft/apm](https://github.com/microsoft/apm)。`apm.yml` で宣言し `apm.lock.yaml` で固定する、npm / pip 的な方式（CI での再現性・監査向き）。前提インストール: `brew install microsoft/apm/apm`。

**導入**:

```bash
# 全体
apm install baserproject/baser-skills --target claude,agent-skills --ssh

# 個別
apm install baserproject/baser-skills/skills/php-migration --target claude,agent-skills --ssh
```

> **バージョン固定**: パッケージ名に `#1.0.0` のように付与します（`#^1.0.0` の semver 範囲指定も可。1系の最新に解決）。ref を省略すると main 最新に解決され、`unpinned ... drift` 警告が出ます。

**アップデート**:

```bash
# 全体
apm update -y

# 個別
apm update baserproject/baser-skills/skills/php-migration -y
```

- `apm install <package>` が npm install / composer require 相当（`apm.yml` 自動生成・追記 + lockfile 更新まで一括）。repo 指定で全スキル、`skills/<name>` 指定で個別。private は `--ssh` を付与。
- 固定インストールでも `apm.lock.yaml` がある間は再現可能。本番運用ではバージョン固定を推奨。
- `--target` で配置先を指定します。`claude` → `.claude/skills/`（Claude Code 用）、`agent-skills` → `.agents/skills/`（Copilot / Codex などが読む共通パス）。⚠️ **Claude Code は `.agents/skills/` を読まない**ため、Claude Code を含めるなら `claude,agent-skills` のように併記が必要です。
- `apm.lock.yaml` に `resolved_commit` / `version` / `content_hash` を依存ごとに記録（**同一 repo・別バージョンの同居も可**）。SKILL.md は無改変。

**注意事項**
- ⚠️ **バージョン固定には smart 転送が必須**。GitHub の `https`/`ssh` は問題なし。`file://` や `git://`、スキームなしのローカルパスは ref が解決されない（HEAD に化ける / ローカルコピー扱いになる）ので使わないこと。
- private repo は git の認証に委譲。`--ssh` でショートハンドを SSH 解決に固定できる。
- `apm.yml` / `apm.lock.yaml` は **コミット推奨**（再現性）。取得キャッシュ `apm_modules/` は `.gitignore` 推奨。
　

### 3. gh skill（GitHub CLI 公式）

[GitHub CLI](https://cli.github.com/) v2.90.0 以降に同梱。`gh` の認証をそのまま使うため private repo でも追加設定不要です。

**導入**:

```bash
# 全体
gh skill install baserproject/baser-skills --all --agent claude-code

# 個別
gh skill install baserproject/baser-skills php-migration --agent claude-code
```

> **バージョン固定**: `--pin 1.0.0` を付与します。`--pin` 無しは最新リリースを取得し、`gh skill update` で以後も最新に追従します。

**アップデート**:

```bash
# 全体
gh skill update

# 個別
gh skill update php-migration
```

- `--agent` で配置先が決まります（`claude-code` → `.claude/skills/`、`github-copilot` → `.github/skills/`、`universal` → `.agents/skills/` など）。非対話時の既定は `github-copilot`。`--scope user` でユーザー全体へ（既定 `project`）。
- 複数スキルを非対話で入れるには `--all`（または個別にスキル名）が必要。
- `--pin` で固定したスキルは更新対象外（`--unpin` で解除、または新バージョンを再 install）。

**注意事項**
- ⚠️ **導入時に SKILL.md の frontmatter へ provenance メタデータ（`metadata.github-*`）が書き込まれます**（利用側コピーのみ。提供元 repo は無改変）。`gh skill update` はこのメタを見て更新判定します。
- 専用 lockfile は作られません（出所は各 SKILL.md が保持）。

---
　

## 配置先と git 管理の早見表

| ツール | 既定の配置先 | バージョン固定 | SKILL.md 改変 | lockfile |
| --- | --- | --- | --- | --- |
| skills.sh | `.agents/skills/` + 各agentへsymlink（Claude Code は `.claude/skills/` への symlink） | ❌ ハッシュのみ | なし | `skills-lock.json` |
| APM | `--target` 指定先（`claude` / `agent-skills` など） | ✅ lockに記録 | なし | `apm.lock.yaml` |
| gh skill | `--agent` 指定先（例 `claude-code` → `.claude/skills/`） | ✅ `--pin` | あり（metadata付与） | なし |

- ⚠️ **`.agents/skills/` を直接読むのは Copilot / Codex など**。**Claude Code は `.agents/skills/` を読まず `.claude/skills/`（と `~/.claude/skills/`）のみ**を見ます（[claude-code#31005](https://github.com/anthropics/claude-code/issues/31005)）。そのため Claude Code 向けには `.claude/skills/` への配置（または symlink）が必要です。
  - skills.sh は自動で `.claude/skills/` への symlink を張る／gh skill は `--agent claude-code` で直接配置／APM は `--target claude` を併記、で対応できます。
- 各ツールの生成物（`apm_modules/`、`apm.lock.yaml`、`skills-lock.json`、デプロイされたスキル等）をリポジトリにコミットするかどうかは運用方針に合わせて `.gitignore` を調整してください。

---
　

## メンテナ向け: スキルの公開

スキルを追加・更新したら `gh skill publish` でリリースします。

```bash
# 検証のみ（公開しない）
gh skill publish --dry-run

# 検証 + agent-skills トピック付与 + リリース作成（v なしの semver タグ）
gh skill publish --tag 1.0.0
```

- 公開には `skills/<name>/SKILL.md` 構成、frontmatter の `name`/`description`、および repo の **`agent-skills` トピック**（`gh skill publish` が付与）が必要です。
- `description` に `: `（コロン+空白）を含む場合は frontmatter が不正な YAML になるため、**値全体をクォート**してください。

---

## ライセンス

[MIT License](LICENSE) — Copyright (c) 2010-present, NPO baser foundation。各スキルの frontmatter にも `license: MIT` を記載しています。
