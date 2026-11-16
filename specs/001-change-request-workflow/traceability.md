# Traceability: Change Request Workflow (First Version)

**Feature**: [spec.md](./spec.md) | **Tasks**: [tasks.md](./tasks.md) (T042) | **Date**: 2026-11-17

Maps every functional requirement and success criterion to the tests that cover it. Input for
`/speckit-converge` and evidence for SC-004.

Path abbreviations: `U/` = `tests/unit/domain/`, `I/` = `tests/integration/`, `A/` = `tests/api/`.
Test files: `U/test_model.py`, `U/test_rules_common.py`, `U/test_us1_requester_rules.py`,
`U/test_us2_review_rules.py`, `U/test_us4_rework_rules.py`, `I/test_sqlite_repository.py`,
`I/test_sqlite_users.py`, `I/test_concurrency.py`, `A/test_us1_create_view_list.py` (A/us1-cvl),
`A/test_us1_edit_submit.py` (A/us1-es), `A/test_us2_review.py`, `A/test_us3_stale_writes.py`,
`A/test_us4_rework.py`, `tests/architecture/test_architecture.py`.

## Functional requirements

| Req | Covered by (file :: test) | Status |
|-----|---------------------------|--------|
| FR-001 | I/test_sqlite_repository.py :: test_add_assigns_increasing_ids_and_version_one, test_get_returns_stored_request, test_update_with_current_version_writes_and_increments; A/us1-cvl :: test_requester_creates_draft | Covered |
| FR-002 | U/test_model.py :: test_status_has_exactly_the_workflow_values, test_transition_table_is_exactly_the_specified_workflow; I/test_sqlite_repository.py :: test_status_outside_workflow_cannot_be_inserted | Covered |
| FR-003 | U/test_rules_common.py :: test_next_status_rejects_transition_not_in_table; U/test_us1_requester_rules.py :: test_edit_outside_draft_or_changes_requested_is_invalid_status, test_submit_outside_draft_or_changes_requested_is_invalid_status; U/test_us2_review_rules.py :: test_review_outside_pending_review_is_invalid_status; A/test_us2_review.py :: test_review_outside_pending_review_is_invalid_status | Covered |
| FR-004 | U/test_rules_common.py :: test_text_at_the_limits_is_accepted, test_text_over_the_limit_is_rejected, test_blank_text_is_rejected, test_missing_text_is_rejected, test_non_string_text_is_rejected; A/us1-cvl :: test_create_with_invalid_fields_is_invalid_input | Covered |
| FR-005 | U/test_us1_requester_rules.py :: test_requester_creates_draft_owned_by_caller, test_create_without_requester_role_is_forbidden; A/us1-cvl :: test_requester_creates_draft, test_create_without_requester_role_is_forbidden | Covered |
| FR-006 | U/test_us1_requester_rules.py :: test_owner_edits_own_draft, test_edit_outside_draft_or_changes_requested_is_invalid_status; U/test_us4_rework_rules.py :: test_owner_edits_returned_request_and_keeps_reason; A/us1-es :: test_owner_edits_draft, test_edit_outside_draft_is_invalid_status; A/test_us4_rework.py :: test_owner_edits_returned_request | Covered |
| FR-007 | U/test_us1_requester_rules.py :: test_owner_submits_own_draft; U/test_us4_rework_rules.py :: test_owner_resubmits_returned_request_and_keeps_reason; A/us1-es :: test_owner_submits_draft; A/test_us4_rework.py :: test_owner_resubmits_returned_request | Covered |
| FR-008 | U/test_us1_requester_rules.py :: test_edit_and_submit_are_forbidden_for_non_owner_or_owner_without_requester_role; A/us1-es :: test_other_requesters_cannot_see_or_change_draft, test_reviewer_cannot_edit_or_submit_someone_elses_draft, test_owner_who_lost_requester_role_can_view_but_not_change; A/test_us4_rework.py :: test_other_users_cannot_edit_or_resubmit | Covered |
| FR-009 | U/test_model.py :: test_approved_is_terminal; A/us1-es :: test_edit_outside_draft_is_invalid_status[Approved]; A/test_us4_rework.py :: test_resubmitted_request_is_approved_and_then_locked | Covered |
| FR-010 | U/test_us2_review_rules.py :: test_reviewer_who_is_not_the_requester_approves; A/test_us2_review.py :: test_reviewer_approves_pending_request | Covered |
| FR-011 | U/test_us2_review_rules.py :: test_request_changes_sets_status_and_reason, test_request_changes_replaces_earlier_reason, test_request_changes_requires_valid_reason; A/test_us2_review.py :: test_reviewer_requests_changes_and_requester_sees_reason, test_request_changes_without_valid_reason_is_invalid_input; A/test_us4_rework.py :: test_requester_sees_reviewer_reason | Covered |
| FR-012 | U/test_us2_review_rules.py :: test_dual_role_owner_cannot_approve_own_request; A/test_us2_review.py :: test_dual_role_owner_cannot_approve_own_request, test_self_approval_with_outdated_version_is_forbidden | Covered (HTTP is the only entry point; the rule lives in the Domain) |
| FR-013 | A/us1-cvl :: test_unauthenticated_calls_are_rejected (all seven operations: create, list, view, edit, submit, approve, request-changes); A/test_us3_stale_writes.py :: test_every_rejection_category_leaves_the_row_unchanged, test_no_token_and_unknown_id_is_unauthenticated; I/test_sqlite_users.py :: test_removed_role_is_absent_on_next_lookup; A/us1-es :: test_owner_who_lost_requester_role_can_view_but_not_change | Covered (G1 closed) |
| FR-014 | I/test_concurrency.py :: all four tests; I/test_sqlite_repository.py :: test_update_with_other_version_writes_nothing; A/us1-es :: test_stale_version_is_conflict; A/test_us3_stale_writes.py :: test_edit_based_on_outdated_version_is_conflict, test_two_reviewers_on_same_version_exactly_one_wins | Covered |
| FR-015 | U/test_rules_common.py :: test_owner_sees_own_request_with_any_roles_or_none, test_reviewer_sees_any_request, test_requester_only_non_owner_sees_nothing, test_no_role_non_owner_sees_nothing; A/us1-cvl :: test_owner_views_own_request, test_owner_without_any_role_views_own_request, test_request_of_another_user_is_hidden, test_listing_respects_visibility, test_owner_without_any_role_lists_own_requests; A/test_us2_review.py :: test_user_who_cannot_see_the_request_gets_not_found, test_reviewer_views_any_request | Covered |
| FR-016 | U/test_us2_review_rules.py :: test_dual_role_owner_cannot_request_changes_on_own_request; A/test_us2_review.py :: test_dual_role_owner_cannot_request_changes_on_own_request | Covered (HTTP is the only entry point; the rule lives in the Domain) |
| FR-017 | U/test_model.py :: test_approved_is_terminal; A/us1-cvl :: test_delete_and_unlisted_routes_are_rejected (reject, cancel) | Covered |
| FR-018 | A/test_us3_stale_writes.py :: test_every_rejection_category_leaves_the_row_unchanged (all six categories); every `assert_error` in `A/` checks status and `code` | Covered |
| FR-019 | A/us1-cvl :: test_delete_and_unlisted_routes_are_rejected; U/test_us2_review_rules.py :: test_caller_without_reviewer_role_is_forbidden; U/test_us1_requester_rules.py :: test_create_without_requester_role_is_forbidden | Covered |
| FR-020 | U/test_us1_requester_rules.py :: test_forbidden_beats_invalid_input, test_invalid_input_beats_conflict, test_conflict_beats_invalid_status, test_create_forbidden_is_reported_before_invalid_input; U/test_us2_review_rules.py :: test_self_approval_with_stale_version_is_forbidden, test_invalid_reason_beats_conflict, test_conflict_beats_invalid_status; A/test_us3_stale_writes.py :: the six contract check-order tests; A/us1-cvl :: test_create_forbidden_before_invalid_input; A/us1-es :: test_invalid_input_reported_before_conflict | Covered |
| FR-021 | U/test_model.py :: test_there_is_no_delete_operation; A/us1-cvl :: test_delete_and_unlisted_routes_are_rejected | Covered |
| FR-022 | A/us1-es :: test_repeated_submit; A/test_us3_stale_writes.py :: test_resubmit_with_old_version_is_conflict_and_with_current_is_invalid_status; I/test_concurrency.py :: test_second_call_with_same_version_is_conflict | Covered |
| FR-023 | I/test_sqlite_users.py :: test_removed_role_is_absent_on_next_lookup; A/us1-es :: test_owner_who_lost_requester_role_can_view_but_not_change; A/test_us2_review.py :: test_reviewer_who_lost_the_role_is_rejected_and_others_can_still_review | Covered |

## Success criteria

| SC | Covered by | Status |
|----|------------|--------|
| SC-001 | A/test_us2_review.py :: test_dual_role_owner_cannot_approve_own_request, test_dual_role_owner_cannot_request_changes_on_own_request, test_self_approval_with_outdated_version_is_forbidden (each asserts status stays PendingReview) | Covered |
| SC-002 | I/test_concurrency.py :: all four tests (deterministic, one result per run); A/test_us3_stale_writes.py :: test_two_reviewers_on_same_version_exactly_one_wins | Covered |
| SC-003 | A/test_us3_stale_writes.py :: test_every_rejection_category_leaves_the_row_unchanged; every `assert_rejected` in A/us1-es, A/test_us2_review.py, A/test_us4_rework.py compares the stored row before and after | Covered |
| SC-004 | This table: every allowed transition (U/test_model.py, U/test_us4_rework_rules.py :: test_full_cycle_until_approval_using_only_domain_rules) and every rejected transition, role and ownership check maps to at least one passing test | Covered |
| SC-005 | A/test_us4_rework.py :: test_new_request_reaches_approved_in_three_operations | Covered |
| SC-006 | I/test_sqlite_repository.py :: test_status_outside_workflow_cannot_be_inserted, test_status_outside_workflow_cannot_be_written_by_update; U/test_model.py :: test_status_has_exactly_the_workflow_values | Covered |

## Planning assumptions (plan.md)

| PA | Covered by |
|----|------------|
| PA-1 | U/test_us1_requester_rules.py :: test_edit_keeps_changes_requested_reason; U/test_us2_review_rules.py :: test_approve_keeps_changes_requested_reason; U/test_us4_rework_rules.py :: both "keeps_reason" tests |
| PA-2 | I/test_sqlite_repository.py :: test_lists_are_ordered_by_id; A/us1-cvl :: test_listing_respects_visibility |
| PA-3 | A/us1-cvl :: test_listing_respects_visibility (dave → empty), test_owner_without_any_role_lists_own_requests |
| PA-4 | U/test_us1_requester_rules.py :: test_edit_with_invalid_body_is_invalid_input (fields missing) |
| PA-5 | U/test_rules_common.py :: test_blank_text_is_rejected, test_text_values_are_returned_unchanged_not_trimmed |
| PA-6 | A/us1-cvl :: test_unknown_or_non_numeric_id_is_not_found |
| PA-7 | U/test_us1_requester_rules.py :: test_unknown_extra_fields_are_ignored; A/us1-es :: test_unknown_extra_field_is_ignored |

## Architecture (Constitution Principle I)

`tests/architecture/test_architecture.py` :: test_domain_has_no_http_persistence_or_outer_layer_imports,
test_application_has_no_http_persistence_or_outer_layer_imports,
test_route_handlers_have_no_business_conditions_and_call_one_use_case, plus three self-tests.

## Gaps

None open.

- **G1 — closed on 2026-11-17.** FR-013 (unauthenticated callers rejected for *all* operations)
  was tested over HTTP for create, list, view and edit only. `A/us1-cvl ::
  test_unauthenticated_calls_are_rejected` now also covers submit, approve and request-changes,
  for all four kinds of bad credentials, and checks that no stored row changes. To show the test
  is not vacuous, `submit` was temporarily changed to skip authentication: all 4 cases failed;
  the code was restored unchanged.
