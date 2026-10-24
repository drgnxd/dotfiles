import { lstat, mkdir, open } from "node:fs/promises"
import { constants } from "node:fs"
import { homedir, userInfo } from "node:os"
import { join } from "node:path"
import type { Plugin } from "@opencode-ai/plugin"

type Generation = "v1" | "v2"
type AskedRecord = { timestamp: string; generation: Generation; kind: "asked"; request_id: string; permission: string; action: string; candidates: string[]; candidates_redacted: number }
type RepliedRecord = { timestamp: string; generation: Generation; kind: "replied"; request_id: string; reply: string }
type EventRecord = AskedRecord | RepliedRecord
type V2Event = { type: string; data?: Record<string, unknown> }
type V2Context = { event: { subscribe(options: { signal: AbortSignal }): AsyncIterable<V2Event> } }

const sensitive = /(?:https?:\/\/[^\s/:@]+:[^\s/@]+@|(?:authorization|bearer|password|passwd|token|secret|api[_-]?key)\s*[:=]\s*\S|\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}))/i
const containsCredential = (candidate: string) => sensitive.test(candidate)

export function normalizeRecord(generation: Generation, kind: "asked" | "replied", data: Record<string, unknown>, timestamp = new Date().toISOString()): EventRecord | undefined {
  const requestId = kind === "asked" ? data.id : data.requestID
  if (typeof requestId !== "string" || requestId.length === 0) return
  if (kind === "replied") {
    const reply = data.reply
    return typeof reply === "string" ? { timestamp, generation, kind, request_id: requestId, reply } : undefined
  }

  const permission = generation === "v1" ? data.permission : data.permission ?? data.action
  const action = generation === "v1" ? "ask" : data.action
  if (typeof permission !== "string" || typeof action !== "string") return
  const raw = generation === "v1" ? data.always : data.save
  const candidates = Array.isArray(raw) ? [...new Set(raw.filter((value): value is string => typeof value === "string"))].sort() : []
  const safeCandidates = candidates.filter((candidate) => !containsCredential(candidate))
  return {
    timestamp,
    generation,
    kind,
    request_id: requestId,
    permission,
    action,
    candidates: safeCandidates,
    candidates_redacted: candidates.length - safeCandidates.length,
  }
}

export async function appendRecord(record: EventRecord): Promise<void> {
  const stateHome = process.env.XDG_STATE_HOME ?? join(homedir(), ".local", "state")
  const directory = join(stateHome, "opencode", "permission-review")
  const file = join(directory, "events.jsonl")
  const uid = Number(userInfo().uid)
  await mkdir(directory, { recursive: true, mode: 0o700 })
  const directoryStat = await lstat(directory)
  if (directoryStat.isSymbolicLink() || !directoryStat.isDirectory() || directoryStat.uid !== uid) throw new Error("unsafe permission review directory")
  const directoryHandle = await open(directory, constants.O_RDONLY | (constants.O_DIRECTORY ?? 0) | (constants.O_NOFOLLOW ?? 0))
  try {
    const openedDirectoryStat = await directoryHandle.stat()
    if (!openedDirectoryStat.isDirectory() || openedDirectoryStat.uid !== uid) throw new Error("unsafe permission review directory")
    if ((openedDirectoryStat.mode & 0o777) !== 0o700) await directoryHandle.chmod(0o700)
  } finally {
    await directoryHandle.close()
  }
  let handle
  try {
    try {
      const fileStat = await lstat(file)
      if (fileStat.isSymbolicLink() || !fileStat.isFile() || fileStat.uid !== uid) throw new Error("unsafe permission review file")
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error
    }
    handle = await open(file, constants.O_WRONLY | constants.O_APPEND | constants.O_CREAT | (constants.O_NOFOLLOW ?? 0), 0o600)
    const fileStat = await handle.stat()
    if (!fileStat.isFile() || fileStat.uid !== uid) throw new Error("unsafe permission review file")
    if ((fileStat.mode & 0o777) !== 0o600) await handle.chmod(0o600)
    await handle.writeFile(`${JSON.stringify(record)}\n`, "utf8")
  } finally {
    await handle?.close()
  }
}

async function safeLog(record: EventRecord | undefined): Promise<void> {
  if (!record) return
  try {
    await appendRecord(record)
  } catch {
    console.error("OpenCode permission review log write failed")
  }
}

const server: Plugin = async () => ({
  event: async ({ event }) => {
    if (!event || typeof event !== "object") return
    const value = event as { type?: string; properties?: Record<string, unknown> }
    if (value.type === "permission.asked") await safeLog(normalizeRecord("v1", "asked", value.properties ?? {}))
    if (value.type === "permission.replied") await safeLog(normalizeRecord("v1", "replied", value.properties ?? {}))
  },
})

export default {
  id: "permission-review-log",
  server,
  setup(ctx: V2Context) {
    const controller = new AbortController()
    void (async () => {
      for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
        try {
          const kind = event.type === "permission.v2.asked" ? "asked" : event.type === "permission.v2.replied" ? "replied" : undefined
          if (kind) await safeLog(normalizeRecord("v2", kind, event.data ?? {}))
        } catch {
          console.error("OpenCode permission review event ignored")
        }
      }
    })().catch(() => console.error("OpenCode permission review event stream stopped"))
    return () => controller.abort()
  },
}
