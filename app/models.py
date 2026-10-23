from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    applied_at: Mapped[str] = mapped_column(Text, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    must_change_password: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    account_access: Mapped[str] = mapped_column(
        Text, nullable=False, default="member", server_default=text("'member'")
    )


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class ValueStream(Base):
    __tablename__ = "value_streams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class DeliveryGroup(Base):
    __tablename__ = "delivery_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    value_stream_id: Mapped[int] = mapped_column(ForeignKey("value_streams.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    delivery_group_id: Mapped[int] = mapped_column(ForeignKey("delivery_groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sizing_method: Mapped[str] = mapped_column(
        Text, nullable=False, default="tshirt", server_default=text("'tshirt'")
    )
    size_xs: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    size_s: Mapped[int] = mapped_column(Integer, nullable=False, default=2, server_default=text("2"))
    size_m: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default=text("3"))
    size_l: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default=text("5"))
    size_xl: Mapped[int] = mapped_column(Integer, nullable=False, default=8, server_default=text("8"))
    wip_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2, server_default=text("2"))


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint(
            "(delivery_group_id IS NOT NULL AND team_id IS NULL) "
            "OR (delivery_group_id IS NULL AND team_id IS NOT NULL)",
            name="memberships_one_place",
        ),
        Index(
            "memberships_person_group",
            "person_id",
            "delivery_group_id",
            unique=True,
            sqlite_where=text("delivery_group_id IS NOT NULL"),
        ),
        Index(
            "memberships_person_team",
            "person_id",
            "team_id",
            unique=True,
            sqlite_where=text("team_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    delivery_group_id: Mapped[int | None] = mapped_column(ForeignKey("delivery_groups.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))


class RoleAssignment(Base):
    __tablename__ = "role_assignments"
    __table_args__ = (
        CheckConstraint(
            "("
            "role = 'stream_owner' AND value_stream_id IS NOT NULL "
            "AND delivery_group_id IS NULL AND team_id IS NULL"
            ") OR ("
            "role IN ('group_facilitator', 'product_manager', 'business_stakeholder') "
            "AND delivery_group_id IS NOT NULL AND value_stream_id IS NULL AND team_id IS NULL"
            ") OR ("
            "role IN ('product_owner', 'scrum_master', 'technical_lead', 'team_member') "
            "AND value_stream_id IS NULL AND delivery_group_id IS NULL"
            ")",
            name="role_assignments_place",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    value_stream_id: Mapped[int | None] = mapped_column(ForeignKey("value_streams.id"))
    delivery_group_id: Mapped[int | None] = mapped_column(ForeignKey("delivery_groups.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    value_stream_id: Mapped[int] = mapped_column(ForeignKey("value_streams.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class Initiative(Base):
    __tablename__ = "initiatives"
    __table_args__ = (
        CheckConstraint(
            "state IN ('Proposed', 'Shaping', 'Ready', 'Active', 'Done')",
            name="initiatives_state",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(
        Text, nullable=False, default="Proposed", server_default=text("'Proposed'")
    )


class Feature(Base):
    __tablename__ = "features"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('feature', 'platform', 'prototype', 'experiment')",
            name="features_kind",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    initiative_id: Mapped[int] = mapped_column(ForeignKey("initiatives.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(
        Text, nullable=False, default="feature", server_default=text("'feature'")
    )
    value_sooner: Mapped[int | None] = mapped_column(Integer)
    urgency: Mapped[int | None] = mapped_column(Integer)
    risk: Mapped[int | None] = mapped_column(Integer)
    economic_size: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(
        Text, nullable=False, default="Discover", server_default=text("'Discover'")
    )
    approved_by_person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"))
    approved_definition: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    changes_production: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    architecture_applies: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    pii_applies: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    measure_name: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    threshold: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    dataset_label: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    latency_target: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )


class Story(Base):
    __tablename__ = "stories"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('feature', 'platform', 'prototype', 'experiment')",
            name="stories_kind",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    feature_id: Mapped[int] = mapped_column(ForeignKey("features.id"), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(
        Text, nullable=False, default="feature", server_default=text("'feature'")
    )
    estimate_label: Mapped[str | None] = mapped_column(Text)
    estimate_value: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(
        Text, nullable=False, default="Discover", server_default=text("'Discover'")
    )
    approved_by_person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"))
    approved_definition: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    changes_production: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    measure_name: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    threshold: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    dataset_label: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    latency_target: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )


class StageChange(Base):
    __tablename__ = "stage_changes"
    __table_args__ = (
        CheckConstraint("target_kind IN ('feature', 'story')", name="stage_changes_kind"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    target_kind: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    from_stage: Mapped[str] = mapped_column(Text, nullable=False)
    to_stage: Mapped[str] = mapped_column(Text, nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    changed_at: Mapped[str] = mapped_column(Text, nullable=False)


class DoneCheck(Base):
    __tablename__ = "done_checks"
    __table_args__ = (
        CheckConstraint("target_kind IN ('feature', 'story')", name="done_checks_kind"),
    )

    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    target_kind: Mapped[str] = mapped_column(Text, primary_key=True)
    target_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item: Mapped[str] = mapped_column(Text, primary_key=True)
    done: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))


class PlanningCycle(Base):
    __tablename__ = "planning_cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    delivery_group_id: Mapped[int] = mapped_column(ForeignKey("delivery_groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    starts_on: Mapped[str] = mapped_column(Text, nullable=False)
    ends_on: Mapped[str] = mapped_column(Text, nullable=False)


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    planned_signal: Mapped[str] = mapped_column(Text, nullable=False)
    actual_signal: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    happens_on: Mapped[str] = mapped_column(Text, nullable=False)


class Dependency(Base):
    __tablename__ = "dependencies"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'done', 'blocked')", name="dependencies_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner_person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    needed_by: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="open", server_default=text("'open'")
    )
    opened_on: Mapped[str] = mapped_column(Text, nullable=False)
    providing_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))


class DependentWork(Base):
    __tablename__ = "dependent_work"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'done', 'not_needed')",
            name="dependent_work_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    feature_id: Mapped[int] = mapped_column(ForeignKey("features.id"), nullable=False)
    needed: Mapped[str] = mapped_column(Text, nullable=False)
    done_looks_like: Mapped[str] = mapped_column(Text, nullable=False)
    needed_by: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="open", server_default=text("'open'")
    )
    providing_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("cycle_id", "feature_id", "kind", name="reviews_cycle_feature_kind"),
        CheckConstraint("kind IN ('architecture', 'pii')", name="reviews_kind"),
        CheckConstraint("result IN ('approved', 'changes_requested')", name="reviews_result"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    feature_id: Mapped[int] = mapped_column(ForeignKey("features.id"), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    reviewed_on: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)


class Risk(Base):
    __tablename__ = "risks"
    __table_args__ = (
        CheckConstraint(
            "state IN ('open', 'owned', 'accepted', 'mitigated', 'closed')",
            name="risks_state",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(
        Text, nullable=False, default="open", server_default=text("'open'")
    )


class ConfidenceVote(Base):
    __tablename__ = "confidence_votes"
    __table_args__ = (
        UniqueConstraint("cycle_id", "person_id", name="confidence_votes_cycle_person"),
        CheckConstraint("score BETWEEN 1 AND 5", name="confidence_votes_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)


class CapacityNote(Base):
    __tablename__ = "capacity_notes"
    __table_args__ = (UniqueConstraint("cycle_id", "team_id", name="capacity_notes_cycle_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)


class OutcomeLink(Base):
    __tablename__ = "outcome_links"
    __table_args__ = (
        CheckConstraint(
            "(feature_id IS NOT NULL AND story_id IS NULL) "
            "OR (feature_id IS NULL AND story_id IS NOT NULL)",
            name="outcome_links_one_target",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    outcome_id: Mapped[int] = mapped_column(ForeignKey("outcomes.id"), nullable=False)
    feature_id: Mapped[int | None] = mapped_column(ForeignKey("features.id"))
    story_id: Mapped[int | None] = mapped_column(ForeignKey("stories.id"))


class GroupDecision(Base):
    __tablename__ = "group_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    acting_role: Mapped[str] = mapped_column(Text, nullable=False)


class Iteration(Base):
    __tablename__ = "iterations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("planning_cycles.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    starts_on: Mapped[str] = mapped_column(Text, nullable=False)
    ends_on: Mapped[str] = mapped_column(Text, nullable=False)


class IterationStory(Base):
    __tablename__ = "iteration_stories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    iteration_id: Mapped[int] = mapped_column(ForeignKey("iterations.id"), nullable=False)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False, unique=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))


class WipException(Base):
    __tablename__ = "wip_exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    iteration_id: Mapped[int] = mapped_column(ForeignKey("iterations.id"), nullable=False)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class SyncNote(Base):
    __tablename__ = "sync_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    note_on: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    acting_role: Mapped[str] = mapped_column(Text, nullable=False)


class CrossTeamNote(Base):
    __tablename__ = "cross_team_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    impediment: Mapped[str] = mapped_column(Text, nullable=False)
    dependency: Mapped[str] = mapped_column(Text, nullable=False)
    asked_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    acting_role: Mapped[str] = mapped_column(Text, nullable=False)


class RetroNote(Base):
    __tablename__ = "retro_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    iteration_id: Mapped[int] = mapped_column(ForeignKey("iterations.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    acting_role: Mapped[str] = mapped_column(Text, nullable=False)


class PromotedLearning(Base):
    __tablename__ = "promoted_learnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    retro_note_id: Mapped[int] = mapped_column(ForeignKey("retro_notes.id"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)


class Policy(Base):
    __tablename__ = "policies"
    __table_args__ = (
        CheckConstraint("effect IN ('block', 'warning')", name="policies_effect"),
        CheckConstraint(
            "from_stage IN ('', 'Discover', 'Define', 'Build', 'Check', 'Ship')",
            name="policies_from",
        ),
        CheckConstraint(
            "to_stage IN ('Discover', 'Define', 'Build', 'Check', 'Ship')",
            name="policies_to",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    delivery_group_id: Mapped[int] = mapped_column(ForeignKey("delivery_groups.id"), nullable=False)
    from_stage: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=text("''")
    )
    to_stage: Mapped[str] = mapped_column(Text, nullable=False)
    effect: Mapped[str] = mapped_column(Text, nullable=False)


class PolicyApproval(Base):
    __tablename__ = "policy_approvals"
    __table_args__ = (
        UniqueConstraint(
            "policy_id", "target_kind", "target_id", name="policy_approvals_once"
        ),
        CheckConstraint("target_kind IN ('feature', 'story')", name="policy_approvals_kind"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    target_kind: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    approved_at: Mapped[str] = mapped_column(Text, nullable=False)


class Evidence(Base):
    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint("target_kind IN ('feature', 'story')", name="evidence_target"),
        CheckConstraint("actor_kind IN ('person', 'agent')", name="evidence_actor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    target_kind: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    actor_kind: Mapped[str] = mapped_column(Text, nullable=False)
    actor_name: Mapped[str] = mapped_column(Text, nullable=False)
    happened_at: Mapped[str] = mapped_column(Text, nullable=False)
    before_text: Mapped[str] = mapped_column(Text, nullable=False)
    after_text: Mapped[str] = mapped_column(Text, nullable=False)
