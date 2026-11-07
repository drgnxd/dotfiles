#!/usr/bin/env bun
// Create a detached task worktree and record which session created it.
//
// The record is a single write-once file in the worktree's Git administration
// directory, so Git deletes it together with the worktree (`git worktree move`
// keeps it but invalidates it, because it names the original path). It is
// supporting evidence only; it never authorizes removal or integration.

import { spawnSync } from "node:child_process"
import { randomBytes } from "node:crypto"
import { closeSync, constants, fstatSync, fsyncSync, lstatSync, mkdirSync, openSync, readFileSync, readSync, realpathSync, writeSync } from "node:fs"
import { basename, dirname, isAbsolute, join, resolve } from "node:path"

const MARKER = "session-owner"
const MARKER_VERSION = "1"
const MAX_MARKER_BYTES = 4096
const FIELDS = ["version", "session", "tool", "base", "path", "created"] as const
const TOOLS = ["opencode", "claude-code", "unknown"]
const NAME_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$/
const SESSION_RE = /^[A-Za-z0-9_.-]{1,128}$/
const OID_RE = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/
const TIME_RE = /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/
// Inherited from a hook context or a user shell, these would redirect Git to another repository.
const GIT_ENV_DROP = new Set([
  "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
  "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_PREFIX",
  "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
])
const GIT_ENV_DROP_PREFIXES = ["GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"]
const OWNER_EXIT = { mine: 0, other: 1, unknown: 3, unrecorded: 4 } as const
const ERROR_EXIT = 2

type Env = Record<string, string | undefined>
type Fields = Record<string, string>
type Status = keyof typeof OWNER_EXIT

export interface Context {
  env: Env
  cwd: string
  out: (text: string) => void
  err: (text: string) => void
  // Replaceable so tests can fail the step after the worktree exists.
  writeMarker?: (admin: string, fields: Fields) => void
}

export class Failure extends Error {}

function git(ctx: Pick<Context, "env" | "cwd">, args: string[], options: { cwd?: string; check?: boolean } = {}) {
  const env: Record<string, string> = {}
  for (const [key, value] of Object.entries(ctx.env)) {
    if (value === undefined || GIT_ENV_DROP.has(key) || GIT_ENV_DROP_PREFIXES.some((prefix) => key.startsWith(prefix))) continue
    env[key] = value
  }
  const result = spawnSync("git", args, { cwd: options.cwd ?? ctx.cwd, env, encoding: "utf8" })
  if (result.error) throw new Failure(`git ${args.join(" ")}: ${result.error.message}`)
  const status = result.status ?? -1
  if ((options.check ?? true) && status !== 0) throw new Failure(`git ${args.join(" ")}: ${result.stderr.trim()}`)
  return { status, stdout: result.stdout.trim() }
}

// Like realpath(3) but tolerates a path whose tail does not exist yet.
export function realpath(path: string): string {
  try {
    return realpathSync(path)
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error
    const parent = dirname(path)
    return parent === path ? path : join(realpath(parent), basename(path))
  }
}

export function currentSession(env: Env): { tool: string; session: string } {
  const found: { tool: string; session: string }[] = []
  for (const [name, tool] of [["OPENCODE_SESSION_ID", "opencode"], ["CLAUDE_CODE_SESSION_ID", "claude-code"]] as const) {
    const value = env[name] ?? ""
    if (value === "") continue
    if (!SESSION_RE.test(value) || value === "unknown") throw new Failure(`${name} is not a valid session ID`)
    found.push({ tool, session: value })
  }
  if (found.length > 1) throw new Failure("both OpenCode and Claude Code session IDs are set; refusing to guess")
  return found[0] ?? { tool: "unknown", session: "unknown" }
}

export function stateBase(env: Env): string {
  const value = env.XDG_STATE_HOME ?? ""
  return realpath(isAbsolute(value) ? value : join(env.HOME ?? "", ".local/state"))
}

function resolveFrom(base: string, raw: string): string {
  return realpath(isAbsolute(raw) ? raw : join(base, raw))
}

export function adminDir(ctx: Pick<Context, "env" | "cwd">, worktree: string): string {
  return realpath(git(ctx, ["rev-parse", "--absolute-git-dir"], { cwd: worktree }).stdout)
}

export function verifyPointers(worktree: string, admin: string): void {
  const dotGit = join(worktree, ".git")
  const stat = lstatSync(dotGit)
  let forward: string
  if (stat.isFile()) {
    const line = readFileSync(dotGit, "utf8").trim()
    if (!line.startsWith("gitdir: ")) throw new Failure(`unexpected .git file in ${worktree}`)
    forward = resolveFrom(worktree, line.slice("gitdir: ".length))
  } else {
    forward = realpath(dotGit)
  }
  if (forward !== admin) throw new Failure(`.git of ${worktree} does not point to ${admin}`)
  const raw = readFileSync(join(admin, "gitdir"), "utf8").trim()
  const target = isAbsolute(raw) ? raw : join(admin, raw)
  if (basename(target) !== ".git" || realpath(dirname(target)) !== realpath(worktree)) {
    throw new Failure(`${admin}/gitdir does not point back to ${worktree}`)
  }
}

export function writeMarker(admin: string, fields: Fields): void {
  if (Object.values(fields).some((value) => value.includes("\n"))) throw new Failure("marker values must not contain newlines")
  const body = Object.entries(fields).map(([key, value]) => `${key}=${value}\n`).join("")
  const fd = openSync(join(admin, MARKER), constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW, 0o600)
  try {
    writeSync(fd, body)
    fsyncSync(fd)
  } finally {
    closeSync(fd)
  }
}

export function readMarker(ctx: Pick<Context, "env" | "cwd">, worktree: string): Fields | null {
  const admin = adminDir(ctx, worktree)
  let fd: number
  try {
    fd = openSync(join(admin, MARKER), constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK)
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return null
    throw new Failure(`unsafe marker in ${admin}: ${(error as Error).message}`)
  }
  let data: Buffer
  try {
    if (!fstatSync(fd).isFile()) throw new Failure(`unsafe marker in ${admin}: not a regular file`)
    data = Buffer.alloc(MAX_MARKER_BYTES + 1)
    data = data.subarray(0, readSync(fd, data, 0, data.length, null))
  } finally {
    closeSync(fd)
  }
  if (data.length > MAX_MARKER_BYTES) throw new Failure(`marker in ${admin} is too large`)
  const lines = new TextDecoder("utf-8", { fatal: true }).decode(data).split("\n")
  if (lines[lines.length - 1] === "") lines.pop()
  const fields: Fields = {}
  for (const line of lines) {
    const index = line.indexOf("=")
    const key = line.slice(0, index)
    if (index < 0 || key in fields) throw new Failure(`malformed marker in ${admin}`)
    fields[key] = line.slice(index + 1)
  }
  if (Object.keys(fields).sort().join(",") !== [...FIELDS].sort().join(",")) {
    throw new Failure(`marker in ${admin} does not have exactly the expected fields`)
  }
  const { version = "", session = "", tool = "", base = "", path = "", created = "" } = fields
  if (version !== MARKER_VERSION) throw new Failure(`unsupported marker version in ${admin}`)
  const known = tool !== "unknown"
  const valid =
    TOOLS.includes(tool) && known === (session !== "unknown") && (!known || SESSION_RE.test(session)) &&
    OID_RE.test(base) && TIME_RE.test(created)
  if (!valid) throw new Failure(`marker in ${admin} has invalid values`)
  if (path !== realpath(worktree)) throw new Failure(`marker in ${admin} names a different path: ${path}`)
  return fields
}

function repoName(ctx: Context): string {
  let common = realpath(resolve(ctx.cwd, git(ctx, ["rev-parse", "--git-common-dir"]).stdout))
  if (basename(common) === ".git") common = dirname(common)
  return basename(common)
}

function registered(ctx: Context, path: string): boolean {
  const target = realpath(path)
  return git(ctx, ["worktree", "list", "--porcelain"]).stdout.split("\n")
    .some((line) => line.startsWith("worktree ") && realpath(line.slice("worktree ".length)) === target)
}

function create(ctx: Context, name: string, baseRev: string): number {
  if (!NAME_RE.test(name)) throw new Failure("name must match [A-Za-z0-9][A-Za-z0-9._-]{0,80}")
  const { tool, session } = currentSession(ctx.env)
  const base = git(ctx, ["rev-parse", "--verify", "--end-of-options", `${baseRev}^{commit}`]).stdout
  let path = join(stateBase(ctx.env), repoName(ctx), "worktrees", `${name}-${randomBytes(4).toString("hex")}`)
  mkdirSync(dirname(path), { recursive: true })
  try {
    git(ctx, ["worktree", "add", "--detach", path, base])
  } catch (error) {
    // Git keeps the worktree when only a post-checkout hook fails.
    if (error instanceof Failure && (lstatExists(path) || registered(ctx, path))) {
      throw new Failure(`worktree ${path} exists but is unrecorded and preserved; inspect before retrying: ${error.message}`)
    }
    throw error
  }
  try {
    path = realpath(path)
    if (git(ctx, ["rev-parse", "HEAD"], { cwd: path }).stdout !== base) throw new Failure("new worktree HEAD does not match the base OID")
    if (git(ctx, ["symbolic-ref", "-q", "HEAD"], { cwd: path, check: false }).status !== 1) throw new Failure("new worktree HEAD is not detached")
    const admin = adminDir(ctx, path)
    verifyPointers(path, admin)
    const created = new Date().toISOString().replace(/\.\d{3}Z$/, "Z")
    ;(ctx.writeMarker ?? writeMarker)(admin, { version: MARKER_VERSION, session, tool, base, path, created })
  } catch (error) {
    throw new Failure(`worktree ${path} exists but is unrecorded and preserved: ${(error as Error).message}`)
  }
  try {
    if (session === "unknown") ctx.err("warning: no session ID found; recorded as unknown\n")
    ctx.out(`path=${path}\nbase=${base}\ntool=${tool} session=${session}\n`)
  } catch {
    // The worktree and its record already exist; a closed output stream is not a failure.
  }
  return 0
}

function lstatExists(path: string): boolean {
  try {
    lstatSync(path)
    return true
  } catch {
    return false
  }
}

function owner(ctx: Context, target: string): number {
  const path = realpath(resolve(ctx.cwd, target))
  if (realpath(git(ctx, ["rev-parse", "--show-toplevel"], { cwd: path }).stdout) !== path) throw new Failure(`${path} is not a worktree root`)
  const fields = readMarker(ctx, path)
  let status: Status
  if (fields === null) {
    status = "unrecorded"
  } else {
    const { tool, session } = currentSession(ctx.env)
    if (fields.tool === "unknown" || fields.session === "unknown" || session === "unknown") status = "unknown"
    else status = fields.tool === tool && fields.session === session ? "mine" : "other"
  }
  ctx.out(`status=${status}\n`)
  if (fields !== null) ctx.out(`session=${fields.session} tool=${fields.tool}\nbase=${fields.base} created=${fields.created}\n`)
  return OWNER_EXIT[status]
}

const USAGE = `usage: wt-session.ts <command>
  whoami                          print the current session ID (exit 1 when unknown)
  create <name> [--base <rev>]    create and record a detached worktree (default base refs/heads/main)
  owner [path]                    compare a worktree's record with this session
                                  (exit 0 mine, 1 other, 3 unknown, 4 unrecorded, 2 error)
`

export function main(argv: string[], ctx: Context): number {
  try {
    const [command, ...rest] = argv
    if (command === "-h" || command === "--help") {
      ctx.out(USAGE)
      return 0
    }
    if (command === "whoami" && rest.length === 0) {
      const { tool, session } = currentSession(ctx.env)
      ctx.out(`tool=${tool} session=${session}\n`)
      return session === "unknown" ? 1 : 0
    }
    if (command === "create") {
      const positional: string[] = []
      let base = "refs/heads/main"
      for (let i = 0; i < rest.length; i++) {
        const arg = rest[i] as string
        if (arg === "--base") {
          const value = rest[++i]
          if (value === undefined) throw new Failure("--base needs a value")
          base = value
        } else if (arg.startsWith("-")) {
          throw new Failure(`unknown option ${arg}`)
        } else {
          positional.push(arg)
        }
      }
      if (positional.length !== 1) throw new Failure("create takes exactly one name")
      return create(ctx, positional[0] as string, base)
    }
    if (command === "owner" && rest.length <= 1) {
      if (rest[0] === "-h" || rest[0] === "--help") {
        ctx.out(USAGE)
        return 0
      }
      return owner(ctx, rest[0] ?? ".")
    }
    ctx.err(USAGE)
    return ERROR_EXIT
  } catch (error) {
    ctx.err(`error: ${(error as Error).message}\n`)
    return ERROR_EXIT
  }
}

if (import.meta.main) {
  process.exit(
    main(process.argv.slice(2), {
      env: process.env,
      cwd: process.cwd(),
      out: (text) => void process.stdout.write(text),
      err: (text) => void process.stderr.write(text),
    }),
  )
}
