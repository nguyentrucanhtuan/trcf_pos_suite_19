---
name: trcf-odoo19-module
description: >
  Engineer Odoo Community modules for version 19+, including new module creation, feature modification, and algorithm optimization.
  Use when Claude needs to: (1) scaffold new modules, (2) upgrade/refactor existing modules, (3) debug backend/frontend issues
  across ORM, Views/XML, Security, Controllers, and OWL, (4) optimize performance and business logic algorithms,
  (5) run install/upgrade validation and testing with a release goal of zero ERROR/CRITICAL and no unresolved warnings in test logs.
---

# Phát triển Module Odoo 19

## Core Workflow

1. Capture requirements and constraints.
Identify module scope, target app flow (POS/Inventory/Sales/Purchase/HR/Accounting), acceptance criteria, and technical constraints before coding.

2. Select execution path.
Choose one path: `new_module`, `modify_module`, `bug_fix`, or `algorithm_optimization`, then load only the required reference files.

3. Implement with TRCF standards.
Build or update models, views, security, controllers, and OWL components using TRCF naming, Odoo 19+ conventions, and minimal-risk refactoring.

4. Run mandatory verification.
Run install or upgrade command, check logs, and confirm zero `ERROR`/`CRITICAL`; treat unresolved warnings as release blockers until validated or fixed.

5. Validate behavior and performance.
Verify business flow, access rights, UI rendering, algorithm correctness, and query/performance impact for changed areas.

6. Deliver production-ready output.
Return changed files, executed test commands, log summary, remaining risks (if any), and next actions; do not claim completion if validation gates fail.

## Routing Rules

- If the request is `new_module`, use `assets/module_template/` first, then read `references/ORM_REFERENCE.md` and `references/VIEWS_REFERENCE.md`.
- If the request is `modify_module`, inspect current code impact first, then read only the relevant references for changed layers (ORM/Views/Controllers/OWL/Security).
- If the request is `bug_fix`, read `references/TROUBLESHOOTING.md` first, reproduce the issue, apply minimal fix, and run install/upgrade validation.
- If the request is `algorithm_optimization`, profile query and logic hotspots first, then read `references/BEST_PRACTICES.md` and ORM guidance before refactoring.
- If the request includes OWL/frontend behavior, read `references/OWL_GUIDE.md` before changing JS/XML templates.
- If the request includes HTTP/API flows, read `references/CONTROLLERS_REFERENCE.md` before changing routes/controllers.
- If the request includes test scope, release readiness, or quality checks, read `references/TESTING_CHECKLIST.md` and execute mandatory verification gates.
- Always load the minimum required references; avoid loading all reference files by default.

## Testing & Verification Gates

Apply all gates for any code change. A task is `PASS` only when all required gates pass.

- Gate 1: Install/Upgrade integrity.
Run install (`-i`) for new modules or upgrade (`-u`) for existing modules. Fail if command exits non-zero.
If execution cannot be performed (environment/access limitation), mark gate as `FAIL` with `Not Executed` evidence.

- Gate 2: Log hygiene.
Fail if logs contain any `ERROR` or `CRITICAL`. Treat unresolved warnings as blockers unless explicitly justified and accepted by user.

- Gate 3: View and model validity.
Fail if XML/view parsing, field definition, access rule, or dependency issues appear during startup/update.

- Gate 4: Functional smoke test.
Validate the changed business flow end-to-end (create/edit/confirm/search/report actions as relevant). Fail on any broken flow.

- Gate 5: Security and access.
Validate role-based access (`ir.model.access.csv`, record rules if any). Fail if unauthorized actions are allowed or authorized actions are blocked.

- Gate 6: Performance sanity for algorithm changes.
For optimization tasks, compare before/after behavior and query load. Fail if latency or query count regresses without business justification.

- Gate 7: Delivery readiness.
Do not claim completion unless all required gates pass. If any gate fails, return blocker details, root cause, and next fix actions.
Never infer successful verification without command evidence.

## Output Contract

For every implementation task, return output in a release-oriented structure.

- Section 1: Scope summary.
State requested objective, implemented approach, and affected module/domain scope.

- Section 2: Changed artifacts.
List all changed files with short purpose per file (model/view/security/controller/owl/test/data).

- Section 3: Executed verification.
List exact commands executed for install/upgrade/test and relevant environment assumptions.

- Section 4: Gate status.
Report each verification gate as `PASS` or `FAIL` with concise evidence.

- Section 5: Log summary.
Report whether logs contain `ERROR`/`CRITICAL`; if warnings exist, classify as resolved or unresolved with reason.

- Section 6: Functional validation summary.
Describe tested business flows and observed outcomes.

- Section 7: Risks and next actions.
If any gate fails, return blocker, root cause hypothesis, and concrete next fix step. If all gates pass, mark output as ready for deployment validation.

## Self-Upgrade Loop

Continuously improve the skill after real task execution.

- Trigger for update.
Apply this loop when a new error pattern, a missing guardrail, or a repeatable optimization pattern is discovered.

- Update troubleshooting knowledge.
Append new entries to `references/TROUBLESHOOTING.md` using format: `Error -> Cause -> Fix -> Verification`.

- Update best-practice knowledge.
Append validated implementation patterns to `references/BEST_PRACTICES.md` with context, constraints, and expected impact.

- Promote stable patterns.
If a pattern repeats and is deterministic, convert it into a script under `scripts/` or into a reusable template under `assets/`.

- Prevent noisy updates.
Do not add speculative notes. Only persist knowledge that has been reproduced or validated in at least one real fix.

- Keep references lean.
Merge duplicates, remove obsolete guidance, and keep entries concise to avoid context bloat.

## Resource Map

Use resources intentionally to minimize context load and maximize execution reliability.

- `references/ORM_REFERENCE.md`
Load for models, fields, compute/inverse, constraints, ORM APIs, and data integrity logic.

- `references/VIEWS_REFERENCE.md`
Load for XML structure, list/form/search views, modifiers, actions, and view validation fixes.

- `references/CONTROLLERS_REFERENCE.md`
Load for HTTP/JSON routes, request handling, auth/csrf/cors decisions, and controller patterns.

- `references/OWL_GUIDE.md`
Load for OWL components, services/hooks/state, frontend architecture, and JS/XML integration.

- `references/TESTING_CHECKLIST.md`
Load when building the verification plan, smoke tests, release checks, and regression scope.

- `references/TROUBLESHOOTING.md`
Load first for bug-fix tasks, startup/update failures, traceback interpretation, and recurring issue handling.

- `references/BEST_PRACTICES.md`
Load for optimization/refactor tasks and for selecting robust patterns after functionality is stable.

- `assets/module_template/`
Use for new module scaffolding and consistent TRCF baseline structure before custom implementation.

- `scripts/` (create when needed)
Create deterministic scripts for repeated tasks such as scaffold automation, structure linting, and verification orchestration.
Only add scripts when the same manual process appears repeatedly or is error-prone.

## Implementation Standards

Apply these standards to all created or modified Odoo 19+ Community modules.

- Naming and module structure.
Use `trcf_` prefix for module folders and consistent technical names for models, views, actions, and XML IDs.

- Backend model quality.
Require explicit `_description`, clear field semantics, safe compute/depends logic, and minimal side effects in create/write overrides.

- View correctness.
Use Odoo 19-compatible view tags and modifiers, keep forms readable, and ensure actions/menus/search views are coherent.

- Security first.
Define `ir.model.access.csv` for all user-facing models and add record rules when row-level isolation is required.

- Algorithm optimization policy.
Prefer reducing query count, avoiding N+1 patterns, and using ORM-native aggregation/batching before micro-optimizations.

- Refactor discipline.
Keep changes scoped to requirement boundaries, preserve backward-compatible behavior when possible, and document risky changes in output summary.

- OWL/frontend discipline.
Use service-based architecture, explicit state transitions, and predictable component lifecycle handling for maintainable UI behavior.

## Command Baseline

Use these commands as the default verification entry points.

```bash
# Install new module
./odoo-bin -c odoo19.conf -d <database> -i <module_name> --stop-after-init

# Upgrade existing module
./odoo-bin -c odoo19.conf -d <database> -u <module_name> --stop-after-init

# Development mode for frontend/XML iteration
./odoo-bin -c odoo19.conf -d <database> --dev=xml,css,js

# Full debug mode
./odoo-bin -c odoo19.conf -d <database> --dev=all

# SQL logging for performance diagnosis
./odoo-bin -c odoo19.conf -d <database> --log-sql
```

## Maintenance Rules

- Keep `SKILL.md` orchestration-focused; keep deep technical detail in `references/`.
- When a new recurring operation appears, promote it to `scripts/`.
- When creating new module scaffolding assets, update `assets/module_template/` and document usage in `Resource Map`.
- For any `references/*.md` file longer than 100 lines, maintain a concise table of contents at the top.
