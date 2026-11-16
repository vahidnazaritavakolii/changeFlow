# Analysis: Change Request Workflow (First Version)

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Tasks**: [tasks.md](./tasks.md)
| **Date**: 2026-11-17

This file records the `/speckit-analyze` report, the human review findings, and the written
decision on every finding required by the constitution before implementation starts.

## Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | spec.md:258 (FR-015a), spec.md:191 (edge case); data-model.md:58; tasks.md:82 (T005), tasks.md:231 (T025) | FR-015(a) lets a requester always see their own request. data-model.md and T005 say a user with no roles sees nothing. So an owner who has lost the Requester role gets **404** under the data model, but **403** under the spec's edge case and T025. | Decide: the owner always sees their own request (recommended; matches the FR-015 wording and the edge case). Then update the visibility table in data-model.md and T005. |
| I2 | Inconsistency | HIGH | spec.md:233 (FR-008) vs spec.md:258 (FR-015), FR-020, US1 scenario 6 | FR-008 says edit or submit by a non-owner is **forbidden**. FR-015 and FR-020 say a Requester-only non-owner gets **not found**, because they can't see the request. | Reword FR-008 to apply only to callers who can see the request; anyone else gets not found under FR-015. |
| I3 | Inconsistency | MEDIUM | spec.md:111 (US2 scenario 4) | "A user without the Reviewer role tries to approve → forbidden" only holds if that user can see the request. A non-owner without the Reviewer role gets 404. T032 already handles this; the spec text is ambiguous. | Change the scenario to "the request's requester, who lacks the Reviewer role" and add the 404 case for others. |
| I4 | Inconsistency | LOW | spec.md:218 (FR-003); data-model.md:49 | FR-003 says any invalid transition gets "invalid status", but under FR-020 a forbidden, invalid-input or conflict failure is reported first. | Add "subject to the check order in FR-020". |
| I5 | Inconsistency | LOW | checklists/requirements.md:39 | The checklist note still says A1–A5 are reviewable assumptions; they are now requirements. (The checklist is outside the three core files.) | Update the note (you held this back earlier). |
| D1 | Duplication | LOW | spec.md:228 (FR-006), spec.md:235 (FR-009) | FR-009 ("Approved not editable") repeats the Approved clause of FR-006. | Keep both, or make FR-009 refer to FR-006. |
| C1 | Coverage | LOW | spec.md:199 (edge case) | No task tests "an edit that changes nothing is a normal edit" (version still goes up by one). | Add a test case to T027. |
| C2 | Coverage | LOW | FR-019, FR-021; contracts/http-api.md "Not provided" | FR-021 is tested only in the Domain (T004). Nothing checks over HTTP that `DELETE /change-requests/{id}` and other unlisted routes are rejected. | Add a test case to T026 asserting 404 or 405 with the row unchanged. |
| U1 | Underspecification | LOW | contracts/http-api.md; tasks T009/T028 | The behaviour for unknown extra fields in a request body is not stated. | State in the contract that extra fields are ignored (or rejected), and test it. |
| A1 | Ambiguity | LOW | spec A6; tasks T005/T009/T031 | The field limits in A6 are still an open assumption but are written into several tasks. | Keep the limits as one constant in `rules.py` so a decision on A6 is a single edit. |
| T1 | Terminology | LOW | data-model.md (`requester`, `reviewer`), spec (Requester, Reviewer); RequestChanges / `request-changes` / `request_changes` | Each concept has several spellings across the files. The mapping is consistent, but nowhere states it. | Add a one-line naming note to data-model.md. |
| X1 | Task quality | LOW | tasks.md US3/US4 notes, T038, T041 | US3 and US4 tests will probably pass when written, so "write tests first and watch them fail" gives less evidence there. tasks.md already says so. | Accept as written, or merge the US3/US4 tests into US1/US2. |

**Coverage summary**

| Requirement | Has task? | Task IDs | Notes |
|-------------|-----------|----------|-------|
| FR-001 | Yes | T008, T011, T014 | |
| FR-002 | Yes | T004, T008 | |
| FR-003 | Yes | T009, T025, T031 | Wording: I4 |
| FR-004 | Yes | T005, T009, T026 | |
| FR-005 | Yes | T025, T026, T028 | |
| FR-006 | Yes | T025, T027, T028, T039 | |
| FR-007 | Yes | T027, T028 | |
| FR-008 | Yes | T025, T027 | Conflict: I2 |
| FR-009 | Yes | T025, T027, T040 | |
| FR-010 | Yes | T031–T035 | |
| FR-011 | Yes | T031, T033 | |
| FR-012 | Yes | T031, T032, T033 | |
| FR-013 | Yes | T018, T026, T032 | |
| FR-014 | Yes | T016, T036–T038 | |
| FR-015 | Yes | T005, T009, T026, T029 | Conflict: I1 |
| FR-016 | Yes | T031, T032, T033 | |
| FR-017 | Yes | T004 | |
| FR-018 | Yes | T020, T026, T027, T037 | |
| FR-019 | Partial | T025 | No HTTP check: C2 |
| FR-020 | Yes | T025, T031, T037 | |
| FR-021 | Partial | T004 | Domain only: C2 |
| FR-022 | Yes | T027 | |
| FR-023 | Yes | T015, T032 | |
| SC-001 | Yes | T032 | |
| SC-002 | Yes | T036, T037 | |
| SC-003 | Yes | T027, T037 | |
| SC-004 | Yes | T042 | |
| SC-005 | Yes | T040 | |
| SC-006 | Yes | T014 | |

**Constitution alignment:** no violations.
- Principle I: the plan and the architecture test (T024) enforce it.
- Principle IV: there are tests per transition and per rule, checks on stored rows, and a recorded final run (T044).
- Governance gate: the constitution requires these findings to be fixed or accepted in writing before implementation. No file records that yet.

**Unmapped tasks:** none. The setup and polish tasks (T001–T003, T042–T044) support everything rather than one requirement.

**Metrics**
- Total requirements: 29 (23 FR + 6 SC)
- Total tasks: 44
- Coverage: 100% have at least one task (FR-019 and FR-021 only partly)
- Ambiguities: 2 (U1, A1)
- Duplications: 1 (D1)
- Critical issues: 0

### Next actions
- With no critical issues, implementation isn't blocked, but **fix I1 and I2 before `/speckit-implement`**: they change which status code the tests expect.
  - **I1:** edit FR-015 and the edge cases in spec.md, the visibility table in data-model.md, and T005 in tasks.md.
  - **I2 and I3:** reword FR-008 and US2 scenario 4 in spec.md.
- **C1 and C2:** add the test cases to T026 and T027 in tasks.md.
- The other low findings can be accepted as they are. Either way, record each finding as fixed or accepted, for example in a short section of plan.md, to meet the constitution's gate.

## Human review findings

- **H1** — plan.md "Performance Goals" says "SC-006/A8 removed", but after renumbering SC-006
  now means "no status outside the workflow".
- **H2** — plan.md "Structure Decision" says the four packages match "the four responsibilities
  required by Principle I"; Principle I does not require four layers, the justification is
  research R8.
- **H3** — README.md is a deliverable but has no task.

## Decisions

| ID | Decision | Reason | Files changed |
|----|----------|--------|---------------|
| I1 | Fixed | The owner of a request can always view it, with or without any role; an owner without the Requester role gets forbidden on edit and submit | spec.md (FR-015, role-removed edge case), data-model.md (visibility table), tasks.md (T005, T025, T029), plan.md (PA-3) |
| I2 | Fixed | "Forbidden" in FR-008 applies only to callers who can see the request; others get "not found" under FR-015 | spec.md (FR-008) |
| I3 | Fixed | US2 scenario 4 now names the request's requester without the Reviewer role (forbidden) and adds the not-found case | spec.md (US2 scenario 4) |
| I4 | Fixed | FR-003 is made subject to the FR-020 check order | spec.md (FR-003) |
| I5 | Fixed | Stale note about A1–A5 corrected | checklists/requirements.md |
| D1 | Accepted | FR-009 kept for traceability to product rule 5 | — |
| C1 | Fixed | Test added: edit with identical values succeeds and increases the version by one | tasks.md (T027) |
| C2 | Fixed | Test added: `DELETE /change-requests/{id}` and an unlisted route are rejected (404 or 405) with the stored row unchanged | tasks.md (T026) |
| U1 | Fixed | Unknown extra body fields are ignored (planning assumption PA-7), stated in the contract and tested | plan.md (PA-7), contracts/http-api.md, tasks.md (T027) |
| A1 | Fixed | Field limits required as module-level constants in `rules.py` | tasks.md (T009) |
| T1 | Fixed | One-line naming note added | data-model.md |
| X1 | Accepted | Already documented in tasks.md (US3/US4 notes) | — |
| H1 | Fixed | Wording no longer reuses the live identifier SC-006 | plan.md (Performance Goals) |
| H2 | Fixed | Structure Decision now points to research R8 instead of Principle I | plan.md (Structure Decision) |
| H3 | Accepted | README is written after converge | — |
