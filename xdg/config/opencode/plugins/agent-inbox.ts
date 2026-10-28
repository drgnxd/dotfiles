import { spawn, spawnSync, type ChildProcess } from "node:child_process"
import type { Plugin } from "@opencode-ai/plugin"

type PermissionAsked = { id?: unknown; sessionID?: unknown; permission?: unknown }
type PermissionReplied = { requestID?: unknown; sessionID?: unknown }
type Event = { type?: string; properties?: Record<string, unknown> }
type Pending = { sessionID: string; permissionID: string; child: ChildProcess }
type Client = {
  postSessionIdPermissionsPermissionId(input: {
    path: { id: string; permissionID: string }
    body: { response: "once" | "reject" }
  }): Promise<unknown>
}

const ID = /^[A-Za-z0-9_-]{8,128}$/

export function responseForDecision(decision: string): "once" | "reject" | undefined {
  return decision === "allow" ? "once" : decision === "deny" ? "reject" : undefined
}

export function pendingKey(sessionID: string, permissionID: string): string {
  return `${sessionID}\u0000${permissionID}`
}

export function safeAsked(value: PermissionAsked): { sessionID: string; permissionID: string; toolName: string } | undefined {
  if (typeof value.sessionID !== "string" || !value.sessionID || typeof value.id !== "string" || !ID.test(value.id)) return
  if (typeof value.permission !== "string" || !/^[A-Za-z0-9_.:-]{1,128}$/.test(value.permission)) return
  return { sessionID: value.sessionID, permissionID: value.id, toolName: value.permission }
}

const plugin: Plugin = async ({ client }) => {
  const api = client as unknown as Client
  const pending = new Map<string, Pending>()
  const cancel = (entry: Pending) => {
    entry.child.kill("SIGTERM")
    pending.delete(pendingKey(entry.sessionID, entry.permissionID))
    const cleanup = spawn("agent-inbox", ["permission-cancel", entry.permissionID], {
      stdio: "ignore",
      env: { ...process.env, AGENT_INBOX_CLIENT: "opencode", OPENCODE_SESSION_ID: entry.sessionID },
    })
    cleanup.unref()
  }
  const onExit = () => {
    for (const entry of pending.values()) {
      entry.child.kill("SIGTERM")
      spawnSync("agent-inbox", ["permission-cancel", entry.permissionID], {
        stdio: "ignore",
        timeout: 2500,
        env: { ...process.env, AGENT_INBOX_CLIENT: "opencode", OPENCODE_SESSION_ID: entry.sessionID },
      })
    }
    pending.clear()
  }
  process.once("exit", onExit)

  return {
    event: async ({ event }) => {
      const value = event as Event
      const properties = value.properties ?? {}
      if (value.type === "permission.asked") {
        const safe = safeAsked(properties as PermissionAsked)
        if (!safe) return
        const key = pendingKey(safe.sessionID, safe.permissionID)
        const existing = pending.get(key)
        if (existing) cancel(existing)
        const child = spawn("agent-inbox", ["permission-request"], {
          stdio: ["pipe", "pipe", "ignore"],
          env: { ...process.env, AGENT_INBOX_CLIENT: "opencode", OPENCODE_SESSION_ID: safe.sessionID },
        })
        const entry = { sessionID: safe.sessionID, permissionID: safe.permissionID, child }
        pending.set(key, entry)
        child.stdin.end(JSON.stringify({ tool_name: safe.toolName, external_request_id: safe.permissionID }))
        let output = ""
        child.stdout.setEncoding("utf8").on("data", (chunk: string) => { output = (output + chunk).slice(0, 16) })
        child.once("close", () => {
          if (pending.get(key) !== entry) return
          pending.delete(key)
          const response = responseForDecision(output.trim())
          if (!response) return
          void api.postSessionIdPermissionsPermissionId({
            path: { id: safe.sessionID, permissionID: safe.permissionID },
            body: { response },
          }).catch(() => undefined)
        })
      } else if (value.type === "permission.replied") {
        const eventID = properties.requestID
        const sessionID = properties.sessionID
        if (typeof eventID === "string" && typeof sessionID === "string") {
          const item = pending.get(pendingKey(sessionID, eventID))
          if (item) cancel(item)
        }
      } else if (value.type === "session.deleted") {
        const sessionID = properties.sessionID ?? properties.id
        if (typeof sessionID !== "string") return
        for (const entry of pending.values()) {
          if (entry.sessionID === sessionID) cancel(entry)
        }
      } else if (value.type === "session.idle") {
        const sessionID = properties.sessionID
        if (typeof sessionID !== "string" || !sessionID) return
        const child = spawn("agent-inbox", ["complete"], {
          stdio: "ignore",
          env: { ...process.env, AGENT_INBOX_CLIENT: "opencode", OPENCODE_SESSION_ID: sessionID },
        })
        child.unref()
      }
    },
  }
}

export default plugin
