# 開発ワークフロー

## 1. ローカル変更
```bash
# 設定を編集
cd ~/.local/share/chezmoi
$EDITOR dot_config/zsh/.zshrc.tmpl

# 変更を適用
chezmoi apply

# 差分確認
chezmoi diff
```

## 2. Git 管理
```bash
# 変更をステージング
cd ~/.local/share/chezmoi
git add .

# コミット
git commit -m "feat(zsh): add new alias"

# プッシュ
git push origin main
```

## 3. 新マシンへのデプロイ
```bash
# リポジトリをクローン
chezmoi init --apply https://github.com/yourusername/dotfiles.git

# ユーザー固有設定を追加
cp ~/.config/git/config.local.example ~/.config/git/config.local
$EDITOR ~/.config/git/config.local
```
