# XDG Base Directory 準拠

## 概要
XDG Base Directory Specification に従い、設定とデータの保存先を
統一しています。

```
$XDG_CONFIG_HOME (~/.config)   -> アプリケーション設定
$XDG_CACHE_HOME (~/.cache)     -> 非必須キャッシュデータ
$XDG_DATA_HOME (~/.local/share) -> ユーザー固有データ
$XDG_STATE_HOME (~/.local/state) -> 永続的なアプリケーション状態
```

## 利点
- ホームディレクトリが散らからない
- バックアップ/同期が簡単
- macOS/Linux で同じ構造を維持

## Atuin
Atuin は設定と履歴データに XDG path を使用しますが、ファイルログの既定値は
旧来の `~/.atuin/logs` です。Home Manager でログディレクトリを上書きし、
永続ログを XDG state 配下に保存します。

```toml
[logs]
dir = "~/.local/state/atuin/logs"
```

## macOS アプリケーション
Homebrew の trust 操作には `XDG_CONFIG_HOME` を明示し、状態を
`~/.config/homebrew` 配下に保持します。Hammerspoon は native の
`MJConfigFile` preference で `~/.config/hammerspoon/init.lua` を読み込み、
reload watcher は `~/.hammerspoon` ではなく `hs.configdir` を基準にします。

## Docker と Lima
シンボリックリンクではなく環境変数で XDG パスに合わせています。

```bash
export DOCKER_CONFIG="$XDG_CONFIG_HOME/docker"
export LIMA_HOME="$XDG_DATA_HOME/lima"
```

## 互換性のための例外
Ollama と Scilab は GUI または model 以外の状態を完全には redirect できないため、
home directory の互換 link を維持します。CodexBar は現在 Claude OAuth lock を
`~/.codexbar` にハードコードしています。Determinate Nix の XDG switch は
system-level restricted setting のため、legacy user profile shim を維持します。

## 判断理由
- 標準仕様に従い移植性を確保
- upstream が対応する範囲で旧来の path を不要化
