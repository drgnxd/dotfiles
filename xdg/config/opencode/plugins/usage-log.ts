import { appendFile, mkdir } from "node:fs/promises"
import { homedir } from "node:os"
import { join } from "node:path"

import type { Plugin } from "@opencode-ai/plugin"

type CompletedAssistantMessage = {
  id: string
  role: "assistant"
  time: { completed?: number }
  modelID: string
  providerID: string
  mode: string
  cost: number
  tokens: {
    input: number
    output: number
    reasoning: number
    cache: { read: number; write: number }
  }
  finish?: string
}

function isCompletedAssistantMessage(event: unknown): event is {
  type: "message.updated"
  properties: { info: CompletedAssistantMessage }
} {
  if (!event || typeof event !== "object") return false
  const value = event as { type?: unknown; properties?: { info?: unknown } }
  const info = value.properties?.info
  if (value.type !== "message.updated" || !info || typeof info !== "object") return false
  const message = info as Partial<CompletedAssistantMessage>
  return message.role === "assistant" && typeof message.id === "string" && message.time?.completed !== undefined
}

export const UsageLogPlugin: Plugin = async () => {
  const logged = new Set<string>()

  return {
    event: async ({ event }) => {
      if (!isCompletedAssistantMessage(event)) return

      const message = event.properties.info
      if (logged.has(message.id)) return
      logged.add(message.id)

      const completedAt = message.time.completed
      if (completedAt === undefined) return

      const timestamp = new Date(completedAt).toISOString()
      const month = timestamp.slice(0, 7)
      const stateHome = process.env.XDG_STATE_HOME ?? join(homedir(), ".local", "state")
      const directory = join(stateHome, "opencode", "oc-usage")
      const record = {
        timestamp,
        provider: message.providerID,
        model: message.modelID,
        agent: message.mode,
        finish_reason: message.finish ?? null,
        input_tokens: message.tokens.input,
        output_tokens: message.tokens.output,
        reasoning_tokens: message.tokens.reasoning,
        cache_read_tokens: message.tokens.cache.read,
        cache_write_tokens: message.tokens.cache.write,
        cost_usd: message.cost,
      }

      await mkdir(directory, { recursive: true })
      await appendFile(join(directory, `oc-usage-${month}.jsonl`), `${JSON.stringify(record)}\n`, "utf8")
    },
  }
}

export default UsageLogPlugin
