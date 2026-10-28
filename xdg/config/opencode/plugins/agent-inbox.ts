import { spawn, type ChildProcess } from "node:child_process"
import type { Plugin } from "@opencode-ai/plugin"
import {
  deletedSessionID,
  forgetFailedWaiter,
  helperEnv,
  pendingKey,
  respondToPermission,
  safeAsked,
} from "../lib/agent-inbox"

type Event = { type?: string; properties?: Record<string, unknown> }
type Pending = { sessionID: string; permissionID: string; child: ChildProcess }

const plugin: Plugin = async ({ client }) => {
  const pending = new Map<string, Pending>()
  const clear = (entry: Pending) => forgetFailedWaiter(pending, entry)
  const cancel = (entry: Pending) => {
    entry.child.kill("SIGTERM")
    clear(entry)
  }
  const onExit = () => {
    for (const entry of pending.values()) entry.child.kill("SIGTERM")
    pending.clear()
  }
  process.once("exit", onExit)

  return {
    event: async ({ event }) => {
      const value = event as Event
      const properties = value.properties ?? {}
      if (value.type === "permission.asked") {
        const safe = safeAsked(properties)
        if (!safe) return
        const key = pendingKey(safe.sessionID, safe.permissionID)
        const existing = pending.get(key)
        if (existing) cancel(existing)
        const child = spawn("agent-inbox", ["permission-request"], {
          stdio: ["pipe", "pipe", "ignore"],
          env: helperEnv("opencode", safe.sessionID),
        })
        const entry = { sessionID: safe.sessionID, permissionID: safe.permissionID, child }
        pending.set(key, entry)
        child.once("error", () => clear(entry))
        child.stdin?.once("error", () => cancel(entry))
        child.once("exit", (code) => {
          if (code !== 0) clear(entry)
        })
        child.stdin?.end(JSON.stringify({ tool_name: safe.toolName, external_request_id: safe.permissionID }))
        let output = ""
        child.stdout?.setEncoding("utf8").on("data", (chunk: string) => { output = (output + chunk).slice(0, 16) })
        child.once("close", async () => {
          if (pending.get(key) !== entry) return
          clear(entry)
          await respondToPermission(
            (input) => client.postSessionIdPermissionsPermissionId(input),
            safe.sessionID,
            safe.permissionID,
            output.trim(),
          )
        })
      } else if (value.type === "permission.replied") {
        const eventID = properties.requestID
        const sessionID = properties.sessionID
        if (typeof eventID === "string" && typeof sessionID === "string") {
          const item = pending.get(pendingKey(sessionID, eventID))
          if (item) cancel(item)
        }
      } else if (value.type === "session.deleted") {
        const sessionID = deletedSessionID(properties)
        if (!sessionID) return
        for (const entry of pending.values()) {
          if (entry.sessionID === sessionID) cancel(entry)
        }
      } else if (value.type === "session.idle") {
        const sessionID = properties.sessionID
        if (typeof sessionID !== "string" || !sessionID) return
        const child = spawn("agent-inbox", ["complete"], {
          stdio: "ignore",
          env: helperEnv("opencode", sessionID),
        })
        child.once("error", () => undefined)
        child.unref()
      }
    },
  }
}

export default plugin
