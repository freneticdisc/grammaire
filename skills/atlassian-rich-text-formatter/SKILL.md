---
name: atlassian-rich-text-formatter
description: >
  Generate Atlassian-ready rich text for Jira and Confluence from raw content or context. Use before creating or
  updating Jira descriptions, comments, environment fields, textarea custom fields, Confluence pages, blog posts, or
  comments when the endpoint needs ADF JSON, Jira wiki markup, Confluence storage XHTML, or Confluence wiki markup.
---

# Atlassian Rich Text Formatter

Return only the formatted content or requested JSON fragment. Do not call Atlassian APIs.

## Pick Format

- Jira Cloud REST rich text: use ADF JSON for `description`, comments, `environment`, and textarea custom fields.
- Jira wiki markup: use only when a wiki renderer, legacy platform, or caller explicitly requires Jira wiki syntax.
- Confluence REST body: use storage XHTML with `representation: "storage"`.
- Confluence wiki markup: use only for legacy/admin inputs that explicitly accept wiki markup.
- Markdown: use only when the endpoint or UI paste workflow explicitly accepts Markdown.

Ask for the product, endpoint, or field renderer if a live update target is ambiguous.

## Rules

- Preserve the user's meaning and structure; do not invent project keys, account IDs, versions, labels, statuses, or
  IDs.
- Convert headings, lists, links, tables, and code fences into the target-native representation.
- Keep commands, logs, JSON, XML, SQL, and config in code blocks with indentation preserved.
- Use tables only for true row/column data; otherwise prefer bullets.
- Escape user text inside JSON strings and XML/HTML storage values.
- Do not leave raw Markdown markers such as `#`, `**bold**`, backticks, or pipe-table separators unless the target is
  Markdown.
- When editing existing ADF or storage content, preserve unsupported nodes, macros, and attributes unless replacing the
  full body.

## ADF

Root: `{ "version": 1, "type": "doc", "content": [] }`

Common nodes:

- Paragraph: `{ "type": "paragraph", "content": [{ "type": "text", "text": "Text" }] }`
- Heading: `{ "type": "heading", "attrs": { "level": 2 }, "content": [...] }`
- Bullet list: `{ "type": "bulletList", "content": [{ "type": "listItem", "content": [paragraph] }] }`
- Ordered list: `{ "type": "orderedList", "content": [{ "type": "listItem", "content": [paragraph] }] }`
- Code block: `{ "type": "codeBlock", "attrs": { "language": "json" }, "content": [{ "type": "text", "text": "..." }] }`
- Marks: `{ "type": "strong" }`, `{ "type": "em" }`, `{ "type": "code" }`,
  `{ "type": "link", "attrs": { "href": "https://example.com" } }`

Jira field wrapper: `{ "fields": { "description": <adf-doc> } }`

## Wiki

```text
h2. Heading
Paragraph with *bold*, _italic_, {{inline code}}, and [link text|https://example.com].
* Bullet
# Numbered item
{code:json}
{"key": "value"}
{code}
||Column A||Column B||
|A1|B1|
```

## Confluence Storage

```xml
<h2>Heading</h2>
<p>Paragraph with <strong>bold</strong>, <em>italic</em>, <code>inline code</code>, and <a href="https://example.com">link text</a>.</p>
<ul><li><p>Bullet</p></li></ul>
<ol><li><p>Numbered item</p></li></ol>
<ac:structured-macro ac:name="code"><ac:plain-text-body><![CDATA[{"key": "value"}]]></ac:plain-text-body></ac:structured-macro>
<table><tbody><tr><th>Column A</th><th>Column B</th></tr><tr><td>A1</td><td>B1</td></tr></tbody></table>
```

Confluence body wrapper: `{ "body": { "representation": "storage", "value": "<p>Content</p>" } }`
