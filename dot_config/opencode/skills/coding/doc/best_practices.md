# Language-Specific Best Practices

## Python

### Module Structure
```python
"""Module summary."""

import os
import sys

DEFAULT_TIMEOUT = 30


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Virtual Environments
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Dependencies
```text
requirements.txt
pyproject.toml
```

## Shell Script

### Template
```bash
#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

main() {
    local arg1="$1"
    : "$arg1"
}

main "$@"
```

### Best Practices

- Always quote variables: "${var}"
- Use `set -euo pipefail`
- Keep functions small and focused

## JavaScript and TypeScript

### Modern Syntax
```javascript
const MAX_RETRIES = 3;

const sum = (a, b) => a + b;

const { name, age } = user;

const newArray = [...oldArray, newItem];
```

### Async and Await
```javascript
async function fetchData(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Fetch error:", error);
        throw error;
    }
}
```
