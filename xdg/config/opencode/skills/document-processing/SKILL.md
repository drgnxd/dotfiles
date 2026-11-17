---
name: document-processing
description: Use for substantial reading, transformation or verification of PDF and other document files, including routing a PDF to pdf-reader or researcher.
---

# Document Processing

Determine format, provenance and whether text or visual layout carries the evidence. Cite page or section identifiers for consequential claims. Avoid assuming unextracted tables or images are absent. For local PDFs use the existing isolated pdf-reader agent; do not silently broaden its file permissions. For non-PDF sources use the appropriate supported reader and record any extraction limitations.

## Routing PDFs

- Delegate a user-supplied local PDF's exact path and question to `pdf-reader`; for multi-source research, run that analysis alongside independent web research when practical.
- Keep local PDFs and their contents with the network-disabled `pdf-reader`; fetch web-hosted PDFs through `researcher` (`fetch_pdf` in OpenCode; `WebFetch` in Claude Code, which returns a processed summary rather than full text), and pass network researchers only the minimum non-sensitive research brief.
