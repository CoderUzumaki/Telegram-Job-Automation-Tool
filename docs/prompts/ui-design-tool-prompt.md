# UI Design Prompt — Stitch / v0 / Lovable

Copy everything below the line into your design tool.

---

## Prompt

Design a **desktop-first web UI** for **Telegram Job Radar** — a personal job-post triage inbox for a single user. This is a local productivity tool (like a mail client), not a SaaS marketing product. The backend will be FastAPI + HTMX; your design will be adapted to server-rendered HTML with minimal JavaScript.

### Product context

The user monitors a private Telegram channel with ~100 job posts per day. An automated pipeline parses each post, scores relevance with AI, and surfaces the best matches in an inbox. The user reviews each job, clicks approve or reject, and approved jobs export to Google Sheets with URLs and parsed fields pre-filled.

**Core pain solved:** No more manually copying URLs or re-typing company/role from Telegram posts.

### Primary screen: Master-detail inbox

Design the main triage experience:

**Left panel — Inbox list (~360px fixed width)**
- Scrollable list of job cards, sorted by relevance score (highest first)
- Each list item shows:
  - Company name (primary, bold)
  - Role title (secondary)
  - Relevance score badge (0–100, color-coded: green ≥80, amber 50–79, gray <50)
  - Relative time ("2h ago")
  - Link count ("3 links")
- Selected item: accent left border + highlighted background
- Hover state on items
- Header shows inbox count badge, e.g. "Inbox (12)"

**Right panel — Detail view (flexible width)**
- Empty state when nothing selected: "Select a job to review"
- When selected, show:
  - **Header:** Company · Role, score badge, posted time
  - **Extracted fields table:** Company, Role, Batch, Stipend, Location — each with a small source pill (`parser` in blue, `llm` in purple)
  - **Tags row:** chips like `ppo`, `remote`, `hybrid`
  - **Links section:** clickable URL list with domain emphasized, external-link icon, 2–4 links typical
  - **Relevance reason:** 1–2 sentence AI explanation in a subtle quote/callout block
  - **Raw post:** collapsible section (collapsed by default) showing original Telegram text
  - **Action bar (sticky bottom):** primary green "Approve" button, secondary outline "Reject" button

**Top navigation bar**
- App name: "Job Radar"
- Nav links: Inbox (active), Settings
- Status indicators on the right:
  - Telegram connection: green dot + "Connected"
  - Optional subtle sync time

### Secondary screen: Settings

Single-page settings with clear sections:

1. **Job profile** — textarea or tag input for target roles, skills, preferred locations
2. **Filter rules** — include keywords (green) and exclude keywords (red), tag-style inputs
3. **Score threshold** — slider 0–100 with current value label ("Show jobs scoring above 65")
4. **Integrations status**
   - Telegram: connected / reconnect hint
   - Google Sheets: connected / "Export to CSV instead" note
5. **Save** button per section with inline success feedback

### Visual style

- **Aesthetic:** Clean, utilitarian, calm — think Superhuman meets Linear, but simpler. No gradients, no illustrations, no hero sections.
- **Density:** Information-dense list; user scans 20–30 items quickly. Prefer compact over spacious.
- **Color mode:** Light mode primary; optionally show a dark mode variant.
- **Palette suggestions:**
  - Background: off-white `#f8f9fa`
  - Surface/cards: white with subtle border `#e2e8f0`
  - Text: near-black `#1a202c`, muted `#64748b`
  - Accent/links: blue `#3b82f6`
  - Approve/success: green `#16a34a`
  - Reject/danger: red `#dc2626`
- **Typography:** System font stack only (no custom web fonts). Tabular nums for scores.
- **Icons:** Minimal line icons for external links, connection status, collapse/expand

### States to design

1. **Default inbox** with 5–6 list items and one selected showing full detail
2. **Empty inbox** — friendly message suggesting settings adjustment
3. **Export failed banner** on an approved item — amber warning + "Retry export" button
4. **Parser unmatched indicator** — subtle dimmed list item or small warning icon with tooltip "Template not recognized; fields may be incomplete"
5. **Settings page** with sample data filled in

### Sample data for mockups

Use realistic Indian tech job post context:

| Company | Role | Score | Tags |
|---------|------|-------|------|
| Google | SDE Intern | 82 | ppo, remote |
| Amazon | SDE-1 | 76 | hybrid |
| Razorpay | Backend Intern | 71 | fintech |
| Startup XYZ | Full Stack | 45 | — |
| Infosys | Systems Engineer | 38 | — |

Detail panel example for Google:
- Batch: 2025 (parser)
- Location: Remote (llm)
- Links: `careers.google.com/jobs/...`, `forms.gle/abc123`
- Reason: "Matches your SDE intern target, remote-friendly, PPO mentioned."

### Interaction notes (for implementation reference)

- Clicking list item updates detail panel without full page reload (HTMX pattern)
- Approve removes item from list with subtle animation
- No modal dialogs for approve/reject — inline actions only
- Desktop-only for MVP (1280px+ viewport); mobile can wait

### Do NOT include

- User avatars or social features
- Analytics dashboards or charts
- Multi-user admin panels
- Marketing landing page elements
- Sidebar with 10+ navigation items
- Chat or messaging UI

### Deliverables requested

1. Inbox master-detail screen (primary)
2. Settings screen
3. Component specs: score badge, source pill, list item, link row, action buttons
4. Light mode required; dark mode optional bonus

### Output format preference

Provide high-fidelity mockups with consistent spacing (4px grid), component names labeled, and hex colors documented for handoff to a developer implementing plain CSS + HTML templates.

---

## Tips for each tool

| Tool | Suggestion |
|------|------------|
| **v0** | Paste full prompt; ask for React first then note "adapt aesthetic to plain HTML/CSS" |
| **Stitch (Google)** | Emphasize master-detail layout and sample data table |
| **Lovable** | May generate React — focus on layout/components; ignore routing/auth boilerplate |

After generating mockups, save exports to `docs/design-exports/` for reference during Step 5 implementation.
