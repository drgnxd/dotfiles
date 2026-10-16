import { expect, mock, test } from "bun:test"

mock.module("@opencode-ai/plugin", () => ({
  tool: Object.assign((definition: unknown) => definition, {
    schema: {
      string: () => ({ describe: () => ({}) }),
      number: () => ({ optional: () => ({ describe: () => ({}) }) }),
    },
  }),
}))

const { fetchAndReadPdf, readBoundedPdf, validatePdfUrl } = await import("../tools/fetch_pdf")

test("accepts HTTP(S) PDF URLs, matching webfetch", () => {
  expect(validatePdfUrl("https://example.org/report.pdf").hostname).toBe("example.org")
  expect(validatePdfUrl("http://example.org/report.pdf").hostname).toBe("example.org")
  expect(() => validatePdfUrl("file:///tmp/report.pdf")).toThrow("http:// or https://")
})

test("follows redirects using standard webfetch behavior", async () => {
  let requestUrl = ""
  let requestInit: RequestInit | undefined
  const fetcher: typeof fetch = async (url, init) => {
    requestUrl = String(url)
    requestInit = init
    return new Response("%PDF-1.7", {
      headers: { "content-type": "application/pdf" },
    })
  }
  const { response } = await fetchAndReadPdf(new URL("https://example.org/report.pdf"), 30, fetcher)
  expect(requestUrl).toBe("https://example.org/report.pdf")
  expect(requestInit?.redirect).toBe("follow")
  expect(response.ok).toBe(true)
})

test("accepts recognized PDF MIME types with PDF magic bytes", async () => {
  for (const contentType of ["application/pdf", "application/octet-stream", "application/x-pdf"]) {
    const response = new Response("%PDF-1.7\nbody", { headers: { "content-type": contentType } })
    const bytes = await readBoundedPdf(response)
    expect(new TextDecoder().decode(bytes.subarray(0, 5))).toBe("%PDF-")
  }
})

test("rejects non-PDF payloads and response types", async () => {
  await expect(
    readBoundedPdf(new Response("<html>", { headers: { "content-type": "text/html" } })),
  ).rejects.toThrow("Expected a PDF")
  await expect(
    readBoundedPdf(new Response("not PDF", { headers: { "content-type": "application/pdf" } })),
  ).rejects.toThrow("magic bytes")
})

test("enforces the response cap while streaming", async () => {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new Uint8Array(5 * 1024 * 1024))
      controller.enqueue(new Uint8Array([1]))
      controller.close()
    },
  })
  const response = new Response(body, { headers: { "content-type": "application/pdf" } })
  await expect(readBoundedPdf(response)).rejects.toThrow("5 MiB")
})
