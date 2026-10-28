import { spawn, type ChildProcess } from "node:child_process"
import type { Plugin } from "@opencode-ai/plugin"

type PermissionAsked = { id?: unknown; sessionID?: unknown; permission?: unknown }
type PermissionReplied = { requestID?: unknown; sessionID?: unknown }
type Event = { type?: string; properties?: Record<string, unknown> }
type Pending = { sessionID: string; permissionID: string; child: ChildProcess }
const ID = /^[A-Za-z0-9_-]{8,128}$/
const ENV_KEYS = ["PATH", "HOME", "XDG_STATE_HOME", "ZELLIJ_SESSION_NAME", "ZELLIJ_PANE_ID"] as const
type PluginClient = Parameters<Plugin>[0]["client"]
type PermissionPost = PluginClient["postSessionIdPermissionsPermissionId"]

export function helperEnv(clientName: string, sessionID?: string): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {}
  for (const key of ENV_KEYS) {
    if (process.env[key] !== undefined) env[key] = process.env[key]
  }
  env.AGENT_INBOX_CLIENT = clientName
  // The helper stores permission and idle events against this exact OpenCode session.
  if (sessionID) env.OPENCODE_SESSION_ID = sessionID
  return env
}

export function responseForDecision(decision: string): "once" | "reject" | undefined {
  return decision === "allow" ? "once" : decision === "deny" ? "reject" : undefined
}

export async function respondToPermission(
  postPermission: PermissionPost,
  sessionID: string,
  permissionID: string,
  decision: string,
): Promise<void> {
  const response = responseForDecision(decision)
  if (!response) return
  try {
    await postPermission({ path: { id: sessionID, permissionID }, body: { response } })
  } catch {
    return
  }
}

export function pendingKey(sessionID: string, permissionID: string): string {
  return `${sessionID}\u0000${permissionID}`
}

export function forgetFailedWaiter<T extends { sessionID: string; permissionID: string }>(pending: Map<string, T>, entry: T): void {
  const key = pendingKey(entry.sessionID, entry.permissionID)
  if (pending.get(key) === entry) pending.delete(key)
}

export function deletedSessionID(properties: unknown): string | undefined {
  if (typeof properties !== "object" || properties === null) return
  const info = (properties as { info?: unknown }).info
  if (typeof info !== "object" || info === null) return
  const id = (info as { id?: unknown }).id
  return typeof id === "string" ? id : undefined
}

export function safeAsked(value: PermissionAsked): { sessionID: string; permissionID: string; toolName: string } | undefined {
  if (typeof value.sessionID !== "string" || !value.sessionID || typeof value.id !== "string" || !ID.test(value.id)) return
  if (typeof value.permission !== "string" || !/^[A-Za-z0-9_.:-]{1,128}$/.test(value.permission)) return
  return { sessionID: value.sessionID, permissionID: value.id, toolName: value.permission }
}

const plugin: Plugin = async ({ client }) => {
  const pending = new Map<string, Pending>()
  const clear = (entry: Pending) => forgetFailedWaiter(pending, entry)
  const cancel = (entry: Pending) => {
    entry.child.kill("SIGTERM")
    clear(entry)
  }
  const onExit = () => {
    for (const entry of pending.values()) {
      entry.child.kill("SIGTERM")
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
