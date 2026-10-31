import { expect, test } from "bun:test"
import { tool } from "@opencode-ai/plugin"
import fetchPdf from "../tools/fetch_pdf"

test("fetch_pdf retains the plugin tool and schema contract", () => {
  expect(tool(fetchPdf)).toBe(fetchPdf)
  expect(fetchPdf.args.url.safeParse("https://example.com/file.pdf").success).toBe(true)
  expect(fetchPdf.args.url.safeParse(42).success).toBe(false)
  expect(fetchPdf.args.timeout.safeParse(undefined).success).toBe(true)
  expect(fetchPdf.args.timeout.safeParse(30).success).toBe(true)
  expect(fetchPdf.args.timeout.safeParse("30").success).toBe(false)
  expect(typeof fetchPdf.execute).toBe("function")
})
