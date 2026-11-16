<!--
Sync Impact Report
- Version change: template (unversioned) → 1.0.0
- Modified principles: all template placeholders replaced (initial adoption)
  - [PRINCIPLE_1_NAME] → I. Separation of Responsibilities (NON-NEGOTIABLE)
  - [PRINCIPLE_2_NAME] → II. Security by Default
  - [PRINCIPLE_3_NAME] → III. Data Integrity Under Concurrency
  - [PRINCIPLE_4_NAME] → IV. Evidence-Based Quality
  - [PRINCIPLE_5_NAME] → V. Simplicity and Incremental Growth
  - (added) VI. Traceable Decisions
- Added sections: Architectural Constraints; Development Workflow & Quality Gates;
  Governance (filled)
- Removed sections: none
- Pre-ratification amendment (version kept at 1.0.0, not yet committed):
  - Architectural Constraints: fixed four-layer list replaced by inward
    dependency rule + per-feature simplest structure decided in the plan
  - Development Workflow: added analyze and converge steps; analyze findings
    gate implementation; "implemented" vs "complete" definitions split
- Templates: not modified (dependent templates read the constitution at runtime)
- Follow-up TODOs: none
-->

# ChangeFlow Constitution

ChangeFlow is a change-request management system delivered as an HTTP API and
extended feature by feature. This constitution defines the rules every feature,
plan, and task MUST satisfy.

## Core Principles

### I. Separation of Responsibilities (NON-NEGOTIABLE)

- All business rules MUST live in the Domain or Application layer.
- API handlers MUST only: parse the request, call exactly one use case, and map
  the result or error to an HTTP response.
- API handlers MUST NOT contain any condition on request status, ownership, or
  role.
- The Domain layer MUST NOT depend on HTTP or persistence libraries.

**Rationale**: Business rules that live in one place can be tested in isolation
and are applied identically regardless of entry point. Rules leaked into
handlers get duplicated, drift, and are bypassed by new entry points.

### II. Security by Default

- Every state-changing operation MUST verify identity, current permission, and
  current request state before changing anything.
- Access MUST be denied unless explicitly allowed.
- Authorization rules that protect business integrity (e.g. no self-approval)
  MUST be enforced in the Domain, so every entry point inherits them.

**Rationale**: Permissions and state change over time; checking them at the
moment of the write, and denying by default, prevents privilege mistakes from
becoming integrity violations.

### III. Data Integrity Under Concurrency

- No write may silently overwrite a newer change. Stale writes MUST be rejected
  with an explicit conflict result.
- A request MUST never be left in a state outside the defined workflow; a
  failed operation MUST leave the request in its prior valid state.

**Rationale**: Multiple actors act on the same request. Lost updates and
invalid intermediate states corrupt the audit value of the system.

### IV. Evidence-Based Quality

- Domain rules MUST have unit tests that run without HTTP or a database.
- Every state transition and every authorization rule MUST have an automated
  test, covering both the allowed and the rejected case.
- Sensitive tests (authorization, state transitions, concurrency conflicts)
  MUST verify the persisted state, not only the HTTP response.
- Only real, reproducible build and test results may be reported. Results that
  were not actually executed MUST NOT be claimed.

**Rationale**: A passing HTTP status does not prove that the stored data is
correct; only observed, repeatable evidence counts as proof of quality.

### V. Simplicity and Incremental Growth

- No layer, abstraction, or dependency may be added without a present,
  documented need.
- Features outside the current scope MUST NOT be implemented early.

**Rationale**: The system grows feature by feature. Speculative structure adds
cost and constrains future features before their requirements are known.

### VI. Traceable Decisions

- Product behaviour not stated in the requirements MUST be resolved through
  clarification or recorded as a reviewable assumption; it MUST NOT be decided
  silently in code.
- Technology choices MUST be justified in research artifacts, not in this
  constitution.

**Rationale**: Unrecorded decisions cannot be reviewed, challenged, or
reversed deliberately.

## Architectural Constraints

- Dependencies point inward: API handlers and persistence code depend on
  Application/Domain, never the reverse.
- The concrete layer and folder structure is decided per feature in the plan
  and MUST be the simplest structure that satisfies Principle I.
- Use-case results and errors MUST be explicit (e.g. not found, forbidden,
  invalid state, conflict, validation error) so handlers map them to HTTP
  responses without business logic.
- The request workflow (states and allowed transitions) MUST be defined in the
  Domain as the single source of truth.

## Development Workflow & Quality Gates

- Each feature follows specify → clarify (when ambiguities exist) → plan →
  tasks → analyze → implement → converge.
- Findings from analyze MUST be resolved or explicitly accepted in writing
  before implementation starts.
- Every plan MUST include a Constitution Check against Principles I–VI before
  design and again after design.
- Assumptions made during specification or planning MUST be listed explicitly
  in the spec or plan for review.
- A feature is implemented when its build succeeds and its automated tests
  pass in a reproducible run, with the actual output available. It is complete
  only when, in addition, converge reports no open gap against the spec and
  this constitution, and every human acceptance criterion has been evaluated
  by a responsible person with the real result recorded. Unfinished or
  unevaluated items MUST be reported as such.

## Governance

- This constitution overrides plans, tasks, and other practices. Where they
  conflict, the constitution wins.
- Any deviation MUST be justified in writing in the plan's Complexity
  Tracking (or equivalent) section, stating the violated rule, the reason, and
  the simpler alternative that was rejected.
- Amendments require a written reason and a version bump following semantic
  versioning:
  - MAJOR: removal or backward-incompatible redefinition of a principle or
    governance rule.
  - MINOR: a new principle or section, or materially expanded guidance.
  - PATCH: clarifications and wording fixes without semantic change.
- Reviews of specs, plans, tasks, and code MUST verify compliance with this
  constitution.

**Version**: 1.0.0 | **Ratified**: 2026-11-17 | **Last Amended**: 2026-11-17
