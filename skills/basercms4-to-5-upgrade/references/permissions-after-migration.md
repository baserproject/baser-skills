# 移行後のアクセスルールと、管理者以外の管理画面の性能（雛形）

`SKILL.md` の「移行後のユーザーグループのアクセスルール」「移行後の性能」で使う雛形。どちらも baserCMS 5.4 系の実案件で動かして確かめたもの。`<Plugin>` はサイトの独自プラグインの名前に置き換える。

## 1. アクセスルールを5系の標準で作り直して確かめるスクリプト

移行の復元の後に流す（移行を一本道のスクリプトにしているなら、その工程に入れる）。変えるのは先頭の3つ（`OPERATORS`・`DENY_PLUGINS`・`EXPECT`）だけ。

- `EXPECT` には、そのグループに見せる画面（コンテンツ管理・独自プラグイン）と見せない画面（システム設定・ユーザー・テーマ・ユーティリティ・移行ツール）を並べる
- **CLI ではルーティングを読まないと、判定がすべて「許可」になる**ので、確かめる前に `routes()`・`pluginRoutes()` を呼んでいる
- お気に入り（bc-favorite）は管理画面のページが無く API だけなので、確かめるのは API の URL

```php
<?php
/**
 * ユーザーグループのアクセスルールを、5系の標準（各プラグインの config/permission.php）で作り直し、判定を確かめる
 *
 *   php rebuild_permissions.php   （baserCMS のルートで流す）
 *
 * - 管理画面の「アクセスルールグループ」の再構築と同じ処理（rebuildByUserGroup）。何度流しても同じ結果
 * - permission.php を持たないプラグインはフルアクセスになるので、使わせないものは拒否にする（DENY_PLUGINS）
 * - 最後に PermissionsService::check() で EXPECT の URL を確かめ、違えば終了コード 1
 */
use BaserCore\Service\PermissionGroupsServiceInterface;
use BaserCore\Service\PermissionsServiceInterface;
use BaserCore\Utility\BcUtil;
use Cake\ORM\TableRegistry;

const OPERATORS = 2; // 作り直すユーザーグループの ID（例 operators）
// permission.php を持たず「フルアクセス」になるプラグインのうち、運営者には使わせないもの
const DENY_PLUGINS = ['BcDbMigrator', 'BcAddonMigrator', 'BcMcp']; // サイトに合わせて足す（静的書き出しのプラグインなど）

// [URL, 期待（true=見られる）]
const EXPECT = [
    ['/baser/admin/baser-core/contents/index', true],
    ['/baser/admin/baser-core/pages/edit/1', true],
    ['/baser/admin/bc-blog/blog_posts/index/1', true],
    ['/baser/admin/bc-mail/mail_messages/index/1', true],
    ['/baser/admin/bc-uploader/uploader_files/index', true],
    // ['/baser/admin/<独自プラグイン>/<コントローラ>/index', true], // 独自プラグインの画面も足す
    // お気に入りは管理画面のページが無く、API だけで動く
    ['/baser/api/admin/bc-favorite/favorites/index.json', true],
    ['/baser/api/admin/baser-core/contents/index.json', true],
    ['/baser/admin/baser-core/site_configs/index', false],
    ['/baser/admin/baser-core/users/index', false],
    ['/baser/admin/baser-core/user_groups/index', false],
    ['/baser/admin/baser-core/permission_groups/index', false],
    ['/baser/admin/baser-core/plugins/index', false],
    ['/baser/admin/baser-core/sites/index', false],
    ['/baser/admin/baser-core/themes/index', false],
    ['/baser/admin/baser-core/utilities/maintenance', false],
    ['/baser/admin/bc-db-migrator/migration4/index', false],
    ['/baser/admin/bc-addon-migrator/migration4/index', false],
    ['/baser/api/admin/baser-core/users/index.json', false],
];

$root = getcwd(); // baserCMS のルート（vendor/ と config/ がある場所）で流す
require $root . '/vendor/autoload.php';
$app = new \App\Application($root . '/config');
$app->bootstrap();
$app->pluginBootstrap();
$container = $app->getContainer();
\BaserCore\Utility\BcContainer::set($container);

$groups = $container->get(PermissionGroupsServiceInterface::class);
$groups->rebuildByUserGroup(OPERATORS);

$permissionGroups = TableRegistry::getTableLocator()->get('BaserCore.PermissionGroups');
$permissions = TableRegistry::getTableLocator()->get('BaserCore.Permissions');
$denied = 0;
foreach (DENY_PLUGINS as $plugin) {
    $ids = $permissionGroups->find()->where(['plugin' => $plugin])->all()->extract('id')->toList();
    if (!$ids) continue;
    $denied += $permissions->updateAll(['auth' => false], ['user_group_id' => OPERATORS, 'permission_group_id IN' => $ids]);
}
BcUtil::clearAllCache();

$total = $permissions->find()->where(['user_group_id' => OPERATORS])->count();
$old = $permissions->find()->where(['user_group_id' => OPERATORS, 'url NOT LIKE' => '/baser/%', 'url <>' => '/'])->count();
echo "運営者のルール: {$total} 件（フルアクセスを拒否に変えたもの {$denied} 件）\n";

// 判定の確認（PermissionsService は作り直したルールを読み直すよう、新しく取り出す）
// ★判定は URL をルーティングで解析する。CLI では読み込まれていないので読み込む（無いと解析に失敗し、全部「許可」になる）
$builder = \Cake\Routing\Router::createRouteBuilder('/');
$app->routes($builder);
$app->pluginRoutes($builder);
$service = new \BaserCore\Service\PermissionsService();
$ng = 0;
foreach (EXPECT as [$url, $want]) {
    $got = $service->check($url, [OPERATORS]);
    $mark = ($got === $want) ? 'OK  ' : 'NG  ';
    if ($got !== $want) $ng++;
    printf("  %s%s %s\n", $mark, $got ? '見られる' : '見られない', $url);
}
if ($old) {
    echo "★4系の URL のままのルールが {$old} 件残っている\n";
    $ng++;
}
exit($ng ? 1 : 0);
```

## 2. 管理者以外の管理画面を速くする（PermissionsService の差し替え）

### 2-1. まず、直っている版か確かめる

コアの `vendor/baserproject/baser-core/src/Service/PermissionsService.php` の `check()` で、公開側の URL を解析せずに返す処理や、判定の結果を控える処理が入っていれば、上流で直っているので差し替えは要らない。入っていなければ 2-2 へ。

遅いかどうかは、管理者以外のアカウントで、記事の多いブログの記事一覧を開いて確かめる（管理者だと判定を通らないので速い）。原因の確かめ方: MySQL の `general_log` を一時的に有効にし、そのページを1回開いて、`Contents.url IN (...)` の問い合わせが行の数だけ大量に出ていないか見る。

### 2-2. クラスを置く

`plugins/<Plugin>/src/Service/CachedPermissionsService.php`:

```php
<?php
/**
 * アクセスルールの判定を、1回のリクエストの間だけ使い回して速くする PermissionsService
 *
 * 管理者以外（運営者など）の管理画面で、判定のたびに次をやり直して遅くなるのを避ける。
 *   - 公開側の URL の解析（Router::parseRequest() がコンテンツを DB から大量に探す）
 *   - ルールの URL を正規表現に組み立て直す
 *   - ユーザーグループをユーザー全員ごと読む（UserGroupsService::get()）
 * 公開側の URL は、公開側の認証が無効（BcPrefixAuth.Front.disabled）なら解析せずに許可を返す。
 * アクセスルールを書き換えたときは控えを捨てる。
 *
 * コアに同じ改善が入った版に上げたら、このクラスとプラグインの差し替えを消す。
 */
namespace <Plugin>\Service;

use BaserCore\Service\PermissionsService;
use BaserCore\Service\UserGroupsServiceInterface;
use BaserCore\Utility\BcUtil;
use Cake\Core\Configure;
use Cake\Datasource\EntityInterface;

class CachedPermissionsService extends PermissionsService
{

    /**
     * ルールの URL → 組み立てた正規表現
     * @var array<string, string>
     */
    private static array $patterns = [];

    /**
     * 判定の結果（キーは URL・グループ・メソッド・ログインユーザー）
     * @var array<string, bool>
     */
    private static array $results = [];

    /**
     * 判定の中で読み込んだユーザーグループ（キーは ID）
     * @var array<int|string, EntityInterface>
     */
    private static array $userGroups = [];

    /**
     * addCheck() で足された「拒否」の正規表現（親の defaultDenies は private で見えないので、こちらでも持つ）
     * @var string[]
     */
    private static array $denies = [];

    /**
     * 控えを捨てる
     */
    public static function clearCache(): void
    {
        self::$patterns = [];
        self::$results = [];
        self::$userGroups = [];
    }

    /**
     * 判定の中（parent::check()）でユーザーグループを読むときだけ、読み込んだものを使い回す
     */
    public function getService($service)
    {
        $instance = parent::getService($service);
        if ($service !== UserGroupsServiceInterface::class) {
            return $instance;
        }
        return new class ($instance, self::$userGroups) {
            public function __construct(private object $inner, private array &$cache)
            {
            }

            public function get($id): EntityInterface
            {
                return $this->cache[$id] ??= $this->inner->get($id);
            }

            public function __call(string $name, array $arguments): mixed
            {
                return $this->inner->{$name}(...$arguments);
            }
        };
    }

    public function check(string $url, array $userGroupId, string $method = 'GET'): bool
    {
        $front = $this->checkFront($url, $userGroupId);
        if ($front !== null) {
            return $front;
        }
        $key = implode("\n", [$url, implode(',', $userGroupId), $method, (string)(BcUtil::loginUser()?->id ?? '')]);
        if (!array_key_exists($key, self::$results)) {
            self::$results[$key] = parent::check($url, $userGroupId, $method);
        }
        return self::$results[$key];
    }

    /**
     * 公開側の URL なら、親の check() と同じ結果を、URL の解析をせずに返す。管理画面・管理 API の URL なら null
     *
     * 親の check() は、公開側の URL だと次の順で必ず許可になる（公開側の認証が無効のとき）:
     * 管理者グループ → 許可 ／ addCheck() の拒否に当たる → 拒否 ／ それ以外 → checkGroup() で prefix が Front → 無効なので許可
     * ほかのドメインの URL は、親でも解析せずに許可になる。
     */
    private function checkFront(string $url, array $userGroupId): ?bool
    {
        if (!Configure::read('BcPrefixAuth.Front.disabled')) {
            return null;
        }
        if (in_array(Configure::read('BcApp.adminGroupId'), $userGroupId)) {
            return true;
        }
        $path = $url;
        if (preg_match('/^(https?:\/\/[^\/]+?\/)(.*)$/', $url, $m)) {
            if ($m[1] !== Configure::read('BcEnv.siteUrl')) {
                return null;
            }
            $path = '/' . $m[2];
        }
        [$path] = explode('?', $path);
        $core = '/' . BcUtil::getBaserCorePrefix();
        $admin = $core . (Configure::read('BcPrefixAuth.Admin.alias') ?: '/' . BcUtil::getAdminPrefix());
        $apiAdmin = $core . (Configure::read('BcPrefixAuth.Api/Admin.alias') ?: '/' . Configure::read('BcApp.apiPrefix') . '/admin');
        foreach ([$admin, $apiAdmin] as $prefix) {
            if ($path === $prefix || str_starts_with($path, $prefix . '/') || str_starts_with($path, $prefix . '.')) {
                return null;
            }
        }
        foreach (self::$denies as $deny) {
            if (preg_match($deny, $url)) {
                return false;
            }
        }
        return true;
    }

    public function convertRegexUrl(string $url)
    {
        // {loginUserId} はログインユーザーで置き換わるので、ユーザーごとに控える
        $key = $url;
        if (str_contains($url, '{loginUserId}')) {
            $key .= "\n" . (string)(BcUtil::loginUser()?->id ?? '');
        }
        if (!array_key_exists($key, self::$patterns)) {
            self::$patterns[$key] = parent::convertRegexUrl($url);
        }
        return self::$patterns[$key];
    }

    public function create(array $postData): EntityInterface
    {
        self::clearCache();
        return parent::create($postData);
    }

    public function update(EntityInterface $target, array $data): EntityInterface
    {
        self::clearCache();
        return parent::update($target, $data);
    }

    public function publish($id): bool
    {
        self::clearCache();
        return parent::publish($id);
    }

    public function unpublish($id): bool
    {
        self::clearCache();
        return parent::unpublish($id);
    }

    public function copy(int $permissionId)
    {
        self::clearCache();
        return parent::copy($permissionId);
    }

    public function delete(int $id): bool
    {
        self::clearCache();
        return parent::delete($id);
    }

    public function batch($method, array $ids): bool
    {
        self::clearCache();
        return parent::batch($method, $ids);
    }

    public function addCheck(string $url, bool $auth)
    {
        self::clearCache();
        if (!$auth) {
            self::$denies[] = $this->convertRegexUrl($url);
        }
        return parent::addCheck($url, $auth);
    }

}
```

### 2-3. プラグインで差し替える

`plugins/<Plugin>/src/<Plugin>Plugin.php`:

```php
use <Plugin>\Service\CachedPermissionsService;
use BaserCore\Service\PermissionsServiceInterface;
use Cake\Core\ContainerInterface;

    public function services(ContainerInterface $container): void
    {
        parent::services($container);
        $container->extend(PermissionsServiceInterface::class)->setConcrete(CachedPermissionsService::class);
    }
```

### 2-4. 確かめる

1. コンテナから取り出したサービスが差し替え後のクラスになっているか: `get_class($app->getContainer()->get(PermissionsServiceInterface::class))`
2. 判定の結果が元と同じか: 元の `new PermissionsService()` と差し替え後のサービスに、管理画面・管理 API・公開側・ほかのドメイン・`javascript:` の URL を、管理者と管理者以外のグループで渡し、結果を比べる（1件も違わないこと）
3. 管理者以外のアカウントで、遅かった画面の表示時間を比べる
