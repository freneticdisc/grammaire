# Endpoint Scoring

Use this rubric when `SKILL.md` Step 3 asks you to score endpoint matches.

For every `(path, method)` pair, compute a relevance score against the operation:

| Signal                               | Weight | Details                                                                 |
|--------------------------------------|--------|-------------------------------------------------------------------------|
| Action verb match in `summary`       | 3      | e.g., "create" in operation -> "Create issue" in summary                |
| Resource noun match in `summary`     | 3      | e.g., "issue" in operation -> "Get issue" in summary                    |
| Action verb match in `operationId`   | 2      | camelCase parsing: `createIssue` -> ["create", "issue"]                 |
| Resource noun match in path template | 2      | `/rest/api/3/issue/{issueIdOrKey}`                                      |
| Key query param name match           | 2      | e.g., operation mentions "JQL" -> endpoint has `jql` query param        |
| Key request body field match         | 2      | e.g., operation mentions "transition" -> body has `transition.id` field |
| Match in `description`               | 1      | Fallback for edge cases                                                 |
| Synonym expansion match              | 2      | Apply synonyms from Step 1                                              |
| Tag match                            | 1      | e.g., tag "Issues" for issue operations                                 |

Include an endpoint if its total weighted score is at least 5. Prefer precision to recall; a tight match is better
than a loose one.

Important edge cases:

- If the operation mentions "bulk", restrict to endpoints with "bulk" in path or summary.
- If the operation is read-only (get/list/search/find), de-prioritize POST/PUT/DELETE endpoints.
- If the operation involves a specific resource by ID, prefer paths with `{issueIdOrKey}`, `{id}`, or `{pageId}`
  parameters.
- If nothing scores above the threshold, lower the threshold and retry with just the primary resource noun. Never return
  an empty result without trying synonyms first.
