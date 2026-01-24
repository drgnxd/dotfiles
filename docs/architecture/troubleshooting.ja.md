# トラブルシューティング

## chezmoi の問題

**状態がおかしい場合**:
```bash
chezmoi state dump  # 現在の状態を確認
chezmoi state reset # 状態をリセット
```

**差分が大きすぎる場合**:
```bash
chezmoi diff | less  # ページャーで確認
```

## スクリプト実行エラー

**ガードフラグが設定されていない**:
```
[ERROR] Refusing to proceed without ALLOW_DEFAULTS=1
```
**解決策**: 必要な環境変数を設定して再実行

**sudo パスワードのタイムアウト**:
```
sudo: a password is required
```
**解決策**: `sudo -v` で認証を更新

## Homebrew の問題

**Brewfile のロックエラー**:
```bash
rm ~/Library/Caches/Homebrew/Brewfile.lock.json
brew bundle --file ~/.config/homebrew/Brewfile
```
