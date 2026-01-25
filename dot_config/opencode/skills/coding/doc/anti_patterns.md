# Anti-Patterns to Avoid

## God Objects

Bad:
```python
class Application:
    def __init__(self):
        self.db = Database()
        self.cache = Cache()
        self.logger = Logger()
        self.email = EmailService()
```

Guideline: split large objects into focused services.

## Premature Optimization

Bad:
```python
def parse(items):
    return [item for item in items if item is not None]
```

Guideline: write clear code first, then optimize after measuring.

## Magic Numbers

Bad:
```python
if user.age > 18:
    allow_access()
```

Good:
```python
LEGAL_AGE = 18
if user.age > LEGAL_AGE:
    allow_access()
```
