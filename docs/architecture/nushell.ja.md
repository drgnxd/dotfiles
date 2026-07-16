# Nushell設定

Nushellは、全てをデータとして扱うモダンなシェルです。この設定は、XDG準拠と条件付きコマンド読み込みを備えた、モジュール化され保守性の高い構成を提供します。

## アーキテクチャ

`autoload/`ディレクトリパターンを使用したモジュール構造を採用しています：

```
dot_config/nushell/
├── env.nu                  # ~/.config/nushell/env.nu
├── config.nu               # ~/.config/nushell/config.nu
├── autoload/
│   ├── 00-helpers.nu       # 共通ヘルパー
│   ├── 01-env.nu           # 環境変数とXDGパス
│   ├── 02-path.nu          # path-addヘルパーを使ったPATH設定
│   ├── 03-aliases.nu       # フォールバック付きエイリアス
│   ├── 04-functions.nu     # カスタム関数とラッパー
│   ├── 05-completions.nu   # コマンド補完
│   ├── 06-integrations.nu  # 統合キャッシュ更新の遅延ラッパー
│   ├── 07-abbreviations.nu # Fish風の略語展開（Space/Enter）
│   ├── 09-lima.nu          # Lima/Dockerの遅延ラッパー
│   └── 10-source-tools.nu  # キャッシュ読み込み
└── modules/
    ├── integrations.nu     # キャッシュ生成（オンデマンド）
    └── lima.nu             # Lima/Dockerコマンド
```

## モジュール読み込み

`env.nu` と `config.nu` は、`$nu.home-dir` から `~/.config/nushell` を組み立てて `config_dir` を求め、その配下を相対的に `source` します：

```nushell
# env.nu
const config_dir = ($nu.home-dir | path join '.config' 'nushell')
source ($config_dir | path join 'autoload' '01-env.nu')
source ($config_dir | path join 'autoload' '02-path.nu')

# config.nu
const config_dir = ($nu.home-dir | path join '.config' 'nushell')
source ($config_dir | path join 'autoload' '00-constants.nu')
source ($config_dir | path join 'autoload' '00-helpers.nu')
...
```

この方式により、Home Manager で設定ファイル本体が `/nix/store` 側にあっても、`~/.config/nushell` を基準に安定してモジュール解決できます。

ユーザー名やホームディレクトリが変わっても、手動で固定パスを書き換える必要はありません。

重い処理は`modules/`に分離し、`autoload/`の軽量ラッパーが `autoload/00-constants.nu` で定義したモジュール定数経由で `overlay use` して必要時に読み込みます。これにより起動を軽くしつつ、ハードコードされたパス依存を避けます。

`config.nu` は意図的に `06-integrations.nu`、`09-lima.nu`、`10-source-tools.nu` の順に読み込みます。`10-source-tools.nu` は `integrations-cache-update` を呼ぶ消費側ステージのため、そのコマンド定義後に実行する必要があります。

## 主な機能

### 1. XDG Base Directory準拠

全てのアプリケーションデータはXDG準拠の場所に保存されます：
- 設定: `~/.config/`
- キャッシュ: `~/.cache/`
- データ: `~/.local/share/`
- 状態: `~/.local/state/`

完全なXDGパス設定は`01-env.nu`を参照してください。

### 2. 条件付きコマンド読み込み

コマンドは、標準ツールへの自動フォールバック付きで定義されます：

```nushell
export def g [...args] {
    if (has-cmd rg) {
        rg ...$args
    } else {
        ^grep ...$args
    }
}
```

これにより、モダンなツール（bat、fd、ripgrep）がインストールされていない異なるシステムでも設定が機能します。

### 3. PATH管理ヘルパー

PATHは、存在するパスだけを先頭追加する小さなヘルパーで管理します：

```nushell
def --env path-add [new_path: string] {
    if ($new_path | path exists) {
        $env.PATH = ($env.PATH | prepend $new_path | uniq)
    }
}
```

### 4. ENV_CONVERSIONS

コロン区切りの環境変数（PATH、TERMINFO_DIRS等）は、適切なコンバータで処理されます：

```nushell
$env.ENV_CONVERSIONS = ($env.ENV_CONVERSIONS | default {}) | merge {
    "PATH": {
        from_string: {|s| $s | split row (char esep) | path expand --no-symlink }
        to_string: {|v| $v | path expand --no-symlink | str join (char esep) }
    }
}
```

## 利用可能なエイリアスとコマンド

### ファイル操作
- `la`, `ld`, `lf`, `lsize` - リスト表示の派生（全/ディレクトリ/ファイル/サイズ順）
- `cat` - ファイル表示（使用可能な場合はbatを使用）
- `f` - ファイル検索（使用可能な場合はfdを使用）

### 検索
- `g` - ripgrepで検索（フォールバックはgrep）

### アプリケーションショートカット
- `lg` - LazyGit
- `oc`, `ocd` - opencode
- `pload` - Proton Pass CLI

### Lima/Docker
- `lls` - Lima VM一覧
- `dctx` - Dockerコンテキスト切り替え
- `dctx-reset` - デフォルトにリセット

### 関数
- `y` - cwd追跡付きYaziファイルマネージャ
- `zk` - git同期付きZettelkastenノート
- `ppget` - Proton Passパスワード取得
- `upgrade-all` / `update` - 統合システムアップグレード
- `save-stats` - Stats.app設定のエクスポート
- `bundle-id` - macOSアプリのバンドルID取得
- `integrations-cache-update` - runtime cache 方式の Carapace init script を再生成

## サードパーティ統合

### プロンプトとツール統合
- **Starship** - 安全性を重視したクロスシェルプロンプト
- **Zoxide** - スマートディレクトリジャンプ
- **Carapace** - コマンド補完
- **Atuin** - シェル履歴同期
- **Direnv** - PWD 変更フックによる環境管理と状態検出（キャッシュと prompt ごとの subprocess はなし）

Plan B では Starship、Zoxide、Atuin の init script を Nix build 時に生成し、`~/.config/nushell/generated/` 以下へ配備します。activation 後に `autoload/10-source-tools.nu` がこの再現可能な生成物を読み込みます。

Plan A の runtime cache は Carapace だけに使用します。`integrations-cache-update` が `~/.cache/nushell-init` 以下の init script を更新します。鮮度確認には、Nix 管理システムでは解決済みの `/nix/store` path を使い、Nix 管理外の path では SHA-256 に fallback します。

Direnv は `autoload/10-source-tools.nu` で `$env.config.hooks.env_change.PWD` にフック登録されており、`cd` 時に `direnv export json` を実行して環境変数の差分を自動反映します。薄い `direnv` wrapper は `direnv allow` が成功した後に同じ同期を再実行するため、再度 `cd` しなくても indicator が更新されます。hook は読み込み済み状態を `DIRENV_DIR`、blocked 状態を `DIRENV_BLOCKED` で公開し、Starship は両方を `env_var` module で描画するため、prompt ごとに direnv subprocess を起動しません。

### Starship プロンプトの安全設計

プロンプトは両端を丸く揃えた Solarized Dark の静かな `base02` Neutral Rail（共有 carrier 上に blue の location、green の VCS、cyan の environment を前景色で表示し、orange の dirty state と red の anomaly は該当時だけ chip として表示）で、通常時は意図的に静かに保ちます。左 prompt に表示するのは、欠落すると操作ミスにつながる情報だけです。対象は OS、SSH/root の識別情報、現在地、Git branch と working tree の状態、Nix shell、Direnv、仮想環境、SSH agent の異常表示です。toolchain は flake で固定するため、言語やツールの version module は表示しません。終了ステータス、コマンド実行時間、バックグラウンドジョブは入力位置から離れた `right_format` に表示します。

仮想環境の表示には Starship の `env_var.VIRTUAL_ENV_PROMPT` module を使い、prompt ごとの subprocess は起動しません。`uv` や新しい activation script は通常 `VIRTUAL_ENV_PROMPT` を設定しますが、`VIRTUAL_ENV` だけを設定するツールでは segment を表示しません。その場合は module の対象を `VIRTUAL_ENV` に切り替えることで、仮想環境の full path を表示できます。

各 prompt の直前に Nushell hook が `SSH_AUTH_SOCK` の設定有無と socket path の存在を確認します。異常時だけ `PASS_AGENT_DOWN=✗` を設定して Starship に赤い警告を表示し、socket が戻れば変数を削除します。これは subprocess を使わない stat check であり、agent 自体の状態確認ではありません。process 終了後に残った stale socket を検出できない点は既知の制約です。

Plan B の Starship init は Nushell の transient prompt command も設定します。実行済み prompt を Starship の character に置き換え、scrollback を character と command だけに縮約します。この経路の `starship module character` には直前の `--status` 値が渡らないため、transient character が常に success color になる場合があります。

## 設定値

### 履歴
- 形式: SQLite
- 最大サイズ: 1,000,000エントリ
- 入力時同期: 有効
- 分離: 無効

### UI
- バナー: 無効
- エラースタイル: Fancy
- 編集モード: Readline互換（Nushell の `emacs` モード）
- Kittyプロトコル: 有効
- ブラケット貼り付け: 有効

### 補完
- 大文字小文字区別: なし
- アルゴリズム: Prefix
- 外部補完: Carapace（使用可能な場合）

## Zshからの移行

この設定は以前のZshセットアップを置き換えます。主な変更点：

1. **.zshenv/.zshrcなし** - Nushellは`env.nu`と`config.nu`を使用
2. **.aliasesなし** - エイリアスは`03-aliases.nu`の`export def`コマンド
3. **.functionsなし** - 関数は`04-functions.nu`の`export def`
4. **モジュールシステム** - シェルのソースではなくNushellのモジュールシステムを使用

## ローカル上書き

マシン固有の設定には`~/.config/nushell/local.nu`を使用してください。
このファイルは Home Manager の activation 時に、存在しない場合は空ファイルとして自動作成されます。
必要な上書き設定を追記してください：

```nushell
# ~/.config/nushell/local.nu
$env.MY_LOCAL_VAR = "value"
alias mylocal = echo "local alias"
```

セキュリティ上センシティブな値はこの `local.nu` に置いてください。特に `OLLAMA_ORIGINS` は `autoload/01-env.nu` では設定せず、必要な拡張機能 UUID を `local.nu` で明示設定する設計です。

このファイルは`config.nu`の最後で自動的に読み込まれます。

## 参考

- [Nushell Book](https://www.nushell.sh/book/)
- [Nushell Cookbook](https://www.nushell.sh/cookbook/)
