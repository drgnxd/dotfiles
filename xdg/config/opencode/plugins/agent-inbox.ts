import { spawn, type ChildProcess } from "node:child_process"
import { homedir } from "node:os"
import { join } from "node:path"
import { pathToFileURL } from "node:url"
import type { Plugin } from "@opencode-ai/plugin"
import type { deletedSessionID, forgetFailedWaiter, helperEnv, pendingKey, respondToPermission, safeAsked } from "../lib/agent-inbox"

type Helpers = typeof import("../lib/agent-inbox")

type Event = { type?: string; properties?: Record<string, unknown> }
type V2Event = { type: string; data?: Record<string, unknown> }
type V2Context = {
  event?: { subscribe?: (options?: { signal?: AbortSignal }) => AsyncIterable<V2Event> }
  permission?: { reply?: (input: { sessionID: string; requestID: string; decision: "once" | "reject" }) => Promise<unknown> }
}
type Pending = { sessionID: string; permissionID: string; child: ChildProcess }
type Post = Parameters<typeof respondToPermission>[0]

async function loadHelpers(): Promise<Helpers> {
  const configHome = process.env.XDG_CONFIG_HOME || join(homedir(), ".config")
  return await import(pathToFileURL(join(configHome, "opencode/lib/agent-inbox.ts")).href)
}

// Both plugin APIs feed the same bridge: it forwards permission prompts to the agent-inbox helper and
// relays the user's answer back through `post`.
function createBridge(helpers: Helpers, post: Post) {
  const { deletedSessionID, forgetFailedWaiter, helperEnv, pendingKey, respondToPermission, safeAsked }: Helpers = helpers
  const pending = new Map<string, Pending>()
  const clear = (entry: Pending) => forgetFailedWaiter(pending, entry)
  const cancel = (entry: Pending) => {
    entry.child.kill("SIGTERM")
    clear(entry)
  }

  return {
    asked(value: unknown) {
      const safe = safeAsked(value)
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
        await respondToPermission(post, safe.sessionID, safe.permissionID, output.trim())
      })
    },
    replied(sessionID: unknown, requestID: unknown) {
      if (typeof requestID !== "string" || typeof sessionID !== "string") return
      const item = pending.get(pendingKey(sessionID, requestID))
      if (item) cancel(item)
    },
    deleted(sessionID: string | undefined) {
      if (!sessionID) return
      for (const entry of pending.values()) {
        if (entry.sessionID === sessionID) cancel(entry)
      }
    },
    completed(sessionID: unknown) {
      if (typeof sessionID !== "string" || !sessionID) return
      const child = spawn("agent-inbox", ["complete"], {
        stdio: "ignore",
        env: helperEnv("opencode", sessionID),
      })
      child.once("error", () => undefined)
      child.unref()
    },
    dispose() {
      for (const entry of pending.values()) entry.child.kill("SIGTERM")
      pending.clear()
    },
    deletedSessionID,
  }
}

const server: Plugin = async ({ client }) => {
  const helpers = await loadHelpers()
  const bridge = createBridge(helpers, (input) => client.postSessionIdPermissionsPermissionId(input))
  process.once("exit", () => bridge.dispose())

  return {
    event: async ({ event }) => {
      const value = event as Event
      const properties = value.properties ?? {}
      if (value.type === "permission.asked") bridge.asked(properties)
      else if (value.type === "permission.replied") bridge.replied(properties.sessionID, properties.requestID)
      else if (value.type === "session.deleted") bridge.deleted(bridge.deletedSessionID(properties))
      else if (value.type === "session.idle") bridge.completed(properties.sessionID)
    },
  }
}

// One default export serves both plugin APIs: OpenCode 1.x calls `server`, 2.x calls `setup`.
export default {
  id: "agent-inbox",
  server,
  async setup(ctx: V2Context) {
    const subscribe = ctx.event?.subscribe
    const reply = ctx.permission?.reply
    if (!subscribe || !reply) return
    const helpers = await loadHelpers()
    const bridge = createBridge(helpers, async (input) =>
      reply({ sessionID: input.path.id, requestID: input.path.permissionID, decision: input.body.response }),
    )
    const controller = new AbortController()
    void (async () => {
      for await (const event of subscribe.call(ctx.event, { signal: controller.signal })) {
        const data = event.data ?? {}
        if (event.type === "permission.asked") bridge.asked({ id: data.id, sessionID: data.sessionID, permission: data.action })
        else if (event.type === "permission.replied") bridge.replied(data.sessionID, data.requestID)
        else if (event.type === "session.deleted") bridge.deleted(typeof data.sessionID === "string" ? data.sessionID : undefined)
        else if (event.type === "session.execution.succeeded") bridge.completed(data.sessionID)
      }
    })().catch(() => undefined)
    return () => {
      controller.abort()
      bridge.dispose()
    }
  },
}
