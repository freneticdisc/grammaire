---
name: atlassian-api
description: >
  Direct access to Atlassian Jira and Confluence APIs for coding agents. Use this skill whenever a task involves reading
  or writing Jira issues, projects, boards, sprints, comments, attachments, worklogs, or Confluence pages, spaces,
  macros, or attachments. Trigger on any request mentioning Jira, Confluence, Atlassian, tickets, epics, sprints,
  backlogs, wiki pages, or any related workflow.
license: GPLv3
compatibility: Designed for Claude, Cline, Codex, KiloCode (or similar products)
---

# Atlassian Confluence & Jira API Skill

Use for Jira/Confluence/Atlassian tasks.

## Runtime And Client Requirements

- Python `>=3.12` required.
- Use Python + `httpx` for all Atlassian API calls.
- Run scripts with `uv`.
- Do not use `curl` or non-Python HTTP clients.

## Flow

1. Check `uv` first:

- `uv --version`
- If missing, stop and handle per agent policy.

2. Resolve variables:

- `uv run scripts/variables.py`
- Use `config_file`.

3. Require `url` or `alias`.
  - If a full Jira/Confluence page URL is provided (for example, `/browse/<KEY>` or `/wiki/...`), extract the base URL
    and use that for API calls.
  - Example: `https://jira.company.com/browse/TASK-123` -> `https://jira.company.com`.

4. If user gives `alias`:

- Use `atlassian-config` `get(config_path, alias)` to resolve `url` and `token_variable`.
- If lookup fails, ask for a valid alias or URL.

5. If user gives `url`:

- Use it directly.
- Ask whether to save it via `atlassian-config` `save(...)`.

6. Auth:

- If `token_variable` exists, check env, then `.env`, `.env.local`, `.env.development`, `.env.production`, `~/.env`.
- If token found, use Bearer auth.
- If token missing, run `uv run scripts/browser.py "<url>"`, read `state_file`, build cookie auth, set `X-XSRF-TOKEN`
  from `atlassian.xsrf.token` or `XSRF-TOKEN` or `atl.xsrf.token`, and use `X-Atlassian-Token: no-check` for
  multipart/upload.

7. Execute REST calls in Python with `httpx` via `uv`.

## 401 Rules

- Token auth + `401`:
  - Clearly tell user the PAT token has expired.
  - Stop and request refreshed token (or alternate auth).

- Browser-cookie auth + `401`:
  - Ask to run: `uv run scripts/browser.py "<url>" true`
  - Reload `state_file`, rebuild headers, retry the same REST call once.

## References

Use [references/QUICK-LINKS.md](references/QUICK-LINKS.md) for Jira/Confluence API endpoints.

## Guardrails

- Do not call APIs before URL resolution.
- Do not assume aliases without `atlassian-config`.
- Do not hardcode secrets.
- Never display or log headers, cookies, or tokens.
- If no valid token and no session state, stop and report blocker.
