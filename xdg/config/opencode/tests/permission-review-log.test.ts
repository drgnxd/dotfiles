import { expect, test } from "bun:test"
import { normalizeRecord } from "../plugins/permission-review-log"

test("normalizes and sorts persistent candidates without unrelated fields", () => {
  expect(normalizeRecord("v1", "asked", { id: "r1", permission: "edit", always: ["z", "a", "a"], sessionID: "secret" }, "2026-01-01T00:00:00.000Z")).toEqual({ timestamp: "2026-01-01T00:00:00.000Z", generation: "v1", kind: "asked", request_id: "r1", permission: "edit", action: "ask", candidates: ["a", "z"] })
})

test("redacts credential-like persistent candidates and omits their values", () => {
  const record = normalizeRecord("v2", "asked", { requestID: "r", permission: "bash", save: ["safe", "token=super-secret"] })
  expect(record).toMatchObject({ candidates_redacted: true })
  expect(JSON.stringify(record)).not.toContain("super-secret")
  expect(JSON.stringify(record)).not.toContain("safe")
})

test("normalizes replies and ignores incomplete data", () => {
  expect(normalizeRecord("v1", "replied", { id: "r", permission: "edit", response: "reject", metadata: { secret: "x" } })?.action).toBe("reject")
  expect(normalizeRecord("v1", "asked", { permission: "edit" })).toBeUndefined()
})
