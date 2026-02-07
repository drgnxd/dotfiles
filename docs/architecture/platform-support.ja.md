## macOS (darwin)
**パッケージマネージャー**: Nix（nix-darwin + home-manager）

**システム統合**:
- nix-darwin の `system.defaults` と activation scripts
- `launchd.user.agents` による LaunchAgent 管理
- Hammerspoon と Stats の設定は Home Manager で管理

**アプリ**:
- nixpkgs で不足する GUI アプリは nix-darwin の `homebrew` で管理

## Linux
Linux は現在対象外です。
