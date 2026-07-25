---
name: obsidian-vault
description: Search, create, and manage notes in the Obsidian vault with wikilinks and index notes. Use when user wants to find, create, or organize notes in Obsidian.
---

# Obsidian Vault

## Vault location

`/Users/marvin/IdeaProjects/knowledge/knowledge/`

Structured with folders following OpenClaw Wiki conventions.

## Folder conventions

| Folder | Purpose |
|--------|---------|
| `sources/` | Raw materials — articles, docs, transcripts. Add `<!-- openclaw:wiki:raw-source -->` marker. |
| `entities/` | People, orgs, tools, projects — concrete entities. |
| `concepts/` | Abstract concepts, patterns, principles, terminology. |
| `syntheses/` | Cross-source, cross-entity comprehensive analysis. |
| `reports/` | OpenClaw auto-generated reports (claim health, contradictions, etc.). |
| `wiki/` | Wiki namespace (comparisons, concepts, domains, etc.) with `_index.md` per section. |
| `_templates/` | Obsidian note templates per page type. |
| `_attachments/` | Images, PDFs, binary resources. |
| `inbox.md` | Staging area — raw ideas, to be sorted later. |

## Naming conventions

- **kebab-case** for filenames in syntheses/ (e.g., `code-knowledge-graph-tools-comparison.md`)
- **Title case** for human-facing titles in frontmatter
- Use OpenClaw-style frontmatter: `pageType`, `id`, `title`, `status`, `tags`, `updatedAt`, `confidence`
- Obsidian callouts: `> [!important]`, `> [!tip]`, `> [!abstract]`, `> [!warning]`, `> [!danger]`, `> [!quote]`, `> [!info]`
- Managed blocks: `<!-- openclaw:...:start -->` to `<!-- openclaw:...:end -->` — do NOT edit inside these markers

## Linking

- Use Obsidian `[[wikilinks]]` syntax: `[[folder/note-name|Display Title]]`
- Notes link to related pages at the bottom under `## 相关页面`
- Index notes (`_index.md` or `index.md`) aggregate related topics with wikilinks

## Workflows

### Search for notes

```bash
# Search by filename
find "/Users/marvin/IdeaProjects/knowledge/knowledge/" -name "*.md" | grep -i "keyword"

# Search by content
grep -rl "keyword" "/Users/marvin/IdeaProjects/knowledge/knowledge/" --include="*.md"
```

Or use Grep/Glob tools directly on the vault path.

### Create a new note

1. Choose correct folder (`syntheses/`, `entities/`, `concepts/`, `sources/`)
2. Use kebab-case filename (e.g., `my-analysis-topic.md`)
3. Add OpenClaw-style frontmatter (pageType, id, title, status, tags)
4. Write content with Obsidian callouts
5. Add `[[wikilinks]]` to related pages under `## 相关页面`
6. Update the relevant `index.md` or `_index.md`

### Find related notes

Search for `[[Note Title]]` across the vault to find backlinks:

```bash
grep -rl "\\[\\[note-name\\]\\]" "/Users/marvin/IdeaProjects/knowledge/knowledge/"
```

### Find index notes

```bash
find "/Users/marvin/IdeaProjects/knowledge/knowledge/" -name "*index*" -o -name "*_index*"
```
