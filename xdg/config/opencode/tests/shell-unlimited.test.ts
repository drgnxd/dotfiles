import { expect, test } from "bun:test"
import plugin from "../plugins/shell-unlimited"

test("only unspecified shell timeouts become unlimited", async () => {
  let hook: (event: { tool: string; input: unknown }) => void = () => { throw new Error("hook not registered") }
  await plugin.setup({ tool: { hook: (_name, callback) => { hook = callback } } })

  const omitted: { command: string; timeout?: number } = { command: "echo ok" }
  hook({ tool: "shell", input: omitted })
  expect(omitted.timeout).toBe(0)

  for (const timeout of [0, 1, 120000]) {
    const input = { command: "echo ok", timeout }
    hook({ tool: "shell", input })
    expect(input.timeout).toBe(timeout)
  }

  const other: { timeout?: number } = {}
  hook({ tool: "other", input: other })
  expect(other.timeout).toBeUndefined()
  hook({ tool: "shell", input: null })
})
