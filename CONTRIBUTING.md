# Contributing

The Duskmantle Knowledge Management appliance is optimized for experienced operators and coding agents. Please review the following documents before opening a pull request:

1. [`docs/KNOWLEDGE_MANAGEMENT.md`](docs/KNOWLEDGE_MANAGEMENT.md) — System objectives and baseline specification.
2. [`docs/KNOWLEDGE_MANAGEMENT_DESIGN.md`](docs/KNOWLEDGE_MANAGEMENT_DESIGN.md) — Current architectural blueprint for the turnkey container.
3. [`docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md`](docs/KNOWLEDGE_MANAGEMENT_IMPLEMENTATION_PLAN.md) — Phase plan and milestones.
4. [`docs/RISK_MITIGATION_PLAN.md`](docs/RISK_MITIGATION_PLAN.md) — Active risk mitigations and open questions.
5. [`AGENTS.md`](AGENTS.md) — Contributor workflow and coding conventions.

## Getting Started
- Use Python 3.12+ and follow the setup steps in the README to build the container locally.
- Keep changes scoped; bundle related code, config, and documentation updates together.
- Add or update tests under `tests/` and run the smoke container tests before submitting.

## Pull Request Checklist
- [ ] Conventional Commit-style title (`feat:`, `fix:`, `docs:`...)
- [ ] Description covering scope, testing, and risk mitigation impact
- [ ] Updated documentation or configuration references as needed
- [ ] Added/updated tests and smoke runs where applicable

We will iterate on contribution policies as the project matures. If you encounter blockers, open a discussion issue with host environment details and reproduction steps.
