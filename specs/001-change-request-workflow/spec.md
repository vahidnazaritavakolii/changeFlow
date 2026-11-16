# Feature Specification: Change Request Workflow (First Version)

**Feature Branch**: none created (work is on `main`; spec directory `specs/001-change-request-workflow`)

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "ChangeFlow — change request workflow (first version). Employees
submit change requests that must be reviewed before final approval; nobody may approve their own
request. Roles: Requester, Reviewer (one user may hold both). Workflow: Draft → PendingReview →
Approved / ChangesRequested → PendingReview. Seven confirmed product rules; eight undecided
behaviours to be clarified or recorded as assumptions. HTTP API only; UI, notifications,
execution of approved changes, user/role administration and AI capabilities are out of scope."

## Clarifications

### Session 2026-11-17

- Q: Who may view or list change requests created by other users, and what does a caller get
  when opening a request they may not see? → A: Requesters see only their own requests;
  Reviewers see all requests; a request the caller may not see is reported as "not found".
- Q: If a user holds both roles, may they use RequestChanges on a request they created? → A: No.
  It is forbidden, like self-approval; every review decision comes from someone other than the
  requester.
- Q: Should this version add a terminal rejection by a reviewer and/or cancellation by the
  requester? → A: Neither. Only the four statuses Draft, PendingReview, ChangesRequested and
  Approved exist; rejection and cancellation are out of scope for this version.
- Q: When an operation fails several checks at once, in what order are they applied? → A:
  identity → existence/visibility ("not found") → permission ("forbidden") → input validity,
  including missing version ("invalid input") → version ("conflict") → status ("invalid
  status"); the first failing check determines the single reported outcome.
- Q: Should this version keep a performance target (SC-006/A8), and should SC-002 stay a
  100-run stress test? → A: Remove SC-006 and A8 (performance targets out of scope for this
  version); replace SC-002 with a deterministic criterion: every state-changing operation based
  on an outdated version is rejected as conflict with stored data unchanged, and of two
  operations based on the same version exactly one succeeds. (Former SC-007 renumbered SC-006.)
- Q: Should each of assumptions A1–A7 become a confirmed decision or stay an open reviewable
  assumption? → A: A1–A5 are confirmed decisions (now FR-021–FR-023, FR-006, FR-011); A6
  (field limits) and A7 (identity mechanism) remain open reviewable assumptions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create, edit and submit a change request (Priority: P1)

An employee with the Requester role records a proposed change (title, description, reason). The
request starts as a Draft that only its owner can edit. When it is ready, the owner submits it,
and it moves to PendingReview.

**Why this priority**: Without capturing and submitting requests there is nothing to review. This
is the entry point of the whole workflow and on its own already replaces informal requests with a
recorded, owned, structured request.

**Independent Test**: A Requester creates a request, edits it, submits it, and reads it back. Its
stored content matches the last edit and its status is PendingReview.

**Acceptance Scenarios**:

1. **Given** an authenticated user with the Requester role, **When** they create a request with a
   title, description and reason, **Then** the request is stored with status Draft, with that user
   recorded as requester, and an initial version.
2. **Given** a Draft owned by the caller, **When** the caller edits its title, description or
   reason using the request's current version, **Then** the changes are stored and the version
   changes.
3. **Given** a Draft owned by the caller, **When** the caller submits it using its current
   version, **Then** its status becomes PendingReview.
4. **Given** a user without the Requester role, **When** they try to create a request, **Then**
   the operation is rejected as forbidden and no request is stored.
5. **Given** a request missing a title, description or reason (or with only blank text),
   **When** a Requester tries to create or edit it, **Then** the operation is rejected as invalid
   input and nothing is stored or changed.
6. **Given** a Draft owned by user A, **When** user B holding only the Requester role tries to
   view, edit or submit it, **Then** the operation is rejected as not found and the stored
   request is unchanged; **When** user B holds the Reviewer role and tries to edit or submit it,
   **Then** the operation is rejected as forbidden and the stored request is unchanged.
9. **Given** requests owned by users A and B, **When** user A (Requester only) lists requests,
   **Then** only A's requests are returned; **When** a Reviewer lists requests, **Then** both
   users' requests are returned.
7. **Given** an unauthenticated caller, **When** they attempt any operation, **Then** it is
   rejected as unauthenticated and nothing is changed.
8. **Given** a request in PendingReview or Approved, **When** its owner tries to edit it,
   **Then** the operation is rejected as not allowed in the current status and the stored request
   is unchanged.

---

### User Story 2 - Review: approve or request changes (Priority: P2)

A user with the Reviewer role looks at a request that is pending review and either approves it or
returns it to the requester with a reason explaining what must change. A reviewer can never
approve a request they created themselves, even if they also hold the Requester role.

**Why this priority**: Review is the core business value — changes are formally checked before
approval — and the self-approval ban is the system's main integrity rule. It depends on Story 1
producing pending requests.

**Independent Test**: With a request in PendingReview created by user A, user B (Reviewer)
approves it and the stored status is Approved; in a separate setup, user A (holding both roles)
tries to approve their own request and the stored status remains PendingReview.

**Acceptance Scenarios**:

1. **Given** a request in PendingReview created by another user, **When** a Reviewer approves it
   using its current version, **Then** its status becomes Approved.
2. **Given** a request in PendingReview created by another user, **When** a Reviewer requests
   changes with a non-blank reason using its current version, **Then** its status becomes
   ChangesRequested and the reason is stored with the request and visible to its requester.
3. **Given** a request in PendingReview created by user A, who also holds the Reviewer role,
   **When** user A tries to approve it, **Then** the operation is rejected as forbidden
   (self-approval) and the stored status remains PendingReview.
4. **Given** a request in PendingReview, **When** a user without the Reviewer role tries to
   approve it or request changes, **Then** the operation is rejected as forbidden and the stored
   request is unchanged.
5. **Given** a request in Draft, ChangesRequested or Approved, **When** a Reviewer tries to
   approve it or request changes, **Then** the operation is rejected as not allowed in the current
   status and the stored request is unchanged.
6. **Given** a request in PendingReview, **When** a Reviewer requests changes without a reason
   (or with only blank text), **Then** the operation is rejected as invalid input and the stored
   request is unchanged.
7. **Given** a request in PendingReview created by user A, who also holds the Reviewer role,
   **When** user A tries to request changes on it, **Then** the operation is rejected as
   forbidden (FR-016) and the stored status remains PendingReview.

---

### User Story 3 - Protection against concurrent and stale changes (Priority: P2)

Several people may act on the same request at nearly the same time (for example, two reviewers,
or a requester editing in two places). Any operation based on an outdated version of a request is
rejected with an explicit conflict, so no newer change is silently overwritten and the request
never ends up in a status outside the workflow.

**Why this priority**: A confirmed product rule. Without it, approvals and edits can be lost or
contradict each other, which undermines trust in every recorded decision.

**Independent Test**: Read a request, change it once using its current version, then attempt a
second change using the old version. The second attempt is rejected as a conflict and the stored
request still reflects only the first change.

**Acceptance Scenarios**:

1. **Given** a Draft at version V that has since been edited to version V+1, **When** its owner
   submits an edit based on version V, **Then** the operation is rejected as a conflict and the
   stored request remains exactly as at version V+1.
2. **Given** a request in PendingReview, **When** two different Reviewers simultaneously attempt
   to approve and to request changes, both based on the same version, **Then** exactly one
   succeeds, the other is rejected as a conflict, and the stored status is the result of the one
   that succeeded.
3. **Given** any rejected operation (conflict, forbidden, invalid status or invalid input),
   **When** the request is read afterwards, **Then** its stored content, status and version are
   identical to those before the attempt.

---

### User Story 4 - Correct a returned request and resubmit (Priority: P3)

When a reviewer returns a request, its owner reads the reviewer's reason, corrects the request and
submits it again, which puts it back into PendingReview. This cycle can repeat until the request
is approved.

**Why this priority**: Completes the workflow loop. Without it, a returned request is a dead end,
but the system still delivers value (capture plus approval) before this story exists.

**Independent Test**: Starting from a request in ChangesRequested, its owner edits it and
submits; the stored status is PendingReview with the corrected content, and a reviewer can then
approve it.

**Acceptance Scenarios**:

1. **Given** a request in ChangesRequested owned by the caller, **When** the caller edits it
   using its current version, **Then** the changes are stored and the status remains
   ChangesRequested.
2. **Given** a request in ChangesRequested owned by the caller, **When** the caller submits it
   using its current version, **Then** its status becomes PendingReview.
3. **Given** a request in ChangesRequested owned by user A, **When** user B tries to edit or
   submit it, **Then** the operation is rejected (not found if B cannot see it, otherwise
   forbidden, per FR-015) and the request is unchanged.
4. **Given** a request that has been returned and resubmitted, **When** a Reviewer other than its
   requester approves it, **Then** its status becomes Approved and it can no longer be edited.

---

### Edge Cases

- **Repeated operation**: a request already in PendingReview is submitted again, or an Approved
  request is approved again → if the repeat uses the old version it is rejected as conflict; if
  it uses the current version it is rejected as invalid status; nothing changes (FR-020,
  FR-022).
- **Several failures at once**: e.g. a Reviewer approves their own request using an outdated
  version → reported as forbidden, because permission is checked before version (FR-020).
- **Role removed mid-flow**: a user loses the Requester role while owning a Draft, or loses the
  Reviewer role between reading and approving a request → the operation is rejected as forbidden
  at the time it is attempted, because current permission is checked on every operation
  (FR-013, FR-023).
- **Request does not exist**: any operation on an unknown request is rejected as not found and
  nothing is changed.
- **Missing version**: a state-changing operation that does not state which version it is based
  on is rejected as invalid input.
- **Edits that change nothing**: an edit whose values equal the stored values is treated as a
  normal edit (accepted if all rules pass).
- **Hiding existence**: a caller who may not see a request (a Requester-only user acting on
  someone else's request) gets "not found", exactly as for a request that does not exist
  (FR-015).

## Requirements *(mandatory)*

### Functional Requirements

**Change request data and lifecycle**

- **FR-001**: The system MUST store, for each change request: a unique identifier, title,
  description of the change, reason for the change, identifier of the requester, current status,
  and a version that changes with every successful modification.
- **FR-002**: The only valid statuses MUST be Draft, PendingReview, ChangesRequested and
  Approved, and the only valid status transitions MUST be:
  Draft → PendingReview (Submit), PendingReview → Approved (Approve), PendingReview →
  ChangesRequested (RequestChanges), ChangesRequested → PendingReview (Submit).
- **FR-003**: Any operation that would cause a transition not listed in FR-002 MUST be rejected
  with an "invalid status" outcome, and the stored request MUST be unchanged.
- **FR-004**: Title, description and reason MUST be non-blank on create and on every edit, and
  within the length limits in assumption A6; otherwise the operation MUST be rejected as
  invalid input.

**Requester operations**

- **FR-005**: A user holding the Requester role MUST be able to create a change request; it MUST
  start in Draft with the caller recorded as its requester.
- **FR-006**: The requester of a request MUST be able to edit its title, description and reason
  only while it is in Draft or ChangesRequested; editing in PendingReview or Approved MUST be
  rejected as invalid status.
- **FR-007**: The requester of a request MUST be able to submit it when it is in Draft or
  ChangesRequested, moving it to PendingReview.
- **FR-008**: Edit and submit MUST be rejected as forbidden when the caller is not the request's
  requester or does not currently hold the Requester role.
- **FR-009**: An Approved request MUST NOT be editable by anyone.

**Reviewer operations**

- **FR-010**: A user holding the Reviewer role MUST be able to approve a request in PendingReview,
  moving it to Approved.
- **FR-011**: A user holding the Reviewer role MUST be able to request changes on a request in
  PendingReview, with a non-blank reason, moving it to ChangesRequested; the most recent reason
  MUST be stored with the request and visible to its requester. Only the most recent reason is
  kept; a history of earlier reasons is not part of this version.
- **FR-012**: Approval by the request's own requester MUST be rejected as forbidden, regardless of
  the roles that user holds. This rule MUST apply to every way of performing an approval.

**Security, integrity and concurrency**

- **FR-013**: Every operation that changes a request MUST, before changing anything, verify (a)
  the caller's identity, (b) the caller's permission at that moment, and (c) the request's status
  at that moment. If any check fails, nothing MUST change. Unauthenticated callers MUST be
  rejected for all operations.
- **FR-014**: Every operation that changes a request MUST state the version of the request it is
  based on. If that version is not the current version, the operation MUST be rejected with a
  "conflict" outcome and the stored request MUST remain unchanged. Of several concurrent
  operations based on the same version, at most one MUST succeed.
- **FR-015**: Visibility MUST be: (a) the requester of a request can view it, including its
  status and the most recent change-request reason, and can list all requests they own; (b) a
  user currently holding the Reviewer role can view and list all requests; (c) no other user can
  view or list a request. A request the caller may not see MUST be reported as "not found", for
  viewing and for every other operation on it, so its existence is not revealed.
- **FR-016**: RequestChanges by the request's own requester MUST be rejected as forbidden,
  regardless of the roles that user holds, and the stored request MUST be unchanged. Like
  FR-012, this rule MUST apply to every way of performing the operation.
- **FR-017**: Approved MUST be the only terminal status. This version MUST NOT offer rejection
  by a reviewer or cancellation/withdrawal by the requester; a request that is not approved
  remains in Draft, PendingReview or ChangesRequested.
- **FR-018**: Every rejected operation MUST report a distinguishable outcome category:
  unauthenticated, forbidden, not found, invalid status, invalid input, or conflict.
- **FR-019**: Default denial: any operation or caller/role combination not explicitly allowed by
  this specification MUST be rejected as forbidden.
- **FR-020**: When an operation fails more than one check, the checks MUST be applied in this
  order and only the first failure MUST be reported: (1) identity → unauthenticated; (2)
  existence and visibility → not found; (3) permission (role, ownership, self-approval,
  self-RequestChanges) → forbidden; (4) input validity, including a missing version → invalid
  input; (5) version → conflict; (6) status → invalid status. Viewing and listing apply steps
  (1)–(2) only.
- **FR-021**: The system MUST NOT offer any way to delete a change request, in any status, for
  any user.
- **FR-022**: A repeated operation MUST NOT be treated as an idempotent success. Because the
  first operation changes the request's status and version, a repetition MUST be rejected as
  conflict (if based on the old version) or invalid status (if based on the current version),
  per FR-020, and nothing MUST change.
- **FR-023**: Removing a role from a user MUST NOT change existing requests: they keep their
  status and requester, and ownership is never transferred automatically. The user can no
  longer perform operations that require the removed role (checked at the time of each
  operation, FR-013); their requests in PendingReview can still be reviewed by other Reviewers.

### Key Entities

- **Change Request**: a proposed change to the company's software or processes. Attributes:
  identifier, title, description of the change, reason for the change, requester (a user),
  status (one of the workflow statuses), version, and the most recent change-request reason
  given by a reviewer (if any).
- **User**: a person known to the system with an identity and zero or more roles (Requester,
  Reviewer). Users and their roles are managed outside this feature.
- **Role**: Requester (may create and own change requests) or Reviewer (may approve or return
  requests). A user may hold both.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of self-approval and self-RequestChanges attempts in acceptance testing are
  rejected, and the stored status remains unchanged in every case.
- **SC-002**: For every state-changing operation (edit, submit, approve, request changes), an
  attempt based on an outdated version is rejected as conflict and the stored request is
  unchanged; and when two operations based on the same version are both attempted, exactly one
  succeeds and the stored request reflects only that one. Each check gives the same result on
  every run.
- **SC-003**: For 100% of rejected operations (every rejection category in FR-018), the stored
  request's content, status and version are identical before and after the attempt, verified
  by reading the stored state, not only the returned result.
- **SC-004**: Every allowed transition in FR-002 and every rejected transition, role check and
  ownership check in this specification is covered by at least one passing acceptance scenario.
- **SC-005**: A new request can be taken from creation to approval in three operations
  (create and submit by the requester, approve by a different reviewer), with no manual
  intervention outside the system.
- **SC-006**: No request is ever observed in a status outside the defined workflow statuses
  during any test run.

## Assumptions

The items below are **open reviewable assumptions** about behaviour the product owner has not
defined. They are used for planning but are not final product decisions and may be overturned.
Former assumptions A1–A5 were confirmed on 2026-11-17 and are now requirements (A1 → FR-021,
A2 → FR-006, A3 → FR-022, A4 → FR-023, A5 → FR-011).

- **A6 — Field limits (open reviewable assumption)**: Title is at most 200 characters;
  description and reason are each at most 10,000 characters. Longer values are rejected as
  invalid input (FR-004).
- **A7 — Identity (open reviewable assumption)**: Callers are identified by an existing identity
  mechanism; how users authenticate and how roles are assigned are outside this feature. The
  concrete mechanism is to be chosen and justified in planning research.
- **Out of scope**: user interface; notifications; executing or deploying approved changes; user
  and role administration; terminal rejection and cancellation/withdrawal of requests;
  performance and load targets; audit history beyond the current state; AI, RAG, MCP and
  multi-agent capabilities.
