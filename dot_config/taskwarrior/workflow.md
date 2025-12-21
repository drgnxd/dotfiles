# Taskwarrior GTD Workflow

## 1. Capture
Put all tasks into `project:Inbox` (automatically assigned by `default.project=Inbox`).
```sh
task add "..."
```

## 2. Process
Assign project, tags, and due dates to tasks in Inbox and route them to the exit until Inbox is empty.
```sh
task inbox
task <ID> modify project:uni.math tags:asgn,next due:friday
```

## 3. Do
Focus on Ready/Next tasks and exclude waiting tasks.
```sh
task ready
task <ID> start
task <ID> done
```

## 4. Review
Periodically check waiting, due dates, and Inbox.
```sh
task waiting            # Check reply-waiting/held tasks
task all project:Inbox  # Check for unprocessed items
task projects           # Medium-to-long term inventory
```

---
## Tags Legend
- Context: form(Admin), exam(Exam), quiz(Quiz), asgn(Assignment)
- State:   next(Next Action), wait(Waiting), mit(Most Important Task), 5min(Gap time)
