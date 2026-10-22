# Architecture decisions

JR-002 records the existing LLD baseline; it does not certify implementation or release readiness. Human review remains pending. Local authoritative specifications are in Agent_Docs (not tracked); these records preserve the implementation-facing decisions in Git.

- [ADR-0001: Local modular monolith without HTTP](ADR-0001.md)
- [ADR-0002: Private versioned IPC](ADR-0002.md)
- [ADR-0003: Single database writer and transactional ports](ADR-0003.md)
- [ADR-0004: Local-first retention and provenance](ADR-0004.md)
- [ADR-0005: Validated external application actions](ADR-0005.md)
- [ADR-0006: Telegram behind an application-owned port](ADR-0006.md)
- [ADR-0007: Staged native platform strategy](ADR-0007.md)
- [ADR template](template.md)
- [Release policy register](../release-policy.md)

Prefer high cohesion within modules and loose coupling between them. Domain policies depend on values and ports, application services coordinate them, infrastructure implements ports, and composition roots wire concrete dependencies. Avoid shared mutable globals and feature modules importing each other's adapter internals.

Next implementation: JR-003, host/worker IPC and supervisor. The existing UI remains a state-only prototype.

