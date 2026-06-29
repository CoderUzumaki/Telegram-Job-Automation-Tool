# Design System — Telegram Job Radar

Visual and interaction guidelines for the FastAPI + HTMX inbox. This doc informs implementation in `app/templates/` and `app/static/style.css`, and serves as reference when adapting designs from Stitch / v0 / Lovable.

## Design principles

1. **Triage speed** — User scans 20–30 items/day; density over decoration
2. **Decision clarity** — Score, company, role visible without opening detail
3. **Trust signals** — Show parser vs LLM source; surface export/processing errors
4. **Local tool feel** — Not a SaaS marketing site; utilitarian, calm, focused
5. **Keyboard-friendly** — Power user may triage quickly (future: j/k navigation)

## Layout

### Master-detail inbox (primary screen)

```
┌─────────────────────────────────────────────────────────────┐
│  Job Radar          [Inbox 12]  Settings    ● Connected     │
├──────────────────┬──────────────────────────────────────────┤
│  INBOX LIST      │  DETAIL PANEL                            │
│  (320–400px)     │  (flex grow)                             │
│                  │                                          │
│  ┌────────────┐  │  Google · SDE Intern                     │
│  │ Google     │  │  Score: 82  ·  Posted 2h ago             │
│  │ SDE · 82   │  │                                          │
│  └────────────┘  │  Company    Google        [parser]       │
│  ┌────────────┐  │  Role       SDE Intern    [parser]       │
│  │ Amazon ... │  │  Batch      2025          [parser]       │
│  └────────────┘  │  Location   Remote        [llm]          │
│                  │  Tags       ppo, remote                  │
│                  │                                          │
│                  │  Links (3)                               │
│                  │  • careers.google.com/...                │
│                  │  • forms.gle/...                         │
│                  │                                          │
│                  │  Why relevant                            │
│                  │  "Matches SDE profile, remote OK..."     │
│                  │                                          │
│                  │  [Approve ✓]  [Reject ✗]                 │
└──────────────────┴──────────────────────────────────────────┘
```

- **List panel:** Scrollable; selected row highlighted
- **Detail panel:** Empty state: "Select a job to review"
- **Mobile (defer MVP):** Stack list above detail; acceptable to desktop-only for v1

### Settings page

Single page, sections:
- Job profile (roles, skills, locations — textarea or tag inputs)
- Filter rules (include/exclude keywords)
- Score threshold (slider 0–100)
- Connection status (Telegram, Google Sheets)
- Save per section with inline success message

## Color palette

Utilitarian dark-friendly palette (user may run late-night triage):

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--bg` | `#f8f9fa` | `#0f1117` | Page background |
| `--surface` | `#ffffff` | `#1a1d27` | Cards, panels |
| `--border` | `#e2e8f0` | `#2d3348` | Dividers |
| `--text` | `#1a202c` | `#e2e8f0` | Primary text |
| `--text-muted` | `#64748b` | `#94a3b8` | Meta, timestamps |
| `--accent` | `#3b82f6` | `#60a5fa` | Links, selected row |
| `--success` | `#16a34a` | `#4ade80` | Approve, exported |
| `--danger` | `#dc2626` | `#f87171` | Reject, errors |
| `--warning` | `#d97706` | `#fbbf24` | Processing errors |
| `--score-high` | `#16a34a` | `#4ade80` | Score ≥ 80 |
| `--score-mid` | `#ca8a04` | `#facc15` | Score 50–79 |
| `--score-low` | `#64748b` | `#94a3b8` | Score < 50 |

Default: **light mode**. Dark via `prefers-color-scheme` or toggle (defer toggle to post-MVP).

## Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Page title | System UI stack | 18px | 600 |
| List item title (company) | System UI | 14px | 600 |
| List item subtitle (role) | System UI | 13px | 400 |
| Body | System UI | 14px | 400 |
| Meta / timestamps | System UI | 12px | 400 |
| Score badge | Tabular nums | 12px | 600 |
| Monospace (URLs) | ui-monospace | 12px | 400 |

Font stack: `system-ui, -apple-system, "Segoe UI", sans-serif`

No web font loading for MVP — faster, local-tool aesthetic.

## Components

### Score badge

Pill shape. Color by tier:
- **High (≥80):** green background, dark text
- **Mid (50–79):** amber
- **Low (<50):** muted gray

Always show numeric score, not just color.

### Source badge

Small pill next to extracted fields:
- `parser` — blue tint
- `llm` — purple tint
- `manual` — gray (future)

### List item

```
┌─────────────────────────────────────┐
│ Google                    [82]      │
│ SDE Intern · 2h ago · 3 links      │
└─────────────────────────────────────┘
```

- Selected: left border 3px accent + subtle background
- Hover: background shift
- Optional: dimmed if `parser_matched=false` with tooltip "Unparsed template"

### Action buttons

| Button | Style | Position |
|--------|-------|----------|
| Approve | Solid green | Detail footer, primary |
| Reject | Outline red | Detail footer, secondary |
| Retry processing | Outline warning | Error state only |
| Retry export | Outline warning | Export failed state |

HTMX: on approve/reject, animate list item out (optional CSS transition).

### Links list

- Full URL visible (truncated middle if long)
- External link icon
- Domain bold prefix: `careers.google.com` / ...
- Open in new tab (`target="_blank" rel="noopener"`)

### Empty states

| Context | Message |
|---------|---------|
| Empty inbox | "No jobs match your profile right now. Check back later or adjust settings." |
| No selection | "Select a job from the list to review" |
| Processing errors | Link to count + "View errors" (defer dedicated page) |
| Export failed | Inline banner on approved item with Retry |

### Status bar (header)

Compact indicators:
- Telegram: green dot + "Connected" / red + "Disconnected"
- Inbox count badge
- Optional: pending processing count (small)

## Spacing scale

4px base: `4, 8, 12, 16, 24, 32`

- Panel padding: 16px
- List item padding: 12px 16px
- Section gaps in detail: 24px

## Motion

Minimal for HTMX MVP:
- List item fade-out on approve/reject (150ms)
- Detail panel cross-fade on selection (100ms)
- No page transitions

## Accessibility

- Contrast ratio ≥ 4.5:1 for body text
- Focus rings on interactive elements
- Buttons have aria-labels where icon-only
- Score not conveyed by color alone (numeric always shown)

## What NOT to build (MVP)

- Sidebar navigation with 10 items
- Charts/analytics dashboard
- Avatar/user profile chrome
- Marketing hero sections, footers
- Modal dialogs for approve (inline actions only)
- Toast notification library — simple inline banner sufficient

## Implementation notes

- Pure CSS in `app/static/style.css` — no Tailwind build step unless user adds later
- HTMX swaps partials; design components as Jinja2 macros in `templates/partials/`
- Match mockups from design tools loosely — prioritize function over pixel perfection

## Related

- [prompts/ui-design-tool-prompt.md](./prompts/ui-design-tool-prompt.md)
- [api-contract.md](./api-contract.md)
