#!/usr/bin/env bash

external_agents_trim() {
  local value=$1

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  EXTERNAL_AGENTS_TRIMMED=$value
}

external_agents_contains() {
  local needle=$1
  shift
  local value

  for value in "$@"; do
    [[ $value == "$needle" ]] && return 0
  done

  return 1
}

external_agents_error() {
  printf 'invalid external-agent manifest: %s\n' "$1" >&2
  return 1
}

external_agents_canonical_path() {
  case "$1" in
  /*) ;;
  *) return 1 ;;
  esac
  case "$1" in
  *'//'* | *'/./'* | *'/../'* | */. | */.. | *'|'* | *'#'* | *$'\r'* | *$'\n'*) return 1 ;;
  esac
  [[ $1 != *[[:cntrl:]]* ]] || return 1
  return 0
}

external_agents_load_manifest() {
  local manifest=$1
  local line label owner source deployed program0 state relaunch extra
  local key value lock_label
  local prefix='' lock_path=''
  local prefix_seen=0
  local lock_path_seen=0
  local -a labels=() owners=() sources=() deployed_paths=() programs=() states=() relaunch_flags=() locked_labels=()

  EXTERNAL_AGENT_LABELS=()
  EXTERNAL_AGENT_OWNERS=()
  EXTERNAL_AGENT_SOURCES=()
  EXTERNAL_AGENT_DEPLOYED=()
  EXTERNAL_AGENT_PROGRAMS=()
  EXTERNAL_AGENT_STATES=()
  EXTERNAL_AGENT_RELAUNCH=()
  EXTERNAL_AGENT_LOCKED_LABELS=()
  EXTERNAL_AGENT_PREFIX=''
  EXTERNAL_AGENT_LOCK_PATH=''

  [[ -f $manifest && ! -L $manifest ]] || {
    external_agents_error "manifest is missing or is not a regular file: $manifest"
    return 1
  }

  while IFS= read -r line || [[ -n $line ]]; do
    line=${line%$'\r'}
    external_agents_trim "$line"
    line=$EXTERNAL_AGENTS_TRIMMED
    [[ -n $line ]] || continue

    case "$line" in
    '# relaunch-prefix='*)
      ((prefix_seen == 0)) || {
        external_agents_error 'duplicate relaunch-prefix'
        return 1
      }
      prefix_seen=1
      value=${line#\# relaunch-prefix=}
      external_agents_trim "$value"
      value=$EXTERNAL_AGENTS_TRIMMED
      [[ $value =~ ^[A-Za-z0-9][A-Za-z0-9._-]*\.$ ]] || {
        external_agents_error 'invalid relaunch-prefix'
        return 1
      }
      prefix=$value
      ;;
    '# relaunch-lock-path='*)
      ((lock_path_seen == 0)) || {
        external_agents_error 'duplicate relaunch-lock-path'
        return 1
      }
      lock_path_seen=1
      value=${line#\# relaunch-lock-path=}
      external_agents_trim "$value"
      value=$EXTERNAL_AGENTS_TRIMMED
      external_agents_canonical_path "$value" || {
        external_agents_error 'invalid relaunch-lock-path'
        return 1
      }
      lock_path=$value
      ;;
    '# relaunch-lock-label='*)
      value=${line#\# relaunch-lock-label=}
      external_agents_trim "$value"
      lock_label=$EXTERNAL_AGENTS_TRIMMED
      [[ $lock_label =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && $lock_label != *.plist ]] || {
        external_agents_error 'invalid relaunch-lock-label'
        return 1
      }
      external_agents_contains "$lock_label" "${locked_labels[@]}" && {
        external_agents_error "duplicate relaunch-lock-label: $lock_label"
        return 1
      }
      locked_labels+=("$lock_label")
      ;;
    '# relaunch-'*)
      external_agents_error 'unknown relaunch directive'
      return 1
      ;;
    '# ' | '#'*)
      ;;
    *)
      line=${line%%#*}
      external_agents_trim "$line"
      line=$EXTERNAL_AGENTS_TRIMMED
      [[ -n $line ]] || continue
      local delimiters=${line//[^|]/}
      [[ ${#delimiters} -eq 6 ]] || {
        external_agents_error 'records must contain exactly seven pipe-separated fields'
        return 1
      }
      IFS='|' read -r label owner source deployed program0 state relaunch extra <<<"$line"
      [[ -z ${extra:-} ]] || {
        external_agents_error 'record has too many fields'
        return 1
      }
      for key in label owner source deployed program0 state relaunch; do
        external_agents_trim "${!key}"
        printf -v "$key" '%s' "$EXTERNAL_AGENTS_TRIMMED"
      done
      [[ $label =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && $label != *.plist ]] || {
        external_agents_error "invalid extensionless Label: $label"
        return 1
      }
      [[ $state == enabled || $state == disabled ]] || {
        external_agents_error "invalid desired state for $label"
        return 1
      }
      [[ $relaunch == true || $relaunch == false ]] || {
        external_agents_error "invalid relaunch flag for $label"
        return 1
      }
      [[ $state != disabled || $relaunch == false ]] || {
        external_agents_error "disabled job cannot be relaunch-enabled: $label"
        return 1
      }
      for value in "$owner" "$source" "$deployed" "$program0"; do
        external_agents_canonical_path "$value" || {
          external_agents_error "non-canonical absolute path in record for $label"
          return 1
        }
      done
      [[ $source == "$owner"/* && ${source##*/} == "$label.plist" ]] || {
        external_agents_error "source plist is outside owner or has wrong name: $label"
        return 1
      }
      external_agents_contains "$label" "${labels[@]}" && {
        external_agents_error "duplicate Label: $label"
        return 1
      }
      labels+=("$label")
      owners+=("$owner")
      sources+=("$source")
      deployed_paths+=("$deployed")
      programs+=("$program0")
      states+=("$state")
      relaunch_flags+=("$relaunch")
      ;;
    esac
  done <"$manifest"

  ((prefix_seen == 1)) || {
    external_agents_error 'missing relaunch-prefix'
    return 1
  }
  if ((lock_path_seen != 0 || ${#locked_labels[@]} > 0)); then
    ((lock_path_seen == 1 && ${#locked_labels[@]} > 0)) || {
      external_agents_error 'relaunch-lock-path and relaunch-lock-label directives must be paired'
      return 1
    }
  fi
  for lock_label in "${locked_labels[@]}"; do
    local found=0 index
    for index in "${!labels[@]}"; do
      if [[ ${labels[index]} == "$lock_label" && ${states[index]} == enabled && ${relaunch_flags[index]} == true ]]; then
        found=1
        break
      fi
    done
    ((found == 1)) || {
      external_agents_error "lock label is not an enabled relaunch target: $lock_label"
      return 1
    }
  done

  EXTERNAL_AGENT_LABELS=("${labels[@]}")
  EXTERNAL_AGENT_OWNERS=("${owners[@]}")
  EXTERNAL_AGENT_SOURCES=("${sources[@]}")
  EXTERNAL_AGENT_DEPLOYED=("${deployed_paths[@]}")
  EXTERNAL_AGENT_PROGRAMS=("${programs[@]}")
  EXTERNAL_AGENT_STATES=("${states[@]}")
  EXTERNAL_AGENT_RELAUNCH=("${relaunch_flags[@]}")
  # shellcheck disable=SC2034
  EXTERNAL_AGENT_LOCKED_LABELS=("${locked_labels[@]}")
  EXTERNAL_AGENT_PREFIX=$prefix
  # shellcheck disable=SC2034
  EXTERNAL_AGENT_LOCK_PATH=$lock_path
  return 0
}

external_agents_validate_files() {
  local launch_agents_dir=$1
  local owner source deployed program label state value git_root source_parent deployed_parent source_label deployed_label source_program deployed_program
  local index

  for index in "${!EXTERNAL_AGENT_LABELS[@]}"; do
    label=${EXTERNAL_AGENT_LABELS[index]}
    owner=${EXTERNAL_AGENT_OWNERS[index]}
    source=${EXTERNAL_AGENT_SOURCES[index]}
    deployed=${EXTERNAL_AGENT_DEPLOYED[index]}
    program=${EXTERNAL_AGENT_PROGRAMS[index]}
    state=${EXTERNAL_AGENT_STATES[index]}

    if [[ $state == enabled ]]; then
      value="$launch_agents_dir/$label.plist"
    else
      value="$launch_agents_dir/$label.plist.disabled"
    fi
    [[ $deployed == "$value" ]] || {
      EXTERNAL_AGENTS_ERROR="$label has an unexpected deployed plist path"
      return 1
    }
    git_root=$(/usr/bin/git -C "$owner" rev-parse --show-toplevel 2>/dev/null) || {
      EXTERNAL_AGENTS_ERROR="$label owner repository cannot be resolved"
      return 1
    }
    [[ $git_root == "$owner" ]] || {
      EXTERNAL_AGENTS_ERROR="$label owner path is not the canonical Git root"
      return 1
    }
    [[ -f $source && ! -L $source ]] || {
      EXTERNAL_AGENTS_ERROR="$label source plist is missing or not a regular file"
      return 1
    }
    [[ -f $deployed && ! -L $deployed ]] || {
      EXTERNAL_AGENTS_ERROR="$label deployed plist is missing or not a regular file"
      return 1
    }
    source_parent=$(cd -- "${source%/*}" && pwd -P) || {
      EXTERNAL_AGENTS_ERROR="$label source directory cannot be resolved"
      return 1
    }
    deployed_parent=$(cd -- "${deployed%/*}" && pwd -P) || {
      EXTERNAL_AGENTS_ERROR="$label deployed directory cannot be resolved"
      return 1
    }
    [[ "$source_parent/${source##*/}" == "$source" && "$deployed_parent/${deployed##*/}" == "$deployed" ]] || {
      EXTERNAL_AGENTS_ERROR="$label plist path is not canonical"
      return 1
    }
    if [[ $state == enabled && -e "$launch_agents_dir/$label.plist.disabled" ]] || [[ $state == disabled && -e "$launch_agents_dir/$label.plist" ]]; then
      EXTERNAL_AGENTS_ERROR="$label has conflicting enabled/disabled plist copies"
      return 1
    fi
    /usr/bin/cmp -s "$source" "$deployed" || {
      EXTERNAL_AGENTS_ERROR="$label source and deployed plists differ"
      return 1
    }
    source_label=$(/usr/bin/plutil -extract Label raw -o - "$source" 2>/dev/null) || {
      EXTERNAL_AGENTS_ERROR="$label source plist Label cannot be read"
      return 1
    }
    deployed_label=$(/usr/bin/plutil -extract Label raw -o - "$deployed" 2>/dev/null) || {
      EXTERNAL_AGENTS_ERROR="$label deployed plist Label cannot be read"
      return 1
    }
    [[ $source_label == "$label" && $deployed_label == "$label" ]] || {
      EXTERNAL_AGENTS_ERROR="$label plist Label does not match the manifest"
      return 1
    }
    source_program=$(/usr/bin/plutil -extract ProgramArguments.0 raw -o - "$source" 2>/dev/null) || {
      EXTERNAL_AGENTS_ERROR="$label source ProgramArguments[0] cannot be read"
      return 1
    }
    deployed_program=$(/usr/bin/plutil -extract ProgramArguments.0 raw -o - "$deployed" 2>/dev/null) || {
      EXTERNAL_AGENTS_ERROR="$label deployed ProgramArguments[0] cannot be read"
      return 1
    }
    [[ $source_program == "$program" && $deployed_program == "$program" ]] || {
      EXTERNAL_AGENTS_ERROR="$label ProgramArguments[0] does not match the manifest"
      return 1
    }
  done
  return 0
}

external_agents_validate_records() {
  local launch_agents_dir=$1 domain=$2
  local label state deployed path output disabled_output line
  local index

  external_agents_validate_files "$launch_agents_dir" || return 1
  for index in "${!EXTERNAL_AGENT_LABELS[@]}"; do
    label=${EXTERNAL_AGENT_LABELS[index]}
    deployed=${EXTERNAL_AGENT_DEPLOYED[index]}
    state=${EXTERNAL_AGENT_STATES[index]}

    if [[ $state == enabled ]]; then
      output=$(/bin/launchctl print "$domain/$label" 2>/dev/null) || {
        EXTERNAL_AGENTS_ERROR="$label is expected enabled but is not loaded"
        return 1
      }
      path=''
      while IFS= read -r line; do
        external_agents_trim "$line"
        line=$EXTERNAL_AGENTS_TRIMMED
        case "$line" in
        'path = '*) path=${line#path = } ;;
        esac
      done <<<"$output"
      [[ $path == "$deployed" ]] || {
        EXTERNAL_AGENTS_ERROR="$label launchctl path does not match the deployed plist"
        return 1
      }
      disabled_output=$(/bin/launchctl print-disabled "$domain" 2>/dev/null) || {
        EXTERNAL_AGENTS_ERROR="cannot query disabled state for $label"
        return 1
      }
      external_agents_get_disabled_state "$disabled_output" "$label" || {
        EXTERNAL_AGENTS_ERROR="cannot parse disabled state for $label"
        return 1
      }
      [[ $EXTERNAL_AGENTS_DISABLED_STATE != disabled ]] || {
        EXTERNAL_AGENTS_ERROR="$label is disabled in launchctl but marked enabled in the manifest"
        return 1
      }
    else
      if /bin/launchctl print "$domain/$label" >/dev/null 2>&1; then
        EXTERNAL_AGENTS_ERROR="$label is marked disabled but remains loaded"
        return 1
      fi
    fi
  done
  return 0
}

external_agents_get_disabled_state() {
  local output=$1 label=$2 line trimmed found=0 state
  local entry_pattern='^"([^"[:cntrl:]]+)"[[:space:]]+=>[[:space:]]+(enabled|disabled)$'
  local header=0 footer=0

  while IFS= read -r line; do
    external_agents_trim "$line"
    trimmed=$EXTERNAL_AGENTS_TRIMMED
    if ((header == 0)); then
      [[ -z $trimmed ]] && continue
      [[ $trimmed == 'disabled services = {' ]] || return 1
      header=1
      continue
    fi
    if [[ $trimmed == '}' ]]; then
      footer=1
      continue
    fi
    ((footer == 0)) || {
      [[ -z $trimmed ]] && continue
      return 1
    }
    [[ -n $trimmed ]] || continue
    if [[ $trimmed =~ $entry_pattern ]]; then
      if [[ ${BASH_REMATCH[1]} == "$label" ]]; then
        ((found == 0)) || return 1
        found=1
        state=${BASH_REMATCH[2]}
      fi
    else
      return 1
    fi
  done <<<"$output"
  ((header == 1 && footer == 1)) || return 1
  if ((found == 0)); then
    state=enabled
  fi
  EXTERNAL_AGENTS_DISABLED_STATE=$state
}

external_agents_recover_one() {
  local manifest=$1 launch_agents_dir=$2 domain=$3 label=$4
  local index=-1 candidate loaded_output line path disabled_output source deployed program attempt result deployed_file deployed_label loaded_label
  local -a loaded_labels=()

  external_agents_load_manifest "$manifest" || return 1
  external_agents_validate_files "$launch_agents_dir" || return 1
  external_agents_loaded_labels "$domain" || {
    EXTERNAL_AGENTS_ERROR="could not read loaded services in $domain"
    return 1
  }
  loaded_labels=("${EXTERNAL_AGENTS_LOADED_LABELS[@]}")
  for loaded_label in "${loaded_labels[@]}"; do
    case "$loaded_label" in
    "$EXTERNAL_AGENT_PREFIX"*)
      if ! external_agents_contains "$loaded_label" "${EXTERNAL_AGENT_LABELS[@]}"; then
        EXTERNAL_AGENTS_ERROR="loaded job '$loaded_label' is missing from the external inventory"
        return 1
      fi
      ;;
    esac
  done
  for deployed_file in "$launch_agents_dir"/"$EXTERNAL_AGENT_PREFIX"*.plist "$launch_agents_dir"/"$EXTERNAL_AGENT_PREFIX"*.plist.disabled; do
    [[ -e $deployed_file ]] || continue
    deployed_label=${deployed_file##*/}
    deployed_label=${deployed_label%.plist.disabled}
    deployed_label=${deployed_label%.plist}
    if ! external_agents_contains "$deployed_label" "${EXTERNAL_AGENT_LABELS[@]}"; then
      EXTERNAL_AGENTS_ERROR="deployed plist '${deployed_file##*/}' is missing from the external inventory"
      return 1
    fi
  done

  for candidate in "${!EXTERNAL_AGENT_LABELS[@]}"; do
    if [[ ${EXTERNAL_AGENT_LABELS[candidate]} == "$label" ]]; then
      index=$candidate
      break
    fi
  done
  [[ $index -ge 0 ]] || {
    EXTERNAL_AGENTS_ERROR="Label is not registered: $label"
    return 1
  }
  [[ ${EXTERNAL_AGENT_STATES[index]} == enabled && ${EXTERNAL_AGENT_RELAUNCH[index]} == true ]] || {
    EXTERNAL_AGENTS_ERROR="$label is not an enabled relaunch target"
    return 1
  }
  source=${EXTERNAL_AGENT_SOURCES[index]}
  deployed=${EXTERNAL_AGENT_DEPLOYED[index]}
  program=${EXTERNAL_AGENT_PROGRAMS[index]}

  disabled_output=$(/bin/launchctl print-disabled "$domain" 2>/dev/null) || {
    EXTERNAL_AGENTS_ERROR="cannot query disabled state for $label"
    return 1
  }
  external_agents_get_disabled_state "$disabled_output" "$label" || {
    EXTERNAL_AGENTS_ERROR="cannot parse disabled state for $label"
    return 1
  }
  [[ $EXTERNAL_AGENTS_DISABLED_STATE != disabled ]] || {
    EXTERNAL_AGENTS_ERROR="$label is disabled in launchctl"
    return 1
  }

  loaded_output=$(/bin/launchctl print "$domain/$label" 2>/dev/null || true)
  if [[ -n $loaded_output ]]; then
    path=''
    while IFS= read -r line; do
      external_agents_trim "$line"
      line=$EXTERNAL_AGENTS_TRIMMED
      case "$line" in
      'path = '*) path=${line#path = } ;;
      esac
    done <<<"$loaded_output"
    [[ $path == "$deployed" ]] || {
      EXTERNAL_AGENTS_ERROR="$label is loaded from an unexpected plist"
      return 1
    }
    printf '%s: already loaded from the expected plist; no action\n' "$label"
    return 0
  fi

  external_agents_validate_files "$launch_agents_dir" || return 1
  disabled_output=$(/bin/launchctl print-disabled "$domain" 2>/dev/null) || {
    EXTERNAL_AGENTS_ERROR="cannot recheck disabled state for $label"
    return 1
  }
  external_agents_get_disabled_state "$disabled_output" "$label" || {
    EXTERNAL_AGENTS_ERROR="cannot parse disabled state for $label"
    return 1
  }
  [[ $EXTERNAL_AGENTS_DISABLED_STATE != disabled ]] || {
    EXTERNAL_AGENTS_ERROR="$label became disabled before bootstrap"
    return 1
  }

  result=0
  for attempt in 1 2 3; do
    if /bin/launchctl bootstrap "$domain" "$deployed" 2>/dev/null; then
      result=1
      break
    fi
    /bin/sleep "$((attempt * 3))"
  done
  [[ $result -eq 1 ]] || {
    EXTERNAL_AGENTS_ERROR="$label bootstrap failed; it may remain unloaded"
    return 1
  }

  loaded_output=$(/bin/launchctl print "$domain/$label" 2>/dev/null) || {
    EXTERNAL_AGENTS_ERROR="$label bootstrap returned but the service is still unloaded"
    return 1
  }
  path=''
  while IFS= read -r line; do
    external_agents_trim "$line"
    line=$EXTERNAL_AGENTS_TRIMMED
    case "$line" in
    'path = '*) path=${line#path = } ;;
    esac
  done <<<"$loaded_output"
  [[ $path == "$deployed" ]] || {
    EXTERNAL_AGENTS_ERROR="$label bootstrap loaded an unexpected plist"
    return 1
  }
  disabled_output=$(/bin/launchctl print-disabled "$domain" 2>/dev/null) || {
    EXTERNAL_AGENTS_ERROR="cannot verify disabled state after bootstrapping $label"
    return 1
  }
  external_agents_get_disabled_state "$disabled_output" "$label" || {
    EXTERNAL_AGENTS_ERROR="cannot parse disabled state after bootstrapping $label"
    return 1
  }
  [[ $EXTERNAL_AGENTS_DISABLED_STATE != disabled ]] || {
    # shellcheck disable=SC2034
    EXTERNAL_AGENTS_ERROR="$label became disabled during bootstrap"
    return 1
  }
  printf '%s: recovered from the expected plist; sentinel unchanged\n' "$label"
}

external_agents_loaded_labels() {
  local domain=$1 output line in_services=0 found_services=0 found_end=0
  local -a labels=()

  output=$(/bin/launchctl print "$domain" 2>/dev/null) || return 1
  while IFS= read -r line; do
    if ((in_services == 0)); then
      if [[ $line =~ ^[[:space:]]services[[:space:]]\=[[:space:]]\{$ ]]; then
        in_services=1
        found_services=1
      fi
      continue
    fi
    if [[ $line =~ ^[[:space:]]\}$ ]]; then
      found_end=1
      break
    fi
    if [[ $line =~ ^[[:space:]]*([0-9]+)[[:space:]]+([^[:space:]]+)[[:space:]]+([A-Za-z0-9._-]+)[[:space:]]*$ ]]; then
      labels+=("${BASH_REMATCH[3]}")
    fi
  done <<<"$output"
  ((found_services == 1 && found_end == 1)) || return 1
  EXTERNAL_AGENTS_LOADED_LABELS=("${labels[@]}")
}
