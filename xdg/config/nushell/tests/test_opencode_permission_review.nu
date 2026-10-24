use ../autoload/09-opencode-permission-review.nu review-rows
use std/assert

let rows = [
  { timestamp: '2026-01-01T00:00:00.000Z', generation: v1, kind: asked, request_id: a, permission: edit, action: ask, candidates: [x] }
  { timestamp: '2026-01-01T00:01:00.000Z', generation: v1, kind: replied, request_id: a, permission: edit, action: always }
  { timestamp: '2026-01-02T00:00:00.000Z', generation: v2, kind: asked, request_id: b, permission: bash, action: ask, candidates_redacted: true }
  { timestamp: '2026-01-02T00:01:00.000Z', generation: v2, kind: replied, request_id: b, permission: bash, action: once }
  { timestamp: '2026-01-02T00:02:00.000Z', generation: v2, kind: replied, request_id: b, permission: bash, action: reject }
]
let report = (review-rows $rows 0 ('2026-01-03T00:00:00Z' | into datetime))
assert ($report.observed_through == '2026-01-02T00:02:00.000Z')
assert (($report.groups | where outcome == always | length) == 1)
assert (($report.groups | where outcome == reply_conflict | length) == 1)
assert (($report.groups | where candidates == candidates_redacted | length) == 1)
