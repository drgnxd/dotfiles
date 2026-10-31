import { spawnSync } from "node:child_process"
import type { SpawnSyncOptionsWithStringEncoding, SpawnSyncReturns } from "node:child_process"
import { homedir } from "node:os"
import { join } from "node:path"

import type { Plugin } from "@opencode-ai/plugin"

const GUARD_TIMEOUT_MS = 15000
const TIMEOUT_REASON = "guard timed out after 15 seconds; operation blocked. Inspect guard and provenance-query latency before retrying; do not bypass the guard."
const GUARDED_TOOLS = new Set(["edit", "write", "multiedit", "patch", "apply_patch", "bash", "shell", "notebookedit"])

type V2Context = {
  location: { directory: string }
  tool: {
    hook(name: "execute.before", callback: (event: { tool: string; input: unknown }) => void | Promise<void>): unknown
  }
}

type GuardRunner = (command: string, args: string[], options: SpawnSyncOptionsWithStringEncoding) => SpawnSyncReturns<string>

export function guardReason(tool: string, args: unknown, directory: string, run: GuardRunner = spawnSync): string | undefined {
  const name = tool.toLowerCase()
  if (!GUARDED_TOOLS.has(name)) return undefined
  try {
    const configHome = process.env.XDG_CONFIG_HOME ?? join(homedir(), ".config")
    const script = join(configHome, "opencode", "skills", "git-workflow", "scripts", "worktree_guard.py")
    // The guard script keys its shell analysis on "bash", the V1 tool name.
    const result = run("python3", ["-I", script, "--client", "opencode"], {
      input: JSON.stringify({ tool: name === "shell" ? "bash" : tool, args, cwd: directory }),
      encoding: "utf8",
      timeout: GUARD_TIMEOUT_MS,
    })
    if ((result.error as NodeJS.ErrnoException | undefined)?.code === "ETIMEDOUT") {
      return TIMEOUT_REASON
    }
    if (result.status === 0 && result.stdout) {
      const verdict = JSON.parse(result.stdout) as { block?: boolean; reason?: string }
      if (verdict.block === true) return verdict.reason ?? "blocked by worktree-guard"
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException | undefined)?.code === "ETIMEDOUT") return TIMEOUT_REASON
    // Non-timeout failures retain the existing fail-open behavior.
  }
  return undefined
}

const server: Plugin = async ({ directory }) => ({
  "tool.execute.before": async (input, output) => {
    const reason = guardReason(String(input.tool), output.args, directory)
    if (reason !== undefined) throw new Error(`worktree-guard: ${reason}`)
  },
})

// One default export serves both plugin APIs: OpenCode 1.x calls `server`, 2.x calls `setup`.
export default {
  id: "worktree-guard",
  server,
  async setup(ctx: V2Context) {
    await ctx.tool.hook("execute.before", (event) => {
      const reason = guardReason(String(event.tool), event.input, ctx.location.directory)
      if (reason !== undefined) throw new Error(`worktree-guard: ${reason}`)
    })
  },
}
