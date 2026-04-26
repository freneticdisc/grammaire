# Atlassian API Domain Knowledge

Reference notes to improve endpoint matching quality. Read this file when:

- The operation is ambiguous or uses informal language
- You need to map user intent to correct Jira/Confluence resource names
- You're unsure whether an operation targets Jira or Confluence

---

## Jira API Structure

### Resource Taxonomy

The Jira REST API is organized around these primary resources (with their path segments):

| Resource               | Path Segment                            | Notes                                                |
|------------------------|-----------------------------------------|------------------------------------------------------|
| Issues                 | `/issue`                                | Core resource; also covers subtasks                  |
| Issue search           | `/search`                               | JQL-based; also `GET /issue/picker` for autocomplete |
| Issue comments         | `/issue/{id}/comment`                   |                                                      |
| Issue attachments      | `/issue/{id}/attachments`               | Upload uses multipart/form-data                      |
| Issue transitions      | `/issue/{id}/transitions`               | Status changes (workflow)                            |
| Issue watchers         | `/issue/{id}/watchers`                  |                                                      |
| Issue votes            | `/issue/{id}/votes`                     |                                                      |
| Issue links            | `/issueLink`                            | Creates/reads links between issues                   |
| Issue changelog        | `/issue/{id}/changelog`                 | History of field changes                             |
| Issue worklog          | `/issue/{id}/worklog`                   | Time tracking                                        |
| Issue remotelinks      | `/issue/{id}/remotelink`                | Links to external systems                            |
| Projects               | `/project`                              | Project CRUD + configuration                         |
| Project components     | `/project/{id}/component`, `/component` |                                                      |
| Project versions       | `/project/{id}/version`, `/version`     | Also called "fix versions"                           |
| Project roles          | `/project/{id}/role`                    |                                                      |
| Boards                 | `/board`                                | Agile boards (Scrum/Kanban)                          |
| Sprints                | `/sprint`                               | Scrum sprints                                        |
| Backlogs               | `/board/{id}/backlog`                   | Kanban/Scrum backlog                                 |
| Users                  | `/user`                                 | Account lookup, search, properties                   |
| Groups                 | `/group`                                | Group membership                                     |
| Filters                | `/filter`                               | Saved JQL filters                                    |
| Dashboards             | `/dashboard`                            |                                                      |
| Workflows              | `/workflow`                             | Issue workflows                                      |
| Workflow schemes       | `/workflowscheme`                       |                                                      |
| Screens                | `/screens`                              | Issue screens                                        |
| Fields                 | `/field`                                | Custom + system fields                               |
| Field configurations   | `/fieldconfiguration`                   |                                                      |
| Issue types            | `/issuetype`                            |                                                      |
| Priorities             | `/priority`                             |                                                      |
| Statuses               | `/status`                               |                                                      |
| Resolutions            | `/resolution`                           |                                                      |
| Permissions            | `/permissions`, `/permissionscheme`     |                                                      |
| Notification schemes   | `/notificationscheme`                   |                                                      |
| Security schemes       | `/issuesecurityschemes`                 |                                                      |
| Audit log              | `/auditing`                             |                                                      |
| Application properties | `/application-properties`               | Jira config                                          |
| Announcements          | `/announcementBanner`                   |                                                      |

### Jira v3 vs v2 Differences

- **v3 is preferred** — it uses richer user objects (`accountId` instead of `username`)
  and supports more modern response formats.
- Most endpoint paths are identical between v2 and v3 (only the `/rest/api/2/` vs
  `/rest/api/3/` prefix differs).
- v3 adds some endpoints not in v2 (e.g., bulk operations, newer async APIs).
- v2 is maintained for backwards compatibility but new integrations should use v3.

### Common Jira Operation → Endpoint Mappings

| User says...                           | Likely endpoint(s)                                              |
|----------------------------------------|-----------------------------------------------------------------|
| "create an issue" / "log a ticket"     | `POST /rest/api/3/issue`                                        |
| "get/fetch issue details"              | `GET /rest/api/3/issue/{issueIdOrKey}`                          |
| "update issue fields"                  | `PUT /rest/api/3/issue/{issueIdOrKey}`                          |
| "delete an issue"                      | `DELETE /rest/api/3/issue/{issueIdOrKey}`                       |
| "search issues" / "find issues by JQL" | `GET /rest/api/3/search`, `POST /rest/api/3/search/jql`         |
| "add a comment"                        | `POST /rest/api/3/issue/{issueIdOrKey}/comment`                 |
| "transition issue" / "change status"   | `POST /rest/api/3/issue/{issueIdOrKey}/transitions`             |
| "get available transitions"            | `GET /rest/api/3/issue/{issueIdOrKey}/transitions`              |
| "assign issue" / "assign to user"      | `PUT /rest/api/3/issue/{issueIdOrKey}/assignee`                 |
| "upload/add attachment"                | `POST /rest/api/3/issue/{issueIdOrKey}/attachments`             |
| "create a project"                     | `POST /rest/api/3/project`                                      |
| "list all projects"                    | `GET /rest/api/3/project/search`                                |
| "create sprint"                        | `POST /rest/agile/1.0/sprint` (Agile API — note different base) |
| "move issues to sprint"                | `POST /rest/agile/1.0/sprint/{id}/issue`                        |
| "bulk create issues"                   | `POST /rest/api/3/issue/bulk`                                   |
| "bulk edit issues"                     | `PUT /rest/api/3/issue/bulk`                                    |
| "watch an issue"                       | `POST /rest/api/3/issue/{issueIdOrKey}/watchers`                |
| "get issue changelog"                  | `GET /rest/api/3/issue/{issueIdOrKey}/changelog`                |
| "add issue link"                       | `POST /rest/api/3/issueLink`                                    |
| "log work" / "add worklog"             | `POST /rest/api/3/issue/{issueIdOrKey}/worklog`                 |

---

## Confluence API Structure

### Resource Taxonomy

| Resource       | v2 Path Segment                                   | v1 Path Segment                  | Notes             |
|----------------|---------------------------------------------------|----------------------------------|-------------------|
| Pages          | `/pages`                                          | `/content` (type=page)           | Core content type |
| Blog posts     | `/blogposts`                                      | `/content` (type=blogpost)       |                   |
| Spaces         | `/spaces`                                         | `/space`                         |                   |
| Labels         | `/labels`                                         | `/label`                         |                   |
| Attachments    | `/pages/{id}/attachments`                         | `/content/{id}/child/attachment` |                   |
| Comments       | `/pages/{id}/footer-comments`, `/inline-comments` | `/content/{id}/child/comment`    |                   |
| Children       | (via parent properties)                           | `/content/{id}/child`            |                   |
| Ancestors      | (via space hierarchy)                             | `/content/{id}/ancestor`         |                   |
| Templates      | `/templates`                                      | `/template`                      |                   |
| Users          | `/users`                                          | `/user`                          |                   |
| Search         | `/search`                                         | `/search`                        | CQL-based         |
| Tasks          | `/tasks`                                          | —                                | v2 only           |
| Whiteboards    | `/whiteboards`                                    | —                                | v2 only           |
| Databases      | `/databases`                                      | —                                | v2 only           |
| Custom content | `/custom-content`                                 | —                                | v2 only           |
| Properties     | `/pages/{id}/properties`                          | `/content/{id}/property`         |                   |
| Restrictions   | `/pages/{id}/restrictions`                        | `/content/{id}/restriction`      |                   |
| Watchers       | —                                                 | `/user/watch/content/{id}`       | v1 only           |
| Long tasks     | `/longtask`                                       | `/longtask`                      | Async task status |

### Confluence v2 vs v1 Differences

- **v2 is preferred** — cleaner resource-oriented paths, cursor-based pagination, less
  nested responses.
- v1 uses a unified `/content` endpoint with type query params; v2 has dedicated paths
  per content type (`/pages`, `/blogposts`, etc.).
- v2 added new content types: whiteboards, databases, smart links, custom content.
- v1 supports some operations v2 doesn't yet (e.g., content watching, macro rendering).
- Confluence v1 base URL: `/wiki/rest/api/`
- Confluence v2 base URL: `/wiki/api/v2/`

### Common Confluence Operation → Endpoint Mappings

| User says...                                | Likely endpoint(s)                                     |
|---------------------------------------------|--------------------------------------------------------|
| "create a page"                             | `POST /wiki/api/v2/pages`                              |
| "get/fetch a page"                          | `GET /wiki/api/v2/pages/{id}`                          |
| "update a page"                             | `PUT /wiki/api/v2/pages/{id}`                          |
| "delete a page"                             | `DELETE /wiki/api/v2/pages/{id}`                       |
| "search Confluence" / "find content by CQL" | `GET /wiki/api/v2/search`, `GET /wiki/rest/api/search` |
| "create a space"                            | `POST /wiki/api/v2/spaces`                             |
| "list spaces"                               | `GET /wiki/api/v2/spaces`                              |
| "get children of page"                      | `GET /wiki/api/v2/pages/{id}/children`                 |
| "add label to page"                         | `PUT /wiki/api/v2/pages/{id}/labels`                   |
| "add attachment"                            | `POST /wiki/api/v2/pages/{id}/attachments`             |
| "add comment to page"                       | `POST /wiki/api/v2/pages/{id}/footer-comments`         |
| "create blog post"                          | `POST /wiki/api/v2/blogposts`                          |
| "get page properties"                       | `GET /wiki/api/v2/pages/{id}/properties`               |
| "get page restrictions"                     | `GET /wiki/api/v2/pages/{id}/restrictions`             |

---

## Cross-Product Disambiguation

Some operations are ambiguous — apply these rules:

| Signals pointing to Jira                          | Signals pointing to Confluence                                    |
|---------------------------------------------------|-------------------------------------------------------------------|
| "issue", "ticket", "bug", "story", "epic", "task" | "page", "blog", "space", "wiki"                                   |
| "sprint", "board", "backlog"                      | "content", "macro", "template"                                    |
| "JQL"                                             | "CQL"                                                             |
| "transition", "workflow", "status"                | "restriction", "label" (more commonly used in Confluence context) |
| "project key" (e.g., "PROJ-123")                  | "space key"                                                       |
| "assignee", "reporter"                            | "author", "creator"                                               |

If the operation is ambiguous (e.g., "search for content"), include results from **both**
Jira and Confluence, clearly labeled.

---

## Known Endpoint Quirks

- **Jira Agile/Software endpoints** (`/rest/agile/1.0/`) are **not included** in the Jira v2/v3 specs above — they live
  in a separate "Jira Software" API spec. If the operation involves boards or sprints and nothing matches in the
  standard spec, note this to the user.
- **Async operations**: Several Jira bulk operations return a `taskId` and require polling
  `GET /rest/api/3/task/{taskId}`. Mention this if the operation is a known async one (bulk archive, bulk delete,
  export).
- **Pagination**: Jira uses `startAt`/`maxResults`; Confluence v2 uses cursor-based (`cursor` param). This affects which
  search/list endpoints to recommend for large result sets.
- **Deprecated endpoints**: Some v1 Confluence paths are deprecated in favor of v2. If both versions match, always list
  v2 first and note v1 deprecation where applicable.
- **Authentication note**: All endpoints require OAuth 2.0 or API token basic auth. The base URL pattern is
  `https://<your-domain>.atlassian.net`.