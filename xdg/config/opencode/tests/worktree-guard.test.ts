import { expect, test } from "bun:test"
import type { SpawnSyncReturns } from "node:child_process"
import { lstat, mkdtemp, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import plugin, { guardReason } from "../plugins/worktree-guard"

test("guard timeout blocks while normal verdicts and other failures retain their behavior", () => {
  const timeout = Object.assign(new Error("timeout"), { code: "ETIMEDOUT" })
  const result = (status: number | null, stdout: string, error?: Error) => ({ status, stdout, error }) as SpawnSyncReturns<string>
  let calls = 0
  const run = (_command: string, _args: string[], options: { timeout?: number }) => {
    calls++
    expect(options.timeout).toBe(15000)
    return result(null, "", timeout)
  }
  expect(guardReason("Read", {}, "/", run)).toBeUndefined()
  expect(calls).toBe(0)
  expect(guardReason("shell", {}, "/", run)).toContain("operation blocked")
  expect(guardReason("shell", {}, "/", () => { throw timeout })).toContain("operation blocked")
  expect(guardReason("edit", {}, "/", () => result(0, '{"block":false}'))).toBeUndefined()
  expect(guardReason("edit", {}, "/", () => result(0, '{"block":true,"reason":"denied"}'))).toBe("denied")
  expect(guardReason("edit", {}, "/", () => result(1, ""))).toBeUndefined()
  expect(guardReason("edit", {}, "/", () => result(0, "invalid"))).toBeUndefined()
})

test("V2 hook blocks a real timed-out guard subprocess", async () => {
  const dir = await mkdtemp(join(tmpdir(), "worktree-guard-timeout-"))
  const previousPath = process.env.PATH
  const fake = join(dir, "python3")
  let hook: (event: { tool: string; input: unknown }) => void = () => { throw new Error("hook not registered") }
  try {
    await writeFile(fake, "#!/bin/sh\nexec /bin/sleep 30\n", { mode: 0o700 })
    process.env.PATH = dir
    await plugin.setup({ location: { directory: dir }, tool: { hook: (_name, callback) => { hook = callback } } })
    expect(() => hook({ tool: "Read", input: {} })).not.toThrow()
    expect(() => hook({ tool: "shell", input: { command: "git status" } })).toThrow("guard timed out after 15 seconds")
  } finally {
    if (previousPath === undefined) delete process.env.PATH
    else process.env.PATH = previousPath
    expect((await lstat(dir)).isDirectory()).toBe(true)
    await rm(dir, { recursive: true })
  }
}, 25000)
