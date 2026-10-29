import { expect, test } from "bun:test"
import { chmod, lstat, mkdir, mkdtemp, readFile, rm, symlink } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import permissionReviewPlugin from "../plugins/permission-review-log"
import { appendRecord, normalizeRecord, shouldReportEventStreamFailure } from "../plugins/permission-review-log"

test("does not report a normal event stream abort during plugin teardown", () => {
  const controller = new AbortController()
  expect(shouldReportEventStreamFailure(controller.signal)).toBe(true)
  controller.abort()
  expect(shouldReportEventStreamFailure(controller.signal)).toBe(false)
})

test("skips V2 stream setup when the runtime context has no event API", () => {
  expect(permissionReviewPlugin.setup({})).toBeUndefined()
})

test("consumes V2 permission events when the runtime exposes the event API", async () => {
  const stateHome = await mkdtemp(join(tmpdir(), "permission-review-v2-test-"))
  const previousStateHome = process.env.XDG_STATE_HOME
  process.env.XDG_STATE_HOME = stateHome
  const file = join(stateHome, "opencode", "permission-review", "events.jsonl")
  const events = [
    { type: "permission.v2.asked", data: { id: "v2-ask", action: "bash", resources: ["not-recorded"], save: ["safe"] } },
    { type: "permission.v2.replied", data: { requestID: "v2-ask", reply: "once" } },
    { type: "permission.asked", data: { id: "v2-plain", action: "shell", resources: ["not-recorded"] } },
    { type: "permission.replied", data: { requestID: "v2-plain", reply: "reject" } },
  ]
  try {
    const stop = permissionReviewPlugin.setup({
      event: {
        subscribe() {
          return {
            async *[Symbol.asyncIterator]() {
              yield* events
            },
          }
        },
      },
    })
    let content = ""
    for (let attempt = 0; attempt < 100; attempt++) {
      try {
        content = await readFile(file, "utf8")
        if (content.trim().split("\n").length >= 4) break
      } catch {}
      await new Promise((resolve) => setTimeout(resolve, 10))
    }
    expect(content).toContain('"kind":"asked"')
    expect(content).toContain('"kind":"replied"')
    expect(content).toContain('"candidates":["safe"]')
    expect(content).toContain('"request_id":"v2-plain"')
    expect(content).not.toContain("not-recorded")
    stop?.()
  } finally {
    if (previousStateHome === undefined) delete process.env.XDG_STATE_HOME
    else process.env.XDG_STATE_HOME = previousStateHome
    await rm(stateHome, { recursive: true, force: true })
  }
})

test("normalizes the V1 asked schema and retains only safe persistent suggestions", () => {
  const record = normalizeRecord("v1", "asked", {
    id: "v1-ask",
    permission: "edit",
    always: ["safe-pattern", "token=do-not-store", "another-safe", "safe-pattern"],
    sessionID: "not-recorded",
    metadata: { privateField: "not-recorded" },
    tool: "not-recorded",
  }, "2026-01-01T00:00:00.000Z")
  expect(record).toEqual({
    timestamp: "2026-01-01T00:00:00.000Z",
    generation: "v1",
    kind: "asked",
    request_id: "v1-ask",
    permission: "edit",
    action: "ask",
    candidates: ["another-safe", "safe-pattern"],
    candidates_redacted: 1,
  })
  expect(JSON.stringify(record)).not.toContain("do-not-store")
  expect(JSON.stringify(record)).not.toContain("not-recorded")
})

test("normalizes V1 replies from requestID and reply only", () => {
  expect(normalizeRecord("v1", "replied", { requestID: "v1-ask", reply: "always", permission: "ignored", sessionID: "ignored" })).toMatchObject({
    generation: "v1", kind: "replied", request_id: "v1-ask", reply: "always",
  })
  expect(normalizeRecord("v1", "replied", { id: "wrong-field", response: "always" })).toBeUndefined()
})

test("normalizes the V2 asked and replied payload shapes", () => {
  expect(normalizeRecord("v2", "asked", { id: "v2-ask", action: "bash", resources: ["not-recorded"], save: ["safe"] })).toMatchObject({
    generation: "v2", kind: "asked", request_id: "v2-ask", permission: "bash", action: "bash", candidates: ["safe"], candidates_redacted: 0,
  })
  expect(normalizeRecord("v2", "replied", { requestID: "v2-ask", reply: "once", metadata: "ignored" })).toMatchObject({
    generation: "v2", kind: "replied", request_id: "v2-ask", reply: "once",
  })
})

test("rejects incomplete events and filters common credential-like candidates", () => {
  expect(normalizeRecord("v1", "asked", { id: "missing-permission", always: ["x"] })).toBeUndefined()
  const record = normalizeRecord("v1", "asked", { id: "r", permission: "edit", always: ["https://user:password@example.org", "Authorization: Bearer secret", "ghp_123456789012345678901234567890"] })
  expect(record).toMatchObject({ candidates: [], candidates_redacted: 3 })
  expect(JSON.stringify(record)).not.toMatch(/password|secret|ghp_/)
})

test("creates an owner-only directory and file, and refuses a symlink log", async () => {
  const stateHome = await mkdtemp(join(tmpdir(), "permission-review-test-"))
  const previousStateHome = process.env.XDG_STATE_HOME
  process.env.XDG_STATE_HOME = stateHome
  const record = normalizeRecord("v1", "asked", { id: "r", permission: "edit", always: [] })!
  const directory = join(stateHome, "opencode", "permission-review")
  const file = join(directory, "events.jsonl")
  const target = join(stateHome, "outside")
  try {
    await appendRecord(record)
    expect((await lstat(directory)).mode & 0o777).toBe(0o700)
    expect((await lstat(file)).mode & 0o777).toBe(0o600)
    expect(await readFile(file, "utf8")).toContain('"request_id":"r"')
    await chmod(file, 0o644)
    await appendRecord(record)
    expect((await lstat(file)).mode & 0o777).toBe(0o600)
    await rm(file)
    await mkdir(target)
    await symlink(target, file)
    await expect(appendRecord(record)).rejects.toThrow("unsafe permission review file")
  } finally {
    if (previousStateHome === undefined) delete process.env.XDG_STATE_HOME
    else process.env.XDG_STATE_HOME = previousStateHome
    await rm(stateHome, { recursive: true, force: true })
  }
})
