export def review-rows [rows: list<record>, days: int, now: datetime] {
  let valid = ($rows | where {|row| try { ($row.kind in ['asked' 'replied']) and ($row.generation in ['v1' 'v2']) and ($row.request_id | str length) > 0 and (($row.timestamp | into datetime) != null) and (if $row.kind == 'asked' { ($row.permission | str length) > 0 and ($row.action | str length) > 0 and ($row.candidates | describe | str starts-with 'list') and ($row.candidates_redacted | into int) >= 0 } else { $row.reply in ['once' 'always' 'reject'] }) } catch { false } })
  let asks = ($valid | where kind == asked)
  let replies = ($valid | where kind == replied)
  let malformed = ($rows | length) - ($valid | length)
  let requestKeys = ($asks | each {|row| [$row.generation $row.request_id] | to nuon } | uniq)
  let duplicateAsks = ($asks | length) - ($requestKeys | length)
  let replyGroups = ($replies | group-by {|row| [$row.generation $row.request_id] | to nuon })
  let duplicateReplies = ($replyGroups | values | each {|group| ($group | length) - ($group | get reply | uniq | length) } | math sum | default 0)
  let orphanReplies = ($replies | where {|row| not ($requestKeys | any {|key| $key == ([$row.generation $row.request_id] | to nuon) }) } | length)
  let cutoff = if $days == 0 { null } else { $now - ($days * 24hr) }
  let firstAsks = ($asks | group-by {|row| [$row.generation $row.request_id] | to nuon } | values | each {|group| $group | first })
  let askedWindow = if $cutoff == null { $firstAsks } else { $firstAsks | where {|row| ($row.timestamp | into datetime) >= $cutoff } }
  let requests = ($askedWindow | each {|ask|
    let replyGroup = ($replyGroups | get -o ([ $ask.generation $ask.request_id ] | to nuon) | default [])
    let distinctReplies = ($replyGroup | get -o reply? | default [] | uniq)
    let outcome = if ($distinctReplies | length) == 0 { 'reply_not_observed' } else if ($distinctReplies | length) > 1 { 'reply_conflict' } else { $distinctReplies | first }
    let suggestions = ($ask.candidates | sort | uniq)
    let candidateClass = if (($ask.candidates_redacted | into int) > 0 and ($suggestions | is-empty)) { 'redacted' } else if ($suggestions | is-empty) { 'none' } else { 'listed' }
    { generation: $ask.generation, request_id: $ask.request_id, permission: $ask.permission, action: $ask.action, candidates: $suggestions, redacted: $ask.candidates_redacted, candidate_class: $candidateClass, outcome: $outcome, timestamp: ($ask.timestamp | into datetime) }
  })
  let grouped = ($requests | group-by {|row| [$row.permission $row.action $row.candidates $row.redacted $row.candidate_class] | to nuon } | values | each {|group|
    let first = ($group | get timestamp | sort | first)
    let last = ($group | get timestamp | sort | last)
    { permission: $group.0.permission, action: $group.0.action, candidates: (if $group.0.candidate_class == 'redacted' { 'candidates_redacted' } else if $group.0.candidate_class == 'none' { 'no persistent candidate' } else { $group.0.candidates }), candidates_redacted: $group.0.redacted, asks: ($group | length), once: ($group | where outcome == once | length), always: ($group | where outcome == always | length), reject: ($group | where outcome == reject | length), reply_not_observed: ($group | where outcome == reply_not_observed | length), reply_conflict: ($group | where outcome == reply_conflict | length), first_asked: ($first | date to-timezone Asia/Tokyo | format date '%Y-%m-%d %H:%M:%S %Z'), last_asked: ($last | date to-timezone Asia/Tokyo | format date '%Y-%m-%d %H:%M:%S %Z') }
  })
  let windowStart = if $cutoff == null { if ($firstAsks | is-empty) { null } else { $firstAsks | get timestamp | each {|value| $value | into datetime } | sort | first | date to-timezone Asia/Tokyo | format date '%Y-%m-%d %H:%M:%S %Z' } } else { $cutoff | date to-timezone Asia/Tokyo | format date '%Y-%m-%d %H:%M:%S %Z' }
  { asked_window_start_jst: $windowStart, asked_window_end_jst: ($now | date to-timezone Asia/Tokyo | format date '%Y-%m-%d %H:%M:%S %Z'), observed_through_jst: (if ($valid | is-empty) { null } else { $valid | get timestamp | each {|value| $value | into datetime } | sort | last | date to-timezone Asia/Tokyo | format date '%Y-%m-%d %H:%M:%S %Z' }), report_time_jst: ($now | date to-timezone Asia/Tokyo | format date '%Y-%m-%d %H:%M:%S %Z'), counts: { duplicate_asks: $duplicateAsks, duplicate_replies: $duplicateReplies, conflicting_replies: ($replyGroups | values | where {|group| ($group | get reply | uniq | length) > 1 } | length), orphan_replies: $orphanReplies, malformed_or_incomplete: $malformed, asks: ($askedWindow | length), candidates_redacted: (if ($requests | is-empty) { 0 } else { $requests | get redacted | math sum }) }, groups: $grouped }
}

export def normalize-review-rows [rows] {
  $rows | each {|row| if ($row | describe | str starts-with 'record') { $row } else { { malformed: true } } }
}

# Review the local permission log without passing it to OpenCode model context.
# Credential filtering is best-effort; same-user code can still read the file.
# Data is retained indefinitely until the user manually removes the log.
export def oc-permission-review [days: int = 30] {
  if $days < 0 { error make {msg: 'days must be zero or greater'} }
  let stateHome = ($env.XDG_STATE_HOME? | default ($nu.home-path | path join '.local/state'))
  let path = ($stateHome | path join 'opencode/permission-review/events.jsonl')
  if not ($path | path exists) { print 'No permission review log found.'; return }
  let parsed = (open --raw $path | lines | each {|line| try { $line | from json } catch { null } })
  let report = (review-rows (normalize-review-rows $parsed) $days (date now))
  $report
}
