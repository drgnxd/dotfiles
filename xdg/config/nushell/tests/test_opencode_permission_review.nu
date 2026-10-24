use ../autoload/09-opencode-permission-review.nu [normalize-review-rows review-rows]
use std/assert

let rows = [
  { timestamp: '2026-01-01T00:00:00.000Z', generation: v1, kind: asked, request_id: a, permission: edit, action: ask, candidates: [z a], candidates_redacted: 1 }
  { timestamp: '2026-01-01T00:00:00.000Z', generation: v1, kind: asked, request_id: a, permission: edit, action: ask, candidates: [a z], candidates_redacted: 1 }
  { timestamp: '2026-01-03T00:00:00.000Z', generation: v1, kind: replied, request_id: a, reply: always }
  { timestamp: '2026-01-03T00:00:01.000Z', generation: v1, kind: replied, request_id: a, reply: always }
  { timestamp: '2026-01-04T00:00:00.000Z', generation: v1, kind: replied, request_id: orphan, reply: reject }
  { timestamp: '2026-01-01T02:00:00.000Z', generation: v2, kind: asked, request_id: b, permission: bash, action: ask, candidates: [], candidates_redacted: 2 }
  { timestamp: '2026-01-01T03:00:00.000Z', generation: v2, kind: replied, request_id: b, reply: once }
  { timestamp: '2026-01-01T03:01:00.000Z', generation: v2, kind: replied, request_id: b, reply: reject }
  { timestamp: '2026-01-01T04:00:00.000Z', generation: v1, kind: asked, request_id: c, permission: edit, action: ask, candidates: [a z], candidates_redacted: 1 }
  { timestamp: '2026-01-01T05:00:00.000Z', generation: v1, kind: replied, request_id: c, reply: once }
  { timestamp: '2026-01-01T06:00:00.000Z', generation: v1, kind: asked, request_id: d, permission: read, action: ask, candidates: [], candidates_redacted: 0 }
  { timestamp: '2026-01-01T07:00:00.000Z', generation: v1, kind: replied, request_id: d, reply: reject }
  { timestamp: '2025-12-01T00:00:00.000Z', generation: v1, kind: asked, request_id: old, permission: edit, action: ask, candidates: [old], candidates_redacted: 0 }
  { timestamp: 'not a valid row' }
  { timestamp: 'not a timestamp', generation: v1, kind: asked, request_id: bad-time, permission: edit, action: ask, candidates: [], candidates_redacted: 0 }
]

let now = ('2026-01-04T00:00:00Z' | into datetime)
let mixed = (normalize-review-rows ($rows | append [42 'unexpected' [a b] null]))
let all = (review-rows $mixed 0 $now)
let bounded = (review-rows $mixed 3 $now)
assert ($all.asked_window_start_jst | str contains '+09:00')
assert (($all.groups | where permission == edit | first).asks == 2)
assert (($all.groups | where permission == edit | first).always == 1)
assert (($all.groups | where permission == edit | first).once == 1)
assert (($all.groups | where permission == edit | first).candidates == [a z])
assert (($all.groups | where permission == bash | first).candidates == 'candidates_redacted')
assert (($all.groups | where permission == bash | first).reply_conflict == 1)
assert (($all.groups | where permission == read | first).candidates == 'no persistent candidate')
assert ($all.counts.duplicate_asks == 1)
assert ($all.counts.duplicate_replies == 1)
assert ($all.counts.conflicting_replies == 1)
assert ($all.counts.orphan_replies == 1)
assert ($all.counts.malformed_or_incomplete == 6)
assert ($all.counts.candidates_redacted == 4)
assert (($all.groups | where candidates == [old] | length) == 1)
assert (($bounded.groups | where candidates == [old] | length) == 0)
assert (($bounded.groups | where permission == edit | first).always == 1)
assert ($all.asked_window_end_jst | str contains '+09:00')
assert ($all.report_time_jst | str contains '+09:00')
assert ($all.observed_through_jst != null)
assert ($all.report_time_jst != null)
