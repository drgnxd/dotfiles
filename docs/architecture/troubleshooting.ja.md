## Nix の問題

**darwin-rebuild が失敗する**:
```bash
darwin-rebuild build --flake ~/.config/nix-config#macbook
```
まずは build でエラー内容を確認し、該当の Nix ファイルを修正します。

**flake の依存が解決できない**:
```bash
nix flake update --flake ~/.config/nix-config
```
ネットワークや入力更新の問題を確認します。

## secrets の問題

**agenix がファイルを見つけられない**:
```bash
ls secrets
```
`secrets/*.age` が存在するか、`secrets/secrets.nix` のキーが正しいか確認します。

## Homebrew (nix-darwin) の問題

**cask のインストール失敗**:
```bash
darwin-rebuild switch --flake ~/.config/nix-config#macbook
```
エラーに応じて該当 cask を調整します。
