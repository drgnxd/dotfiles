# Skill Examples

Real-world examples of well-structured Agent Skills.

---

## Example 1: Minimal Skill (Guidelines Only)

**Structure**:
```
naming_conventions/
└── SKILL.md
```

**SKILL.md Content**:

```markdown
---
name: naming_conventions
description: File and code naming standards for consistency across projects. Use when creating new files, variables, functions, or classes.
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Naming Conventions

Standardized naming rules for files and code elements.

## Purpose

Ensures consistency and readability across projects by enforcing uniform naming patterns.

---

## Core Principles

1. **Clarity**: Names should reveal intent
2. **Consistency**: Follow language conventions
3. **Searchability**: Avoid ambiguous abbreviations
4. **ASCII-only**: No special characters or non-English

---

## File Naming

### Rule
Use lowercase with underscores (snake_case)

**Examples**:
```
✅ Good:
user_profile.ts
calculate_total.py
api_client.go

❌ Bad:
UserProfile.ts
user-profile.ts (kebab-case discouraged for files)
```

---

## Code Naming

### JavaScript/TypeScript
```typescript
// Variables/Functions: camelCase
const userName = "Alice";
function calculateTotal() {}

// Classes/Interfaces: PascalCase
class UserProfile {}
interface ApiResponse {}

// Constants: SCREAMING_SNAKE_CASE
const MAX_RETRY = 3;
```

### Python
```python
# Variables/Functions: snake_case
user_name = "Alice"
def calculate_total():
    pass

# Classes: PascalCase
class UserProfile:
    pass

# Constants: SCREAMING_SNAKE_CASE
MAX_RETRY = 3
```

---

## Related Skills

- `code_structure`: For organizing code files
- `documentation_standards`: For documenting code

---

**Created**: 2024-01-25
```

---

## Example 2: Skill with Refs

**Structure**:
```
api_design/
├── SKILL.md
└── refs/
    ├── rest_ex.md
    └── openapi_tpl.yaml
```

**SKILL.md Content**:

```markdown
---
name: api_design
description: RESTful API design standards and conventions. Use when designing new APIs or reviewing API specifications.
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# API Design Standards

Guidelines for designing consistent, maintainable RESTful APIs.

## Purpose

Standardizes API design to improve developer experience and reduce integration issues.

---

## Core Principles

1. **Resource-Oriented**: URLs represent resources, not actions
2. **Stateless**: Each request contains all necessary information
3. **Standard Methods**: Use HTTP methods semantically
4. **Consistent Naming**: Follow predictable URL patterns

---

## URL Structure

### Rule
Use plural nouns for collections, nested resources show relationships

**Examples**:
```
✅ Good:
GET /users
GET /users/123
GET /users/123/orders
POST /users
DELETE /users/123

❌ Bad:
GET /getUsers
GET /user/123 (singular)
POST /createUser (verb in URL)
```

---

## HTTP Methods

### GET - Retrieve Resources
```
GET /users          → List all users
GET /users/123      → Get specific user
```

### POST - Create Resources
```
POST /users
Body: { "name": "Alice", "email": "alice@example.com" }
```

### PUT - Replace Resources
```
PUT /users/123
Body: { "name": "Alice Updated", "email": "alice@example.com" }
```

### PATCH - Partial Update
```
PATCH /users/123
Body: { "email": "newemail@example.com" }
```

### DELETE - Remove Resources
```
DELETE /users/123
```

---

## Response Formats

### Success Response
```json
{
  "data": {
    "id": "123",
    "name": "Alice"
  },
  "meta": {
    "timestamp": "2024-01-25T10:00:00Z"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {
        "field": "email",
        "issue": "Must be valid email"
      }
    ]
  }
}
```

---

## Examples

For comprehensive REST API examples, see [refs/rest_ex.md](refs/rest_ex.md)

For OpenAPI specification template, see [refs/openapi_tpl.yaml](refs/openapi_tpl.yaml)

---

## Related Skills

- `error_handling`: For API error responses
- `documentation_standards`: For API documentation

---

**Created**: 2024-01-25
```

**refs/rest_ex.md**:
```markdown
# REST API Examples

## User Management API

### List Users with Pagination
```http
GET /users?page=1&limit=20&sort=created_at:desc
```

Response:
```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "limit": 20
  }
}
```

(More detailed examples...)
```

---

## Example 3: Skill with Scripts

**Structure**:
```
csv_validator/
├── SKILL.md
├── scripts/
│   └── validate.py
└── refs/
    └── validation_rules.md
```

**SKILL.md Content**:

```markdown
---
name: csv_validator
description: CSV file validation rules and automated checking. Use when processing or validating CSV data files.
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: analysis
---

# CSV Validator

Standards and tools for validating CSV file integrity.

## Purpose

Ensures CSV files meet quality standards before processing, preventing data issues downstream.

---

## Core Principles

1. **Structure First**: Validate format before content
2. **Early Detection**: Catch issues before processing
3. **Clear Reporting**: Provide actionable error messages
4. **Automated**: Use scripts for consistent validation

---

## Validation Rules

### Header Validation
- Headers must be present (first row)
- No duplicate column names
- Column names: lowercase, underscore-separated
- No empty headers

### Data Validation
- No empty rows
- Consistent column count per row
- Expected data types per column
- Required fields are non-empty

---

## Usage

### Automated Validation

Run the validation script:

```bash
python scripts/validate.py --input data.csv --rules refs/validation_rules.md
```

**Options**:
- `--input`: Path to CSV file
- `--rules`: Path to validation rules (optional)
- `--strict`: Fail on warnings (default: errors only)

**Dependencies**:
- Python 3.8+
- pandas
- pyyaml

---

## Examples

### Valid CSV
```csv
user_id,name,email,age
1,Alice,alice@example.com,30
2,Bob,bob@example.com,25
```

### Invalid CSV (duplicate headers)
```csv
user_id,name,name,age
1,Alice,Smith,30
```
Error: `Duplicate column name: name`

---

## References

For detailed validation rules, see [refs/validation_rules.md](refs/validation_rules.md)

---

**Created**: 2024-01-25
```

**scripts/validate.py**:
```python
#!/usr/bin/env python3
"""
CSV Validator Script
Usage: python validate.py --input data.csv
"""

import pandas as pd
import argparse
import sys

def validate_csv(filepath):
    """Validate CSV file structure and content."""
    try:
        df = pd.read_csv(filepath)
        
        # Check for duplicate headers
        if df.columns.duplicated().any():
            print("ERROR: Duplicate column names found")
            return False
        
        # Check for empty rows
        if df.isnull().all(axis=1).any():
            print("WARNING: Empty rows detected")
        
        print("✓ CSV validation passed")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    
    success = validate_csv(args.input)
    sys.exit(0 if success else 1)
```

---

## Example 4: Process/Workflow Skill

**Structure**:
```
code_review/
└── SKILL.md
```

**SKILL.md Content**:

```markdown
---
name: code_review
description: Code review checklist and process guidelines. Use when reviewing pull requests or conducting peer reviews.
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Code Review Process

Systematic approach to reviewing code changes.

## Purpose

Ensures code quality, knowledge sharing, and catches issues before production.

---

## Core Principles

1. **Constructive**: Focus on improvement, not criticism
2. **Thorough**: Check functionality, style, and security
3. **Timely**: Review within 24 hours
4. **Educational**: Explain reasoning in comments

---

## Review Checklist

### Functionality
- [ ] Code does what it claims to do
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs or logic errors

### Code Quality
- [ ] Follows naming conventions
- [ ] Functions are single-purpose
- [ ] No code duplication (DRY)
- [ ] Complexity is reasonable

### Testing
- [ ] Tests are included for new features
- [ ] Tests cover edge cases
- [ ] All tests pass
- [ ] Test names are descriptive

### Documentation
- [ ] Code is self-documenting
- [ ] Complex logic has comments
- [ ] Public APIs are documented
- [ ] README updated if needed

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevention
- [ ] XSS prevention (if applicable)

---

## Review Process

### 1. Initial Scan (2 minutes)
- Read PR description
- Check size (< 400 lines ideal)
- Identify scope and purpose

### 2. Detailed Review (10-30 minutes)
- Go through checklist
- Leave inline comments
- Note patterns (good and bad)

### 3. Summary Comment
Provide:
- Overall assessment (Approve/Request Changes/Comment)
- Key strengths
- Critical issues (if any)
- Suggestions for improvement

### 4. Follow-up
- Respond to author's questions
- Re-review after changes
- Approve when ready

---

## Comment Templates

### Requesting Change
```
🔴 **Critical**: [Issue description]

This could cause [specific problem]. Consider [alternative approach].
```

### Suggestion
```
💡 **Suggestion**: [Improvement idea]

This would improve [aspect]. Example: [code snippet]
```

### Praise
```
✅ **Nice work**: [What was good]

This shows [positive quality]. Keep it up!
```

---

## Decision Framework

```
PR Size < 400 lines:
  → Full detailed review

PR Size 400-800 lines:
  → Request split if possible
  → Focus on high-risk areas

PR Size > 800 lines:
  → Request split into smaller PRs
  → High-level architecture review only
```

---

## Related Skills

- `naming_conventions`: For checking names
- `code_structure`: For organizational standards
- `testing_guidelines`: For test quality

---

**Created**: 2024-01-25
```

---

## Key Takeaways from Examples

### Pattern Selection

1. **Minimal (Example 1)**: Simple guidelines, no external files needed
2. **With References (Example 2)**: Core rules + detailed examples/templates
3. **With Scripts (Example 3)**: Automation required
4. **Process-Based (Example 4)**: Workflow checklists and procedures

### Common Success Factors

- **Clear YAML metadata**: Makes skill discoverable
- **Focused purpose**: Single responsibility
- **Practical examples**: Real ✅/❌ patterns
- **Progressive detail**: Essential first, details in refs/
- **Under 500 lines**: Main SKILL.md stays concise
