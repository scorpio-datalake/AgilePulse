"""Persistence boundary injected into service code.

SqlStore is a Facade over the SQLAlchemy session. Route handlers receive a
Database through get_store. They do not import query functions or open sessions.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from fastapi import Request
from sqlalchemy.orm import Session

from app import db as database
from app.db import connect


class Database(Protocol):
    def user_by_username(self, username: str) -> dict | None: ...
    def user_by_id(self, user_id: int) -> dict | None: ...
    def set_password(self, user_id: int, password: str) -> None: ...
    def has_added_user(self, organization_id: int) -> bool: ...
    def organization_tree(self, organization_id: int) -> list[dict]: ...
    def list_portfolios(self, organization_id: int) -> list[dict]: ...
    def get_portfolio(self, organization_id: int, portfolio_id: int) -> dict | None: ...
    def create_portfolio(self, organization_id: int, name: str) -> int: ...
    def rename_portfolio(self, organization_id: int, portfolio_id: int, name: str) -> bool: ...
    def list_value_streams(self, portfolio_id: int) -> list[dict]: ...
    def get_value_stream(self, organization_id: int, value_stream_id: int) -> dict | None: ...
    def create_value_stream(self, organization_id: int, portfolio_id: int, name: str) -> int | None: ...
    def rename_value_stream(self, organization_id: int, value_stream_id: int, name: str) -> bool: ...
    def list_delivery_groups(self, value_stream_id: int) -> list[dict]: ...
    def get_delivery_group(self, organization_id: int, delivery_group_id: int) -> dict | None: ...
    def create_delivery_group(self, organization_id: int, value_stream_id: int, name: str) -> int | None: ...
    def rename_delivery_group(self, organization_id: int, delivery_group_id: int, name: str) -> bool: ...
    def list_teams(self, delivery_group_id: int) -> list[dict]: ...
    def get_team(self, organization_id: int, team_id: int) -> dict | None: ...
    def create_team(self, organization_id: int, delivery_group_id: int, name: str) -> int | None: ...
    def rename_team(self, organization_id: int, team_id: int, name: str) -> bool: ...
    def list_people(self, organization_id: int) -> list[dict]: ...
    def get_person(self, organization_id: int, person_id: int) -> dict | None: ...
    def create_person(self, organization_id: int, name: str) -> int: ...
    def person_by_user_id(self, user_id: int) -> dict | None: ...
    def membership_scope(self, person_id: int) -> dict: ...
    def role_for_person(self, person_id: int) -> dict | None: ...
    def list_streams_for_roles(self, organization_id: int) -> list[dict]: ...
    def list_teams_for_assignment(self, organization_id: int) -> list[dict]: ...
    def list_groups_for_roles(self, organization_id: int) -> list[dict]: ...
    def create_person_with_role(self, organization_id: int, name: str, role: str, *, value_stream_id: int | None = None, delivery_group_id: int | None = None, team_id: int | None = None) -> tuple[int | None, str | None]: ...
    def set_account_access(self, organization_id: int, person_id: int, account_access: str) -> str | None: ...
    def rename_person(self, organization_id: int, person_id: int, name: str) -> bool: ...
    def list_members(self, organization_id: int, *, delivery_group_id: int | None = None, team_id: int | None = None) -> list[dict]: ...
    def add_membership(self, organization_id: int, person_id: int, *, delivery_group_id: int | None = None, team_id: int | None = None) -> str | None: ...
    def get_membership(self, organization_id: int, membership_id: int) -> dict | None: ...
    def remove_membership(self, organization_id: int, membership_id: int) -> dict | None: ...
    def list_role_assignments(self, organization_id: int, *, value_stream_id: int | None = None, delivery_group_id: int | None = None, team_id: int | None = None) -> list[dict]: ...
    def assign_role(self, organization_id: int, person_id: int, role: str, *, value_stream_id: int | None = None, delivery_group_id: int | None = None, team_id: int | None = None, commit: bool = True) -> str | None: ...
    def list_goals(self, value_stream_id: int) -> list[dict]: ...
    def get_goal(self, organization_id: int, goal_id: int) -> dict | None: ...
    def create_goal(self, organization_id: int, value_stream_id: int, name: str) -> int | None: ...
    def rename_goal(self, organization_id: int, goal_id: int, name: str) -> bool: ...
    def list_initiatives(self, goal_id: int) -> list[dict]: ...
    def get_initiative(self, organization_id: int, initiative_id: int) -> dict | None: ...
    def create_initiative(self, organization_id: int, goal_id: int, name: str) -> int | None: ...
    def rename_initiative(self, organization_id: int, initiative_id: int, name: str) -> bool: ...
    def set_initiative_state(self, organization_id: int, initiative_id: int, state: str) -> bool: ...
    def list_features(self, initiative_id: int) -> list[dict]: ...
    def get_feature(self, organization_id: int, feature_id: int) -> dict | None: ...
    def create_feature(self, organization_id: int, initiative_id: int, name: str, kind: str) -> int | None: ...
    def update_feature(self, organization_id: int, feature_id: int, name: str, kind: str) -> bool: ...
    def set_feature_priority(self, organization_id: int, feature_id: int, value_sooner: int, urgency: int, risk: int, economic_size: int) -> bool: ...
    def list_stories(self, feature_id: int) -> list[dict]: ...
    def get_story(self, organization_id: int, story_id: int) -> dict | None: ...
    def create_story(self, organization_id: int, feature_id: int, name: str, kind: str) -> int | None: ...
    def update_story(self, organization_id: int, story_id: int, name: str, kind: str) -> bool: ...
    def set_story_estimate(self, organization_id: int, story_id: int, team_id: int, label: str | None, value: int) -> bool: ...
    def list_teams_for_sizing(self, organization_id: int) -> list[dict]: ...
    def save_team_sizing(self, organization_id: int, team_id: int, method: str, size_xs: int, size_s: int, size_m: int, size_l: int, size_xl: int) -> bool: ...
    def list_stage_changes(self, target_kind: str, target_id: int) -> list[dict]: ...
    def latest_builder_id(self, target_kind: str, target_id: int) -> int | None: ...
    def record_stage(self, organization_id: int, target_kind: str, target_id: int, from_stage: str, to_stage: str, person_id: int, changed_at: str) -> None: ...
    def approve_definition(self, organization_id: int, target_kind: str, target_id: int, person_id: int, definition: str) -> bool: ...
    def clear_approval(self, organization_id: int, target_kind: str, target_id: int) -> None: ...
    def done_check_map(self, target_kind: str, target_id: int) -> dict[str, int]: ...
    def save_done_checks(self, organization_id: int, target_kind: str, target_id: int, done_items: set[str]) -> None: ...
    def set_feature_path_flags(self, organization_id: int, feature_id: int, changes_production: int, architecture_applies: int, pii_applies: int) -> bool: ...
    def set_story_production(self, organization_id: int, story_id: int, changes_production: int) -> bool: ...
    def person_role(self, organization_id: int, person_id: int) -> dict | None: ...
    def person_on_team(self, person_id: int, team_id: int) -> bool: ...
    def stories_for_team(self, team_id: int) -> list[dict]: ...
    def features_for_stream(self, value_stream_id: int) -> list[dict]: ...
    def stories_for_group(self, delivery_group_id: int) -> list[dict]: ...
    def set_wip_limit(self, organization_id: int, team_id: int, limit: int) -> bool: ...
    def iteration_id_for_story(self, story_id: int) -> int | None: ...
    def build_count(self, iteration_id: int) -> int: ...
    def take_wip_exception(self, iteration_id: int, story_id: int) -> int | None: ...
    def create_cycle(self, organization_id: int, delivery_group_id: int, name: str, starts_on: str, ends_on: str) -> int | None: ...
    def list_cycles(self, delivery_group_id: int) -> list[dict]: ...
    def get_cycle(self, organization_id: int, cycle_id: int) -> dict | None: ...
    def create_iteration(self, organization_id: int, team_id: int, cycle_id: int, name: str, starts_on: str, ends_on: str) -> int | None: ...
    def list_iterations(self, team_id: int) -> list[dict]: ...
    def get_iteration(self, organization_id: int, iteration_id: int) -> dict | None: ...
    def facilitator_person_id(self, organization_id: int, delivery_group_id: int) -> int | None: ...
    def list_cycle_outcomes(self, cycle_id: int) -> list[dict]: ...
    def list_outcome_links(self, outcome_id: int) -> list[dict]: ...
    def list_cycle_reviews(self, cycle_id: int) -> list[dict]: ...
    def list_cycle_votes(self, cycle_id: int) -> list[dict]: ...
    def list_milestones(self, cycle_id: int) -> list[dict]: ...
    def list_dependencies(self, cycle_id: int) -> list[dict]: ...
    def list_dependent_work(self, cycle_id: int) -> list[dict]: ...
    def list_risks(self, cycle_id: int) -> list[dict]: ...
    def list_capacities(self, cycle_id: int) -> list[dict]: ...
    def list_decisions(self, cycle_id: int) -> list[dict]: ...
    def add_outcome(self, organization_id: int, cycle_id: int, team_id: int | None, description: str, planned_signal: str) -> None: ...
    def outcome_cycle_id(self, organization_id: int, outcome_id: int) -> int | None: ...
    def set_outcome_actual(self, outcome_id: int, actual_signal: str) -> None: ...
    def add_milestone(self, organization_id: int, cycle_id: int, name: str, happens_on: str) -> None: ...
    def add_dependency(self, organization_id: int, cycle_id: int, **values) -> None: ...
    def add_dependent_work(self, organization_id: int, cycle_id: int, **values) -> None: ...
    def save_review(self, organization_id: int, cycle_id: int, **values) -> None: ...
    def add_risk(self, organization_id: int, cycle_id: int, description: str, state: str) -> None: ...
    def get_risk(self, organization_id: int, risk_id: int) -> dict | None: ...
    def set_risk_state(self, risk_id: int, state: str) -> None: ...
    def save_confidence(self, organization_id: int, cycle_id: int, person_id: int, score: int) -> None: ...
    def save_capacity(self, organization_id: int, cycle_id: int, team_id: int, note: str) -> None: ...
    def outcome_in_cycle(self, outcome_id: int, cycle_id: int) -> bool: ...
    def add_outcome_link(self, organization_id: int, outcome_id: int, feature_id: int | None, story_id: int | None) -> None: ...
    def add_group_decision(self, organization_id: int, cycle_id: int, statement: str, person_id: int) -> None: ...
    def list_iteration_board(self, iteration_id: int) -> list[dict]: ...
    def list_stories_not_on_iteration(self, team_id: int) -> list[dict]: ...
    def list_iteration_exceptions(self, iteration_id: int) -> list[dict]: ...
    def add_iteration_story(self, organization_id: int, iteration_id: int, story_id: int) -> bool: ...
    def set_iteration_position(self, iteration_id: int, story_id: int, position: int) -> None: ...
    def set_iteration_accepted(self, iteration_id: int, story_id: int, accepted: int) -> None: ...
    def add_wip_exception_row(self, organization_id: int, iteration_id: int, story_id: int, person_id: int, reason: str) -> None: ...
    def add_sync_note(self, organization_id: int, team_id: int, note_on: str, body: str, person_id: int) -> None: ...
    def add_cross_note(self, organization_id: int, team_id: int, impediment: str, dependency: str, asked_team_id: int, person_id: int) -> None: ...
    def add_retro_note(self, organization_id: int, team_id: int, iteration_id: int, body: str, person_id: int) -> None: ...
    def get_retro_note(self, organization_id: int, note_id: int) -> dict | None: ...
    def add_promoted_learning(self, organization_id: int, team_id: int, retro_note_id: int, statement: str) -> None: ...
    def list_group_sync_notes(self, delivery_group_id: int) -> list[dict]: ...
    def list_group_cross_notes(self, delivery_group_id: int) -> list[dict]: ...
    def list_team_retro_notes(self, team_id: int) -> list[dict]: ...
    def list_group_learnings(self, delivery_group_id: int) -> list[dict]: ...
    def list_group_flow_items(self, delivery_group_id: int) -> list[dict]: ...
    def list_stage_stamps(self, target_kind: str, target_ids: list[int]) -> list[dict]: ...
    def list_policies(self, delivery_group_id: int) -> list[dict]: ...
    def add_policy(self, organization_id: int, delivery_group_id: int, from_stage: str, to_stage: str, effect: str) -> int | None: ...
    def policies_for_move(self, organization_id: int, target_kind: str, target_id: int, from_stage: str, to_stage: str) -> list[dict]: ...
    def open_blocks(self, organization_id: int, target_kind: str, target_id: int, from_stage: str) -> list[dict]: ...
    def approve_policy(self, organization_id: int, policy_id: int, target_kind: str, target_id: int, person_id: int, approved_at: str) -> bool: ...
    def list_evidence(self, target_kind: str, target_id: int) -> list[dict]: ...
    def add_evidence(self, organization_id: int, target_kind: str, target_id: int, action: str, actor_kind: str, actor_name: str, happened_at: str, before_text: str, after_text: str) -> None: ...
    def set_criteria(self, organization_id: int, target_kind: str, target_id: int, measure_name: str, threshold: str, dataset_label: str, latency_target: str) -> bool: ...


class SqlStore:
    """SQLite-backed Database. The session stays inside this object."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def user_by_username(self, username: str) -> dict | None:
        return database.user_by_username(self._session, username)

    def user_by_id(self, user_id: int) -> dict | None:
        return database.user_by_id(self._session, user_id)

    def set_password(self, user_id: int, password: str) -> None:
        return database.set_password(self._session, user_id, password)

    def has_added_user(self, organization_id: int) -> bool:
        return database.has_added_user(self._session, organization_id)

    def organization_tree(self, organization_id: int) -> list[dict]:
        return database.organization_tree(self._session, organization_id)

    def list_portfolios(self, organization_id: int) -> list[dict]:
        return database.list_portfolios(self._session, organization_id)

    def get_portfolio(self, organization_id: int, portfolio_id: int) -> dict | None:
        return database.get_portfolio(self._session, organization_id, portfolio_id)

    def create_portfolio(self, organization_id: int, name: str) -> int:
        return database.create_portfolio(self._session, organization_id, name)

    def rename_portfolio(self, organization_id: int, portfolio_id: int, name: str) -> bool:
        return database.rename_portfolio(self._session, organization_id, portfolio_id, name)

    def list_value_streams(self, portfolio_id: int) -> list[dict]:
        return database.list_value_streams(self._session, portfolio_id)

    def get_value_stream(self, organization_id: int, value_stream_id: int) -> dict | None:
        return database.get_value_stream(self._session, organization_id, value_stream_id)

    def create_value_stream(self, organization_id: int, portfolio_id: int, name: str) -> int | None:
        return database.create_value_stream(self._session, organization_id, portfolio_id, name)

    def rename_value_stream(self, organization_id: int, value_stream_id: int, name: str) -> bool:
        return database.rename_value_stream(self._session, organization_id, value_stream_id, name)

    def list_delivery_groups(self, value_stream_id: int) -> list[dict]:
        return database.list_delivery_groups(self._session, value_stream_id)

    def get_delivery_group(self, organization_id: int, delivery_group_id: int) -> dict | None:
        return database.get_delivery_group(self._session, organization_id, delivery_group_id)

    def create_delivery_group(self, organization_id: int, value_stream_id: int, name: str) -> int | None:
        return database.create_delivery_group(self._session, organization_id, value_stream_id, name)

    def rename_delivery_group(self, organization_id: int, delivery_group_id: int, name: str) -> bool:
        return database.rename_delivery_group(self._session, organization_id, delivery_group_id, name)

    def list_teams(self, delivery_group_id: int) -> list[dict]:
        return database.list_teams(self._session, delivery_group_id)

    def get_team(self, organization_id: int, team_id: int) -> dict | None:
        return database.get_team(self._session, organization_id, team_id)

    def create_team(self, organization_id: int, delivery_group_id: int, name: str) -> int | None:
        return database.create_team(self._session, organization_id, delivery_group_id, name)

    def rename_team(self, organization_id: int, team_id: int, name: str) -> bool:
        return database.rename_team(self._session, organization_id, team_id, name)

    def list_people(self, organization_id: int) -> list[dict]:
        return database.list_people(self._session, organization_id)

    def get_person(self, organization_id: int, person_id: int) -> dict | None:
        return database.get_person(self._session, organization_id, person_id)

    def create_person(self, organization_id: int, name: str) -> int:
        return database.create_person(self._session, organization_id, name)

    def person_by_user_id(self, user_id: int) -> dict | None:
        return database.person_by_user_id(self._session, user_id)

    def membership_scope(self, person_id: int) -> dict:
        return database.membership_scope(self._session, person_id)

    def role_for_person(self, person_id: int) -> dict | None:
        return database.role_for_person(self._session, person_id)

    def list_streams_for_roles(self, organization_id: int) -> list[dict]:
        return database.list_streams_for_roles(self._session, organization_id)

    def list_teams_for_assignment(self, organization_id: int) -> list[dict]:
        return database.list_teams_for_assignment(self._session, organization_id)

    def list_groups_for_roles(self, organization_id: int) -> list[dict]:
        return database.list_groups_for_roles(self._session, organization_id)

    def create_person_with_role(self, organization_id: int, name: str, role: str, *, value_stream_id: int | None = None, delivery_group_id: int | None = None, team_id: int | None = None) -> tuple[int | None, str | None]:
        return database.create_person_with_role(self._session, organization_id, name, role, value_stream_id=value_stream_id, delivery_group_id=delivery_group_id, team_id=team_id)

    def set_account_access(self, organization_id: int, person_id: int, account_access: str) -> str | None:
        return database.set_account_access(self._session, organization_id, person_id, account_access)

    def rename_person(self, organization_id: int, person_id: int, name: str) -> bool:
        return database.rename_person(self._session, organization_id, person_id, name)

    def list_members(self, organization_id: int, *, delivery_group_id: int | None = None, team_id: int | None = None) -> list[dict]:
        return database.list_members(self._session, organization_id, delivery_group_id=delivery_group_id, team_id=team_id)

    def add_membership(self, organization_id: int, person_id: int, *, delivery_group_id: int | None = None, team_id: int | None = None) -> str | None:
        return database.add_membership(self._session, organization_id, person_id, delivery_group_id=delivery_group_id, team_id=team_id)

    def get_membership(self, organization_id: int, membership_id: int) -> dict | None:
        return database.get_membership(self._session, organization_id, membership_id)

    def remove_membership(self, organization_id: int, membership_id: int) -> dict | None:
        return database.remove_membership(self._session, organization_id, membership_id)

    def list_role_assignments(self, organization_id: int, *, value_stream_id: int | None = None, delivery_group_id: int | None = None, team_id: int | None = None) -> list[dict]:
        return database.list_role_assignments(self._session, organization_id, value_stream_id=value_stream_id, delivery_group_id=delivery_group_id, team_id=team_id)

    def assign_role(self, organization_id: int, person_id: int, role: str, *, value_stream_id: int | None = None, delivery_group_id: int | None = None, team_id: int | None = None, commit: bool = True) -> str | None:
        return database.assign_role(self._session, organization_id, person_id, role, value_stream_id=value_stream_id, delivery_group_id=delivery_group_id, team_id=team_id, commit=commit)

    def list_goals(self, value_stream_id: int) -> list[dict]:
        return database.list_goals(self._session, value_stream_id)

    def get_goal(self, organization_id: int, goal_id: int) -> dict | None:
        return database.get_goal(self._session, organization_id, goal_id)

    def create_goal(self, organization_id: int, value_stream_id: int, name: str) -> int | None:
        return database.create_goal(self._session, organization_id, value_stream_id, name)

    def rename_goal(self, organization_id: int, goal_id: int, name: str) -> bool:
        return database.rename_goal(self._session, organization_id, goal_id, name)

    def list_initiatives(self, goal_id: int) -> list[dict]:
        return database.list_initiatives(self._session, goal_id)

    def get_initiative(self, organization_id: int, initiative_id: int) -> dict | None:
        return database.get_initiative(self._session, organization_id, initiative_id)

    def create_initiative(self, organization_id: int, goal_id: int, name: str) -> int | None:
        return database.create_initiative(self._session, organization_id, goal_id, name)

    def rename_initiative(self, organization_id: int, initiative_id: int, name: str) -> bool:
        return database.rename_initiative(self._session, organization_id, initiative_id, name)

    def set_initiative_state(self, organization_id: int, initiative_id: int, state: str) -> bool:
        return database.set_initiative_state(self._session, organization_id, initiative_id, state)

    def list_features(self, initiative_id: int) -> list[dict]:
        return database.list_features(self._session, initiative_id)

    def get_feature(self, organization_id: int, feature_id: int) -> dict | None:
        return database.get_feature(self._session, organization_id, feature_id)

    def create_feature(self, organization_id: int, initiative_id: int, name: str, kind: str) -> int | None:
        return database.create_feature(self._session, organization_id, initiative_id, name, kind)

    def update_feature(self, organization_id: int, feature_id: int, name: str, kind: str) -> bool:
        return database.update_feature(self._session, organization_id, feature_id, name, kind)

    def set_feature_priority(self, organization_id: int, feature_id: int, value_sooner: int, urgency: int, risk: int, economic_size: int) -> bool:
        return database.set_feature_priority(self._session, organization_id, feature_id, value_sooner, urgency, risk, economic_size)

    def list_stories(self, feature_id: int) -> list[dict]:
        return database.list_stories(self._session, feature_id)

    def get_story(self, organization_id: int, story_id: int) -> dict | None:
        return database.get_story(self._session, organization_id, story_id)

    def create_story(self, organization_id: int, feature_id: int, name: str, kind: str) -> int | None:
        return database.create_story(self._session, organization_id, feature_id, name, kind)

    def update_story(self, organization_id: int, story_id: int, name: str, kind: str) -> bool:
        return database.update_story(self._session, organization_id, story_id, name, kind)

    def set_story_estimate(self, organization_id: int, story_id: int, team_id: int, label: str | None, value: int) -> bool:
        return database.set_story_estimate(self._session, organization_id, story_id, team_id, label, value)

    def list_teams_for_sizing(self, organization_id: int) -> list[dict]:
        return database.list_teams_for_sizing(self._session, organization_id)

    def save_team_sizing(self, organization_id: int, team_id: int, method: str, size_xs: int, size_s: int, size_m: int, size_l: int, size_xl: int) -> bool:
        return database.save_team_sizing(self._session, organization_id, team_id, method, size_xs, size_s, size_m, size_l, size_xl)

    def list_stage_changes(self, target_kind: str, target_id: int) -> list[dict]:
        return database.list_stage_changes(self._session, target_kind, target_id)

    def latest_builder_id(self, target_kind: str, target_id: int) -> int | None:
        return database.latest_builder_id(self._session, target_kind, target_id)

    def record_stage(self, organization_id: int, target_kind: str, target_id: int, from_stage: str, to_stage: str, person_id: int, changed_at: str) -> None:
        return database.record_stage(self._session, organization_id, target_kind, target_id, from_stage, to_stage, person_id, changed_at)

    def approve_definition(self, organization_id: int, target_kind: str, target_id: int, person_id: int, definition: str) -> bool:
        return database.approve_definition(self._session, organization_id, target_kind, target_id, person_id, definition)

    def clear_approval(self, organization_id: int, target_kind: str, target_id: int) -> None:
        return database.clear_approval(self._session, organization_id, target_kind, target_id)

    def done_check_map(self, target_kind: str, target_id: int) -> dict[str, int]:
        return database.done_check_map(self._session, target_kind, target_id)

    def save_done_checks(self, organization_id: int, target_kind: str, target_id: int, done_items: set[str]) -> None:
        return database.save_done_checks(self._session, organization_id, target_kind, target_id, done_items)

    def set_feature_path_flags(self, organization_id: int, feature_id: int, changes_production: int, architecture_applies: int, pii_applies: int) -> bool:
        return database.set_feature_path_flags(self._session, organization_id, feature_id, changes_production, architecture_applies, pii_applies)

    def set_story_production(self, organization_id: int, story_id: int, changes_production: int) -> bool:
        return database.set_story_production(self._session, organization_id, story_id, changes_production)

    def person_role(self, organization_id: int, person_id: int) -> dict | None:
        return database.person_role(self._session, organization_id, person_id)

    def person_on_team(self, person_id: int, team_id: int) -> bool:
        return database.person_on_team(self._session, person_id, team_id)

    def stories_for_team(self, team_id: int) -> list[dict]:
        return database.stories_for_team(self._session, team_id)

    def features_for_stream(self, value_stream_id: int) -> list[dict]:
        return database.features_for_stream(self._session, value_stream_id)

    def stories_for_group(self, delivery_group_id: int) -> list[dict]:
        return database.stories_for_group(self._session, delivery_group_id)

    def set_wip_limit(self, organization_id: int, team_id: int, limit: int) -> bool:
        return database.set_wip_limit(self._session, organization_id, team_id, limit)

    def iteration_id_for_story(self, story_id: int) -> int | None:
        return database.iteration_id_for_story(self._session, story_id)

    def build_count(self, iteration_id: int) -> int:
        return database.build_count(self._session, iteration_id)

    def take_wip_exception(self, iteration_id: int, story_id: int) -> int | None:
        return database.take_wip_exception(self._session, iteration_id, story_id)

    def create_cycle(self, organization_id: int, delivery_group_id: int, name: str, starts_on: str, ends_on: str) -> int | None:
        return database.create_cycle(self._session, organization_id, delivery_group_id, name, starts_on, ends_on)

    def list_cycles(self, delivery_group_id: int) -> list[dict]:
        return database.list_cycles(self._session, delivery_group_id)

    def get_cycle(self, organization_id: int, cycle_id: int) -> dict | None:
        return database.get_cycle(self._session, organization_id, cycle_id)

    def create_iteration(self, organization_id: int, team_id: int, cycle_id: int, name: str, starts_on: str, ends_on: str) -> int | None:
        return database.create_iteration(self._session, organization_id, team_id, cycle_id, name, starts_on, ends_on)

    def list_iterations(self, team_id: int) -> list[dict]:
        return database.list_iterations(self._session, team_id)

    def get_iteration(self, organization_id: int, iteration_id: int) -> dict | None:
        return database.get_iteration(self._session, organization_id, iteration_id)

    def facilitator_person_id(self, organization_id: int, delivery_group_id: int) -> int | None:
        return database.facilitator_person_id(self._session, organization_id, delivery_group_id)

    def list_cycle_outcomes(self, cycle_id: int) -> list[dict]:
        return database.list_cycle_outcomes(self._session, cycle_id)

    def list_outcome_links(self, outcome_id: int) -> list[dict]:
        return database.list_outcome_links(self._session, outcome_id)

    def list_cycle_reviews(self, cycle_id: int) -> list[dict]:
        return database.list_cycle_reviews(self._session, cycle_id)

    def list_cycle_votes(self, cycle_id: int) -> list[dict]:
        return database.list_cycle_votes(self._session, cycle_id)

    def list_milestones(self, cycle_id: int) -> list[dict]:
        return database.list_milestones(self._session, cycle_id)

    def list_dependencies(self, cycle_id: int) -> list[dict]:
        return database.list_dependencies(self._session, cycle_id)

    def list_dependent_work(self, cycle_id: int) -> list[dict]:
        return database.list_dependent_work(self._session, cycle_id)

    def list_risks(self, cycle_id: int) -> list[dict]:
        return database.list_risks(self._session, cycle_id)

    def list_capacities(self, cycle_id: int) -> list[dict]:
        return database.list_capacities(self._session, cycle_id)

    def list_decisions(self, cycle_id: int) -> list[dict]:
        return database.list_decisions(self._session, cycle_id)

    def add_outcome(self, organization_id: int, cycle_id: int, team_id: int | None, description: str, planned_signal: str) -> None:
        return database.add_outcome(self._session, organization_id, cycle_id, team_id, description, planned_signal)

    def outcome_cycle_id(self, organization_id: int, outcome_id: int) -> int | None:
        return database.outcome_cycle_id(self._session, organization_id, outcome_id)

    def set_outcome_actual(self, outcome_id: int, actual_signal: str) -> None:
        return database.set_outcome_actual(self._session, outcome_id, actual_signal)

    def add_milestone(self, organization_id: int, cycle_id: int, name: str, happens_on: str) -> None:
        return database.add_milestone(self._session, organization_id, cycle_id, name, happens_on)

    def add_dependency(self, organization_id: int, cycle_id: int, **values) -> None:
        return database.add_dependency(self._session, organization_id, cycle_id, **values)

    def add_dependent_work(self, organization_id: int, cycle_id: int, **values) -> None:
        return database.add_dependent_work(self._session, organization_id, cycle_id, **values)

    def save_review(self, organization_id: int, cycle_id: int, **values) -> None:
        return database.save_review(self._session, organization_id, cycle_id, **values)

    def add_risk(self, organization_id: int, cycle_id: int, description: str, state: str) -> None:
        return database.add_risk(self._session, organization_id, cycle_id, description, state)

    def get_risk(self, organization_id: int, risk_id: int) -> dict | None:
        return database.get_risk(self._session, organization_id, risk_id)

    def set_risk_state(self, risk_id: int, state: str) -> None:
        return database.set_risk_state(self._session, risk_id, state)

    def save_confidence(self, organization_id: int, cycle_id: int, person_id: int, score: int) -> None:
        return database.save_confidence(self._session, organization_id, cycle_id, person_id, score)

    def save_capacity(self, organization_id: int, cycle_id: int, team_id: int, note: str) -> None:
        return database.save_capacity(self._session, organization_id, cycle_id, team_id, note)

    def outcome_in_cycle(self, outcome_id: int, cycle_id: int) -> bool:
        return database.outcome_in_cycle(self._session, outcome_id, cycle_id)

    def add_outcome_link(self, organization_id: int, outcome_id: int, feature_id: int | None, story_id: int | None) -> None:
        return database.add_outcome_link(self._session, organization_id, outcome_id, feature_id, story_id)

    def add_group_decision(self, organization_id: int, cycle_id: int, statement: str, person_id: int) -> None:
        return database.add_group_decision(self._session, organization_id, cycle_id, statement, person_id)

    def list_iteration_board(self, iteration_id: int) -> list[dict]:
        return database.list_iteration_board(self._session, iteration_id)

    def list_stories_not_on_iteration(self, team_id: int) -> list[dict]:
        return database.list_stories_not_on_iteration(self._session, team_id)

    def list_iteration_exceptions(self, iteration_id: int) -> list[dict]:
        return database.list_iteration_exceptions(self._session, iteration_id)

    def add_iteration_story(self, organization_id: int, iteration_id: int, story_id: int) -> bool:
        return database.add_iteration_story(self._session, organization_id, iteration_id, story_id)

    def set_iteration_position(self, iteration_id: int, story_id: int, position: int) -> None:
        return database.set_iteration_position(self._session, iteration_id, story_id, position)

    def set_iteration_accepted(self, iteration_id: int, story_id: int, accepted: int) -> None:
        return database.set_iteration_accepted(self._session, iteration_id, story_id, accepted)

    def add_wip_exception_row(self, organization_id: int, iteration_id: int, story_id: int, person_id: int, reason: str) -> None:
        return database.add_wip_exception_row(self._session, organization_id, iteration_id, story_id, person_id, reason)

    def add_sync_note(self, organization_id: int, team_id: int, note_on: str, body: str, person_id: int) -> None:
        return database.add_sync_note(self._session, organization_id, team_id, note_on, body, person_id)

    def add_cross_note(self, organization_id: int, team_id: int, impediment: str, dependency: str, asked_team_id: int, person_id: int) -> None:
        return database.add_cross_note(self._session, organization_id, team_id, impediment, dependency, asked_team_id, person_id)

    def add_retro_note(self, organization_id: int, team_id: int, iteration_id: int, body: str, person_id: int) -> None:
        return database.add_retro_note(self._session, organization_id, team_id, iteration_id, body, person_id)

    def get_retro_note(self, organization_id: int, note_id: int) -> dict | None:
        return database.get_retro_note(self._session, organization_id, note_id)

    def add_promoted_learning(self, organization_id: int, team_id: int, retro_note_id: int, statement: str) -> None:
        return database.add_promoted_learning(self._session, organization_id, team_id, retro_note_id, statement)

    def list_group_sync_notes(self, delivery_group_id: int) -> list[dict]:
        return database.list_group_sync_notes(self._session, delivery_group_id)

    def list_group_cross_notes(self, delivery_group_id: int) -> list[dict]:
        return database.list_group_cross_notes(self._session, delivery_group_id)

    def list_team_retro_notes(self, team_id: int) -> list[dict]:
        return database.list_team_retro_notes(self._session, team_id)

    def list_group_learnings(self, delivery_group_id: int) -> list[dict]:
        return database.list_group_learnings(self._session, delivery_group_id)

    def list_group_flow_items(self, delivery_group_id: int) -> list[dict]:
        return database.list_group_flow_items(self._session, delivery_group_id)

    def list_stage_stamps(self, target_kind: str, target_ids: list[int]) -> list[dict]:
        return database.list_stage_stamps(self._session, target_kind, target_ids)

    def list_policies(self, delivery_group_id: int) -> list[dict]:
        return database.list_policies(self._session, delivery_group_id)

    def add_policy(self, organization_id: int, delivery_group_id: int, from_stage: str, to_stage: str, effect: str) -> int | None:
        return database.add_policy(self._session, organization_id, delivery_group_id, from_stage, to_stage, effect)

    def policies_for_move(self, organization_id: int, target_kind: str, target_id: int, from_stage: str, to_stage: str) -> list[dict]:
        return database.policies_for_move(self._session, organization_id, target_kind, target_id, from_stage, to_stage)

    def open_blocks(self, organization_id: int, target_kind: str, target_id: int, from_stage: str) -> list[dict]:
        return database.open_blocks(self._session, organization_id, target_kind, target_id, from_stage)

    def approve_policy(self, organization_id: int, policy_id: int, target_kind: str, target_id: int, person_id: int, approved_at: str) -> bool:
        return database.approve_policy(self._session, organization_id, policy_id, target_kind, target_id, person_id, approved_at)

    def list_evidence(self, target_kind: str, target_id: int) -> list[dict]:
        return database.list_evidence(self._session, target_kind, target_id)

    def add_evidence(self, organization_id: int, target_kind: str, target_id: int, action: str, actor_kind: str, actor_name: str, happened_at: str, before_text: str, after_text: str) -> None:
        return database.add_evidence(self._session, organization_id, target_kind, target_id, action, actor_kind, actor_name, happened_at, before_text, after_text)

    def set_criteria(self, organization_id: int, target_kind: str, target_id: int, measure_name: str, threshold: str, dataset_label: str, latency_target: str) -> bool:
        return database.set_criteria(self._session, organization_id, target_kind, target_id, measure_name, threshold, dataset_label, latency_target)


@contextmanager
def open_store(path: Path) -> Iterator[SqlStore]:
    session = connect(path)
    try:
        yield SqlStore(session)
    finally:
        session.close()


def get_store(request: Request) -> Iterator[SqlStore]:
    with open_store(request.app.state.settings.database_path) as store:
        yield store

