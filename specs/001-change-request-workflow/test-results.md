# Test Results: Change Request Workflow (First Version)

**Feature**: [spec.md](./spec.md) | **Task**: T044 (re-recorded after T045) | **Run at**: 2026-11-16T22:29:39Z (UTC)

The three commands below were run from the repository root with the virtual environment
(`.venv`) active. Their complete output was captured to a file by the shell and is copied here
unedited; `[exit N]` after each command is the shell exit status.

- **Code under test**: commit `8470289` on `main`, with a clean working tree (`git status
  --short` printed nothing at run time).
- **Result**: 225 passed, 0 failed, 1 warning (`StarletteDeprecationWarning` from FastAPI's test
  client recommending `httpx2` instead of `httpx`; it does not affect results).
- **History**: this run supersedes two earlier T044 runs, both 217 passed: one at commit
  `420c8d0`, and one at `420c8d0` plus the uncommitted G1 test change. The 8 additional tests
  come from T045 (documentation endpoints are not served).

## Output

```text
$ python --version
Python 3.12.3
[exit 0]

$ pip freeze
annotated-doc==0.0.6
annotated-types==0.8.0
anyio==4.16.0
certifi==2026.10.23
-e git+https://github.com/vahidnazaritavakolii/changeFlow.git@8470289f22fca376b28ebaaae009e7286d2dc0e8#egg=changeflow
click==8.5.1
fastapi==0.163.1
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
iniconfig==2.3.1
opentelemetry-api==1.45.2
packaging==26.3
pluggy==1.7.0
pydantic==2.14.3
pydantic_core==2.50.4
Pygments==2.21.0
pytest==9.2.0
starlette==1.10.0
typing-inspection==0.4.5
typing_extensions==4.16.0
uvicorn==0.54.0
[exit 0]

$ pytest -v
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /home/vahid/Desktop/SoftwareEngineeringInArtificialInteligenceEra/Project-01/changeFlow/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/vahid/Desktop/SoftwareEngineeringInArtificialInteligenceEra/Project-01/changeFlow
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.16.0
collecting ... collected 225 items

tests/api/test_us1_create_view_list.py::test_requester_creates_draft PASSED [  0%]
tests/api/test_us1_create_view_list.py::test_create_without_requester_role_is_forbidden[bob] PASSED [  0%]
tests/api/test_us1_create_view_list.py::test_create_without_requester_role_is_forbidden[dave] PASSED [  1%]
tests/api/test_us1_create_view_list.py::test_create_forbidden_before_invalid_input PASSED [  1%]
tests/api/test_us1_create_view_list.py::test_create_with_invalid_fields_is_invalid_input[missing] PASSED [  2%]
tests/api/test_us1_create_view_list.py::test_create_with_invalid_fields_is_invalid_input[blank] PASSED [  2%]
tests/api/test_us1_create_view_list.py::test_create_with_invalid_fields_is_invalid_input[title-too-long] PASSED [  3%]
tests/api/test_us1_create_view_list.py::test_create_with_invalid_fields_is_invalid_input[reason-too-long] PASSED [  3%]
tests/api/test_us1_create_view_list.py::test_create_with_non_json_body_is_invalid_input PASSED [  4%]
tests/api/test_us1_create_view_list.py::test_unauthenticated_calls_are_rejected[none] PASSED [  4%]
tests/api/test_us1_create_view_list.py::test_unauthenticated_calls_are_rejected[scheme] PASSED [  4%]
tests/api/test_us1_create_view_list.py::test_unauthenticated_calls_are_rejected[empty] PASSED [  5%]
tests/api/test_us1_create_view_list.py::test_unauthenticated_calls_are_rejected[unknown] PASSED [  5%]
tests/api/test_us1_create_view_list.py::test_owner_views_own_request PASSED [  6%]
tests/api/test_us1_create_view_list.py::test_owner_without_any_role_views_own_request PASSED [  6%]
tests/api/test_us1_create_view_list.py::test_unknown_or_non_numeric_id_is_not_found[999] PASSED [  7%]
tests/api/test_us1_create_view_list.py::test_unknown_or_non_numeric_id_is_not_found[abc] PASSED [  7%]
tests/api/test_us1_create_view_list.py::test_unknown_or_non_numeric_id_is_not_found[1.5] PASSED [  8%]
tests/api/test_us1_create_view_list.py::test_unknown_or_non_numeric_id_is_not_found[-1] PASSED [  8%]
tests/api/test_us1_create_view_list.py::test_request_of_another_user_is_hidden PASSED [  8%]
tests/api/test_us1_create_view_list.py::test_listing_respects_visibility PASSED [  9%]
tests/api/test_us1_create_view_list.py::test_owner_without_any_role_lists_own_requests PASSED [  9%]
tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[no-token-/docs] PASSED [ 10%]
tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[no-token-/redoc] PASSED [ 10%]
tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[no-token-/openapi.json] PASSED [ 11%]
tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[no-token-/docs/oauth2-redirect] PASSED [ 11%]
tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[valid-token-/docs] PASSED [ 12%]
tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[valid-token-/redoc] PASSED [ 12%]
tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[valid-token-/openapi.json] PASSED [ 12%]
tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[valid-token-/docs/oauth2-redirect] PASSED [ 13%]
tests/api/test_us1_create_view_list.py::test_delete_and_unlisted_routes_are_rejected PASSED [ 13%]
tests/api/test_us1_edit_submit.py::test_owner_edits_draft PASSED         [ 14%]
tests/api/test_us1_edit_submit.py::test_owner_submits_draft PASSED       [ 14%]
tests/api/test_us1_edit_submit.py::test_edit_with_identical_values_increments_version PASSED [ 15%]
tests/api/test_us1_edit_submit.py::test_unknown_extra_field_is_ignored PASSED [ 15%]
tests/api/test_us1_edit_submit.py::test_other_requesters_cannot_see_or_change_draft PASSED [ 16%]
tests/api/test_us1_edit_submit.py::test_reviewer_cannot_edit_or_submit_someone_elses_draft PASSED [ 16%]
tests/api/test_us1_edit_submit.py::test_owner_who_lost_requester_role_can_view_but_not_change PASSED [ 16%]
tests/api/test_us1_edit_submit.py::test_edit_outside_draft_is_invalid_status[PendingReview] PASSED [ 17%]
tests/api/test_us1_edit_submit.py::test_edit_outside_draft_is_invalid_status[Approved] PASSED [ 17%]
tests/api/test_us1_edit_submit.py::test_missing_version_is_invalid_input PASSED [ 18%]
tests/api/test_us1_edit_submit.py::test_non_object_body_is_invalid_input[not json] PASSED [ 18%]
tests/api/test_us1_edit_submit.py::test_non_object_body_is_invalid_input[] PASSED [ 19%]
tests/api/test_us1_edit_submit.py::test_non_object_body_is_invalid_input[[1, 2]] PASSED [ 19%]
tests/api/test_us1_edit_submit.py::test_stale_version_is_conflict PASSED [ 20%]
tests/api/test_us1_edit_submit.py::test_repeated_submit PASSED           [ 20%]
tests/api/test_us1_edit_submit.py::test_invalid_input_reported_before_conflict PASSED [ 20%]
tests/api/test_us2_review.py::test_reviewer_approves_pending_request PASSED [ 21%]
tests/api/test_us2_review.py::test_reviewer_requests_changes_and_requester_sees_reason PASSED [ 21%]
tests/api/test_us2_review.py::test_dual_role_owner_cannot_approve_own_request PASSED [ 22%]
tests/api/test_us2_review.py::test_dual_role_owner_cannot_request_changes_on_own_request PASSED [ 22%]
tests/api/test_us2_review.py::test_self_approval_with_outdated_version_is_forbidden PASSED [ 23%]
tests/api/test_us2_review.py::test_requester_without_reviewer_role_cannot_review_own_request PASSED [ 23%]
tests/api/test_us2_review.py::test_user_who_cannot_see_the_request_gets_not_found PASSED [ 24%]
tests/api/test_us2_review.py::test_review_outside_pending_review_is_invalid_status[Draft] PASSED [ 24%]
tests/api/test_us2_review.py::test_review_outside_pending_review_is_invalid_status[ChangesRequested] PASSED [ 24%]
tests/api/test_us2_review.py::test_review_outside_pending_review_is_invalid_status[Approved] PASSED [ 25%]
tests/api/test_us2_review.py::test_request_changes_without_valid_reason_is_invalid_input[missing] PASSED [ 25%]
tests/api/test_us2_review.py::test_request_changes_without_valid_reason_is_invalid_input[empty] PASSED [ 26%]
tests/api/test_us2_review.py::test_request_changes_without_valid_reason_is_invalid_input[blank] PASSED [ 26%]
tests/api/test_us2_review.py::test_request_changes_without_valid_reason_is_invalid_input[too-long] PASSED [ 27%]
tests/api/test_us2_review.py::test_approve_without_version_is_invalid_input PASSED [ 27%]
tests/api/test_us2_review.py::test_reviewer_views_any_request PASSED     [ 28%]
tests/api/test_us2_review.py::test_reviewer_who_lost_the_role_is_rejected_and_others_can_still_review PASSED [ 28%]
tests/api/test_us3_stale_writes.py::test_edit_based_on_outdated_version_is_conflict PASSED [ 28%]
tests/api/test_us3_stale_writes.py::test_two_reviewers_on_same_version_exactly_one_wins[approve-request-changes] PASSED [ 29%]
tests/api/test_us3_stale_writes.py::test_two_reviewers_on_same_version_exactly_one_wins[request-changes-approve] PASSED [ 29%]
tests/api/test_us3_stale_writes.py::test_every_rejection_category_leaves_the_row_unchanged PASSED [ 30%]
tests/api/test_us3_stale_writes.py::test_no_token_and_unknown_id_is_unauthenticated PASSED [ 30%]
tests/api/test_us3_stale_writes.py::test_requester_editing_hidden_request_with_invalid_body_is_not_found PASSED [ 31%]
tests/api/test_us3_stale_writes.py::test_self_approval_with_outdated_version_is_forbidden PASSED [ 31%]
tests/api/test_us3_stale_writes.py::test_blank_title_with_outdated_version_is_invalid_input PASSED [ 32%]
tests/api/test_us3_stale_writes.py::test_resubmit_with_old_version_is_conflict_and_with_current_is_invalid_status PASSED [ 32%]
tests/api/test_us4_rework.py::test_owner_edits_returned_request PASSED   [ 32%]
tests/api/test_us4_rework.py::test_requester_sees_reviewer_reason PASSED [ 33%]
tests/api/test_us4_rework.py::test_owner_resubmits_returned_request PASSED [ 33%]
tests/api/test_us4_rework.py::test_other_users_cannot_edit_or_resubmit PASSED [ 34%]
tests/api/test_us4_rework.py::test_resubmitted_request_is_approved_and_then_locked PASSED [ 34%]
tests/api/test_us4_rework.py::test_full_rework_cycle_over_http PASSED    [ 35%]
tests/api/test_us4_rework.py::test_new_request_reaches_approved_in_three_operations PASSED [ 35%]
tests/architecture/test_architecture.py::test_domain_has_no_http_persistence_or_outer_layer_imports PASSED [ 36%]
tests/architecture/test_architecture.py::test_application_has_no_http_persistence_or_outer_layer_imports PASSED [ 36%]
tests/architecture/test_architecture.py::test_route_handlers_have_no_business_conditions_and_call_one_use_case PASSED [ 36%]
tests/architecture/test_architecture.py::test_checker_flags_a_handler_with_business_conditions PASSED [ 37%]
tests/architecture/test_architecture.py::test_checker_accepts_a_thin_handler PASSED [ 37%]
tests/architecture/test_architecture.py::test_import_checker_flags_forbidden_imports[import sqlite3\n-sqlite3] PASSED [ 38%]
tests/architecture/test_architecture.py::test_import_checker_flags_forbidden_imports[from fastapi import Request\n-fastapi.Request] PASSED [ 38%]
tests/architecture/test_architecture.py::test_import_checker_flags_forbidden_imports[from ..infrastructure import sqlite_db\n-changeflow.infrastructure.sqlite_db] PASSED [ 39%]
tests/integration/test_concurrency.py::test_write_based_on_an_older_load_writes_nothing PASSED [ 39%]
tests/integration/test_concurrency.py::test_second_call_with_same_version_is_conflict[edit] PASSED [ 40%]
tests/integration/test_concurrency.py::test_second_call_with_same_version_is_conflict[submit] PASSED [ 40%]
tests/integration/test_concurrency.py::test_second_call_with_same_version_is_conflict[approve] PASSED [ 40%]
tests/integration/test_concurrency.py::test_second_call_with_same_version_is_conflict[request_changes] PASSED [ 41%]
tests/integration/test_concurrency.py::test_interleaved_operations_on_same_version_exactly_one_succeeds[edit] PASSED [ 41%]
tests/integration/test_concurrency.py::test_interleaved_operations_on_same_version_exactly_one_succeeds[submit] PASSED [ 42%]
tests/integration/test_concurrency.py::test_interleaved_operations_on_same_version_exactly_one_succeeds[approve] PASSED [ 42%]
tests/integration/test_concurrency.py::test_interleaved_operations_on_same_version_exactly_one_succeeds[request_changes] PASSED [ 43%]
tests/integration/test_concurrency.py::test_approve_and_request_changes_race_exactly_one_wins PASSED [ 43%]
tests/integration/test_sqlite_repository.py::test_add_assigns_increasing_ids_and_version_one PASSED [ 44%]
tests/integration/test_sqlite_repository.py::test_get_unknown_id_returns_none PASSED [ 44%]
tests/integration/test_sqlite_repository.py::test_get_returns_stored_request PASSED [ 44%]
tests/integration/test_sqlite_repository.py::test_lists_are_ordered_by_id PASSED [ 45%]
tests/integration/test_sqlite_repository.py::test_update_with_current_version_writes_and_increments PASSED [ 45%]
tests/integration/test_sqlite_repository.py::test_update_with_other_version_writes_nothing[1] PASSED [ 46%]
tests/integration/test_sqlite_repository.py::test_update_with_other_version_writes_nothing[2] PASSED [ 46%]
tests/integration/test_sqlite_repository.py::test_update_with_other_version_writes_nothing[4] PASSED [ 47%]
tests/integration/test_sqlite_repository.py::test_status_outside_workflow_cannot_be_inserted PASSED [ 47%]
tests/integration/test_sqlite_repository.py::test_status_outside_workflow_cannot_be_written_by_update PASSED [ 48%]
tests/integration/test_sqlite_users.py::test_valid_token_returns_actor_with_current_roles[alice-roles0] PASSED [ 48%]
tests/integration/test_sqlite_users.py::test_valid_token_returns_actor_with_current_roles[bob-roles1] PASSED [ 48%]
tests/integration/test_sqlite_users.py::test_valid_token_returns_actor_with_current_roles[carol-roles2] PASSED [ 49%]
tests/integration/test_sqlite_users.py::test_valid_token_returns_actor_with_current_roles[dave-roles3] PASSED [ 49%]
tests/integration/test_sqlite_users.py::test_unknown_token_returns_none PASSED [ 50%]
tests/integration/test_sqlite_users.py::test_only_the_token_hash_is_stored PASSED [ 50%]
tests/integration/test_sqlite_users.py::test_removed_role_is_absent_on_next_lookup PASSED [ 51%]
tests/unit/domain/test_model.py::test_status_has_exactly_the_workflow_values PASSED [ 51%]
tests/unit/domain/test_model.py::test_role_has_exactly_requester_and_reviewer PASSED [ 52%]
tests/unit/domain/test_model.py::test_transition_table_is_exactly_the_specified_workflow PASSED [ 52%]
tests/unit/domain/test_model.py::test_approved_is_terminal PASSED        [ 52%]
tests/unit/domain/test_model.py::test_there_is_no_delete_operation PASSED [ 53%]
tests/unit/domain/test_rules_common.py::test_owner_sees_own_request_with_any_roles_or_none[roles0] PASSED [ 53%]
tests/unit/domain/test_rules_common.py::test_owner_sees_own_request_with_any_roles_or_none[roles1] PASSED [ 54%]
tests/unit/domain/test_rules_common.py::test_owner_sees_own_request_with_any_roles_or_none[roles2] PASSED [ 54%]
tests/unit/domain/test_rules_common.py::test_owner_sees_own_request_with_any_roles_or_none[roles3] PASSED [ 55%]
tests/unit/domain/test_rules_common.py::test_reviewer_sees_any_request PASSED [ 55%]
tests/unit/domain/test_rules_common.py::test_requester_only_non_owner_sees_nothing PASSED [ 56%]
tests/unit/domain/test_rules_common.py::test_no_role_non_owner_sees_nothing PASSED [ 56%]
tests/unit/domain/test_rules_common.py::test_limits_are_module_level_constants PASSED [ 56%]
tests/unit/domain/test_rules_common.py::test_text_at_the_limits_is_accepted PASSED [ 57%]
tests/unit/domain/test_rules_common.py::test_text_over_the_limit_is_rejected[title-value0] PASSED [ 57%]
tests/unit/domain/test_rules_common.py::test_text_over_the_limit_is_rejected[description-value1] PASSED [ 58%]
tests/unit/domain/test_rules_common.py::test_text_over_the_limit_is_rejected[reason-value2] PASSED [ 58%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[-title] PASSED [ 59%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[-description] PASSED [ 59%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[-reason] PASSED [ 60%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[   -title] PASSED [ 60%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[   -description] PASSED [ 60%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[   -reason] PASSED [ 61%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[\t\n-title] PASSED [ 61%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[\t\n-description] PASSED [ 62%]
tests/unit/domain/test_rules_common.py::test_blank_text_is_rejected[\t\n-reason] PASSED [ 62%]
tests/unit/domain/test_rules_common.py::test_missing_text_is_rejected[title] PASSED [ 63%]
tests/unit/domain/test_rules_common.py::test_missing_text_is_rejected[description] PASSED [ 63%]
tests/unit/domain/test_rules_common.py::test_missing_text_is_rejected[reason] PASSED [ 64%]
tests/unit/domain/test_rules_common.py::test_non_string_text_is_rejected[None] PASSED [ 64%]
tests/unit/domain/test_rules_common.py::test_non_string_text_is_rejected[1] PASSED [ 64%]
tests/unit/domain/test_rules_common.py::test_non_string_text_is_rejected[True] PASSED [ 65%]
tests/unit/domain/test_rules_common.py::test_non_string_text_is_rejected[value3] PASSED [ 65%]
tests/unit/domain/test_rules_common.py::test_non_string_text_is_rejected[value4] PASSED [ 66%]
tests/unit/domain/test_rules_common.py::test_text_values_are_returned_unchanged_not_trimmed PASSED [ 66%]
tests/unit/domain/test_rules_common.py::test_body_that_is_not_a_json_object_is_rejected[None] PASSED [ 67%]
tests/unit/domain/test_rules_common.py::test_body_that_is_not_a_json_object_is_rejected[body1] PASSED [ 67%]
tests/unit/domain/test_rules_common.py::test_body_that_is_not_a_json_object_is_rejected[text] PASSED [ 68%]
tests/unit/domain/test_rules_common.py::test_body_that_is_not_a_json_object_is_rejected[1] PASSED [ 68%]
tests/unit/domain/test_rules_common.py::test_body_that_is_not_a_json_object_is_rejected[body4] PASSED [ 68%]
tests/unit/domain/test_rules_common.py::test_dict_body_is_accepted PASSED [ 69%]
tests/unit/domain/test_rules_common.py::test_version_one_is_valid PASSED [ 69%]
tests/unit/domain/test_rules_common.py::test_invalid_version_values_are_rejected[0] PASSED [ 70%]
tests/unit/domain/test_rules_common.py::test_invalid_version_values_are_rejected[-1] PASSED [ 70%]
tests/unit/domain/test_rules_common.py::test_invalid_version_values_are_rejected[1] PASSED [ 71%]
tests/unit/domain/test_rules_common.py::test_invalid_version_values_are_rejected[True] PASSED [ 71%]
tests/unit/domain/test_rules_common.py::test_invalid_version_values_are_rejected[1.0] PASSED [ 72%]
tests/unit/domain/test_rules_common.py::test_invalid_version_values_are_rejected[None] PASSED [ 72%]
tests/unit/domain/test_rules_common.py::test_missing_version_is_rejected PASSED [ 72%]
tests/unit/domain/test_rules_common.py::test_check_version_accepts_current_version PASSED [ 73%]
tests/unit/domain/test_rules_common.py::test_check_version_rejects_other_version PASSED [ 73%]
tests/unit/domain/test_rules_common.py::test_next_status_follows_transition_table PASSED [ 74%]
tests/unit/domain/test_rules_common.py::test_next_status_rejects_transition_not_in_table PASSED [ 74%]
tests/unit/domain/test_us1_requester_rules.py::test_requester_creates_draft_owned_by_caller PASSED [ 75%]
tests/unit/domain/test_us1_requester_rules.py::test_create_without_requester_role_is_forbidden[caller0] PASSED [ 75%]
tests/unit/domain/test_us1_requester_rules.py::test_create_without_requester_role_is_forbidden[caller1] PASSED [ 76%]
tests/unit/domain/test_us1_requester_rules.py::test_create_forbidden_is_reported_before_invalid_input PASSED [ 76%]
tests/unit/domain/test_us1_requester_rules.py::test_create_with_invalid_text_is_invalid_input PASSED [ 76%]
tests/unit/domain/test_us1_requester_rules.py::test_owner_edits_own_draft PASSED [ 77%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_keeps_changes_requested_reason PASSED [ 77%]
tests/unit/domain/test_us1_requester_rules.py::test_owner_submits_own_draft PASSED [ 78%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_and_submit_are_forbidden_for_non_owner_or_owner_without_requester_role[non-owner-requester] PASSED [ 78%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_and_submit_are_forbidden_for_non_owner_or_owner_without_requester_role[owner-lost-role] PASSED [ 79%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_and_submit_are_forbidden_for_non_owner_or_owner_without_requester_role[owner-reviewer-only] PASSED [ 79%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_and_submit_are_forbidden_for_non_owner_or_owner_without_requester_role[reviewer] PASSED [ 80%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_outside_draft_or_changes_requested_is_invalid_status[PendingReview] PASSED [ 80%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_outside_draft_or_changes_requested_is_invalid_status[Approved] PASSED [ 80%]
tests/unit/domain/test_us1_requester_rules.py::test_submit_outside_draft_or_changes_requested_is_invalid_status[PendingReview] PASSED [ 81%]
tests/unit/domain/test_us1_requester_rules.py::test_submit_outside_draft_or_changes_requested_is_invalid_status[Approved] PASSED [ 81%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_with_stale_version_is_conflict PASSED [ 82%]
tests/unit/domain/test_us1_requester_rules.py::test_submit_with_stale_version_is_conflict PASSED [ 82%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_with_invalid_body_is_invalid_input[body0] PASSED [ 83%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_with_invalid_body_is_invalid_input[body1] PASSED [ 83%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_with_invalid_body_is_invalid_input[None] PASSED [ 84%]
tests/unit/domain/test_us1_requester_rules.py::test_edit_with_invalid_body_is_invalid_input[body3] PASSED [ 84%]
tests/unit/domain/test_us1_requester_rules.py::test_submit_without_version_is_invalid_input PASSED [ 84%]
tests/unit/domain/test_us1_requester_rules.py::test_unknown_extra_fields_are_ignored PASSED [ 85%]
tests/unit/domain/test_us1_requester_rules.py::test_forbidden_beats_invalid_input PASSED [ 85%]
tests/unit/domain/test_us1_requester_rules.py::test_invalid_input_beats_conflict PASSED [ 86%]
tests/unit/domain/test_us1_requester_rules.py::test_conflict_beats_invalid_status PASSED [ 86%]
tests/unit/domain/test_us2_review_rules.py::test_reviewer_who_is_not_the_requester_approves[reviewer] PASSED [ 87%]
tests/unit/domain/test_us2_review_rules.py::test_reviewer_who_is_not_the_requester_approves[dual-role-non-owner] PASSED [ 87%]
tests/unit/domain/test_us2_review_rules.py::test_request_changes_sets_status_and_reason PASSED [ 88%]
tests/unit/domain/test_us2_review_rules.py::test_request_changes_replaces_earlier_reason PASSED [ 88%]
tests/unit/domain/test_us2_review_rules.py::test_approve_keeps_changes_requested_reason PASSED [ 88%]
tests/unit/domain/test_us2_review_rules.py::test_caller_without_reviewer_role_is_forbidden[requester-only] PASSED [ 89%]
tests/unit/domain/test_us2_review_rules.py::test_caller_without_reviewer_role_is_forbidden[no-role] PASSED [ 89%]
tests/unit/domain/test_us2_review_rules.py::test_dual_role_owner_cannot_approve_own_request PASSED [ 90%]
tests/unit/domain/test_us2_review_rules.py::test_dual_role_owner_cannot_request_changes_on_own_request PASSED [ 90%]
tests/unit/domain/test_us2_review_rules.py::test_reviewer_who_lost_the_role_is_forbidden PASSED [ 91%]
tests/unit/domain/test_us2_review_rules.py::test_request_changes_requires_valid_reason[missing] PASSED [ 91%]
tests/unit/domain/test_us2_review_rules.py::test_request_changes_requires_valid_reason[blank] PASSED [ 92%]
tests/unit/domain/test_us2_review_rules.py::test_request_changes_requires_valid_reason[too-long] PASSED [ 92%]
tests/unit/domain/test_us2_review_rules.py::test_request_changes_requires_valid_reason[not-a-string] PASSED [ 92%]
tests/unit/domain/test_us2_review_rules.py::test_request_changes_accepts_reason_at_limit PASSED [ 93%]
tests/unit/domain/test_us2_review_rules.py::test_approve_requires_valid_version[body0] PASSED [ 93%]
tests/unit/domain/test_us2_review_rules.py::test_approve_requires_valid_version[body1] PASSED [ 94%]
tests/unit/domain/test_us2_review_rules.py::test_approve_requires_valid_version[None] PASSED [ 94%]
tests/unit/domain/test_us2_review_rules.py::test_review_outside_pending_review_is_invalid_status[Draft] PASSED [ 95%]
tests/unit/domain/test_us2_review_rules.py::test_review_outside_pending_review_is_invalid_status[ChangesRequested] PASSED [ 95%]
tests/unit/domain/test_us2_review_rules.py::test_review_outside_pending_review_is_invalid_status[Approved] PASSED [ 96%]
tests/unit/domain/test_us2_review_rules.py::test_stale_version_is_conflict PASSED [ 96%]
tests/unit/domain/test_us2_review_rules.py::test_self_approval_with_stale_version_is_forbidden PASSED [ 96%]
tests/unit/domain/test_us2_review_rules.py::test_invalid_reason_beats_conflict PASSED [ 97%]
tests/unit/domain/test_us2_review_rules.py::test_conflict_beats_invalid_status PASSED [ 97%]
tests/unit/domain/test_us4_rework_rules.py::test_owner_edits_returned_request_and_keeps_reason PASSED [ 98%]
tests/unit/domain/test_us4_rework_rules.py::test_owner_resubmits_returned_request_and_keeps_reason PASSED [ 98%]
tests/unit/domain/test_us4_rework_rules.py::test_non_owner_cannot_edit_or_resubmit[other-requester] PASSED [ 99%]
tests/unit/domain/test_us4_rework_rules.py::test_non_owner_cannot_edit_or_resubmit[reviewer] PASSED [ 99%]
tests/unit/domain/test_us4_rework_rules.py::test_full_cycle_until_approval_using_only_domain_rules PASSED [100%]

=============================== warnings summary ===============================
tests/api/test_us1_create_view_list.py::test_requester_creates_draft
  /home/vahid/Desktop/SoftwareEngineeringInArtificialInteligenceEra/Project-01/changeFlow/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 225 passed, 1 warning in 4.65s ========================
[exit 0]
```
