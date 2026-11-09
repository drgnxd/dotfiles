import { afterEach, beforeEach, expect, test } from "bun:test"
import { spawnSync } from "node:child_process"
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, symlinkSync, unlinkSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { adminDir, main, readMarker, realpath, stateBase, verifyPointers, writeMarker, type Context } from "./wt-session"

const SCRIPT = join(import.meta.dir, "wt-session.ts")

type Env = Record<string, string | undefined>

interface Fixture {
  root: string
  repo: string
  state: string
  env: Env
  first: string
}

let fx: Fixture

function sh(cwd: string, env: Env, ...args: string[]): string {
  const result = spawnSync("git", args, { cwd, env: env as Record<string, string>, encoding: "utf8" })
  if (result.status !== 0) throw new Error(`git ${args.join(" ")}: ${result.stderr}`)
  return result.stdout.trim()
}

function git(...args: string[]): string {
  return sh(fx.repo, fx.env, ...args)
}

function commit(message: string): string {
  git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", message)
  return git("rev-parse", "HEAD")
}

beforeEach(() => {
  const root = realpath(mkdtempSync(join(tmpdir(), "wt-session-")))
  const repo = join(root, "proj")
  const state = join(root, "state")
  mkdirSync(repo)
  const env: Env = {
    PATH: process.env.PATH,
    HOME: root,
    XDG_STATE_HOME: state,
    GIT_CONFIG_GLOBAL: "/dev/null",
    GIT_CONFIG_SYSTEM: "/dev/null",
  }
  fx = { root, repo, state, env, first: "" }
  git("init", "-q", "-b", "main")
  fx.first = commit("seed")
})

afterEach(() => {
  rmSync(fx.root, { recursive: true, force: true })
})

function run(argv: string[], session: Env = {}, extra: Env = {}, ctx: Partial<Context> = {}) {
  let out = ""
  let err = ""
  const code = main(argv, {
    env: { ...fx.env, ...session, ...extra },
    cwd: fx.repo,
    out: (text) => void (out += text),
    err: (text) => void (err += text),
    ...ctx,
  })
  return { code, out, err }
}

function fields(text: string): Record<string, string> {
  const result: Record<string, string> = {}
  for (const token of text.split(/\s+/)) {
    const index = token.indexOf("=")
    if (index > 0) result[token.slice(0, index)] = token.slice(index + 1)
  }
  return result
}

const OC = { OPENCODE_SESSION_ID: "ses_abc" }

function create(session: Env = OC, ...extra: string[]): string {
  const result = run(["create", "task", ...extra], session)
  expect(result.code, result.err).toBe(0)
  return fields(result.out).path as string
}

const ctxOf = () => ({ env: fx.env, cwd: fx.repo })
const markerPath = (path: string) => join(adminDir(ctxOf(), path), "session-owner")
const taskDirs = () => readdirSync(join(fx.state, "proj", "worktrees")).filter((name) => name.startsWith("task-"))

function rewrite(path: string, edit: (lines: string[]) => string[]) {
  const lines = readFileSync(markerPath(path), "utf8").split("\n").filter((line) => line !== "")
  writeFileSync(markerPath(path), edit(lines).join("\n") + "\n")
}

function expectOwnerError(path: string, text: string) {
  const result = run(["owner", path], OC)
  expect(result.code, result.out).toBe(2)
  expect(result.err).toContain(text)
}

test("create records an OpenCode session", () => {
  const path = create()
  expect(path.startsWith(join(fx.state, "proj", "worktrees", "task-"))).toBe(true)
  expect(sh(path, fx.env, "rev-parse", "HEAD")).toBe(git("rev-parse", "main"))
  const result = run(["owner", path], OC)
  expect([result.code, fields(result.out).status]).toEqual([0, "mine"])
})

test("create records a Claude Code session", () => {
  const session = { CLAUDE_CODE_SESSION_ID: "claude-test-1" }
  const path = create(session)
  expect(fields(run(["owner", path], session).out).status).toBe("mine")
})

test("create records a Copilot session", () => {
  const session = { COPILOT_AGENT_SESSION_ID: "copilot-test-1" }
  const path = create(session)
  expect(fields(run(["owner", path], session).out).status).toBe("mine")
})

test("another session or tool reads as other", () => {
  const path = create()
  const other = run(["owner", path], { OPENCODE_SESSION_ID: "ses_xyz" })
  expect([other.code, fields(other.out).status]).toEqual([1, "other"])
  expect(fields(run(["owner", path], { CLAUDE_CODE_SESSION_ID: "ses_abc" }).out).status).toBe("other")
})

test("unknown never matches", () => {
  const path = create({})
  const withId = run(["owner", path], OC)
  expect([withId.code, fields(withId.out).status]).toEqual([3, "unknown"])
  const withoutId = run(["owner", path])
  expect([withoutId.code, fields(withoutId.out).status]).toEqual([3, "unknown"])
  expect(fields(run(["owner", create(OC)]).out).status).toBe("unknown")
})

test("the main worktree is unrecorded", () => {
  const result = run(["owner", fx.repo], OC)
  expect([result.code, fields(result.out).status]).toEqual([4, "unrecorded"])
})

test("multiple session IDs are refused before anything is created", () => {
  const result = run(["create", "task"], { OPENCODE_SESSION_ID: "a", CLAUDE_CODE_SESSION_ID: "b" })
  expect(result.code).toBe(2)
  expect(result.err).toContain("refusing to guess")
  expect(existsSync(fx.state)).toBe(false)
})

test("invalid session IDs are refused", () => {
  for (const value of ["bad id;", "unknown"]) {
    expect(run(["create", "task"], { OPENCODE_SESSION_ID: value }).code, value).toBe(2)
  }
  expect(existsSync(fx.state)).toBe(false)
})

test("an invalid name is refused", () => {
  expect(run(["create", "../escape"], OC).code).toBe(2)
  expect(existsSync(fx.state)).toBe(false)
})

test("the default base is the main branch, not a tag", () => {
  const second = commit("second")
  git("tag", "main", fx.first)
  expect(sh(create(), fx.env, "rev-parse", "HEAD")).toBe(second)
})

test("an explicit base is used and recorded", () => {
  commit("second")
  const path = create(OC, "--base", fx.first)
  expect(sh(path, fx.env, "rev-parse", "HEAD")).toBe(fx.first)
  expect(readFileSync(markerPath(path), "utf8")).toContain(`base=${fx.first}`)
})

test("an inherited GIT_DIR is ignored", () => {
  const result = run(["create", "task"], OC, { GIT_DIR: "/dev/null" })
  expect(result.code, result.err).toBe(0)
})

test("inherited Git config variables are ignored", () => {
  const result = run(["create", "task"], OC, {
    GIT_CONFIG_COUNT: "1",
    GIT_CONFIG_KEY_0: "core.worktree",
    GIT_CONFIG_VALUE_0: "/dev/null",
    GIT_CONFIG_PARAMETERS: "'core.worktree'='/nonexistent'",
  })
  expect(result.code, result.err).toBe(0)
})

test("a relative XDG_STATE_HOME is ignored", () => {
  expect(stateBase({ HOME: fx.root, XDG_STATE_HOME: "relative/state" })).toBe(realpath(join(fx.root, ".local/state")))
})

test("a state base that is not absolute is refused", () => {
  for (const env of [{}, { HOME: "" }, { HOME: "relative" }, { HOME: "relative", XDG_STATE_HOME: "also/relative" }]) {
    expect(() => stateBase(env), JSON.stringify(env)).toThrow(/absolute/)
  }
  expect(run(["create", "task"], OC, { HOME: "", XDG_STATE_HOME: "" }).code).toBe(2)
})

test("the Git config variables that point at files are ignored too", () => {
  writeFileSync(join(fx.root, "evil.gitconfig"), "[core]\n\thooksPath = /nonexistent\n")
  const result = run(["create", "task"], OC, { GIT_CONFIG_GLOBAL: join(fx.root, "evil.gitconfig") })
  expect(result.code, result.err).toBe(0)
})

function cleanProcessEnv(): Record<string, string> {
  return { PATH: process.env.PATH ?? "", HOME: fx.root, XDG_STATE_HOME: fx.state }
}

test("the documented bun invocation ignores .env and bunfig.toml from the caller's repository", () => {
  writeFileSync(join(fx.repo, ".env"), "OPENCODE_SESSION_ID=from-dotenv\n")
  writeFileSync(join(fx.repo, "pre.ts"), 'import { writeFileSync } from "node:fs"\nwriteFileSync("PRELOAD_RAN", "1")\n')
  writeFileSync(join(fx.repo, "bunfig.toml"), 'preload = ["./pre.ts"]\n')
  const result = spawnSync("bun", ["--no-env-file", "--config=/dev/null", SCRIPT, "whoami"], { cwd: fx.repo, env: cleanProcessEnv(), encoding: "utf8" })
  expect(result.stdout.trim()).toBe("tool=unknown session=unknown")
  expect(existsSync(join(fx.repo, "PRELOAD_RAN"))).toBe(false)
})

test("plain bun does load .env, which is why the flags are required", () => {
  writeFileSync(join(fx.repo, ".env"), "OPENCODE_SESSION_ID=from-dotenv\n")
  const result = spawnSync("bun", [SCRIPT, "whoami"], { cwd: fx.repo, env: cleanProcessEnv(), encoding: "utf8" })
  expect(result.stdout.trim()).toBe("tool=opencode session=from-dotenv")
})

test("the marker is write-once", () => {
  const admin = adminDir(ctxOf(), create())
  expect(() => writeMarker(admin, { version: "1" })).toThrow(/EEXIST/)
})

test("a marker copied to another worktree is rejected", () => {
  const first = create()
  const second = create({ OPENCODE_SESSION_ID: "ses_xyz" })
  writeFileSync(markerPath(second), readFileSync(markerPath(first)))
  expectOwnerError(second, "different path")
})

test("a symlinked marker is rejected", () => {
  const path = create()
  unlinkSync(markerPath(path))
  symlinkSync("/dev/null", markerPath(path))
  expectOwnerError(path, "unsafe marker")
})

test("a FIFO marker is rejected without blocking", () => {
  const path = create()
  unlinkSync(markerPath(path))
  expect(spawnSync("mkfifo", [markerPath(path)]).status).toBe(0)
  expectOwnerError(path, "not a regular file")
})

test("a directory marker is rejected", () => {
  const path = create()
  unlinkSync(markerPath(path))
  mkdirSync(markerPath(path))
  expectOwnerError(path, "not a regular file")
})

test("a duplicate key is rejected", () => {
  const path = create()
  rewrite(path, (lines) => [...lines, "session=other"])
  expectOwnerError(path, "malformed")
})

test("a missing or extra field is rejected", () => {
  const path = create()
  rewrite(path, (lines) => lines.filter((line) => !line.startsWith("tool=")))
  expectOwnerError(path, "expected fields")
  const other = create()
  rewrite(other, (lines) => [...lines, "status=mine"])
  expectOwnerError(other, "expected fields")
})

test("invalid values are rejected", () => {
  const path = create()
  for (const [from, to] of [
    ["session=ses_abc", "session=x status=mine"],
    ["tool=opencode", "tool=other"],
    ["tool=opencode", "tool=unknown"],
  ] as const) {
    rewrite(path, (lines) => lines.map((line) => (line === from ? to : line)))
    expectOwnerError(path, "invalid values")
    rewrite(path, (lines) => lines.map((line) => (line === to ? from : line)))
  }
})

test("a non-UTF-8 marker is rejected", () => {
  const path = create()
  writeFileSync(markerPath(path), Buffer.from([0x76, 0x3d, 0x31, 0x0a, 0xff, 0xfe, 0x0a]))
  expectOwnerError(path, "error:")
})

test("owner requires a worktree root", () => {
  const path = create()
  mkdirSync(join(path, "sub"))
  expectOwnerError(join(path, "sub"), "not a worktree root")
})

test("owner on a missing path says the path does not exist", () => {
  expectOwnerError(join(fx.state, "missing"), "does not exist")
})

test("a record planted in the main worktree's Git directory is ignored", () => {
  writeMarker(adminDir(ctxOf(), fx.repo), {
    version: "1", session: "ses_abc", tool: "opencode", base: fx.first, path: fx.repo, created: "2026-01-01T00:00:00Z",
  })
  const result = run(["owner", fx.repo], OC)
  expect([result.code, fields(result.out).status]).toEqual([4, "unrecorded"])
})

test("the on-disk record format is fixed", () => {
  const path = create()
  const lines = readFileSync(markerPath(path), "utf8").split("\n")
  expect(lines.pop()).toBe("")
  expect(lines.map((line) => line.split("=")[0])).toEqual(["version", "session", "tool", "base", "path", "created"])
  expect(lines[0]).toBe("version=1")
  expect(lines[1]).toBe("session=ses_abc")
  expect(lines[2]).toBe("tool=opencode")
  expect(lines[4]).toBe(`path=${path}`)
  expect(lines[5]).toMatch(/^created=\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/)
  writeFileSync(markerPath(path), `version=1\nsession=ses_abc\ntool=opencode\nbase=${fx.first}\npath=${path}\ncreated=2026-11-07T15:12:35Z\n`)
  expect(fields(run(["owner", path], OC).out).status).toBe("mine")
})

test("whoami", () => {
  expect(run(["whoami"]).code).toBe(1)
  const result = run(["whoami"], { CLAUDE_CODE_SESSION_ID: "abc" })
  expect([result.code, result.out.trim()]).toEqual([0, "tool=claude-code session=abc"])
})

test("usage errors exit 2 and help exits 0", () => {
  expect(run(["frobnicate"]).code).toBe(2)
  expect(run(["create"], OC).code).toBe(2)
  expect(run(["create", "a", "b"], OC).code).toBe(2)
  expect(run(["create", "a", "--bogus"], OC).code).toBe(2)
  expect(run(["create", "a", "--base"], OC).code).toBe(2)
  const help = run(["--help"])
  expect([help.code, help.out.startsWith("usage:")]).toEqual([0, true])
  expect(existsSync(fx.state)).toBe(false)
})

test("removing the worktree removes the record", () => {
  const path = create()
  const admin = adminDir(ctxOf(), path)
  git("worktree", "remove", path)
  expect(existsSync(admin)).toBe(false)
})

test("moving the worktree invalidates the record", () => {
  const path = create()
  git("worktree", "move", path, `${path}-moved`)
  expectOwnerError(`${path}-moved`, "different path")
})

test("a failed add that leaves a worktree is reported as preserved", () => {
  const hook = join(fx.repo, ".git", "hooks", "post-checkout")
  writeFileSync(hook, "#!/bin/sh\nexit 1\n")
  chmodSync(hook, 0o755)
  const result = run(["create", "task"], OC)
  expect(result.code).toBe(2)
  expect(taskDirs()).toHaveLength(1)
  expect(result.err).toContain("preserved")
})

test("a failure after the add is reported as preserved", () => {
  const result = run(["create", "task"], OC, {}, {
    writeMarker: () => {
      throw new Error("denied")
    },
  })
  expect(result.code).toBe(2)
  expect(result.err).toContain("unrecorded and preserved")
  expect(taskDirs()).toHaveLength(1)
})

test("a failed add without a worktree is a plain error", () => {
  const result = run(["create", "task", "--base", "no-such-rev"], OC)
  expect(result.code).toBe(2)
  expect(result.err).not.toContain("preserved")
})

test("a symlinked .git pointing to its own admin dir verifies", () => {
  const path = create()
  const admin = adminDir(ctxOf(), path)
  unlinkSync(join(path, ".git"))
  symlinkSync(admin, join(path, ".git"))
  verifyPointers(path, admin)
})

test("an admin dir naming another worktree fails", () => {
  const first = create()
  const second = create({ OPENCODE_SESSION_ID: "ses_xyz" })
  const admin = adminDir(ctxOf(), first)
  writeFileSync(join(admin, "gitdir"), join(second, ".git") + "\n")
  expect(() => verifyPointers(first, admin)).toThrow(/does not point back/)
})

const version = /(\d+)\.(\d+)/.exec(spawnSync("git", ["--version"], { encoding: "utf8" }).stdout)
const hasRelativePaths = version !== null && (Number(version[1]) > 2 || (Number(version[1]) === 2 && Number(version[2]) >= 48))

test.skipIf(!hasRelativePaths)("relative worktree paths are supported", () => {
  git("config", "worktree.useRelativePaths", "true")
  const path = create()
  const result = run(["owner", path], OC)
  expect([result.code, fields(result.out).status]).toEqual([0, "mine"])
  expect(readMarker(ctxOf(), path)?.session).toBe("ses_abc")
})
