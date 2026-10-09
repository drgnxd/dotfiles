#!/usr/bin/env python3
"""Pre-tool-use guard that keeps agents out of the main checkout.

Called by a Claude Code PreToolUse hook and an OpenCode `tool.execute.before`
plugin. It protects only the repositories listed in the machine-local config
`$XDG_CONFIG_HOME/worktree-guard/config.json` (absent file: guard disabled):

    {"mode": "warn" | "deny",
     "repos": ["/abs/path/to/primary/checkout"],
     "default_branch": "main",
     "allow_paths": ["/abs/path/glob/in/main/checkout"]}

`warn` only logs what `deny` would block. The guard never blocks on its own
failure: any internal error, timeout, or unparsable input allows the call.
Bash analysis is best effort (git commands only); `sed -i` or redirects into
the main checkout are not caught, and a command it cannot parse is allowed.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from worktree_meta import git_env

GIT_TIMEOUT = 3
EDIT_TOOLS = {"edit", "write", "multiedit", "notebookedit", "patch", "apply_patch"}
GUARDED_TOOLS = EDIT_TOOLS | {"bash", "enterworktree"}
PATH_KEYS = ("file_path", "filePath", "path", "notebook_path")
PATCH_KEYS = ("patchText", "patch", "input")
PATCH_PATH_RE = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+?)\s*$", re.MULTILINE)
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([^\s'\"<>|&;()]+)\1([^\n]*)\n.*?\n[ \t]*\2[ \t]*(?=\n|$)", re.DOTALL)
ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
OPERATOR_RE = re.compile(r"[();&|]+")
OPERATOR_TOKEN_RE = re.compile(r"&&|\|\||\|&|[();&|]")
PAREN_OPEN, PAREN_CLOSE = ["("], [")"]
WRAPPERS = {"env", "sudo", "time", "nohup", "command", "exec", "nice", "builtin", "xargs"}
SHELLS = {"bash", "sh", "zsh", "dash"}
GIT_WRITE = {
    "add", "commit", "checkout", "switch", "reset", "restore", "rebase", "cherry-pick",
    "clean", "pull", "rm", "mv", "apply", "am", "revert", "update-ref", "stash", "merge",
    "branch", "tag", "config", "format-patch", "submodule", "sparse-checkout",
    "update-index", "read-tree", "checkout-index", "bisect", "notes", "replace", "symbolic-ref",
}
GIT_READ = {
    "status", "log", "diff", "show", "rev-parse", "rev-list", "ls-files", "ls-tree", "describe",
    "blame", "grep", "remote", "fetch", "push", "worktree", "annex", "cat-file", "check-ignore",
    "for-each-ref", "reflog", "shortlog", "name-rev", "merge-base", "help", "version", "var",
    "diff-tree", "diff-index", "show-ref", "count-objects", "fsck", "gc", "maintenance",
}
BRANCH_WRITE_FLAGS = {
    "-d", "-D", "-m", "-M", "-c", "-C", "-f", "--force", "--delete", "--move", "--copy",
    "--set-upstream-to", "-u", "--unset-upstream", "--edit-description",
}
LIST_FLAGS = {
    "-l", "--list", "--contains", "--no-contains", "--merged", "--no-merged", "--points-at",
    "--show-current", "-a", "-r", "-v", "-vv", "-n",
}
TAG_WRITE_FLAGS = {"-d", "-a", "-s", "-f", "-m", "-u", "--delete", "--annotate", "--sign", "--force"}
CONFIG_WRITE_FLAGS = {
    "--unset", "--unset-all", "--add", "--replace-all", "--rename-section", "--remove-section",
    "--edit", "-e",
}
CONFIG_READ_WORDS = {"get", "list"}
HOOK_BYPASS_SUBCOMMANDS = {"commit", "merge", "am", "rebase", "push", "cherry-pick", "revert"}
WORKTREE_ADMIN = {"add", "remove", "prune", "move", "lock", "unlock", "repair"}
ANNEX_WRITE = {
    "add", "sync", "unlock", "lock", "fix", "drop", "move", "import", "rekey", "get", "pull",
    "assist", "adjust", "unannex", "undo", "merge",
}
GIT_OPTS_WITH_ARG = {"-c", "-C", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
CASE_INSENSITIVE = sys.platform == "darwin"


class GuardError(Exception):
    pass


@dataclass
class Decision:
    action: str = "allow"  # allow | warn | deny
    rule: str = ""
    reason: str = ""
    target: str = ""

    def stronger(self, other: Decision) -> Decision:
        order = {"allow": 0, "warn": 1, "deny": 2}
        return other if order[other.action] > order[self.action] else self


@dataclass
class Worktree:
    path: str
    protected: bool


@dataclass
class Repo:
    root: str
    gitdir: str
    worktrees: list[Worktree] = field(default_factory=list)


def config_dir(env: dict[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    base = env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "worktree-guard"


def state_dir(env: dict[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    base = env.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "worktree-guard"


def string_list(value: object) -> list[str]:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return []


def load_config() -> dict | None:
    try:
        data = json.loads((config_dir() / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("mode") not in ("warn", "deny"):
        return None
    return data


def key(path: str) -> str:
    path = unicodedata.normalize("NFC", path)
    return path.casefold() if CASE_INSENSITIVE else path


def within(child_key: str, parent_key: str) -> bool:
    return child_key == parent_key or child_key.startswith(parent_key.rstrip("/") + "/")


def canonical(path: str, cwd: str) -> str:
    """Resolve symlinks on the nearest existing ancestor so new files are located too."""
    p = os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))
    head, tail = p, []
    while not os.path.lexists(head) and head != os.path.dirname(head):
        head, name = os.path.split(head)
        tail.append(name)
    return os.path.join(os.path.realpath(head), *reversed(tail))


def run_git(cwd: str, *args: str) -> str:
    try:
        proc = subprocess.run(
            [os.environ.get("WORKTREE_GUARD_GIT") or "git", *args], cwd=cwd, env=git_env(),
            capture_output=True, text=True, timeout=GIT_TIMEOUT, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GuardError(f"git {args[0]} failed: {exc}") from exc
    if proc.returncode != 0:
        raise GuardError(f"git {args[0]} exited {proc.returncode}")
    return proc.stdout


def load_repo(root_text: str, default_branch: str) -> Repo | None:
    root = canonical(root_text, "/")
    if not os.path.isdir(root):
        return None
    common = run_git(root, "rev-parse", "--git-common-dir").strip()
    repo = Repo(root=root, gitdir=canonical(common, root))
    ref = f"refs/heads/{default_branch}"
    for entry in run_git(root, "worktree", "list", "--porcelain").split("\n\n"):
        fields = dict(
            line.split(" ", 1) if " " in line else (line, "") for line in entry.splitlines()
        )
        path = fields.get("worktree")
        if not path or key(canonical(path, "/")) == key(root) or "bare" in fields:
            continue
        protected = "detached" in fields or fields.get("branch") == ref
        repo.worktrees.append(Worktree(canonical(path, "/"), protected))
    return repo


def load_repos(cfg: dict) -> list[Repo]:
    repos = []
    for root_text in string_list(cfg.get("repos")):
        try:
            repo = load_repo(root_text, cfg.get("default_branch", "main"))
        except GuardError as exc:
            log("guard", "load_repo", Decision(), cfg["mode"], error=str(exc)[:200])
            continue
        if repo:
            repos.append(repo)
    return repos


def locate(path: str, repos: list[Repo]) -> tuple[Repo, str] | None:
    """Return (repo, kind) with kind in gitdir | protected | task, or None if untracked by config."""
    k = key(path)
    for repo in repos:
        if within(k, key(repo.gitdir)):
            return repo, "gitdir"
        for wt in sorted(repo.worktrees, key=lambda w: -len(w.path)):
            if within(k, key(wt.path)):
                return repo, "protected" if wt.protected else "task"
        if within(k, key(repo.root)):
            return repo, "protected"
    return None


def check_path(path: str, cwd: str, cfg: dict, repos: list[Repo]) -> Decision:
    canon = canonical(path, cwd)
    k = key(canon)
    if within(k, key(canonical(str(config_dir()), "/"))):
        return Decision("deny", "guard-config", "The guard configuration is user-owned.", canon)
    found = locate(canon, repos)
    if found is None:
        return Decision()
    repo, kind = found
    if kind == "gitdir":
        return Decision("deny", "git-dir", f"{canon} is inside a Git directory; do not edit it.", canon)
    if kind == "protected":
        for pattern in string_list(cfg.get("allow_paths")):
            if fnmatch.fnmatchcase(k, key(canonical(pattern, "/"))):
                return Decision()
        return Decision(
            "deny", "main-checkout",
            f"{canon} is in a protected checkout of {repo.root}. Create a task worktree with "
            "worktree-create.py (git-workflow skill) and edit there.",
            canon,
        )
    return Decision()


def edit_paths(tool_input: dict) -> list[str]:
    paths = [tool_input[k] for k in PATH_KEYS if isinstance(tool_input.get(k), str)]
    for name in PATCH_KEYS:
        text = tool_input.get(name)
        if isinstance(text, str):
            paths.extend(PATCH_PATH_RE.findall(text))
    return paths


def split_segments(command: str) -> list[list[str]]:
    """Split into token lists; subshell parentheses are kept as their own segments."""
    command = command.replace("\\\n", " ")
    command = HEREDOC_RE.sub(lambda m: " " + m.group(3), command).replace("\n", " ; ")
    lexer = shlex.shlex(command, posix=True, punctuation_chars="();&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    segments: list[list[str]] = [[]]
    for token in lexer:
        if not OPERATOR_RE.fullmatch(token):
            segments[-1].append(token)
            continue
        for operator in OPERATOR_TOKEN_RE.findall(token):
            if operator in ("(", ")"):
                segments.extend([list(PAREN_OPEN if operator == "(" else PAREN_CLOSE), []])
            else:
                segments.append([])
    return [s for s in segments if s]


def unresolved(text: str) -> bool:
    return "$" in text or "`" in text


def skip_assignments(tokens: list[str], index: int, env: dict[str, str]) -> int:
    while index < len(tokens) and ENV_ASSIGN_RE.match(tokens[index]):
        name, _, value = tokens[index].partition("=")
        env[name] = value
        index += 1
    return index


def find_git(tokens: list[str]) -> tuple[int, dict[str, str]] | None:
    """Locate `git` at command position, seeing through env/direnv/nix/sudo-style wrappers."""
    env: dict[str, str] = {}
    index = skip_assignments(tokens, 0, env)
    while index < len(tokens):
        name = os.path.basename(tokens[index])
        if name == "git":
            return index, env
        if name in WRAPPERS:
            index += 1
            while index < len(tokens) and (tokens[index].startswith("-") or ENV_ASSIGN_RE.match(tokens[index])):
                index = skip_assignments(tokens, index, env) if ENV_ASSIGN_RE.match(tokens[index]) else index + 1
        elif name == "direnv" and tokens[index + 1:index + 2] == ["exec"]:
            index += 3
        elif name == "nix":
            flags = [i for i, t in enumerate(tokens[index:], index) if t in ("-c", "--command")]
            if not flags:
                return None
            index = flags[0] + 1
        else:
            return None
    return None


def git_invocation(tokens: list[str]) -> tuple[list[str], list[str], dict[str, str]] | None:
    found = find_git(tokens)
    if found is None:
        return None
    index, env = found
    rest = tokens[index + 1:]
    position = 0
    while position < len(rest) and rest[position].startswith("-"):
        position += 2 if rest[position] in GIT_OPTS_WITH_ARG else 1
    return rest[:position], rest[position:], env


def global_target(options: list[str], env: dict[str, str], cwd: str | None) -> str | None:
    """Directory the git command acts on, or None when it cannot be resolved."""
    work_tree = env.get("GIT_WORK_TREE")
    git_dir = "GIT_DIR" in env
    directory = cwd
    index = 0
    while index < len(options):
        option = options[index]
        value = options[index + 1] if index + 1 < len(options) else ""
        if option == "-C":
            if directory is None or unresolved(value):
                return None
            directory = canonical(value, directory)
            index += 1
        elif option.startswith("--work-tree"):
            work_tree = option.partition("=")[2] or value
            index += 0 if "=" in option else 1
        elif option.startswith("--git-dir"):
            git_dir = True
            index += 0 if "=" in option else 1
        elif option == "-c":
            index += 1
        index += 1
    if work_tree is not None:
        if unresolved(work_tree) or directory is None:
            return None
        return canonical(work_tree, directory)
    if git_dir or directory is None:
        return None
    return directory


def positionals(args: list[str]) -> list[str]:
    return [a for a in args if not a.startswith("-")]


def is_git_write(sub: str, args: list[str]) -> bool:
    flags = {a.partition("=")[0] for a in args if a.startswith("-")}
    if sub == "stash":
        return not (args and args[0] in ("list", "show"))
    if sub == "branch":
        if flags & BRANCH_WRITE_FLAGS:
            return True
        return bool(positionals(args)) and not flags & LIST_FLAGS
    if sub == "tag":
        if flags & TAG_WRITE_FLAGS:
            return True
        return bool(positionals(args)) and not flags & (LIST_FLAGS | {"-n"})
    if sub == "config":
        if flags & {"--global", "--system", "--file", "-f"}:
            return False
        if flags & CONFIG_WRITE_FLAGS:
            return True
        words = positionals(args)
        if words and words[0] in CONFIG_READ_WORDS:
            return False
        return len(words) > 1 or (bool(words) and words[0] in ("set", "unset", "edit", "rename-section", "remove-section"))
    if sub == "apply":
        return not flags & {"--check", "--stat", "--numstat", "--summary"}
    if sub == "merge":
        return not {"--ff-only", "--no-overwrite-ignore"} <= flags
    if sub == "submodule":
        return not (args and args[0] in ("status", "summary"))
    if sub in ("sparse-checkout", "notes"):
        return not (args and args[0] in ("list", "show"))
    if sub == "symbolic-ref":
        return len(positionals(args)) > 1
    if sub == "replace":
        return not flags & {"-l", "--list"}
    return sub in GIT_WRITE


def bypasses_hooks(sub: str, args: list[str], options: list[str]) -> bool:
    if sub not in HOOK_BYPASS_SUBCOMMANDS:
        return False
    if "--no-verify" in args:
        return True
    if sub == "commit" and any(re.fullmatch(r"-[a-zA-Z]*n[a-zA-Z]*", a) for a in args):
        return True
    return any(
        options[i].lower().startswith("core.hookspath")
        for i in range(1, len(options))
        if options[i - 1] == "-c"
    )


def resolve_alias(sub: str, args: list[str], options: list[str], target: str) -> tuple[str, list[str], bool]:
    """Return (subcommand, args, is_shell_alias) after expanding a git alias."""
    if sub in GIT_WRITE or sub in GIT_READ:
        return sub, args, False
    value = ""
    for i in range(1, len(options)):
        if options[i - 1] == "-c" and options[i].lower().startswith(f"alias.{sub.lower()}="):
            value = options[i].partition("=")[2]
    if not value:
        try:
            value = run_git(target, "config", "--get", f"alias.{sub}").strip()
        except GuardError:
            return sub, args, False
    if value.startswith("!"):
        return sub, args, True
    words = value.split()
    return (words[0], words[1:] + args, False) if words else (sub, args, False)


def check_git(tokens: list[str], cwd: str | None, repos: list[Repo]) -> Decision:
    parsed = git_invocation(tokens)
    if parsed is None:
        return Decision()
    options, rest, env = parsed
    if not rest:
        return Decision()
    sub, args = rest[0], rest[1:]
    target = global_target(options, env, cwd)
    if target is None:
        write = is_git_write(sub, args) or (sub == "worktree" and args[:1] and args[0] in WORKTREE_ADMIN)
        if write:
            return Decision("warn", "unresolved-target", "Cannot resolve the repository this git command writes to.", cwd or "")
        return Decision()
    found = locate(target, repos)
    if found is None:
        return Decision()
    kind = found[1]
    protected = kind in ("protected", "gitdir")
    sub, args, shell_alias = resolve_alias(sub, args, options, target)
    if shell_alias:
        return Decision("warn", "shell-alias", "A shell alias cannot be analysed.", target)
    if sub == "worktree" and args[:1] and args[0] in WORKTREE_ADMIN:
        hint = "worktree-create.py" if args[0] == "add" else "safe-worktree-remove.py"
        return Decision(
            "deny", "worktree-admin",
            f"git worktree {args[0]} is not allowed directly; use {hint}, or ask the user if it cannot be used.",
            target,
        )
    if bypasses_hooks(sub, args, options):
        return Decision("deny", "no-verify", "Do not bypass commit hooks (--no-verify, core.hooksPath).", target)
    if sub == "annex" and args[:1] and args[0] in ANNEX_WRITE and protected:
        return Decision("deny", "main-checkout", f"git annex {args[0]} writes the protected checkout; use a task worktree.", target)
    if protected and is_git_write(sub, args):
        return Decision(
            "deny", "main-checkout",
            f"git {sub} would write the protected checkout {target}. Use a task worktree "
            "(worktree-create.py); to record a description use `git -C <task worktree> config ...`; "
            "integrate with the skill's ff-only procedure.",
            target,
        )
    return Decision()


def check_bash(command: str, cwd: str, repos: list[Repo], depth: int = 0) -> Decision:
    result = Decision()
    current: str | None = cwd
    stack: list[str | None] = []
    for tokens in split_segments(command):
        if tokens == PAREN_OPEN:
            stack.append(current)
            continue
        if tokens == PAREN_CLOSE:
            current = stack.pop() if stack else current
            continue
        head = os.path.basename(tokens[0])
        if head in ("cd", "pushd"):
            words = [t for t in tokens[1:] if t != "--"]
            if not words:
                current = str(Path.home())
            elif current is None or unresolved(words[0]) or words[0] == "-":
                current = None
            else:
                current = canonical(words[0], current)
            continue
        if head == "popd":
            current = None
            continue
        if head in SHELLS and "-c" in tokens and depth < 3:
            inner = tokens[tokens.index("-c") + 1:][:1]
            if inner and current is not None:
                result = result.stronger(check_bash(inner[0], current, repos, depth + 1))
            continue
        result = result.stronger(check_git(tokens, current, repos))
    return result


def evaluate(tool: str, tool_input: dict, cwd: str, cfg: dict) -> Decision:
    name = tool.lower()
    if name not in GUARDED_TOOLS:
        return Decision()
    command = tool_input.get("command")
    if name == "bash" and not (isinstance(command, str) and "git" in command):
        return Decision()
    repos = load_repos(cfg)
    result = Decision()
    if name in EDIT_TOOLS:
        for path in edit_paths(tool_input):
            result = result.stronger(check_path(path, cwd, cfg, repos))
    elif name == "bash":
        result = check_bash(command, cwd, repos)
    elif locate(canonical(cwd, "/"), repos) is not None:
        result = Decision("deny", "builtin-worktree", "Create the worktree with worktree-create.py instead.", cwd)
    return result


def log(client: str, tool: str, decision: Decision, mode: str, error: str = "") -> None:
    if decision.action == "allow" and not error:
        return
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "client": client, "tool": tool, "mode": mode,
        "decision": decision.action, "rule": decision.rule, "target": decision.target, "error": error,
    }
    try:
        directory = state_dir()
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(directory / "log.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
    except OSError:
        pass


def normalise(client: str, payload: dict) -> tuple[str, dict, str]:
    if client == "claude":
        return payload.get("tool_name", ""), payload.get("tool_input") or {}, payload.get("cwd") or os.getcwd()
    tool, args = payload.get("tool", ""), payload.get("args") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if isinstance(args.get("workdir"), str):
        cwd = canonical(args["workdir"], cwd)
    return tool, args, cwd


def run(client: str, payload: dict) -> tuple[Decision, bool]:
    """Return (decision, blocked). Blocks only for a deny in deny mode."""
    cfg = load_config()
    if cfg is None:
        return Decision(), False
    tool, tool_input, cwd = normalise(client, payload)
    try:
        decision = evaluate(tool, tool_input, cwd, cfg)
    except Exception as exc:  # noqa: BLE001 - fail open: a guard bug must not stop all editing
        log(client, tool, Decision(), cfg["mode"], error=f"{type(exc).__name__}: {exc}"[:200])
        return Decision(), False
    log(client, tool, decision, cfg["mode"])
    return decision, decision.action == "deny" and cfg["mode"] == "deny"


def main(argv: list[str]) -> int:
    client = argv[argv.index("--client") + 1] if "--client" in argv else "claude"
    blocked, decision = False, Decision()
    try:
        decision, blocked = run(client, json.load(sys.stdin))
    except Exception:  # noqa: BLE001 - unreadable payload: allow
        blocked = False
    if client == "claude":
        if blocked:
            print(f"worktree-guard: {decision.reason}", file=sys.stderr)
            return 2
        return 0
    print(json.dumps({"block": blocked, "reason": decision.reason, "rule": decision.rule}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
