import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Search the web with the local SearXNG instance",
  args: {
    search_query: tool.schema.string().describe("The search query"),
  },
  async execute(args) {
    const url = new URL("http://localhost:8080/search")
    url.searchParams.set("q", args.search_query)
    url.searchParams.set("format", "json")

    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`SearXNG request failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return JSON.stringify(data)
  },
})
