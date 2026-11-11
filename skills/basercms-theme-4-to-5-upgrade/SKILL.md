---
name: basercms-theme-4-to-5-upgrade
description: 'baserCMS 4 のテーマ（templates/layout・element・Blog/Pages/Mail テンプレート＋少数の Helper で構成）を baserCMS 5 のテーマプラグインへ移行する際のパターン集。「テーマを4から5へ移行」「BcAddonMigrator でテーマ変換後の手修正」「siteConfig[] 廃止」「fullUrl() 廃止」「blogPosts() 等ショートカットメソッドの実在確認」「メールフォームテンプレートの移行（Mailform→BcBaser mailForm系）」「ウィジェット element の widgets→widget」「ビュー変数が空」「params[Content] 廃止」「css()/js() の inline 第2引数化」「pageTitleHelper could not be found」「BcPage->content() 廃止」「固定ページテンプレートが Pages/templates/ にあって Missing Template」「getBlogs() 廃止」「BlogCategory 配列アクセス」「BcUpload の setTable / BcUploadBehavior 未設定」「アイキャッチ画像404」「サブディレクトリ設置でURLの base が欠ける」等で参照する。テーマ固有の移行パターン（TH-系）と、フロント表示エラーのうちテンプレート・テーマ描画系の実例パターン（F-系）を収録。本スキルは4系イディオムの検出と変換に絞り、5系テーマの正しい書き方の正本は basercms5-theme-development を参照する。プラグイン内部コード（Controller/Table/Entity/管理画面）は basercms-plugin-4-to-5-upgrade、サイト全体の手順は basercms4-to-5-upgrade、テスト実行は basercms-unittest スキルを参照。'
license: MIT
---

# baserCMS テーマの 4 → 5 移行パターン集

本スキルの対象は**テーマ**の baserCMS 4 → 5 移行。テーマは `templates/layout`・`templates/element`・`templates/Blog`・`templates/Pages`・`templates/Mail` などのテンプレートが主体で、Controller/Table を持たず、少数のフロント表示ロジック用 Helper（`src/View/Helper/*.php`）を伴う構成を指す。`BcAddonMigrator` でテーマを5系のテーマプラグインへ変換した**後**に必要となる手作業の書き換えパターン（TH-系）と、フロント表示エラーのうちテンプレート・テーマ描画系の実例パターン（F-系）を収録する。

本スキルが扱うのは**4系テーマコードの検出と変換**である。**5系テーマの正しい書き方の正本は basercms5-theme-development**（プラグイン内部コードは basercms5-plugin-development）であり、変換先の仕様（テーマプラグインの構造・ビュー変数の作法・ヘルパ・アセットとURL・ウィジェット・メールフォーム/ブログテンプレート）に迷ったらそちらを参照する。以下の各節は「4系イディオムの検出（症状・grep パターン）→ 変換の要点 → 正本スキルの該当節」の形で読む。

テーマ変換の全体手順（テーマの zip 化 → `BcAddonMigrator` での変換 → `plugins/` への配置 → 横断5系化 → `sites` テーブルの `theme` への適用）は **basercms4-to-5-upgrade** スキルの該当節（テーマの変換／移行の標準フロー）を参照すること。本スキルはその工程の中から呼ばれ、変換後のテンプレート・Helper を実際に描画が通る状態へ直すための具体策を提供する。

横断対応の原則（1箇所直したら同じパターンを `grep -rn` で全件洗い出し → 機械的に一意な変換は一括適用 → 変更ファイルを全て `php -l` で検証）と、C-0（機械一括変換カタログ）・イベントリスナー/Helper の書き換えパターンは **basercms-plugin-4-to-5-upgrade** スキルを参照。テーマにプラグイン相当の内部コード（Controller/Table/管理画面）が含まれる場合も同スキルを併用する。

## テーマ（Theme）固有の移行パターン（T-/C-系との違い）

> **テーマは Controller/Table を持たない**（プラグインと構造が根本的に異なる）ため、basercms-plugin-4-to-5-upgrade スキルの T-（Table/ORM）・C-（Controller/画面）カタログは基本的に適用外。テーマの主体は `templates/layout` `templates/element` `templates/Blog` `templates/Pages` `templates/Mail` と、少数のフロント表示ロジック用 `src/View/Helper/*.php`。**F-系（フロント表示エラー）が主対象**だが、テーマ特有の"消えたショートカット系ヘルパーメソッド"の当たり方がプラグインと異なるため、以下に固有パターンとしてまとめる（`basercms4-to-5-upgrade` の「テーマの変換」章から呼ばれる想定）。

### TH-1. `$this->BcBaser->siteConfig['key']` / ビュー変数 `$siteConfig['key']` は5系に存在しない
- 検出: テンプレ・Helper の `$siteConfig['key']`／`$this->BcBaser->siteConfig['key']`（`grep -rn "siteConfig\[" templates/ src/`）。5系では構文エラーにならず**未定義変数／未定義プロパティの警告つきで空文字が出力される**だけなので気づきにくい（サイト名・住所等が黙って空になる）。
- 変換: `\BaserCore\Utility\BcSiteConfig::get('key')`（静的メソッド）へ。キーは4系 `site_configs` テーブルの `name` 列と同じ。1箇所で見つけたら grep でテーマ全体（layout・element・Helper）へ横断適用する。
- 静的ユーティリティの5系の作法は basercms5-theme-development §3「ヘルパ」を参照。

### TH-2. グローバル関数 `fullUrl()` は5系に存在しない
- 検出: `Call to undefined function fullUrl()` で Fatal（4系のグローバル関数）。
- 変換: `\BaserCore\Utility\BcUtil::fullUrl($url)`（静的メソッド）へ（basercms5-theme-development §3「ヘルパ」参照）。

### TH-3. 4系専用 Component をテーマ Helper が直接インスタンス化しているコードは即Fatal — 先に baser-core に同等機能が移植されていないか確認する
4系のテーマ独自 Helper が `new XxxComponent(new ComponentCollection())` のように CakePHP2 の Component を直接生成しているコードが、`BcAddonMigrator` の機械変換後もそのまま残ることがある。`Component` 基底クラスも `ComponentCollection` も5系に存在しないため**呼び出された瞬間にFatal**（F-4「ヘルパーの手動インスタンス化」と同根だが、対象が Component である点が異なる）。
- **対処の順序**: いきなり自前で再実装しない。**まず `grep -rli "<機能キーワード>" vendor/baserproject/` で baser-core／該当コアプラグインに同等のユーティリティが既に移植されていないか確認する**。baserCMS5 は主要な4系専用ロジック（Google Geocoding 連携など）を `BaserCore\Utility\*` や `BaserCore\View\Helper\*` として先に移植済みのことが多い。
- **実例**: テーマの `BcGooglemapsHelper::getLocation()` が `new BcGmapsComponent(new ComponentCollection())`（4系 `lib/Baser/Controller/Component/BcGmapsComponent.php`。中身は Google Geocoding API への XML リクエスト）を呼んでいた。調査の結果、baser-core に **`BaserCore\Utility\BcGmaps::getLocation($address)`**（`Cake\Http\Client` でのHTTPリクエスト化＋`Cache` によるキャッシュ付き、戻り値 `['latitude'=>..,'longitude'=>..]` は4系と同一形）が既に存在した。テーマ側は独自の `load()`/`_getScript()` インターフェースは残しつつ、`getLocation()` の中身だけをこのコアユーティリティへの委譲に差し替えるだけで解決した（自前でのHTTPクライアント実装・XMLパース実装は不要だった）。
- **見落としがちな呼び出し元**: Component 呼び出しは Helper 内に隠れているため、要素テンプレート側からは「単なるメソッド呼び出し」にしか見えない。要素テンプレートで実際にそのメソッドへ到達する条件（デフォルト引数のときだけ呼ばれる、等）を先に読み解いてから Helper 側の実装を追う（本例では「緯度経度が明示指定されていないときだけ `loadLocation()`→`getLocation()` に到達する」という条件分岐を確認してから着手した）。

### TH-4. `BcBaserHelper` のショートカットメソッドの実在確認は「関数名 grep」だけでは誤判定する（★訂正済みの教訓）
- 検出: 4系 `BcBaserHelper` にあったフロント用ショートカット（`blogPosts($blogName, $num)` 等）の呼び出し。5系では PluginBaserHelper 機構（各プラグインの `methods()` マッピング）経由で `__call` に委譲されるため、**関数定義が存在しないのが正常**。`grep -rln "function <名前>"` が0件なのを根拠に「5系に代替なし」と判断して呼び出しを無効化してはならない（★実際に誤判定した戒め）。
- 変換の要点: 実在確認は「①関数定義 grep → ②`methods()` マッピング grep」の**2段階**で行う。②にあれば提供プラグイン有効時にそのまま動く（無効時は MissingHelperException 系ではなく BadMethodCall になるので、プラグイン無効の可能性も疑う）。①②とも無い場合のみ本当に廃止 → クエリビルダで手動再実装し、複数箇所に散在するならテーマの Helper に集約する。
- 委譲機構と2段階確認手順の正本は basercms5-theme-development §3「ヘルパ」、ブログ記事取得の再実装の基本形（`getConditionAllowPublish()` 等）は同 §7「ブログテンプレート」を参照。
- **重複実装との突合**: 独自実装の element と機能重複がありうる。ただし「重複」判定の前に**その element が実際に参照されているか**（`grep -rn "element('<名前>'"`）を確認する — 参照ゼロの未接続ファイルなら重複ではなく、4系挙動に忠実な方（元の呼び出し）を復活させるのが正。

### TH-5. layout/element から他プラグインの Helper を直接呼ぶコードは「テーマのバグ」と「依存プラグイン未導入」を区別する
テーマの layout やエレメントが `$this->Banner->showBanner(...)` のように**別プラグインが提供する Helper** を直接呼んでいることがある。移行作業を `フェーズ3.5（棚卸し）` → `フェーズ4-(b)（テーマ/プラグイン機械変換）` → `フェーズ4-(a)（マーケット配布の5系プラグイン導入）` のように段階分けしている場合、その依存プラグインがまだ導入されていない段階でテーマ側だけ見ると `Undefined property: $this->Banner`（Helper未ロード）に見えるが、**これはテーマのコードの不具合ではなく、依存プラグインのフェーズがまだ来ていないだけ**のことがある。
- **対処**: 台帳では「未着手／移行済」ではなく **「見送り（依存プラグイン未導入・フェーズ4-(a)待ち）」**のように区別して記録し、テーマ単体の完了条件に含めない。該当プラグインの導入フェーズが終わった後で改めて動作確認する。
- 呼び出し元のメソッド名・期待するオプション（`['num' => 0]` 等）だけは、後で突き合わせられるよう台帳にメモしておく（導入される5系版プラグインでシグネチャが変わっている可能性があるため）。

### TH-6. `BcSite::findCurrent()` ＋ `getBaseUrl() . 'theme/<name>/'` でテーマ資産URLを組む4系イディオムは即Fatal
- 検出: `grep -rn "BcSite::findCurrent\|'theme/'" templates/ src/`。4系はサイトエンティティからテーマ名を取り `theme/<name>/img/...` 形式のURLを組んでいたが、`BcSite` クラスは5系に存在せず即 Fatal。
- 変換: テーマ資産はプラグイン webroot 配信形式 `$this->BcBaser->getUrl('/<テーマ名snake>/img/...')` へ（正本: basercms5-theme-development §4「アセットとURL」）。

## フロント表示エラーの実例パターン（症状 → 原因 → 修正）

> テーマ／プラグインのフロント表示を復旧させる際に頻出する実例。`BcAddonMigrator` で自動変換した後も残る典型的な不具合。**エラーメッセージで検索して該当パターンに当てる**こと。1つ直すと次のエラーが現れる「玉ねぎ剝き」になるため、`curl -sk -o /dev/null -w "%{http_code}" <URL>` でステータスを見ながら1件ずつ潰す。

### F-1. `MissingTableClassException: Table class for alias 'Content' could not be found.`
- 検出: 4系流の `TableRegistry::getTableLocator()->get('Content')`（単数形・プラグイン接頭辞なし）。
- 変換: コアテーブルは**複数形＋プラグイン接頭辞**（`BaserCore.Contents`/`BaserCore.Sites`）へ。あわせて `find('first', 配列)` → クエリビルダ、配列アクセス → エンティティ（`$content->id`）、`where()` の条件キーはテーブルエイリアス付きへ。参照名の規約は basercms5-theme-development §3「ヘルパ」を参照。

### F-2. 現在のコンテンツ／サイト情報の取得（リクエスト属性の変更）
- 検出: 4系の `$this->request->params['Content']['site_id']`／`params['Site']['device']`（廃止）。
- 変換: リクエスト属性 `currentContent`/`currentSite`（エンティティ）から `->id` `->site_id` `->device` 等で参照する。取り方の正本は basercms5-theme-development §2「View・ビュー変数の作法」。

### F-3. コアプラグインの参照名に `Bc` 接頭辞（Helper・テーブル・エレメント共通）
- 検出: 4系の参照名のまま（`loadHelper('Blog.Blog')`・`get('Blog.BlogContents')`・`getElement('Blog...')`）。
- 変換: コアプラグインは `Bc` 接頭辞へ（`Blog`→`BcBlog`、`Mail`→`BcMail`）。URL配列だけでなくヘルパー読み込み・テーブルエイリアス・エレメントパスすべてが対象。規約の正本は basercms5-theme-development §3「ヘルパ」。

### F-4. ヘルパーの手動インスタンス化（`new XxxHelper(new BcAppView())`）
- 検出: 4系流の `new <Xxx>Helper(new BcAppView())`（`BcAppView` 廃止・DIコンテナ未注入で `getService()` が失敗する）。
- 変換: `$this->getView()->loadHelper('Plugin.Helper')` でロードする（`loadHelper()` はインスタンスを返す）。動的ロードの作法は basercms5-theme-development §3「ヘルパ」を参照。

### F-5. `League\Container\Exception\NotFoundException: Alias (...ServiceInterface) is not being managed` ／ `MissingHelperException`
フロントが依存するプラグイン（例: BcBlog）が **plugins テーブルで `status=0`（無効）** だと、そのプラグインの ServiceProvider がコンテナに登録されず、Helper コンストラクタの `getService(XxxServiceInterface::class)` で落ちる。
- **判別**: `SELECT name, status FROM plugins;` で対象プラグインの status を確認。
- **修正**: v4 で使っていたプラグインを**有効化**する（正攻法は管理画面のプラグイン管理。データ移行済みでテーブルが揃っているなら `UPDATE plugins SET status=1 WHERE name='BcBlog';` でも可）。有効化後は `bin/cake cache clear_all`。
- 補足: コンテナに無いサービスへ依存しないコードに書き換える手もある（例: テンプレートパス決定はサービスを介さず `TableRegistry` でブログコンテンツを引いて `'BcBlog...' . DS . 'Blog' . DS . $contentsTemplate . DS . $template` を組み立てる）。

### F-9. ブログ記事のソート列 `posts_date` は5系に存在しない
`SQLSTATE[42S22]: Unknown column 'BlogPosts.posts_date'`。5系の `blog_posts` の投稿日時カラムは **`posted`**。
- **修正**: ソート指定を `'sort' => 'posted'` にする。カラム名は移行先DBの `SHOW COLUMNS FROM blog_posts;` で確認するのが確実。

### F-11. フロントのヘッダー／メニューが「ログイン時のみ」描画される
ポータル系テーマでは、ヘッダーのナビ・ユーザーメニュー・アプリランチャー等が `if(!empty($user))` で囲まれ、**未ログインだとロゴ＋サイト名しか出ない**ことがある。これは仕様。さらにヘッダーは `CuAppLauncher` `CuCustomUser` `CuTimeCard` 等のプラグインに依存するため、それらが無効だと該当ブロックが空になる。
- **確認のコツ**: 「ヘッダーが出ない」をコードのバグと早合点しない。まず**フロントにログイン**し、依存プラグインの有効化状況（F-5）を確認する。

### F-12. アイキャッチ等の画像404はDBと物理ファイルの不一致のことがある
`/files/blog/.../xxxx_eye_catch.jpg` の `MissingRouteException` が大量に出ても、**該当画像が移行元（4系）のローカルにも存在しない**場合がある（本番サーバーにのみ実体があり、ローカルDBダンプだけ持ってきた等）。移行コードの不具合ではない。
- **判別**: 移行元の `files/`（または `app/webroot/files/`）に実体があるか確認。古い年月の画像が表示でき新しい年月だけ404なら、ローカルに実ファイルが無いだけ。

### F-13. フロントのテーマで `$user` 等のビュー変数が空になりヘッダー等が欠ける
- 検出: 4系はコアがフロント全ビューへ `$user` 等を供給していたが、**5系はフロントに供給しない**（管理画面レイヤー専用）。テーマの element が `$user` を参照していると、ログイン中でも未ログイン扱いになり `if(!empty($user))` 配下（ナビ・ユーザーメニュー等）が丸ごと描画されない。
- 変換: element／レイアウトの先頭で必要な変数を自前で導出する（`BcUtil::loginUser()`＝`UserInterface|false`・`getRequestPrefix()`・`getAuthPrefixes()`）。あわせて4系の `$this->Session->...`（SessionHelper 廃止）→ `$this->getRequest()->getSession()->...`。**element／レイアウト内の `$this` は View 自身**なので `$this->getRequest()` を使う（`getView()` は Helper 用。View で呼ぶと `Call to undefined method ...View::getView()`）。自前導出の正しい書き方は basercms5-theme-development §2「View・ビュー変数の作法」を参照。
- 補足: フロント（prefix=`Front`）の `BcUtil::loginUser()` は、管理画面にログインしていればフロントでもユーザーが取得できる。

### F-14. `BcBaser->css()` / `js()` の第2引数が `$inline` に変わり `media`/属性指定が無視される
- 検出: 4系流に第2引数へ options（`css(['print'], ['media' => 'print'])` 等）を渡している箇所。5系は第2引数が `$inline` のため属性が出力されず、**印刷専用CSSが画面にも適用されてヘッダー等が消える**という分かりにくい症状になる（HTML には出力されており、DevTools で print.css 由来の `display:none`。`<link>` に `media="print"` が無い）。
- 変換: 第2引数に `$inline`（通常 `true`）、属性は第3引数へ。レイアウト／element 内の**全 `css()`/`js()` 呼び出し**を確認する。シグネチャの正本は basercms5-theme-development §4「アセットとURL」。

### F-15. `Attempt to read property "X" on array`（`request->params['Content'][...]` の変換ミス）
- 検出: `BcAddonMigrator` が4系の `params['Content']['entity_id']` 等を `getAttribute('params')->entity_id` のように**配列を誤ってオブジェクト矢印アクセスに変換**した残骸（`getAttribute('params')` は routing パラメータの**配列**）。
- 変換: 現在のコンテンツ情報は `getAttribute('currentContent')`（Content エンティティ）から取る（basercms5-theme-development §2「View・ビュー変数の作法」参照）。`getAttribute('params')` 自体への配列アクセス（`['pass'][1]` 等）は正しいが、**メソッド呼び出し結果への `isset()` は不可** — 一旦変数に受けてから `?? ''` で参照する。

### F-16. ビューでの `$this->getRequest()->url` は廃止
- 検出: 4系の `$this->request->url`（先頭スラッシュ**なし**）。コントローラだけでなくテーマの element にも残りがち。
- 変換: `$this->getRequest()->getPath()`（先頭スラッシュ**あり**）へ。4系で `'/' . $request->url` としていた箇所は先頭の `'/' .` を除去する（F-2 と同根。basercms5-theme-development §2 参照）。

### F-17. メールフォーム（BcMail）テーマテンプレートの移行
- 検出: メールフォームのコンテンツ（type=`MailContent`, plugin=`BcMail`）を表示すると、まず BcMail 無効で `MissingControllerException`（F-5）になり、有効化後もテーマの mail テンプレートが4系の `$this->Mailform->...` API のままで複数段階のエラーになる。
- **(a) フォーム生成**: `No context provider found for value of type 'string'` — `$this->Mailform->create('MailMessage', $opts)` → `$this->BcBaser->createMailForm($mailMessage, ...)`（第1引数はコントローラが view にセットする**エンティティ**）。
- **(b) フォーム系ヘルパー**: 4系 `$this->Mailform->` の各メソッド（`hidden`/`unlockField`/`submit`/`error`/`authCaptcha`/`end`/`freeze` 等）は、フィールド名から **`MailMessage.` 接頭辞を除去**した上で、**basercms5-theme-development §6「メールフォームテンプレート」の対応表どおり** BcBaser の mailForm 系 API（`mailFormHidden`/`unlockMailFormField`/`mailFormSubmit`/`mailFormError`/`mailFormAuthCaptcha`/`endMailForm`/`freezeMailForm` 等）へ変換する。JS が `#MailMessageMode` 等の旧 id を参照する場合の明示 id も同節を参照。
- **(c) file 型フィールドの BcUpload テーブル指定（重要・忘れやすい）**: file 型フィールドがあるテンプレート（index.php / confirm.php）の先頭に `setTableToUpload('BcMail.MailMessages')` が無いと `BcUploadHelper を利用するには … table … を指定してください`（BcException）で落ちる（basercms5-theme-development §6 参照）。
- `element('mail_input')` はコア版にフォールバックするので、テーマに override が無ければ触らなくてよい（同 §6）。
- **(d) メール本文（email）テキストテンプレート**: 4系の `element('../Emails/text/mail_data')` は5系では `element('../email/text/mail_data')`（ディレクトリ名変更）。テンプレ内の `$mailConfig['x']` は配列→**エンティティ**（`$mailConfig->x`）に変わっている。

### F-19. サブディレクトリ設置で画像・アセットURLの `/v5/` が欠ける（外部5系版プラグインにも潜む）
- 検出: リンク切れ画像＋`error.log` の `MissingRouteException: /files/...`。既存の「5系対応版」外部プラグインでも、アップロードURL等を**ルート相対でハードコード**していてサブディレクトリ設置非対応のことがある。
- 変換: リクエストの webroot を前置する（`getAttribute('webroot') . ltrim($url, '/')`）か、リンクURLなら `\Cake\Routing\Router::url($url)` を通すだけでも base が付与される。URL 生成の正本は basercms5-theme-development §4「アセットとURL」。本家未対応ならローカルパッチとしてコメントを残し、上流へ報告候補にする。
- 既存5系版を使うプラグインでも**サブディレクトリでの描画確認は省略しない**こと。

### F-22. `BcUploadHelper::uploadImage()` は5系で第2引数が EntityInterface 必須（4系はファイル名文字列）
- 検出: `第２引数に EntityInterface を指定してください。`（BcException・500）、または `grep -rn "uploadImage('" templates/ src/` で第2引数が文字列/配列値のもの。アイキャッチ・アップロード画像を表示するテンプレ／ヘルパで頻出。
- 変換: `uploadImage('<field>', $entity, ['table' => '<Plugin>.<Tables>', ...])` へ——第1引数は素のフィールド名（4系の `Model.field` 修飾を除去）、第2引数は**フィールドを持つエンティティ**、そして BcUploadHelper はデフォルトで View の plugin/name からテーブルを解決するため **`'table'` オプションで BcUpload behavior 持ちのテーブルを明示**する。テンプレに4系互換の配列データしか無い場合は、供給側（コントローラ/ヘルパの変換処理）で元エンティティも一緒に渡すよう直す。旧 `'size'` オプションは `'imgsize'`。

### F-20. ウィジェット element は4系 `Elements/widgets/`（複数形）→ 5系 `templates/element/widget/`（単数形）
- 検出: フロントに「エレメントテンプレート『<Plugin>.widget/xxx』が見つかりませんでした。」が露出する。`BcAddonMigrator` は4系の `View/Elements/widgets/`（複数形）を `templates/element/widgets/` にそのまま移すが、5系 BcWidgetArea は `element/widget/`（**単数形**）を探すためパスが合わない。
- 変換: `templates/element/widgets/` → `templates/element/widget/` へリネーム（`templates/Admin/element/widgets/` も同様）。中身の5系化（配列→エンティティ等）は別途必要。配置の正本は basercms5-theme-development §5「ウィジェット」。
- **★テーマ側のオーバーライド版も忘れず同様にリネーム**する。プラグイン側だけ直すとテーマのオーバーライド（独自デザイン版）が使われず、プラグインの素のテンプレで「デザインが崩れた」ように見える（実測: カード型ランキングが素のリスト表示になった）。

### F-23. 「初期表示時に要素が見えない／崩れる」系の症状は、まず本番の実HTMLと突き合わせて「移行時に付いた余計なクラス」を疑う
- 検出: 特定のブロックや一覧カードが「スクロールするまで表示されない」「レイアウトが崩れる」といった症状は、直感的には共通JS（アニメーション制御等）やCSSの不具合に見えるが、**5系移行時にテンプレートへ本番には存在しないCSSクラス（`fadeinAnime`/`sideinAnime`等のアニメーション系クラスが典型）が誤って付与されている**ことが真因のことがある。共通JS/CSS側は4系オリジナルと同一仕様で、それ自体は不具合ではないケースがある。
- **判別手順（共通JS/CSSを疑う前に必ず行う）**: 本番サイトの実際のHTMLソース（DevTools の要素パネル、または `view-source:`）で該当要素のclass属性を確認し、ローカル/v5側のテンプレートに書かれているclassと突き合わせる。本番に無いclassがローカルにだけ付いていれば、それがテンプレート側の余計な追加であり、共通JS/CSSを変更せずテンプレートから削除するだけで直る（影響範囲が最小）。
- **★罠: `WebFetch` ツールで本番HTMLを確認しようとしない**。`WebFetch` は取得したHTMLを**Markdownへ変換してから**小型モデルに渡す実装のため、`class`属性を含む大半のHTML属性がこの変換で失われる。「該当クラスは存在しない」という`WebFetch`の回答は偽陰性になりうる（実例: 一度誤った「存在しません」という結果を信じかけ、後にDevToolsのスクリーンショットと`view-source:`の実ソースで確認して訂正した）。class属性の有無を確認したいときは、`curl`（許可されていれば）でHTML生ソースを取得するか、ユーザーにDevTools/`view-source:`のスクリーンショットを依頼する。

### F-24. `View::$pageTitle` は5系に無く、未定義プロパティが「ヘルパー名」として解決されて500になる
- 検出: `Missing Helper` の本文に **`BaserCore.pageTitleHelper` could not be found** と出る。「そんなヘルパーは書いていない」ので原因を見失いやすいが、**`$this->pageTitle` / `$this->_View->pageTitle` を読んだ結果**である（`View::__get()` が未定義プロパティをヘルパーとして解決しにいくため、プロパティ名 + `Helper` という存在しないクラスを探して落ちる）。
- 検出コマンド: `grep -rn '\$this->pageTitle\|->_View->pageTitle' templates/ src/`
- 変換: 取得は `$this->BcBaser->getTitle()`、設定は `$this->BcBaser->setTitle(...)`。
- **★`BcAddonMigrator` はコントローラ内の `$this->pageTitle` しか変換しない**ため、テンプレート・レイアウト・テーマ Helper に必ず残る。移行直後に全件 grep して潰すこと。

### F-25. `BcPageHelper::content()` は5系に無い → `echo $page->contents`
- 検出: `Call to undefined method BaserCore\View\Helper\BcPageHelper::content()`。4系の固定ページテンプレート（`Pages/*.php`）はほぼ全てこれで本文を出力している。
- 変換: `<?php $this->BcPage->content(); ?>` → `<?php echo $page->contents ?>`（コア `bc-front/templates/Pages/default.php` と同じ書き方）。

### F-26. 固定ページテンプレートは `templates/Pages/` 直下に置く（`Pages/templates/` ではない）
- 検出: 固定ページが `Missing Template` になり、探索パスの一覧に `templates/Pages/<name>.php` が並ぶ。
- 原因: 4系テーマは `Pages/templates/<name>.php` という一段深い構成のことがあり、`BcAddonMigrator` はその階層をそのまま `templates/Pages/templates/` へ移すため5系の探索パスから外れる。
- 変換: `templates/Pages/templates/*.php` → `templates/Pages/` 直下へ移動。

### F-27. `BcBaser->getBlogs()` は5系に存在しない
- 検出: `$this->BcBaser->getBlogs(<id>)` が null を返し、その戻り値を使った `blogPosts()` が `$contentsName を省略時は、contentsTemplate オプションで…` という**一見無関係な例外**で落ちる。
- 変換: `blogPosts()` の第1引数には対象ブログのURL（`'/news/'` 等）を直接渡す。ブログのURLは `SELECT bc.id, c.url FROM <prefix>blog_contents bc JOIN <prefix>contents c ON c.entity_id=bc.id AND c.type='BlogContent'` で確認できる。

### F-28. ブログ記事のカテゴリは `$post['BlogCategory']` ではなくエンティティのアソシエーション
- 検出: 一覧テンプレートで `Trying to access array offset on null`。
- 変換: `$post['BlogCategory']['no']` → `$post->blog_category->no`。**カテゴリ未設定の記事があるので必ず `!empty($post->blog_category)` で守る**（4系は配列アクセスで警告止まりだったが、5系でも Warning が出て描画HTMLに混入する）。

### F-29. `BcUploadHelper` は使う前に対象テーブルの設定が要る／テーブル側に BcUpload ビヘイビアが要る
- 症状は2段階で出る。F-22（第2引数エンティティ化）を直した後に続けて出るので、セットで覚える。
  1. `BcUploadHelper を利用するには、$this->BcUpload->setTable() か …` → テンプレートの冒頭で `$this->BcUpload->setTable('<Plugin>.<Tables>');`（または `$this->BcBaser->setTableToUpload(...)`）を呼ぶ。
  2. `BcUploadHelper を利用するには、テーブル <...>Table で BcUploadBehavior の利用設定が必要です。` → Table の `initialize()` に `$this->addBehavior('BaserCore.BcUpload', [...])` を追加する。**設定内容は4系モデルの `public $actsAs['BcUpload']` をそのまま移植できる**（`saveDir` / `fields` / `namefield` / `nameformat` / `imagecopy` のキー構成は同じ）。移植を怠ると画像URLのサフィックス（`thumb_` / `pub_` 等）が生成されず404になる。

### F-30. メールフォームの JS が4系の項目名（`data[MailMessage][xxx]`）・id（`#MailMessageXxx`）を探していて、黙って効かなくなる
- 症状: エラーも 404 も出ないまま、送信や確認画面への遷移だけが失敗する。例: 見た目だけの同意チェックボックスにチェックを入れても、JS が非表示の本物の項目（`multi_check` の必須フィールド）へ写せず、送信すると「エラー：入力内容を確認して再度送信してください。」になる（実際の移行案件の、営業受付フォームで発生）。
- 原因: 5系のメールフォームは input の `name` が `data[MailMessage][xxx][]` → **`xxx[]`**、自動の id が `MailMessageXxx` → **`xxx`（ケバブケース）** に変わった。テーマの JS（テンプレート内の `<script>`・`webroot/js/*.js`・min 版）が4系の名前や id で要素を探していると、何も見つからず何も起きない。行の id（`#RowMessageXxx`）とボタンの id（`#BtnMessageConfirm` など）は5系でも同じ。
- 検出: テーマ全体を `grep -rnE "data\[MailMessage\]|#MailMessage[A-Z]|MailMessage[A-Z][A-Za-z]+"` で探す（`templates/`・`webroot/js/`・`min/` を含める）。見つかったセレクタごとに、5系の画面の HTML にその name / id が本当にあるかを確かめる。
- 直し方:
  - 名前で探さず、**5系でも変わらない行の id の中の要素**で探す: `$('input[name="data[MailMessage][privacy_agree][]"]')` → `$('#RowMessagePrivacyAgree input[type="checkbox"]')`。4系・5系どちらの名前でも動く。
  - JS が `#MailMessageMode` 等の id を前提にしているなら、`mailFormHidden('mode', ['id' => 'MailMessageMode'])` のように id を明示する（F-17・basercms5-theme-development §6）。入力欄なら `mail_input` 側で id を補う。
- **見落としやすい**: 4系と5系の画面の HTML を比べる全件突合では、JS の中の名前の違いは見つからない。移行のときは、**公開中のメールフォームを全部、全項目を埋めて確認画面まで送る**確認を必ず入れる（必須の同意チェック・ファイル添付・数値の項目も埋める。送信までは行わないのでメールは飛ばない）。

### F-31. Ajax で送るメールフォーム（LP などに埋め込んだもの）が、確認・送信でページ全体を返し「空の入力画面に戻る」
- 症状: 「確認する」を押すと、入力した項目が空になった入力画面に戻る。エラーも出ない（実際の移行案件の、LP に埋め込んだ問い合わせフォームで発生）。
- 作り: ページのレイアウトが `$this->Mail->getForm(<mail_contents.id>)` でフォームを埋め込み、テーマの JS が `$.ajax({url: form の action, data: form.serialize()})` で送って、返ってきた HTML を `$('.wrap').html(data)` で差し替える。
- 原因: **4系（CakePHP 2）は Ajax のリクエスト（`X-Requested-With: XMLHttpRequest`）でレイアウトを自動で外していた**（RequestHandler）。**5系は外さない**ので、確認・送信の応答がレイアウト付きのページ全体になり、その中のレイアウトが埋め込む「空の入力フォーム」が差し込まれる。
- 直し方: そのフォームのメールテンプレート（`templates/Mail/<form_template>/index.php`・`confirm.php`・`submit.php`）の先頭で、Ajax のときだけレイアウトを外す:
  ```php
  if ($this->getRequest()->is('ajax')) {
      $this->disableAutoLayout();
  }
  ```
- 検出: テーマ全体を `grep -rnE 'getForm\(|\$\.ajax|\.serialize\(\)'` で探し、メールフォームを Ajax で送る作りが無いかを見る。あれば、`X-Requested-With: XMLHttpRequest` を付けて確認画面まで送り、**応答に `<html` が無く、フォームの送り先が `/submit` になっている**（確認画面の断片が返る）ことを確かめる。
- 4系の `$this->Mail->token()`（戻るボタン対策）も5系に残っているが、5系のコアの `mail_token.js` は4系の項目名（`data[_Token][key]`）と `input[type="submit"]` を探すので、`<button>` のフォームでは何もしない。害は無いが、効いてもいない。

### F-32. メールフォームの移行は、フォームごとに「作り」を棚卸ししてから確かめる
- メールフォームは、テーマ側でテンプレートの HTML を大きく作り変えていたり、独自の仕様（見た目だけのチェックボックスを JS で本物の項目に写す・Ajax で送る・LP に埋め込む・`mail_input` を独自に書き直す・確認画面を出さない など）を持っていたりすることが多い。**全件突合（画面の HTML の比較）では、送信の不具合はほぼ見つからない**（F-30・F-31）。
- 移行の前に、公開中のフォームごとに次を表にしておき、移行の後に1つずつ確かめる:
  - フォームの テンプレート名（`mail_contents.form_template`）と、テーマで上書きしているファイル（`templates/Mail/<名前>/`・`element/*mail*`）
  - JS の有無と中身（項目名・id で要素を探していないか・Ajax で送っていないか）
  - どこに置かれているか（単独のページか、LP などに埋め込み・`getForm()` か）
  - 必須の同意・ファイル添付・数値・選択肢・グループの入力チェック
- 確かめ方: 全項目を埋めて**確認画面まで**送り、確認画面のフォームの送り先が `/submit` になっていることで判定する（URL が `/confirm` でもエラーの文が無くても、入力画面が返っていることがある）。Ajax で送るフォームは `X-Requested-With` を付けて送る。最後に、テスト用の宛先にして**実際に送信まで**通し、管理者への通知と自動返信の2通・文字化けを見る。
