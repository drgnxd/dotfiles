import assert from "node:assert/strict"
import { test } from "node:test"
import { mkdtemp, mkdir, symlink, rm } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import { pathToFileURL } from "node:url"
import {
  deletedSessionID,
  forgetFailedWaiter,
  helperEnv,
  pendingKey,
  respondToPermission,
  responseForDecision,
  safeAsked,
  default as plugin,
} from "../plugins/agent-inbox"

test("plugin loads from a symlinked plugin directory", async () => {
  const temp = await mkdtemp(join(tmpdir(), "opencode-plugin-"))
  try {
    const linkedPlugins = join(temp, "plugins")
    await mkdir(linkedPlugins)
    await symlink(resolve("plugins/agent-inbox.ts"), join(linkedPlugins, "agent-inbox.ts"))
    const loaded = await import(pathToFileURL(join(linkedPlugins, "agent-inbox.ts")).href)
    assert.equal(loaded.default, plugin)
  } finally {
    await rm(temp, { recursive: true, force: true })
  }
})

test("maps allow and deny only to once and reject", () => {
  assert.equal(responseForDecision("allow"), "once")
  assert.equal(responseForDecision("deny"), "reject")
  assert.equal(responseForDecision("always"), undefined)
})

test("calls the typed SDK endpoint with one-shot mappings", async () => {
  const calls: unknown[] = []
  const postPermission = async (input: Parameters<Parameters<typeof respondToPermission>[0]>[0]) => {
    calls.push(input)
    return undefined as never
  }
  await respondToPermission(postPermission, "session-a", "request-a", "allow")
  await respondToPermission(postPermission, "session-b", "request-b", "deny")
  await respondToPermission(postPermission, "session-c", "request-c", "always")
  assert.deepEqual(calls, [
    { path: { id: "session-a", permissionID: "request-a" }, body: { response: "once" } },
    { path: { id: "session-b", permissionID: "request-b" }, body: { response: "reject" } },
  ])
})

test("contains synchronous and asynchronous SDK errors", async () => {
  await assert.doesNotReject(respondToPermission(() => { throw new Error("sync") }, "s", "p", "allow"))
  await assert.doesNotReject(respondToPermission(async () => { throw new Error("async") }, "s", "p", "deny"))
})

test("keys cancellation by exact session and permission identity", () => {
  assert.notEqual(pendingKey("session-a", "req"), pendingKey("session-b", "req"))
  assert.notEqual(pendingKey("session", "req-a"), pendingKey("session", "req-b"))
})

test("spawn failure cleanup removes only the exact pending waiter", () => {
  const pending = new Map<string, { sessionID: string; permissionID: string }>()
  const failed = { sessionID: "session-a", permissionID: "request-a" }
  const replacement = { sessionID: "session-a", permissionID: "request-a" }
  pending.set(pendingKey(failed.sessionID, failed.permissionID), replacement)
  forgetFailedWaiter(pending, failed)
  assert.equal(pending.get(pendingKey(replacement.sessionID, replacement.permissionID)), replacement)
  forgetFailedWaiter(pending, replacement)
  assert.equal(pending.size, 0)
})

test("reads the nested session deletion identity", () => {
  assert.equal(deletedSessionID({ info: { id: "session-a" } }), "session-a")
  assert.equal(deletedSessionID({ id: "wrong-level" }), undefined)
})

test("permission event parser retains only safe fields", () => {
  assert.deepEqual(safeAsked({
    sessionID: "session-a",
    id: "request_1234",
    permission: "Bash",
    command: "not-used",
  }), { sessionID: "session-a", permissionID: "request_1234", toolName: "Bash" })
  assert.equal(safeAsked({ sessionID: "session-a", id: "bad id", permission: "Bash" }), undefined)
})

test("helper environment excludes inherited credentials and includes cache location", () => {
  const oldToken = process.env.API_TOKEN
  const oldTranscript = process.env.CLAUDE_TRANSCRIPT
  const oldCacheHome = process.env.XDG_CACHE_HOME
  process.env.API_TOKEN = "private"
  process.env.CLAUDE_TRANSCRIPT = "private"
  process.env.XDG_CACHE_HOME = "inbox-cache-test"
  try {
    const env = helperEnv("opencode", "session-a")
    assert.equal(env.AGENT_INBOX_CLIENT, "opencode")
    assert.equal(env.OPENCODE_SESSION_ID, "session-a")
    assert.equal(env.XDG_CACHE_HOME, "inbox-cache-test")
    assert.equal(env.API_TOKEN, undefined)
    assert.equal(env.CLAUDE_TRANSCRIPT, undefined)
    assert.ok(Object.keys(env).every((key) => ["PATH", "HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "ZELLIJ_SESSION_NAME", "ZELLIJ_PANE_ID", "AGENT_INBOX_CLIENT", "OPENCODE_SESSION_ID"].includes(key)))
  } finally {
    if (oldToken === undefined) delete process.env.API_TOKEN
    else process.env.API_TOKEN = oldToken
    if (oldTranscript === undefined) delete process.env.CLAUDE_TRANSCRIPT
    else process.env.CLAUDE_TRANSCRIPT = oldTranscript
    if (oldCacheHome === undefined) delete process.env.XDG_CACHE_HOME
    else process.env.XDG_CACHE_HOME = oldCacheHome
  }
})
