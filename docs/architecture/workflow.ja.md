# 開発ワークフロー

## 1. ローカル変更
```bash
# 設定を編集
cd ~/.config/dotfiles
$EDITOR xdg/config/nushell/autoload/03-aliases.nu

# 変更を適用
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# ビルドのみ（検証用）
/run/current-system/sw/bin/darwin-rebuild build --flake path:.
```

## 2. Git 管理
```bash
# 変更をステージング
cd ~/.config/dotfiles
git add .

# コミット
git commit -m "feat(nushell): add new alias"

# プッシュ
git push origin main
```

## 3. 新マシンへのデプロイ
```bash
# リポジトリをクローン
git clone https://github.com/drgnxd/dotfiles.git ~/.config/dotfiles
cd ~/.config/dotfiles

# 適用
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# ユーザー固有設定を追加（任意）
cp ~/.config/git/config.local.example ~/.config/git/config.local
$EDITOR ~/.config/git/config.local
```

## nixpkgs の更新

nixpkgs は週次の flake.lock 更新 PR ではなくローカルで進め、nixpkgs-unstable に一定期間置かれたリビジョンだけが `flake.lock` に入るようにします。

```bash
# nixpkgs を、チャンネルに載ってから 7 日以上経過した nixpkgs-unstable の最新 head に固定
just update-settled

# 全 input を更新(nixpkgs は update-settled を通す)
just update
```

- 待機期間は、master のコミット日ではなく、チャンネルブランチ自体の push 履歴(Hydra 通過後にだけ `nixos-channel-bot` が `nixpkgs-unstable` を進める)で測ります。既定は 7 日です。レシピは、`allow_downgrade=true` を渡さない限り nixpkgs を後退させません。
- 引数なしの `nix flake update` は使わないでください。nixpkgs がブランチ先端まで進みます。`just update` または `just update-one <input>` を使います。
- 適用前にクロージャ差分とビルドを確認し、問題があれば `darwin-rebuild switch --rollback` と `flake.lock` の revert で戻します。
- 実際に悪用されている修正や、信頼できない入力から到達できる導入済みパッケージの修正は、待機期間を適用しません。
- CI の `check-flake-lock-age` は、nixpkgs と home-manager が 30 日を超えると警告します(nix-darwin と agenix は更新が稀なため 90 日)。これが lock を未確認のまま放置する上限です。固定した nixpkgs は最初から 7 日以上古いため、警告までの余裕は約 23 日です。
- 週次 PR は、home-manager と nix-darwin をブランチ先端まで進めます。そこで評価エラーが出る場合は、固定中の nixpkgs より新しい nixpkgs を要求している可能性があります。

## 自動ガベージコレクション
この flake では Determinate Nix が Nix daemon を管理し、`hosts/darwin/default.nix` は `nix.enable = false` のままにしています。そのため nix-darwin の `nix.gc` options は機能せず、ガベージコレクションは user-level の Home Manager service としてスケジュールします。

`nix-gc` user unit はローカル時刻の毎週日曜日 05:00 に、現在の user の profiles を次の retention policy で整理します。

```bash
nh clean user --keep 5 --keep-since 7d
```

macOS では launchd logs は `~/.local/state/launchagents/nix-gc/stdout.log` と `~/.local/state/launchagents/nix-gc/stderr.log` に出力されます。Linux では systemd user service logs を `journalctl --user -u nix-gc.service` で確認できます。
