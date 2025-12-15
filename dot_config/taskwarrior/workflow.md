# Taskwarrior GTD Workflow

## 1. Capture (収集)
すべてのタスクを `project:Inbox` に入れる（`default.project=Inbox` で自動付与）。
```sh
task add "..."
```

## 2. Process (整理)
Inbox を空にするまで、プロジェクト・タグ・期限を付けて出口に回す。
```sh
task inbox
task <ID> modify project:uni.math tags:asgn,next due:friday
```

## 3. Do (実行)
Ready/Next に集中し、待機タスクは除外。
```sh
task ready
task <ID> start
task <ID> done
```

## 4. Review (見直し)
定期的に待機・期限・Inbox を確認する。
```sh
task waiting            # 返信待ち・保留の確認
task all project:Inbox  # 未処理の取りこぼしチェック
task projects           # 中長期の棚卸し
```

---
## Tags Legend
- Context: form(事務), exam(試験), quiz(小テスト), asgn(課題)
- State:   next(次やる), wait(待ち), mit(今日やる), 5min(スキマ)
