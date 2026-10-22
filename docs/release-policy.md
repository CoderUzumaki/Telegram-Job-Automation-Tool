# Release policy register

Status: BLOCKED / UNVERIFIED. Recorded 2026-10-23 for JR-002, from LLD §§20–21. No current legal review has been performed. Whether the proposed product use is permitted remains unresolved. Offline development can proceed; public beta requires human review and resolution of these gates.

Owner roles below are assigned to the project maintainer until named reviewers are appointed. Evidence must include reviewer, review date, applicable terms/version, permitted scope and remaining restrictions. No row is cleared by this document.

| Gate | Accountable owner | Required evidence | Status |
|---|---|---|---|
| Telegram API terms and read-only client obligations | Project maintainer (policy review) | Current terms assessment of this exact job-monitoring workflow; independent advice or platform clarification where needed | UNVERIFIED |
| Content licensing and processing rights | Project maintainer (policy review) | Permission basis for retaining and processing postings; restrictions reflected in product scope | UNVERIFIED |
| Private-group access and consent | Project maintainer (privacy review) | Account access plus source consent model; participant rights assessed separately from user opt-in | UNVERIFIED |
| Branding and client identification | Project maintainer (design review) | App name, assets and disclosures reviewed against current requirements | UNVERIFIED |
| API ID/API hash distribution | Project maintainer (release engineering) | Approved credential provisioning/distribution design; no secrets in repository or diagnostics | UNVERIFIED |
| Sponsored channel content | Project maintainer (policy review) | Applicability assessment and compliant handling or documented scope restriction | UNVERIFIED |
| AI/ML restrictions | Project maintainer (policy review) | Current requirements reviewed; MVP remains rule-based with no Telegram-content LLM processing | UNVERIFIED |
| Session protection and privacy deletion | Project maintainer (security review) | OS-store restore/no plaintext evidence, privacy notice, retention and provenance erasure tests | UNVERIFIED |
| Native distribution | Project maintainer (release engineering) | Per-platform installer, signing, lifecycle and upgrade evidence | UNVERIFIED |

If a gate blocks the workflow, constrain or redesign the product and record an ADR. Do not bypass restrictions. Human checklist review is outstanding; this register is not legal clearance.

Official sources for the reviewer (not verified in this task): [Telegram API terms](https://core.telegram.org/api/terms), [Telegram API application setup](https://core.telegram.org/api/obtaining_api_id). Recheck sources at release time.

See [architecture decisions](decisions/README.md) for technical boundaries.

