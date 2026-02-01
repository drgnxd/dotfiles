# プラットフォームサポート

## macOS (darwin)
**パッケージマネージャー**: Homebrew (`Brewfile.tmpl`)

**システム統合**:
- `system_defaults.sh`: NSUserDefaults の変更
- `Hammerspoon`: ウィンドウ管理、入力切り替え
- `Stats`: システムモニター（plist ベース設定）

**自動化**:
- AppleScript によるログイン項目管理
- `defaults` によるメニューバー設定

## Linux
**パッケージマネージャー**: apt/dnf/pacman など

**共通ツール**:
- Alacritty, Nushell, Tmux, Helix
- Taskwarrior, Yazi, Starship
- CLI ユーティリティ (bat, eza, fd, ripgrep)

**除外**:
- Hammerspoon (macOS 専用)
- Homebrew (macOS 中心)
- `.internal_scripts/darwin/`
