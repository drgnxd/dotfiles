import { chmod, lstat, mkdir, open } from "node:fs/promises"
import { constants } from "node:fs"
import { homedir, userInfo } from "node:os"
import { join } from "node:path"
import type { Plugin } from "@opencode-ai/plugin"

type Generation = "v1" | "v2"
type EventRecord = { timestamp: string; generation: Generation; kind: "asked" | "replied"; request_id: string; permission: string; action: string; candidates?: string[]; candidates_redacted?: true }
type V2Context = { event: { subscribe(options: { signal: AbortSignal }): AsyncIterable<{ type: string; properties?: Record<string, unknown> }> } }

const sensitive = /(?:https?:\/\/[^\s/:@]+:[^\s/@]+@|(?:authorization|bearer|password|passwd|token|secret|api[_-]?key)\s*[:=]\s*\S|\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}))/i
const candidateIsSensitive = (value: string) => sensitive.test(value)

export function normalizeRecord(generation: Generation, kind: "asked" | "replied", properties: Record<string, any>, timestamp = new Date().toISOString()): EventRecord | undefined {
  const requestId = properties.id ?? properties.requestID ?? properties.requestId
  const permission = properties.permission
  const action = kind === "asked" ? "ask" : properties.response ?? properties.action
  if (typeof requestId !== "string" || typeof permission !== "string" || typeof action !== "string") return
  const raw = kind === "asked" ? (generation === "v1" ? properties.always : properties.save) : undefined
  const candidates = Array.isArray(raw) ? [...new Set(raw.filter((v: unknown): v is string => typeof v === "string"))].sort() : []
  const redacted = candidates.some(candidateIsSensitive)
  return { timestamp, generation, kind, request_id: requestId, permission, action, ...(candidates.length ? (redacted ? { candidates_redacted: true as const } : { candidates }) : {}) }
}

async function appendRecord(record: EventRecord): Promise<void> {
  const stateHome = process.env.XDG_STATE_HOME ?? join(homedir(), ".local", "state")
  const directory = join(stateHome, "opencode", "permission-review")
  const file = join(directory, "events.jsonl")
  const uid = Number(userInfo().uid)
  await mkdir(directory, { recursive: true, mode: 0o700 })
  let dirStat = await lstat(directory)
  if (dirStat.isSymbolicLink() || !dirStat.isDirectory() || dirStat.uid !== uid) throw new Error("unsafe permission review directory")
  if ((dirStat.mode & 0o777) !== 0o700) await chmod(directory, 0o700)
  let handle
  try {
    try {
      const st = await lstat(file)
      if (st.isSymbolicLink() || !st.isFile() || st.uid !== uid) throw new Error("unsafe permission review file")
      if ((st.mode & 0o777) !== 0o600) await chmod(file, 0o600)
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error
    }
    handle = await open(file, constants.O_WRONLY | constants.O_APPEND | constants.O_CREAT | (constants.O_NOFOLLOW ?? 0), 0o600)
    const st = await handle.stat()
    if (!st.isFile() || st.uid !== uid) throw new Error("unsafe permission review file")
    if ((st.mode & 0o777) !== 0o600) await handle.chmod(0o600)
    await handle.writeFile(`${JSON.stringify(record)}\n`, "utf8")
  } finally { await handle?.close() }
}

function safeLog(record: EventRecord | undefined): void {
  if (record) void appendRecord(record).catch(() => { console.error("OpenCode permission review log write failed") })
}

const server: Plugin = async () => ({ event: async ({ event }) => {
  if (!event || typeof event !== "object") return
  const value = event as { type?: string; properties?: Record<string, any> }
  if (value.type === "permission.asked") safeLog(normalizeRecord("v1", "asked", value.properties ?? {}))
  if (value.type === "permission.replied") safeLog(normalizeRecord("v1", "replied", value.properties ?? {}))
} })

export default {
  id: "permission-review-log",
  server,
  setup(ctx: V2Context) {
    const controller = new AbortController()
    void (async () => {
      for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
        try {
          const kind = event.type === "permission.v2.asked" ? "asked" : event.type === "permission.v2.replied" ? "replied" : undefined
          if (kind) safeLog(normalizeRecord("v2", kind, event.properties ?? {}))
        } catch { console.error("OpenCode permission review event ignored") }
      }
    })().catch(() => { console.error("OpenCode permission review event stream stopped") })
    return () => controller.abort()
  },
}
