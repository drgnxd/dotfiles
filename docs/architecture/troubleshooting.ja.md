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

第三の失敗窓があります: アプリが(このリポジトリが管理するLaunchAgent plistでは
なく)独自のmacOSログイン項目として登録されている場合、`setenv-user-env`との間に
起動順序の保証がありません。アプリ側のログイン項目が先に起動して`setenv-user-env`
より前に走ると、そのアプリは起動時に継承した古い環境をセッション中ずっと保持し
続けます(`launchctl setenv`は実行中プロセスには反映されません)。確認済みの実例が
CodexBarです: Codex/Claudeの利用量監視CLI subprocessが`CODEX_HOME`/
`CLAUDE_CONFIG_DIR`を必要とするため、レースに負けると再起動後に両プロバイダとも
認証切れに見え、CodexBarを終了して手動で再起動すると復旧します。`setenv-user-env`
は現在、`setenv`実行後に同一スクリプト内でCodexBar自身をQuit→再起動するため
(`hosts/darwin/launchd.nix`の`postSetenvRelaunchApps`)、OSがどちらを先に起動しても
相対順序が保証されます。これは意図的に範囲を絞った修正です: 同じ兄弟エージェント
間の順序レースは`mkLoginApp`の全エントリ(Alacritty・Floorp・Sol・Proton系アプリ)に
原理上存在しますが、今のところ実害が確認されているのはCodexBarのみです。

セッションを再シードして復旧します（エージェントと値の両方が再適用されます）:
```bash
cd ~/.config/dotfiles
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.
```
または応急処置として `PATH` を直接設定します（次のリブートは越えません）:
```bash
launchctl setenv PATH "$HOME/.nix-profile/bin:/etc/profiles/per-user/$USER/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
```

## Nushell 変更後のスケジュールエージェント再登録

Nix の rebuild で Nushell のストアパスが変わった後は、対話的な Aqua
セッションからスケジュールエージェントの再登録を事前確認します。

```bash
cd ~/.config/dotfiles
just relaunch-agents --dry-run
```

dry-run は、アクティブジョブの allow-list、plist のラベル、実行中ジョブ、
会話 lock を確認しますが、state directory の作成、エージェントの bootout /
bootstrap、sentinel の更新は行いません。問題がなければ再登録を実行します。

```bash
just relaunch-agents
```

Nushell パスの sentinel を無視する必要がある場合に限り `--force` を使います。
実行中または会話 lock を保持中のジョブは defer されるため、アイドル状態になって
から再実行します。検証に失敗した場合は、修正して再試行できるよう sentinel は
更新されません。

## 素の `darwin-rebuild switch` が毎回巻き戻すもの

switch は純粋な追加操作ではありません。**毎回**次も行います。

- **Remote Login(SSH)と画面共有 / ARD を無効化する。**
  `system.activationScripts.securityHardening`(`hosts/darwin/default.nix`)が
  `systemsetup -setremotelogin off` と ARD の `kickstart -deactivate -off` を
  無条件で実行し、`com.apple.loginwindow LoginwindowText` も削除する。この Mac
  へリモート接続する場合は switch のたびに再有効化するか、例外をこのスクリプト
  に加える。
- **手動の System Settings 変更を `system.defaults` の値へ戻す**: 固定ダーク
  モード、キーリピート速度、Dock(`autohide`・`static-only`・tilesize 48)、
  Finder(全ファイル表示・カラム表示)、ロケール `en_JP` + 摂氏/cm、マウス・
  トラックパッド速度 7、メニューバー時計(秒/日付/曜日)、Control Center の表示
  項目(Wi-Fi・バッテリー・再生中を非表示)、スクリーンショット保存先
  `~/Desktop/Screenshots`、テキスト自動置換すべてオフ。
- **CodexBarを一瞬Quitして再起動する**: `setenv-user-env`
  (`hosts/darwin/launchd.nix`)は自身のスクリプト内容または`userLaunchdEnv`が
  変わるたびに再実行され、実行のたびにenv再投入後に`postSetenvRelaunchApps`
  (現状CodexBarのみ)の各アプリをQuit→再起動する — 上の「launchd 環境変数の
  問題」節を参照。
- **アプリが作る「ログイン時に起動」エージェントを毎回削除する**:
  `eu.exelban.Stats(.LaunchAtLogin)`・`org.p0deje.Maccy`・旧
  `setenv.SCIHOME` を `~/Library/LaunchAgents` から `rm` する(これらのログイン
  エージェントは nix-darwin が管理する)。Stats や Maccy 側で「ログイン時に
  起動」を入れ直しても残らない。
- **Homebrew `onActivation.cleanup = "zap"`**: `hosts/darwin/default.nix` の
  `homebrew.*` に列挙されていない formula / cask / tap / MAS アプリは
  アンインストールされ、cask は **zap**(Application Support / 設定データごと
  削除)される。設定へ追加し忘れた手動 `brew install` は、次の switch で
  データごと消える。(潜在: 設定は `cask "tailscale"` だが実体は改名後の
  `tailscale-app` で入っている。Homebrew は改名を解決するが、いずれ設定を
  合わせること。)

### switch が触らないもの

- **nix 管理外の LaunchAgent。** `com.drgnxd.*` の自動化エージェント
  (`accretion`・`~/repos/scripts`・`~/repos/archivist` 由来)は安全。activation スクリプトの
  ユーザエージェント整理ループは `/run/current-system/user/Library/LaunchAgents/*`
  (nix が宣言したエージェント)だけを走査し、`~/Library/LaunchAgents` を
  glob せず、nix 管理外の plist を認識しない。`/run/current-system/activate`
  を読んで確認済み。
- `~/.local/state/**`(ジョブ状態・ログ・restic リポジトリ・`failure.json`)、
  `~/repos/**`、Proton Drive CLI のセッション、`~/.ssh`。
- home-manager 管理の dotfiles は読み取り専用の Nix ストアへのシンボリック
  リンクなので、その場で編集できない。`~/.config` 配下の `*.before-nix` は
  Nix 移行時の一度きりのバックアップで、以降の switch が生成するものではない。

### switch が依存するが git bundle バックアップから漏れる gitignore 済み入力

`local/identity.nix`(`hostname` を設定する。これが無いと flake に
`darwinConfigurations.<hostname>` が無く switch が失敗する)、`local/packages.nix`、
`local/claude-auto-mode-environment.nix` は gitignore されており、
**`com.drgnxd.dotfiles-backup` の git bundle に入らない** — ホーム全体の
restic バックアップにのみ含まれる。`~/.ssh/id_ed25519` は全 `secrets/*.age` を
復号する agenix の identity で、失うと activation が壊れると同時に secrets が
復元不能になる。この鍵は独立した控えを保持すること。
