---
name: atlassian-endpoint-resolver
description: >
  Resolves the best-matching Atlassian API endpoints for a given inferred `operation` (what the user wants to do).
  Use this skill whenever the agent needs to identify which Atlassian REST API endpoint(s) can fulfill a user's
  intent, especially for Jira issues, projects, boards, sprints, workflows, Confluence pages, spaces, or any
  cross-product Atlassian operations. Always trigger when the input includes an `operation` field describing an
  Atlassian action.
---

# Atlassian API Endpoint Resolver

Given an inferred `operation` string describing what the user wants to do, find and return all matching REST API
endpoints across all Atlassian OpenAPI specs.

## Inputs

Required `operation` the inferred intent text and target application (Confluence or Jira).

## API Registry

Fetch these specs at runtime (in parallel where possible) based on the `operation`.

| Priority | API Name       | Version | Spec URL                                                                 |
|----------|----------------|---------|--------------------------------------------------------------------------|
| 1        | Jira API       | v3      | `https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json` |
| 2        | Jira API       | v2      | `https://developer.atlassian.com/cloud/jira/platform/swagger.v3.json`    |
| 1        | Confluence API | v2      | `https://developer.atlassian.com/cloud/confluence/openapi-v2.v3.json`    |
| 2        | Confluence API | v1      | `https://developer.atlassian.com/cloud/confluence/swagger.v3.json`       |

## Step 1 — Parse the operation

Decompose the `operation` string into:

- **Action verbs**: create, get, update, delete, list, search, move, archive, assign,
  transition, comment, watch, link, bulk, export, import, restore, etc.
- **Resource nouns**: issue, project, board, sprint, comment, attachment, user, group,
  permission, workflow, screen, field, filter, dashboard, version, component, space,
  page, blog, content, label, template, etc.
- **Qualifiers/context**: by JQL, by ID, bulk, async, subtask, watchers, votes, etc.

Generate a set of **search terms** from these tokens. Also produce **synonyms**:

- issue ↔ ticket ↔ task
- page ↔ content (Confluence)
- space ↔ project (contextual)
- transition ↔ status change
- comment ↔ note

## Step 2 — Fetch specs and extract paths

For each spec URL in the registry:

1. Fetch the JSON.
2. Read `info.title` and `info.version` (for display labeling).
3. Extract the `paths` object — a map of `{ "/path/template": { "get": {...}, "post": {...}, ... } }`.
4. For each HTTP method object, use `summary`, `description`, `operationId`, `tags`, `parameters`, and
   `requestBody` for matching and output.
   - Extract path parameters and query parameters separately.
   - For `application/json` request bodies, recursively expand same-document `$ref` schemas before returning output.
   - Do not return raw `$ref` as the primary request body schema output.
   - Keep `originalRef` only as optional traceability metadata.
   - Use cycle detection and a depth guard; set `partiallyExpanded: true` if expansion is incomplete.
   - Preserve `multipart/form-data` request bodies for attachment/upload endpoints.

## Step 3 — Score each endpoint

For every `(path, method)` pair, compute a relevance score against the operation:

| Signal                               | Weight | Details                                                                |
|--------------------------------------|--------|------------------------------------------------------------------------|
| Action verb match in `summary`       | 3      | e.g., "create" in operation → "Create issue" in summary                |
| Resource noun match in `summary`     | 3      | e.g., "issue" in operation → "Get issue" in summary                    |
| Action verb match in `operationId`   | 2      | camelCase parsing: `createIssue` → ["create", "issue"]                 |
| Resource noun match in path template | 2      | `/rest/api/3/issue/{issueIdOrKey}`                                     |
| Key query param name match           | 2      | e.g., operation mentions "JQL" → endpoint has `jql` query param        |
| Key request body field match         | 2      | e.g., operation mentions "transition" → body has `transition.id` field |
| Match in `description`               | 1      | Fallback for edge cases                                                |
| Synonym expansion match              | 2      | Apply synonyms from Step 1                                             |
| Tag match                            | 1      | e.g., tag "Issues" for issue operations                                |

**Threshold**: Include an endpoint if its total weighted score **≥ 5**. Prefer precision to recall — a tight match is
better than a loose one.

**Important edge cases:**

- If the operation mentions "bulk", restrict to endpoints with "bulk" in path or summary.
- If the operation is read-only (get/list/search/find), de-prioritize POST/PUT/DELETE endpoints.
- If the operation involves a specific resource by ID (e.g., "get issue by ID"), prefer paths with `{issueIdOrKey}`,
  `{id}`, or `{pageId}` parameters.
- If nothing scores above the threshold, **lower the threshold and retry** with just
  the primary resource noun. Never return an empty result without trying synonyms first.

## Step 4 — Deduplicate across API versions

The same logical endpoint often appears in both v2 and v3 of Jira (or v1 and v2 of Confluence) with identical or
near-identical paths. **Keep all versions** — do not deduplicate across APIs. Each version is a separate entry in the
output.

Within a single API spec, if the exact same `(path, method)` appears more than once (rare), keep only the first
occurrence.

Sort the final matched list by API version **descending**. Within the same API, sort by relevance score descending,
then alphabetically by path.

Before returning results, normalize each matched endpoint's request body schema:

- Always provide `Request Body Schema (Expanded)` for `application/json` payloads
- Never return raw `$ref` as the request body schema output
- If useful, include `Original Ref` as metadata only (not as a substitute for the expanded schema)

## Output Format

Return a structured response as a list of:

- URL
- Path Parameters
- Query Parameters
- Request Body Schema (Expanded, `application/json`)
- Original Ref (optional metadata)
