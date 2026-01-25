# Clean Code Basics

## Principles

- Use meaningful names that reveal intent.
- Keep functions short and focused.
- Prefer explicit behavior over implicit side effects.
- Limit dependencies and avoid hidden global state.
- Keep modules cohesive and responsibilities clear.

## Example: Focused Functions

Good:
```python
def read_file(path: str) -> str:
    with open(path) as handle:
        return handle.read()


def parse_json(text: str) -> dict:
    return json.loads(text)
```

Bad:
```python
def read_and_parse(path: str) -> dict:
    with open(path) as handle:
        return json.loads(handle.read())
```

## Checklist

- One reason to change per function
- Inputs and outputs are clear
- Errors are handled explicitly
- Tests cover public behavior
