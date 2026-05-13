# Plans Directory

This folder stores feature plan files consumed by `/feature-pipeline`.

Naming convention:

- `YYYY-MM-DD-<feature-slug>.md`

Minimum frontmatter:

```yaml
---
feature: <slug>
status: draft
retry_count: 0
created_at: <ISO-8601 datetime>
---
```
