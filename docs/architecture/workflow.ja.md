# 開発ワークフロー

## 1. ローカル変更
```bash
# 設定を編集
cd ~/.config/nix-config
$EDITOR dot_config/nushell/autoload/03-aliases.nu

# 変更を適用
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# ビルドのみ（検証用）
/run/current-system/sw/bin/darwin-rebuild build --flake path:.
```

## 2. Git 管理
```bash
# 変更をステージング
cd ~/.config/nix-config
git add .

# コミット
git commit -m "feat(nushell): add new alias"

# プッシュ
git push origin main
```

## 3. 新マシンへのデプロイ
```bash
# リポジトリをクローン
git clone https://github.com/example/dotfiles.git ~/.config/nix-config
cd ~/.config/nix-config

# 適用
sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.

# ユーザー固有設定を追加（任意）
cp ~/.config/git/config.local.example ~/.config/git/config.local
$EDITOR ~/.config/git/config.local
```

## 自動ガベージコレクション
この flake では Determinate Nix が Nix daemon を管理し、`hosts/darwin/default.nix` は `nix.enable = false` のままにしています。そのため nix-darwin の `nix.gc` options は機能せず、ガベージコレクションは user-level の Home Manager service としてスケジュールします。

`nix-gc` user unit はローカル時刻の毎週日曜日 05:00 に、現在の user の profiles を次の retention policy で整理します。

```bash
nh clean user --keep 5 --keep-since 7d
```

macOS では launchd logs は `~/.local/state/launchagents/nix-gc/stdout.log` と `~/.local/state/launchagents/nix-gc/stderr.log` に出力されます。Linux では systemd user service logs を `journalctl --user -u nix-gc.service` で確認できます。
