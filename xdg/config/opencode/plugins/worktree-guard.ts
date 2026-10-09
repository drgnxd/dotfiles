import { spawnSync } from "node:child_process"
import { homedir } from "node:os"
import { join } from "node:path"

import type { Plugin } from "@opencode-ai/plugin"

const GUARD_TIMEOUT_MS = 8000
const GUARDED_TOOLS = new Set(["edit", "write", "multiedit", "patch", "apply_patch", "bash", "notebookedit"])

export const WorktreeGuardPlugin: Plugin = async ({ directory }) => ({
  "tool.execute.before": async (input, output) => {
    if (!GUARDED_TOOLS.has(String(input.tool).toLowerCase())) return
    let reason: string | undefined
    try {
      const configHome = process.env.XDG_CONFIG_HOME ?? join(homedir(), ".config")
      const script = join(configHome, "opencode", "skills", "git-workflow", "scripts", "worktree_guard.py")
      const result = spawnSync("python3", ["-I", script, "--client", "opencode"], {
        input: JSON.stringify({ tool: input.tool, args: output.args, cwd: directory }),
        encoding: "utf8",
        timeout: GUARD_TIMEOUT_MS,
      })
      if (result.status === 0 && result.stdout) {
        const verdict = JSON.parse(result.stdout) as { block?: boolean; reason?: string }
        if (verdict.block === true) reason = verdict.reason ?? "blocked by worktree-guard"
      }
    } catch {
      // A guard failure must never stop the tool.
    }
    if (reason !== undefined) throw new Error(`worktree-guard: ${reason}`)
  },
})

export default WorktreeGuardPlugin
