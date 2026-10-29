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
  sessionID?: string
  variant?: string
  cost: number
  tokens: {
    input: number
    output: number
    reasoning: number
    cache: { read: number; write: number }
  }
  finish?: string
}

type UsageRecord = {
  completedAt: number
  provider: string
  model: string
  agent: string
  sessionId: string | undefined
  variant: string | undefined
  finish: string | undefined
  cost: number
  tokens: CompletedAssistantMessage["tokens"]
}

type V2StepStarted = {
  type: "session.step.started"
  data: {
    assistantMessageID: string
    sessionID?: string
    agent: string
    model: { id: string; providerID: string; variant?: string }
  }
}

type V2StepEnded = {
  type: "session.step.ended"
  data: { assistantMessageID: string; finish: string; cost: number; tokens: CompletedAssistantMessage["tokens"] }
}

type V2StepFailed = { type: "session.step.failed"; data: { assistantMessageID: string } }

type V2Event = V2StepStarted | V2StepEnded | V2StepFailed | { type: string; data?: unknown }

type V2Context = {
  event: { subscribe(options: { signal: AbortSignal }): AsyncIterable<V2Event> }
}

const STEP_LIMIT = 256

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

async function writeRecord(usage: UsageRecord): Promise<void> {
  const timestamp = new Date(usage.completedAt).toISOString()
  const month = timestamp.slice(0, 7)
  const stateHome = process.env.XDG_STATE_HOME ?? join(homedir(), ".local", "state")
  const directory = join(stateHome, "opencode", "oc-usage")
  const record = {
    timestamp,
    provider: usage.provider,
    model: usage.model,
    agent: usage.agent,
    session_id: usage.sessionId ?? null,
    variant: usage.variant ?? null,
    finish_reason: usage.finish ?? null,
    input_tokens: usage.tokens.input,
    output_tokens: usage.tokens.output,
    reasoning_tokens: usage.tokens.reasoning,
    cache_read_tokens: usage.tokens.cache.read,
    cache_write_tokens: usage.tokens.cache.write,
    cost_usd: usage.cost,
  }

  await mkdir(directory, { recursive: true })
  await appendFile(join(directory, `oc-usage-${month}.jsonl`), `${JSON.stringify(record)}\n`, "utf8")
}

const server: Plugin = async () => {
  const logged = new Set<string>()

  return {
    event: async ({ event }) => {
      if (!isCompletedAssistantMessage(event)) return

      const message = event.properties.info
      if (logged.has(message.id)) return
      logged.add(message.id)

      const completedAt = message.time.completed
      if (completedAt === undefined) return

      await writeRecord({
        completedAt,
        provider: message.providerID,
        model: message.modelID,
        agent: message.mode,
        sessionId: message.sessionID,
        variant: message.variant,
        finish: message.finish,
        cost: message.cost,
        tokens: message.tokens,
      })
    },
  }
}

// One default export serves both plugin APIs: OpenCode 1.x calls `server`, 2.x calls `setup`.
export default {
  id: "usage-log",
  server,
  setup(ctx: V2Context) {
    // 2.x splits a step into started (model, agent) and ended (cost, tokens) events.
    const steps = new Map<
      string,
      { provider: string; model: string; agent: string; sessionId?: string; variant?: string }
    >()
    const controller = new AbortController()

    void (async () => {
      for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
        try {
          if (event.type === "session.step.started") {
            const { data } = event as V2StepStarted
            steps.set(data.assistantMessageID, {
              provider: data.model.providerID,
              model: data.model.id,
              agent: data.agent,
              sessionId: data.sessionID,
              variant: data.model.variant,
            })
            if (steps.size > STEP_LIMIT) steps.delete(steps.keys().next().value as string)
          } else if (event.type === "session.step.failed") {
            steps.delete((event as V2StepFailed).data.assistantMessageID)
          } else if (event.type === "session.step.ended") {
            const { data } = event as V2StepEnded
            const step = steps.get(data.assistantMessageID)
            if (!step) continue
            steps.delete(data.assistantMessageID)
            await writeRecord({
              completedAt: Date.now(),
              provider: step.provider,
              model: step.model,
              agent: step.agent,
              sessionId: step.sessionId,
              variant: step.variant,
              finish: data.finish,
              cost: data.cost,
              tokens: data.tokens,
            })
          }
        } catch {
          // One failed write must not end logging for the rest of the session.
        }
      }
    })().catch(() => {
      // Usage logging must never disturb the session.
    })

    return () => controller.abort()
  },
}
