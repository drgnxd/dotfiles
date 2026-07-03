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
