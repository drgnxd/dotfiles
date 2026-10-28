import assert from "node:assert/strict"
import { test } from "node:test"
import { pendingKey, responseForDecision, safeAsked } from "./agent-inbox"

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
