const ID = /^[A-Za-z0-9_-]{8,128}$/
const ENV_KEYS = ["PATH", "HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "ZELLIJ_SESSION_NAME", "ZELLIJ_PANE_ID"] as const

export type PermissionPost = (input: { path: { id: string; permissionID: string }; body: { response: "once" | "reject" } }) => Promise<unknown>

export function helperEnv(clientName: string, sessionID?: string): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {}
  for (const key of ENV_KEYS) {
    if (process.env[key] !== undefined) env[key] = process.env[key]
  }
  env.AGENT_INBOX_CLIENT = clientName
  if (sessionID) env.OPENCODE_SESSION_ID = sessionID
  return env
}

export function responseForDecision(decision: string): "once" | "reject" | undefined {
  return decision === "allow" ? "once" : decision === "deny" ? "reject" : undefined
}

export async function respondToPermission(postPermission: PermissionPost, sessionID: string, permissionID: string, decision: string): Promise<void> {
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

export function safeAsked(value: unknown): { sessionID: string; permissionID: string; toolName: string } | undefined {
  if (typeof value !== "object" || value === null) return
  const event = value as { id?: unknown; sessionID?: unknown; permission?: unknown }
  if (typeof event.sessionID !== "string" || !event.sessionID || typeof event.id !== "string" || !ID.test(event.id)) return
  if (typeof event.permission !== "string" || !/^[A-Za-z0-9_.:-]{1,128}$/.test(event.permission)) return
  return { sessionID: event.sessionID, permissionID: event.id, toolName: event.permission }
}
