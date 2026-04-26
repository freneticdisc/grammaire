---
name: atlassian-tasks
description: >
  Execute Jira or Confluence operations given an Atlassian URL and task instructions. Use when the user wants to
  create, read, update, delete, or search Jira/Confluence resources and needs endpoint discovery, payload construction,
  and authenticated API execution. Trigger on any request mentioning Jira, Confluence, Atlassian, tickets, epics,
  sprints, backlogs, wiki pages, or related Atlassian workflows.
---

# Atlassian Tasks

## Inputs

| Field            | Required | Description                                                                                      |
|------------------|----------|--------------------------------------------------------------------------------------------------|
| `url`            | No       | Jira/Confluence URL identifying the site and product. May be embedded in `instructions` instead. |
| `instructions`   | Yes      | Operation to perform, optionally containing the target URL inline.                               |
| `pat_token_file` | No       | Absolute path to a PAT file. If omitted, browser auth is used.                                   |

## Preconditions

- `instructions` is mandatory; ask if missing.
- A resolvable Atlassian URL is required. Use `url` if provided; otherwise extract from `instructions` (any host paired
  with `/jira`, `/wiki`, `/confluence`, `/secure`, `/browse`, or `/rest`). If none found, ask.
- Never ask for a token when `pat_token_file` is absent — use Mode B.
- Never assume values for required API fields not supplied by the user; ask explicitly.

## Workflow

1. **Resolve URL.** Prefer `url`; otherwise extract from `instructions`. If multiple candidates, take the most specific.
   If none, stop and ask.
2. **Identify product** (`jira` or `confluence`) from URL and/or instructions.
3. **Resolve endpoint.** Call `atlassian-endpoint-resolver` with the inferred operation (CRUD verb + resource type). Use
   the top-ranked result.
4. **Check for missing fields.** If any required path/query/body field is not derivable from the URL or instructions,
   ask for only those values and wait.
5. **Format rich text.** Before constructing a body that includes Jira descriptions/comments/environment/textarea fields
   or Confluence page/blog/comment bodies, use `atlassian-rich-text-formatter` with the product, endpoint/schema
   context, field name, and source content. Use the returned ADF, wiki markup, or Confluence storage value exactly.
6. **Authenticate.** Mode A (PAT) or Mode B (browser) per rules below.
7. **Execute.** Construct requests and run in sub-agents per rules below.
8. **Return results** per Output spec.

## Authentication

**Mode A — PAT file provided:** Read and strip `pat_token_file`. Send `Authorization: Bearer <token>`,
`Accept: application/json`, and `Content-Type: application/json` (when body present) on every request.

**Mode B — No PAT file:**

1. Launch `atlassian-browser-authentication` with the resolved URL. If it fails or returns no `state_file`, stop and
   report the error.
2. Read `state_file`, extract cookies, and send as a `Cookie` header alongside `Accept` and `Content-Type` on every
   request.
3. On `401 Unauthorized`, rerun `atlassian-browser-authentication` with `FORCE` and retry once.

## Request Construction

- **Base URL:** `<scheme>://<host><context_path>` where `context_path` is the non-API prefix (e.g. `/jira`,
  `/confluence`).
- **Endpoint URL:** Append resolved path to base URL, substitute `{paramName}` tokens, append URL-encoded query params.
- **Body:** JSON built from endpoint schema and user-supplied values only. Do not fabricate or default any field.
- **Rich text fields:** Never pass raw Markdown into Jira or Confluence REST rich-text fields. Use
  `atlassian-rich-text-formatter` to generate the endpoint's expected representation, then insert that value into the
  JSON body without reformatting it.
- **Pagination:** Auto-fetch subsequent pages when a response contains `startAt`/`maxResults`, a pagination token, or
  `_links.next`, unless instructions imply a limit.

## Sub-Agent Rules

- All API requests execute in sub-agents, not the main agent.
- Independent calls run in parallel; dependent calls run sequentially.
- Merge all sub-agent outputs before returning.

## Output

- **Single call:** Return the result directly.
- **Multiple calls, aggregation needed:** Return the combined result as the primary output. Omit per-call breakdowns
  unless the user asks or a call failed.
- **Multiple calls, independent results:** Present each result in execution order.
- **Any failure:** Include the failed step, HTTP status, and a short response excerpt.
