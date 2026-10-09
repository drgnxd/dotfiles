import type { Plugin } from "@opencode-ai/plugin"

export const SessionEnvPlugin: Plugin = async () => ({
  "shell.env": async (input, output) => {
    output.env.OPENCODE_SESSION_ID = input.sessionID ?? ""
  },
})

export default SessionEnvPlugin
