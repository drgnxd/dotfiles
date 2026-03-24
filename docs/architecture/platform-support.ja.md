## macOS (darwin)
**パッケージマネージャー**: Nix（nix-darwin + home-manager）

**システム統合**:
- nix-darwin の `system.defaults` と activation scripts
- `launchd.user.agents` による LaunchAgent 管理
- Hammerspoon と Stats の設定は Home Manager で管理
- Home Manager の activation で、Stats/Hammerspoon の旧アプリ管理 LaunchAgent を無効化し二重起動を防止

**アプリ**:
- nixpkgs で不足する GUI アプリは nix-darwin の `homebrew` で管理

## Linux (x86_64-linux)
**パッケージマネージャー**: Nix（standalone home-manager）

**使い方**:
```bash
home-manager switch --flake ~/.config/nix-config#<user>@<linuxHostname>
```

利用前に `flake.nix` の `user` と `linuxHostname` を環境に合わせて設定してください。

**サポート対象**: すべての CLI ツール、Nushell、Helix、Git、Taskwarrior、Yazi、Zellij、OpenCode、Starship、Zoxide、Atuin、Carapace、Direnv、Alacritty（macOS 専用ウィンドウ機能を除く）。

**Linux で未提供**: Hammerspoon、Stats、Sol、Maccy、macOS system defaults、LaunchAgents、Homebrew casks。Linux デスクトップ統合の代替は Phase 2 ロードマップを参照してください。
