## Nix の問題

**darwin-rebuild が失敗する**:
```bash
cd ~/.config/dotfiles
/run/current-system/sw/bin/darwin-rebuild build --flake path:.
```
まずは build でエラー内容を確認し、該当の Nix ファイルを修正します。

**flake の依存が解決できない**:
```bash
cd ~/.config/dotfiles && nix flake update
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
cd ~/.config/dotfiles
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.
```
エラーに応じて該当 cask を調整します。

## launchd 環境変数の問題

**リブート後、スケジュール LaunchAgent や GUI アプリが `nix` / `git-annex` を見つけられない**:
```bash
launchctl getenv PATH
```
`launchd.user.envVariables`(`hosts/darwin/default.nix`)は activation 時に
キーごとの `launchctl setenv` を一度実行するだけで、値は永続化されません。
そのためリブート（多くは macOS アップデートのリブート）で `PATH`・`XDG_*`・
`CLAUDE_CONFIG_DIR`・`NPM_CONFIG_*` がユーザ launchd セッションから消えます。
`setenv-user-env` ログインエージェント(`hosts/darwin/launchd.nix`)がログイン時に
全セットを再注入するため通常のログインで復旧します。失敗しうるのは、ブートから
このエージェント実行までの間か、エージェント自体が実行されなかった場合です。

セッションを再シードして復旧します（エージェントと値の両方が再適用されます）:
```bash
cd ~/.config/dotfiles
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.
```
または応急処置として `PATH` を直接設定します（次のリブートは越えません）:
```bash
launchctl setenv PATH "$HOME/.nix-profile/bin:/etc/profiles/per-user/$USER/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
```
