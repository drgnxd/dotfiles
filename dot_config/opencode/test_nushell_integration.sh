#!/usr/bin/env bash
set -euo pipefail

readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_RESET='\033[0m'

print_ok() { printf "${COLOR_GREEN}✓${COLOR_RESET} %s\n" "$*"; }
print_err() { printf "${COLOR_RED}✗${COLOR_RESET} %s\n" "$*"; }

cd "$(dirname "$0")"

echo "=== Nushell Skill Integration Tests ==="
echo

# Test 1: YAML syntax
echo "Test 1: YAML syntax validation"
if uv run python -c "import yaml; yaml.safe_load(open('skills/essential/languages.yaml'))" 2>/dev/null; then
	print_ok "languages.yaml is valid"
else
	print_err "languages.yaml has syntax errors"
	exit 1
fi

# Test 2: Catalog validation
echo "Test 2: Catalog validation"
if make validate >/dev/null 2>&1; then
	print_ok "Catalog is valid"
else
	print_err "Catalog validation failed"
	exit 1
fi

# Test 3: Nushell skill loading
echo "Test 3: Nushell skill loading"
if uv run python -c "
from skills_loader import SkillsLoader
result = SkillsLoader().load_for_task('Create a nushell script')
assert 'nushell' in result.lower()
" 2>/dev/null; then
	print_ok "Nushell skill loads correctly"
else
	print_err "Nushell skill not loaded"
	exit 1
fi

# Test 4: Token budget
echo "Test 4: Token budget check"
if uv run python -c "
from skills_loader import SkillsLoader
import re
result = SkillsLoader().load_for_task('Design nushell pipeline')
match = re.search(r'Tokens used: (\d+)/(\d+)', result)
used, limit = int(match.group(1)), int(match.group(2))
assert used <= limit
print(f'{used}/{limit}')
" 2>/dev/null; then
	print_ok "Token budget OK"
else
	print_err "Token budget exceeded"
	exit 1
fi

# Test 5: Existing tests
echo "Test 5: Regression tests"
if make test >/dev/null 2>&1; then
	print_ok "Existing tests pass"
else
	print_err "Regression detected"
	exit 1
fi

echo
print_ok "All tests passed - Nushell skill integration successful"
