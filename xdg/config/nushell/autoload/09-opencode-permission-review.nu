export def review-rows [rows: list<record>, days: int, now: datetime] {
    let asks = ($rows | where kind == asked)
    let replies = ($rows | where kind == replied)
    let observed = ($rows | get timestamp | sort | last)
    let cutoff = if $days == 0 { null } else { $now - ($days * 24hr) }
    let relevant = if $cutoff == null { $asks } else { $asks | where (($in.timestamp | into datetime) >= $cutoff) }
    let joined = ($relevant | each {|ask|
      let matching = ($replies | where {|reply| $reply.generation == $ask.generation and $reply.request_id == $ask.request_id })
      let outcome = if ($matching | is-empty) { 'reply_not_observed' } else if (($matching | get action | uniq | length) > 1) { 'reply_conflict' } else { $matching | first | get action }
      { permission: $ask.permission, action: $ask.action, candidates: ($ask.candidates? | default []), redacted: ($ask.candidates_redacted? | default false), outcome: $outcome, first: $ask.timestamp, last: $ask.timestamp }
    })
    { observed_through: $observed, groups: ($joined | group-by {|row| [$row.permission, $row.action, ($row.candidates | to nuon), $row.redacted, $row.outcome] } | transpose key values | each {|group| let vals = $group.values; { permission: $vals.0.permission, action: $vals.0.action, candidates: (if $vals.0.redacted { 'candidates_redacted' } else if ($vals.0.candidates | is-empty) { 'no persistent candidate' } else { $vals.0.candidates | to nuon }), outcome: $vals.0.outcome, asks: ($vals | length), first_asked: ($vals | get first | sort | first), last_asked: ($vals | get last | sort | last) } }) }
}

export def oc-permission-review [days: int = 30] {
  if $days < 0 { error make {msg: 'days must be zero or greater'} }
  let path = ($env.XDG_STATE_HOME? | default ($nu.home-path | path join '.local/state') | path join 'opencode/permission-review/events.jsonl')
  if not ($path | path exists) { print 'No permission review log found.'; return }
  let parsed = (open --raw $path | lines | each {|line| try { $line | from json } catch { null } })
  let rows = ($parsed | where {|row| $row != null and ($row | get -o timestamp) != null and ($row | get -o generation) != null and ($row | get -o request_id) != null and ($row | get -o kind) != null and ($row | get -o permission) != null and ($row | get -o action) != null })
  let report = (review-rows $rows $days (date now))
  $report
}
