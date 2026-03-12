---
name: atlassian-config
description: >
  Manage alias-keyed JSON config entries with get/save/delete. Use for Atlassian Confluence and Jira endpoint configs
  with fields url, alias, token_variable and optional default alias.
license: GPLv3
compatibility: Designed for Claude, Cline, Codex, KiloCode (or similar products)
---

# Atlassian Config Registry

Use required `config_path` for all operations.

## Rules

- Before writes, create parent dirs (`mkdir -p`; OK if they exist).
- If file missing, initialize `{"entries":{}}`.
- Data shape:

```json
{
  "default": "prod",
  "entries": {
    "prod": {
      "url": "https://api.example.com",
      "token_variable": "API_URL_PROD"
    }
  }
}
```

- Invariants: key is alias; each entry has `url|token_variable`; do not store `alias` inside entry; `default` is
  missing or existing alias.

## Operations

- `get(config_path, alias?)`: use `alias` or `default`.
  - success: `{"url":"...","token_variable":"...","success":true}`
  - failure: `{"error_message":"...","success":false}`

- `save(config_path, url, alias, token_variable, set_as_default=false)`:
  - validate non-empty `config_path|url|alias`
  - if `token_variable` missing, set `ATLASSIAN_[ALIAS]_API_TOKEN` using uppercased alias (example: `prod` ->
    `ATLASSIAN_PROD_API_TOKEN`)
  - upsert `entries[alias]={url,token_variable}`
  - expose explicit "save as default" option; if true set `default=alias`
  - return same JSON shape as `get`

- `delete(config_path, alias)`:
  - delete `entries[alias]` if present; if deleted alias is default, clear default
  - deleted: `{"success":true}`
  - not deleted: `{"error_message":"...","success":false}`

## Output

- Always return JSON only.
- Never include null fields.
- On failures, include `error_message` when available.
