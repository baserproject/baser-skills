---
name: basercms-unittest
description: baserCMS（CakePHP5 / PHPUnit）のユニットテストをローカル Docker 環境で実行・調査する手順。「ユニットテストを実行して」「全テストを走らせて」「このテストだけ流して」「テスト失敗を調べて」等のときに参照する。コンテナ名・実行コマンド・権限自動承認のためのコマンド整形・失敗の集計と切り分け方を収録。
license: MIT
---

# baserCMS ユニットテスト実行ガイド（ローカル）

baserCMS のユニットテストは Docker コンテナ上で実行する。実行・絞り込み・失敗調査の定石をまとめる。

## 実行環境

- 実行は `docker compose`（compose ファイルの場所はローカル環境依存。具体的な配置は `.github/instructions/local.instructions.md` 参照）。
- **PHPコンテナ名: `basercms`**、baserCMS 配置先: **`/var/www/html`**。
- テスト設定: `phpunit.xml.dist`。`<testsuites>` にプラグインごとの testsuite が定義（BaserCore / BcBlog / BcCustomContent / BcMail / BcThemeFile …）。
- DB はローカル環境依存（過去に `bc-db` ホスト無しの失敗があったが、現在は `cu-db` コンテナを利用。この種の接続失敗は環境要因でスルー可）。
- **環境固有情報（compose ファイルの場所・コンテナ名・DB ホスト/接続情報・配置パス等）が `local.instructions.md` 等から判断できない場合は、推測で進めずユーザーに確認する。**

## コマンド整形（重要：権限の自動承認）

- 複合コマンドの**外側**にパイプ `|` やリダイレクト `>` を置くと権限の自動承認が効かず確認プロンプトになる。
- **`docker exec basercms sh -c '...'` の単一引用符内**にリダイレクト・`tail` 等をすべて収めると、単一の `docker exec` コマンド扱いになり自動承認される。
- 安全な読み取り専用コマンド（`grep`/`find`/`ls`/`cat`/`sed -n`/`head`/`tail`）は単体で使う。

## 実行コマンド

### 全テスト（フルスイート）
出力が大きいのでプロジェクトルートの `.phpunit.log`（`/var/www/html/.phpunit.log`）に保存し、末尾だけ表示する。完走まで約10分強かかるため、必要に応じてバックグラウンド実行する。
- **ログは毎回空にしてから出力する**（`: > .phpunit.log` で truncate してから `>>` で追記）。前回ログが残っていても確実にリセットされる。
- `.phpunit.log` は `.gitignore` 済み（コミット対象外）。
```
docker exec basercms sh -c 'cd /var/www/html && : > .phpunit.log; vendor/bin/phpunit --no-coverage >> .phpunit.log 2>&1; tail -45 .phpunit.log'
```

### 単一ファイル / 単一メソッド
```
docker exec basercms sh -c 'cd /var/www/html && vendor/bin/phpunit --no-coverage plugins/baser-core/tests/TestCase/Model/Table/PagesTableTest.php 2>&1 | tail -20'
docker exec basercms sh -c 'cd /var/www/html && vendor/bin/phpunit --no-coverage --filter testBeforeSave plugins/baser-core/tests/TestCase/Model/Table/PagesTableTest.php 2>&1 | tail -20'
```

### 構文チェック（lint）
修正後は必ず実施。暗黙nullable等の非推奨警告も併せて出る。
```
docker exec basercms sh -c 'cd /var/www/html && php -l plugins/baser-core/src/Controller/Admin/ThemesController.php'
```

## 失敗の調査手順

1. **致命的か警告か**を判別。`logs/debug.log` の `debug:` は非推奨警告（動作継続）。`logs/error.log` や Fatal/Exception が本当のエラー。デバッグモードでは警告も画面表示され「エラー」に見えるので注意。
2. **失敗が多いときは根本原因単位で集計**。フルログから例外メッセージを正規化して集計し、systemic な原因（少数の原因が大量の失敗を生む）を先に特定する。
   ```
   docker exec basercms sh -c 'cd /var/www/html && grep -hoE "[A-Za-z\\\\]+Exception: .{0,80}|[A-Za-z\\\\]+Error: .{0,80}" .phpunit.log | sed -E "s/[0-9]+/N/g" | sort | uniq -c | sort -rn | head -30'
   ```
   テストクラス単位の集計:
   ```
   docker exec basercms sh -c 'cd /var/www/html && grep -hoE "^[0-9]+\) [A-Za-z0-9_\\\\]+Test::" .phpunit.log | sort | uniq -c | sort -rn | head -40'
   ```
3. **アプリ src 起因か、テスト/環境/fixture/i18n 起因かを切り分ける**。
   - `git diff HEAD -- <file>` … 当該ファイルが自分の変更対象か。
   - 未変更ファイル かつ プラグインロード依存（`Plugin::isLoaded('X')` が false で behavior 未アタッチ＝`Unknown method` 等）／DIコンテナ未登録（`Alias ... is not being managed by the container`）／外部プラグインクラス未ロード／**英語↔日本語メッセージ不一致**（ロケール/翻訳）なら、移行起因ではなく環境・テスト要因の可能性が高い。
   - **クリーンな baseline は作りにくい**点に注意：フレームワークを上げた後は vendor が入れ替わっているため、単純な `git stash` では移行前の状態を再現できない。
4. **修正 → lint → `--filter` で単体確認 → 全テスト再実行**で件数の改善と新規回帰を確認する。

## フルスイートの落とし穴（環境汚染で「大量失敗」に見えるケース）

単体・部分実行は通るのにフルスイートだけ大量に失敗する場合、ほぼ環境汚染。コード起因と誤認しないこと。

### 1. バックグラウンド実行を kill すると phpunit がオーファン化 → 並行実行で全滅（最重要）
`docker exec ... phpunit` をバックグラウンドにして**タスクを停止しても、コンテナ内の phpunit プロセスは生き残る**。再実行すると**複数 phpunit が同じ test DB を奪い合い**、互いの fixture を truncate/再構築して**双方が大量 error**になる。
- 兆候: ログの進捗カウンタが**重複・交錯**する（例: `61/4442` と `122/4442` が交互に出る／`/ 4442` の行数が想定以上）。
- 必ず確認: `docker exec basercms sh -c 'ps aux | grep -c "[p]hpunit"'`（0 でないなら停止する）。
- 停止: `docker exec basercms sh -c 'pkill -f phpunit'`（`sleep` を付けると権限プロンプト/タイムアウトになりやすいので単体で）。
- 原則: フルスイートは**単一プロセスで完走させ、途中で kill しない**。kill した時は必ずオーファンを掃除してから再実行する。

### 2. 破壊的テストが共有 test DB / vendor / 実ファイルを汚す
`BcComposerTest`（実 composer を実行し composer.json/lock・vendor を書き換え）、移行テスト（一時マイグレーション `*_TestMigration.php` を生成）等は環境を汚し、**残骸が次回 bootstrap を壊す**。
- **`TestMigration.php` の version 重複** → bootstrap の `Migrator` が `Duplicate migration ... has the same version` で起動失敗 → スキーマ未構築 → 全テストが `Base table or view not found: ... .sites` で連鎖 error。掃除: `ls plugins/*/config/Migrations/*TestMigration*` を確認し残骸を削除。
- **vendor が CakePHP 5.0 系にダウングレードされたまま残る** → `__d()` が旧 I18n の `_cake_core_` キャッシュ設定を参照し `cache configuration does not exist`。復旧: `git checkout -- composer.json composer.lock && composer install`。
- **実ファイルの dirty/残骸**: `composer.lock`・`plugins/*/VERSION.txt`・`webroot/files/contents/*`（例 `baser.power.gif`）が残ると、関連テストが「ファイルが消えていない」等で失敗。掃除: `git checkout -- composer.lock plugins/baser-core/VERSION.txt ...` と残骸ファイル削除。
- スキーマが壊れたかの確認: test DB のテーブル数を見る（健全時は数十テーブル。`test_suite_light_dirty_tables` だけ等なら未構築）。`Migrator` は次回 phpunit 実行時の bootstrap で再構築するので、**残骸を消してから**小さなテストを1本流せば復旧する。

### 3. CakePHP の `ErrorTrap` が握った警告は PHPUnit のサマリに出ない
PHP の E_WARNING/E_NOTICE 等が `Cake\Error\ErrorTrap->handleError()` で捕捉されると、**PHPUnit の `Warnings:` 件数には計上されず**、標準出力（=ログ）に `warning: 2 :: ...` として出るだけ。`--display-warnings` でも拾えないことがある。
- 警告を洗うときは**サマリだけでなくログ本文を grep** する: `grep -nE "warning: [0-9]+ ::|on null|Deprecated" .phpunit.log`。
- 例: `Attempt to read property "X" on null`（null 参照）はサービスの `->get()->prop` 等で頻出。null 安全化で解消する。


## プラグイン単体（スタンドアロン）でのテスト実行環境の導入

フルスイート（上記 `basercms` コンテナ）とは別に、**1プラグインだけを独立してテストできる**仕組み。4→5 移行中のプラグインを TDD で進めるのに有効（移植したテストが Table/Service 5系化の検証になる）。

- **実行コンテナはアプリ側**（例: `catchup-portal`、配置先 `/var/www/html/v5`）。DB ホスト（例 `cu-db`）は Docker ネットワーク内でしか解決できないため、**phpunit はコンテナ内で実行**する（ホスト直叩きは接続不可）。
- プラグインは自前の `composer.json` / `vendor/` を持ち、baser-core を dev 依存として取り込む。

### 必要なファイル一式（プラグイン直下）

1. `composer.json` … `require-dev` に以下。**`robmorgan/phinx` は必ず `0.16.10` にピン**（後述の罠）。
   ```json
   "require-dev": {
       "phpunit/phpunit": "10.5.31",
       "josegonzalez/dotenv": "^4.0",
       "baserproject/baser-core": "5.2.1",
       "robmorgan/phinx": "0.16.10",
       "vierge-noire/cakephp-fixture-factories": "^3.0",
       "vierge-noire/cakephp-test-suite-light": "^3.0"
   },
   "autoload-dev": {
       "psr-4": {
           "<Plugin>\\Test\\": "tests/",
           "App\\": "tests/TestApp/src/",
           "BaserCore\\Test\\": "vendor/baserproject/baser-core/tests/"
       }
   },
   "minimum-stability": "dev",
   "prefer-stable": true
   ```
2. `phpunit.xml.dist` … `bootstrap="tests/bootstrap.php"`、`<testsuite>` に `<directory>tests/TestCase/</directory>`、`<extensions>` に `Cake\TestSuite\Fixture\Extension\PHPUnitExtension`。
3. `tests/bootstrap.php` … TestApp の `config/paths.php` 読込 → `vendor/autoload.php` → コア bootstrap → `Configure::load('app')` → **`Configure::load('install')` で test 用 Datasources を設定** → `(new Migrations\TestSuite\Migrator())->runMany([['plugin'=>'BaserCore'],['plugin'=>'<Plugin>']])` でスキーマ構築 → `Configure::write('BcApp.testAppPluginsToLoad', ['<Plugin>'])`。
4. `tests/TestApp/`（最小アプリ骨格）… `config/install.php`（`Datasources.default` と **`Datasources.test`（test 用DB、例 `test_catchup_portal_v5`）**）、`app.php`/`app_local.php`/`bootstrap.php`/`paths.php`/`plugins.php`/`routes.php`、`src/Application.php`、`src/Controller/AppController.php`。
5. `config/Migrations/`（プラグイン側のスキーマ。`*_Initial.php` ＋ `schema-dump-default.lock`）。BaserCore 分は vendor から自動で流れる。
6. **test 用 DB（例 `test_catchup_portal_v5`）を事前作成**しておく。

### ★罠: phinx 0.16.11 で migrations が壊れる（最重要）

`cakephp/migrations 4.6.6` 環境で `robmorgan/phinx` が **0.16.11** に上がると、bootstrap のマイグレーション実行時に次の Fatal で**テスト本体に到達せず全滅**する:
```
Class Migrations\Db\Adapter\PhinxAdapter contains 2 abstract methods and must
therefore be declared abstract or implement the remaining methods
(Phinx\Db\Adapter\AdapterInterface::preExecuteActions, ...::postExecuteActions)
```
phinx 0.16.11 が `AdapterInterface` にメソッドを追加したのに migrations 4.6.6 の `PhinxAdapter` が未実装なため。**対処は phinx を 0.16.10 に固定**（動作実績のあるアプリ本体と同じ版に合わせる）:
```
docker exec -w /var/www/html/v5/plugins/<Plugin> <container> sh -c 'COMPOSER_MEMORY_LIMIT=-1 composer update robmorgan/phinx --with-all-dependencies --no-interaction'
```
composer.json の `require-dev` にも `"robmorgan/phinx": "0.16.10"` を明記して再発を防ぐ。

### 事前確認①: 対象コンテナの特定（思い込み厳禁）

**コンテナ名は決め打ちしない。** 環境には複数の baserCMS 系コンテナが同居することがある（例: `basercms`＝コア monorepo の開発環境 PHP 8.5、`catchup-portal`＝本プロジェクト PHP 8.1）。名前が似ていて取り違えやすい。実行前に**対象アプリが入っているコンテナを実際に確認**する:
```
docker ps -a --format '{{.Names}}\t{{.Status}}'                      # 候補を列挙
docker exec <候補> sh -c 'ls -d /var/www/html/v5 >/dev/null 2>&1 && echo HIT; php -v | head -1'
```
目的のパス（例 `/var/www/html/v5`）が存在し、想定の PHP バージョンが出るコンテナが正解。DB コンテナも同様に、接続先ホスト名（`install.php` の `host`、例 `cu-db`）と一致する名前のものを使う（`bc-db` 等の別 DB と混同しない）。

### 事前確認②: コンテナの稼働（最初に必ず）

特定したら、**アプリコンテナと DB コンテナが両方 Up か確認し、落ちていれば起動する**。停止状態（`Exited`）のまま `docker exec` すると `Connection refused`／コンテナ無し で無駄に詰まる。
```
docker ps -a --format '{{.Names}}\t{{.Status}}' | grep -E '<container>|<db-container>'
docker start <container> <db-container>
```
DB コンテナは起動直後は mysqld がまだ接続を受け付けないことがあるので、**疎通するまで待つ**:
```
for i in $(seq 1 30); do docker exec <db-container> sh -c 'mysqladmin ping -h127.0.0.1 -u<user> -p<pass> 2>/dev/null | grep -q alive' && break; sleep 2; done
```
（接続情報はプラグインの `tests/TestApp/config/install.php` の `Datasources.test`、本番は `v5/config/install.php` を参照。catchup-portal では DB ホスト `cu-db` / DB `test_catchup_portal_v5` / user `catchup`。）

### 実行コマンド

```
docker exec -w /var/www/html/v5/plugins/<Plugin> <container> sh -c 'vendor/bin/phpunit --testdox 2>&1 | tail -60'
```
bootstrap を通過してテスト一覧が出れば、migrations → DB 構築まで成功している。

### 旧4系テスト資産の整理（移行時）

- **集約クラスは削除**: `CakeTestSuite` を継承し `public static function suite()` で束ねるだけの `*AllTest` / `*AllModelTest` は CakePHP5/PHPUnit10 で機能せず（`CakeTestSuite` 不在）、`<directory>` 探索に拾われてロードエラーになる。価値ゼロなので削除。
- **Fixture を5系へ**: `extends CakeTestFixture` ＋ `public $import` / `public $records`（4系）→ `Cake\TestSuite\Fixture\TestFixture` 系へ。
- **テストを5系へ**: `extends BaserTestCase` / `ClassRegistry::init('Plugin.Model')` / `public $fixtures = ['plugin.cpm.User']`（4系記法）→ BaserCore の TestCase 基底＋`fetchTable()` ＋ 5系 fixtures へ。
- 注意: メソッド名が揃っていても **Table 本体が4系のまま**（`$this->Assoc->find('first',...)`・`unbindModel`・`virtualFields`・`Behaviors->detach('BcCache')` 等の残骸／`// TODO baserCMS5移行:` マーカー）のことがある。その場合テストは赤になるのが正しく、SUT の5系化と対で進める。

## メモ

- 全体テストでメソッド名を表示したい場合は環境変数 `SHOW_TEST_METHOD=true`（`BcTestCase::setUp` が対応）。
- ローカル固有の事情は `.github/instructions/local.instructions.md`（`.gitignore` 対象で存在しない場合あり）も参照。

関連: 移行起因の不具合の修正レシピは `cakephp-migration` / `php-migration` スキルへ。
