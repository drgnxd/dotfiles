import type { Plugin } from "@opencode-ai/plugin"

const SHELL_TOOLS = new Set(["bash", "shell"])
const PENDING_LIMIT = 64
const PENDING_TTL_MS = 5000

type V2Context = {
  tool: {
    hook(
      name: "execute.before",
      callback: (event: { tool: string; sessionID: string; input: unknown }) => void | Promise<void>,
    ): unknown
  }
  shell: {
    hook(
      name: "create.before",
      callback: (event: { command: string; env: Record<string, string | undefined> }) => void | Promise<void>,
    ): unknown
  }
}

const server: Plugin = async () => ({
  "shell.env": async (input, output) => {
    output.env.OPENCODE_SESSION_ID = input.sessionID ?? ""
  },
})

// One default export serves both plugin APIs: OpenCode 1.x calls `server`, 2.x calls `setup`.
export default {
  id: "session-env",
  server,
  async setup(ctx: V2Context) {
    // The 2.x shell hook carries no session ID, so the ID is taken from the
    // tool call that spawned the shell and matched by command text.
    const pending: { command: string; sessionID: string; at: number }[] = []

    await ctx.tool.hook("execute.before", (event) => {
      if (!SHELL_TOOLS.has(String(event.tool).toLowerCase())) return
      const command = (event.input as { command?: unknown } | null)?.command
      if (typeof command !== "string") return
      pending.push({ command, sessionID: event.sessionID, at: Date.now() })
      if (pending.length > PENDING_LIMIT) pending.shift()
    })

    await ctx.shell.hook("create.before", (event) => {
      const cutoff = Date.now() - PENDING_TTL_MS
      for (let index = pending.length - 1; index >= 0; index--) {
        if (pending[index].at < cutoff) pending.splice(index, 1)
      }
      const matches = pending.filter((entry) => entry.command === event.command)
      for (const entry of matches) pending.splice(pending.indexOf(entry), 1)
      // An empty ID reads as an unknown session downstream; a wrong ID would pass ownership checks.
      const sessionIDs = new Set(matches.map((entry) => entry.sessionID))
      event.env.OPENCODE_SESSION_ID = sessionIDs.size === 1 ? matches[0].sessionID : ""
    })
  },
}
