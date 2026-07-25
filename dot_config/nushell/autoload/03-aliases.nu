# requires: 00-helpers

export def --wrapped g [...args] {
    cmd-or-fallback rg grep ...$args
}

export def --wrapped f [...args] {
    cmd-or-fallback fd find ...$args
}

export def --wrapped cat [...args] {
    cmd-or-fallback bat cat --primary-args ["--paging=never" "--color=auto"] ...$args
}

export alias .. = cd ..
export alias ... = cd ../..
export alias .... = cd ../../..

export alias c = clear

export def --wrapped cp [...args] {
    ^cp -i ...$args
}

export def --wrapped mv [...args] {
    ^mv -i ...$args
}

export def --wrapped rm [...args] {
    # Skip -i if -f/--force is specified to allow non-interactive removal
    if ($args | any { $in == "-f" or $in == "--force" }) {
        ^rm ...$args
    } else {
        ^rm -i ...$args
    }
}

export def --wrapped la [...args] {
    let paths = ($args | default [])
    if ($paths | is-empty) {
        ls -a
    } else {
        ls -a ...$paths
    }
}

export def --wrapped ld [...args] {
    let paths = ($args | default [])
    if ($paths | is-empty) {
        ls | where type == dir
    } else {
        ls ...$paths | where type == dir
    }
}

export def --wrapped lf [...args] {
    let paths = ($args | default [])
    if ($paths | is-empty) {
        ls | where type == file
    } else {
        ls ...$paths | where type == file
    }
}

export def --wrapped lsize [...args] {
    let paths = ($args | default [])
    if ($paths | is-empty) {
        ls | sort-by size -r
    } else {
        ls ...$paths | sort-by size -r
    }
}

export def --wrapped lg [...args] {
    require-cmd lazygit
    lazygit ...$args
}

export def --wrapped oc [...args] {
    require-cmd opencode
    opencode ...$args
}

export def --wrapped ocd [...args] {
    require-cmd opencode
    opencode --continue ...$args
}

export def --wrapped pload [...args] {
    require-cmd pass-cli
    pass-cli ssh-agent load ...$args
}
