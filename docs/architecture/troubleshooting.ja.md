## Nix の問題

**darwin-rebuild が失敗する**:
```bash
cd ~/.config/nix-config
/run/current-system/sw/bin/darwin-rebuild build --flake path:.
```
まずは build でエラー内容を確認し、該当の Nix ファイルを修正します。

**flake の依存が解決できない**:
```bash
cd ~/.config/nix-config && nix flake update
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
cd ~/.config/nix-config
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.
```
エラーに応じて該当 cask を調整します。
