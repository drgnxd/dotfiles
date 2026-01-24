# XDG Base Directory 準拠

## 概要
XDG Base Directory Specification に従い、設定とデータの保存先を
統一しています。

```
$XDG_CONFIG_HOME (~/.config)   -> アプリケーション設定
$XDG_CACHE_HOME (~/.cache)     -> 非必須キャッシュデータ
$XDG_DATA_HOME (~/.local/share) -> ユーザー固有データ
```

## 利点
- ホームディレクトリが散らからない
- バックアップ/同期が簡単
- macOS/Linux で同じ構造を維持

## Docker と Lima
シンボリックリンクではなく環境変数で XDG パスに合わせています。

```bash
export DOCKER_CONFIG="$XDG_CONFIG_HOME/docker"
export LIMA_HOME="$XDG_DATA_HOME/lima"
```

## 判断理由
- 標準仕様に従い移植性を確保
- 旧来の `~/.docker` や `~/.lima` を不要化
