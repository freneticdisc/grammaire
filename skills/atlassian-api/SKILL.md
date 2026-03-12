---
name: atlassian-api
description: >
  Use this skill for direct Jira and Confluence REST API tasks. It enforces a URL/alias-first flow, resolves aliases
  through the atlassian-config skill, prefers Bearer token auth when available, and falls back to browser session
  cookies when no token variable is present.
license: GPLv3
compatibility: Designed for Claude, Cline, Codex, KiloCode (or similar products)
---

# Atlassian Jira & Confluence API Skill

Use this skill whenever a task involves reading or writing Jira issues, projects, boards, sprints, comments,
attachments, worklogs, or Confluence pages, spaces, macros, or attachments. Trigger on any request mentioning Jira,
Confluence, Atlassian, tickets, epics, sprints, backlogs, wiki pages, or any related workflow.

## Required Execution Flow

1. Run `variables.py` first to resolve required paths:
   - Command: `uv run skills/atlassian-api/scripts/variables.py`
   - Expected JSON keys:
     - `application_dir`
     - `browsers_cache`
     - `config_file`

2. Require either:
   - a full Atlassian URL, or
   - an alias provided by the user.

3. If the user provides an alias:
   - Use the `atlassian-config` skill `get(config_path, alias)` to resolve:
     - `url`
     - `token_variable`
   - `config_path` should come from `variables.py` (`config_file`).
   - If alias lookup fails, ask for a valid alias or URL.

4. If the user provides a URL:
   - Continue with that URL.
   - Ask whether they want to add it to the registry using `atlassian-config` `save(...)`.
   - If yes, collect alias and optional token variable name, then save it.

5. Once URL is resolved, determine token auth:
   - If `token_variable` is known, check process environment first.
   - Also check common env-file locations for exported values:
     - `.env`
     - `.env.local`
     - `.env.development`
     - `.env.production`
     - `~/.env`
   - If token is found, build:
     - `Authorization: Bearer <token>`
     - `Accept: application/json`
     - `Content-Type: application/json` (for write calls)

6. If no token variable/value is found:
   - Run `browser.py` with the resolved URL:
     - `uv run skills/atlassian-api/scripts/browser.py "<url>"`
   - Read returned JSON and capture `state_file`.
   - Load `cookies` from that state file and attach cookies to HTTP calls:
     - `Cookie: name1=value1; name2=value2; ...`
   - Include XSRF header when cookie exists:
     - `X-XSRF-TOKEN` from one of:
       - `atlassian.xsrf.token`
       - `XSRF-TOKEN`
       - `atl.xsrf.token`
   - For uploads/multipart calls, include:
     - `X-Atlassian-Token: no-check`

7. Perform intended Jira/Confluence task with direct REST API calls.

## API Endpoint References

Use links in [references/QUICK-LINKS.md](./references/QUICK-LINKS.md):

- Jira REST v3
- Jira Agile / Board
- Confluence REST v2
- Confluence REST v1
- OAuth scopes
- Atlassian API token management

## Guardrails

- Do not proceed with Jira/Confluence API calls until URL is resolved.
- Do not assume aliases without consulting `atlassian-config`.
- Do not hardcode tokens; always resolve from env/env files.
- If neither Bearer token nor browser session is available, stop and report the blocker.
