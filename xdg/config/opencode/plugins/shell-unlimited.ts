type ToolEvent = { tool: string; input: unknown }

export default {
  id: "shell-unlimited",
  async setup(ctx: { tool: { hook(name: "execute.before", callback: (event: ToolEvent) => void): unknown } }) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "shell" || event.input === null || typeof event.input !== "object") return
      const input = event.input as { timeout?: unknown }
      if (input.timeout === undefined) input.timeout = 0
    })
  },
}
