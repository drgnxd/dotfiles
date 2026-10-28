import assert from "node:assert/strict"
import { test } from "node:test"
import { helperEnv, pendingKey, responseForDecision, safeAsked } from "./agent-inbox"

test("maps allow and deny only to once and reject", () => {
  assert.equal(responseForDecision("allow"), "once")
  assert.equal(responseForDecision("deny"), "reject")
  assert.equal(responseForDecision("always"), undefined)
})

test("keys cancellation by exact session and permission identity", () => {
  assert.notEqual(pendingKey("session-a", "req"), pendingKey("session-b", "req"))
  assert.notEqual(pendingKey("session", "req-a"), pendingKey("session", "req-b"))
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

test("helper environment excludes inherited credentials and transcript variables", () => {
  const oldToken = process.env.API_TOKEN
  const oldTranscript = process.env.CLAUDE_TRANSCRIPT
  process.env.API_TOKEN = "private"
  process.env.CLAUDE_TRANSCRIPT = "private"
  try {
    const env = helperEnv("opencode", "session-a")
    assert.equal(env.AGENT_INBOX_CLIENT, "opencode")
    assert.equal(env.OPENCODE_SESSION_ID, "session-a")
    assert.equal(env.API_TOKEN, undefined)
    assert.equal(env.CLAUDE_TRANSCRIPT, undefined)
    assert.ok(Object.keys(env).every((key) => ["PATH", "HOME", "XDG_STATE_HOME", "ZELLIJ_SESSION_NAME", "ZELLIJ_PANE_ID", "AGENT_INBOX_CLIENT", "OPENCODE_SESSION_ID"].includes(key)))
  } finally {
    if (oldToken === undefined) delete process.env.API_TOKEN
    else process.env.API_TOKEN = oldToken
    if (oldTranscript === undefined) delete process.env.CLAUDE_TRANSCRIPT
    else process.env.CLAUDE_TRANSCRIPT = oldTranscript
  }
})
