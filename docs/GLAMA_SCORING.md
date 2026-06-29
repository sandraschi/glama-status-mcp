# Glama TDQS Scoring Guide

This page explains what Glama is, how the Tool Definition Quality Score
(TDQS) works, and how to use glama-status-mcp to track and improve your
MCP server's docstring quality.

---

## What is Glama?

[Glama](https://glama.ai) is an MCP server registry and quality scoring
platform. It hosts MCP servers, visualizes tool definitions, and assigns
TDQS grades based on docstring quality. Think of it as a code quality
score for your MCP server's documentation.

For each MCP server registered on Glama, a score page at
`glama.ai/mcp/servers/{author}/{repo}/score` shows:

- An overall letter grade (A-F) and numeric score (0-5)
- Per-tool grades with 6-dimensional breakdowns
- Server-level coherence and maintenance scores
- Profile completion percentage

Glama scores are computed by analyzing the docstrings of every tool
registered in an MCP server. The analysis checks for completeness,
clarity, structure, and adherence to docstring best practices.

---

## The TDQS (Tool Definition Quality Score)

TDQS is Glama's proprietary scoring system that evaluates MCP tool
docstrings across 6 weighted dimensions.

### Overall Score Formula

```
Server Score = 0.6 × Mean(all tool scores) + 0.4 × Min(all tool scores)
```

This means ONE bad tool pulls the entire server score down
significantly. The minimum-scoring tool is always the highest-leverage
fix target.

### Grade Thresholds

| Grade | Score Range | Meaning |
|-------|-------------|---------|
| **A** | >= 3.5 | Excellent documentation. Clear, complete, well-structured. |
| **B** | 3.0 - 3.49 | Good. Minor improvements in a few areas. |
| **C** | 2.0 - 2.99 | Adequate. Several tools need documentation work. |
| **D** | 1.0 - 1.99 | Poor. Multiple tools need major attention. |
| **F** | &lt; 1.0 | Failing. Urgent documentation overhaul required. |

---

## The 6 Dimensions

Each tool is scored on 6 dimensions, each weighted differently.

### 1. Purpose Clarity (25% -- highest weight)

Does the first sentence clearly state what the tool does?

- **Good**: "Creates, reads, and deletes files in the project output directory."
- **Poor**: "Handles files."
- **Missing**: No docstring or only a parameter list.

The Purpose dimension has the highest weight because the most important
thing an LLM agent needs to know is what a tool does. If the purpose
is unclear, the agent cannot choose the right tool.

**Fix**: Start every docstring with a clear, specific sentence describing
the tool's primary function. Include what it operates on, what it returns,
and any side effects.

### 2. Usage Guidelines (20%)

When to use and when NOT to use this tool. Preconditions documented.

- **Good**: "Use this to batch-process multiple files. Do NOT use for
  single-file operations -- use file_op instead. Requires the output
  directory to exist."
- **Poor**: No usage guidance at all.
- **Missing**: No mention of preconditions or appropriate use cases.

**Fix**: Add a "When to use" / "When NOT to use" section. Document
preconditions (what must be true before calling this tool) and any
related tools that should be preferred in certain cases.

### 3. Behavioral Transparency (20%)

Return values, side effects, and error conditions are documented.

- **Good**: Includes a `## Return Format` section with the exact JSON
  structure. Documents error conditions and what happens on failure.
- **Poor**: "Returns a dict." No error documentation.
- **Missing**: No return documentation at all.

**Fix**: Add a `## Return Format` section specifying every key in the
response dict, its type, and meaning. Document what happens on failure
(returns error dict vs throws exception).

### 4. Parameter Semantics (15%)

Every parameter has a type annotation, description, and valid values.

- **Good**:
  ```python
  name: Annotated[str, Field(description="Project name. 3-50 chars.")]
  limit: Annotated[int, Field(description="Max results.", ge=1, le=100)]
  ```
- **Poor**: `name: str -- The name.`
- **Missing**: No parameter descriptions.

**Fix**: Use `Annotated[T, Field(description="...")]` on every parameter.
Describe the type, valid values, constraints, and what the parameter
affects. Do NOT use bare `Args:` blocks in docstrings -- fleet standard
requires all parameter documentation via `Field(description=...)`.

### 5. Conciseness & Structure (10%)

Not a wall of text, not a one-liner. Goldilocks zone.

- **Good**: 80-250 words. Uses sections. Well-structured.
- **Poor**: 500-word wall of text (too verbose) or "Does X" (too sparse).
- **Missing**: Confusing or unstructured documentation.

**Fix**: Aim for 80-250 words. Use `##` sections (Return Format,
Examples, Notes). Keep each section focused. Remove redundant
explanations.

### 6. Contextual Completeness (10%)

Can an LLM use this tool correctly without reading the source code?

- **Good**: Includes `## Examples`, edge cases, and non-obvious behavior.
- **Poor**: Example doesn't match the actual API.
- **Missing**: No examples, no edge case documentation.

**Fix**: Add 1-3 concrete Python examples showing real usage. Document
edge cases and non-obvious behavior. Add notes about dependencies or
required state.

---

## Server Coherence

In addition to per-tool TDQS scores, Glama evaluates the server as a
whole across 4 coherence dimensions:

| Dimension | What it measures |
|-----------|-----------------|
| **Disambiguation** | Are tool names distinct enough to avoid confusion? |
| **Naming Consistency** | Are tools named using consistent patterns (verb-led snake_case)? |
| **Tool Count** | Is the number of tools appropriate for the server's scope? |
| **Completeness** | Does the tool surface cover advertised capabilities? |

Server coherence is graded A-F independently of TDQS but contributes
to the overall server profile.

---

## How glama-status-mcp Works with Glama

glama-status-mcp scrapes the Glama score pages to extract:

1. **Per-repo data**: overall grade, score, TDQS mean/min, coherence
   and maintenance grades, profile completion, latest release version
2. **Per-tool data**: name, grade, score, all 6 dimension scores
3. **Refresh history**: timestamps, success/failure counts, errors
4. **Snapshots and deltas**: score changes between refresh runs

The data flows:

```
Glama.ai score pages
        │
        ▼
glama-status-mcp scraper.py  (polite HTTP, 1s delay)
        │
        ▼
SQLite database (6 tables)
        │
        ├─► MCP tools (list, get, worst_tools, report, deltas)
        ├─► Prefab cards (fleet overview, per-repo breakdown)
        ├─► Web dashboard (6 pages)
        ├─► LLM analysis (chat + agentic_analyze + reports)
        └─► reports/ directory (per-repo markdown fix plans)
```

---

## Typical Improvement Workflow

### Step 1: Check current scores

```python
glama_status(operation="list")
glama_status(operation="report")
```

### Step 2: Identify the weakest link

```python
glama_status(operation="worst_tools", limit=10)
```

The worst tool is always the highest-leverage fix target due to the
60/40 mean/min formula.

### Step 3: Get an improvement plan

```python
# Static plan (works everywhere)
glama_improvement_plan(repo_name="your-mcp")

# LLM-powered analysis (works with Ollama/LM Studio or sampling)
glama_agentic_analyze(repo_name="your-mcp")
glama_generate_reports(repo_name="your-mcp")
```

### Step 4: Fix docstrings

Focus on the worst tool first. Common fixes:

1. Add `Field(description=...)` to every undocumented parameter
2. Add a clear first sentence stating the tool's purpose
3. Add "When to use" / "When NOT to use" sections
4. Add `## Return Format` and `## Examples` sections
5. Document error conditions and edge cases

### Step 5: Make a release and sync

1. Push your fixes and make a new release (tag + PyPI publish if applicable)
2. On glama.ai, go to your server page and click "Sync Server"
3. Glama re-analyzes the repository and updates the scores
4. Run `glama_status(operation="refresh")` to pull new scores
5. Check `glama_status(operation="deltas")` to see improvement

---

## FAQ

**Q: Why does one bad tool pull the whole score down?**
The 40% minimum weighting means the worst tool has disproportionate
influence. This is by design -- Glama wants to reward consistent
quality across ALL tools, not just good average quality.

**Q: How often does Glama rescore my server?**
Only when you trigger "Sync Server" on glama.ai. It does not
automatically detect git pushes.

**Q: My repo exists on Glama but shows no scores. Why?**
It hasn't been analyzed yet. Go to your server page on glama.ai and
check if scores appear. Some repos show a page but haven't been
through scoring yet.

**Q: What if two tools have the same name?**
Glama's coherence scoring checks for disambiguation. Tools with
identical or confusingly similar names will score lower on the
Disambiguation dimension.

**Q: Can I use glama-status-mcp to track OTHER people's repos?**
Yes. Add them to `config/fleet-repos.json` with the correct
`glama_author` field, or call `glama_status(operation="add_repo",
repo_name="their-repo", author="their-user")`.
