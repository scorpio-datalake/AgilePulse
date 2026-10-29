import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RoleName = Literal[
    "stream_owner",
    "group_facilitator",
    "product_manager",
    "business_stakeholder",
    "product_owner",
    "scrum_master",
    "technical_lead",
    "team_member",
]

ROLE_RECORD = {
    "stream_owner": "value_stream",
    "group_facilitator": "delivery_group",
    "product_manager": "delivery_group",
    "business_stakeholder": "delivery_group",
    "product_owner": "team",
    "scrum_master": "team",
    "technical_lead": "team",
    "team_member": "team",
}


class SignInForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class PasswordChangeForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    password: str = Field(min_length=1, max_length=128)
    password_again: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_again:
            raise ValueError("match")
        return self


class NameForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)


class ValueStreamForm(NameForm):
    portfolio_id: int = Field(ge=1)


class DeliveryGroupForm(NameForm):
    value_stream_id: int = Field(ge=1)


class TeamForm(NameForm):
    delivery_group_id: int = Field(ge=1)


class MembershipForm(BaseModel):
    person_id: int = Field(ge=1)


class PersonCreateForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    role: RoleName
    value_stream_id: int | None = None
    delivery_group_id: int | None = None

    @model_validator(mode="after")
    def place_role(self):
        expected = ROLE_RECORD[self.role]
        if expected == "team":
            self.value_stream_id = None
            self.delivery_group_id = None
            return self
        if expected == "value_stream":
            if self.value_stream_id is None:
                raise ValueError("stream")
            self.delivery_group_id = None
            return self
        if self.delivery_group_id is None:
            raise ValueError("group")
        self.value_stream_id = None
        return self


WorkKind = Literal["feature", "platform", "prototype", "experiment"]
InitiativeState = Literal["Proposed", "Shaping", "Ready", "Active", "Done"]
SizingMethod = Literal["tshirt", "points"]
TShirtLabel = Literal["XS", "S", "M", "L", "XL"]


class GoalForm(NameForm):
    value_stream_id: int = Field(ge=1)


class InitiativeForm(NameForm):
    goal_id: int = Field(ge=1)


class InitiativeStateForm(BaseModel):
    state: InitiativeState


class FeatureForm(NameForm):
    initiative_id: int = Field(ge=1)
    kind: WorkKind


class StoryForm(NameForm):
    feature_id: int = Field(ge=1)
    kind: WorkKind


class StoryFeatureForm(BaseModel):
    feature_id: int = Field(ge=1)


class PriorityForm(BaseModel):
    value_sooner: int = Field(ge=0)
    urgency: int = Field(ge=0)
    risk: int = Field(ge=0)
    economic_size: int = Field(ge=1)


class SizingForm(BaseModel):
    method: SizingMethod
    size_xs: int = Field(ge=1)
    size_s: int = Field(ge=1)
    size_m: int = Field(ge=1)
    size_l: int = Field(ge=1)
    size_xl: int = Field(ge=1)


class RoleForm(BaseModel):
    person_id: int = Field(ge=1)
    role: RoleName
    value_stream_id: int | None = None
    delivery_group_id: int | None = None
    team_id: int | None = None

    @model_validator(mode="after")
    def matches_record(self):
        present = {
            "value_stream": self.value_stream_id,
            "delivery_group": self.delivery_group_id,
            "team": self.team_id,
        }
        expected = ROLE_RECORD[self.role]
        if present[expected] is None or any(
            value is not None for key, value in present.items() if key != expected
        ):
            raise ValueError("wrong record")
        return self


StageName = Literal["Discover", "Define", "Build", "Check", "Ship"]
DependencyStatus = Literal["open", "done", "blocked"]
DependentStatus = Literal["open", "done", "not_needed"]
ReviewResult = Literal["approved", "changes_requested"]
RiskState = Literal["open", "owned", "accepted", "mitigated", "closed"]


def _iso_date(value: str) -> str:
    return date.fromisoformat(value).isoformat()


class StageForm(BaseModel):
    stage: StageName
    person_id: int = Field(ge=1)


class PersonActionForm(BaseModel):
    person_id: int = Field(ge=1)


class PathFlagsForm(BaseModel):
    changes_production: int = Field(ge=0, le=1)
    architecture_applies: int = Field(ge=0, le=1)
    pii_applies: int = Field(ge=0, le=1)


class ProductionFlagForm(BaseModel):
    changes_production: int = Field(ge=0, le=1)


class CycleForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    delivery_group_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    starts_on: str
    ends_on: str

    @field_validator("starts_on", "ends_on")
    @classmethod
    def dates(cls, value: str) -> str:
        return _iso_date(value)

    @model_validator(mode="after")
    def date_order(self):
        if self.ends_on < self.starts_on:
            raise ValueError("order")
        return self


class OutcomeForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=1, max_length=240)
    planned_signal: str = Field(min_length=1, max_length=240)
    actual_signal: str = Field(default="", max_length=240)
    team_id: int | None = None


class OutcomeActualForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    actual_signal: str = Field(default="", max_length=240)


class MilestoneForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    happens_on: str

    @field_validator("happens_on")
    @classmethod
    def dates(cls, value: str) -> str:
        return _iso_date(value)


class DependencyForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=1, max_length=240)
    owner_person_id: int = Field(ge=1)
    needed_by: str
    opened_on: str
    status: DependencyStatus = "open"
    providing_team_id: int | None = None

    @field_validator("needed_by", "opened_on")
    @classmethod
    def dates(cls, value: str) -> str:
        return _iso_date(value)


class DependentWorkForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    feature_id: int = Field(ge=1)
    needed: str = Field(min_length=1, max_length=240)
    done_looks_like: str = Field(min_length=1, max_length=240)
    needed_by: str
    status: DependentStatus = "open"
    providing_team_id: int | None = None

    @field_validator("needed_by")
    @classmethod
    def dates(cls, value: str) -> str:
        return _iso_date(value)


class ReviewForm(BaseModel):
    feature_id: int = Field(ge=1)
    reviewer_person_id: int = Field(ge=1)
    reviewed_on: str
    result: ReviewResult

    @field_validator("reviewed_on")
    @classmethod
    def dates(cls, value: str) -> str:
        return _iso_date(value)


class RiskForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=1, max_length=240)
    state: RiskState = "open"


class ConfidenceForm(BaseModel):
    person_id: int = Field(ge=1)
    score: int = Field(ge=1, le=5)


class CapacityForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    team_id: int = Field(ge=1)
    note: str = Field(min_length=1, max_length=240)


class OutcomeLinkForm(BaseModel):
    outcome_id: int = Field(ge=1)
    feature_id: int | None = None
    story_id: int | None = None

    @model_validator(mode="after")
    def one_work_item(self):
        if (self.feature_id is None) == (self.story_id is None):
            raise ValueError("one")
        return self


class DecisionForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    statement: str = Field(min_length=1, max_length=240)
    person_id: int = Field(ge=1)


class IterationForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    team_id: int = Field(ge=1)
    cycle_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    starts_on: str
    ends_on: str

    @field_validator("starts_on", "ends_on")
    @classmethod
    def dates(cls, value: str) -> str:
        return _iso_date(value)

    @model_validator(mode="after")
    def date_order(self):
        if self.ends_on < self.starts_on:
            raise ValueError("order")
        return self


class BoardMoveForm(BaseModel):
    story_id: int = Field(ge=1)
    status_id: int = Field(ge=1)


class BoardStatusForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=40)
    color: str
    person_id: int = Field(ge=1)

    @field_validator("color")
    @classmethod
    def hex_color(cls, value: str) -> str:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError("color")
        return value.lower()


class BoardStatusUpdateForm(BoardStatusForm):
    position: int = Field(ge=1)


class BacklogAddForm(BaseModel):
    story_id: int = Field(ge=1)
    person_id: int = Field(ge=1)


class BacklogOrderForm(BaseModel):
    story_id: int = Field(ge=1)
    person_id: int = Field(ge=1)
    position: int = Field(ge=1)


class AcceptForm(BaseModel):
    story_id: int = Field(ge=1)
    person_id: int = Field(ge=1)
    accepted: int = Field(ge=0, le=1)


class WipForm(BaseModel):
    limit: int = Field(ge=1)


class WipExceptionForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    story_id: int = Field(ge=1)
    person_id: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=240)


class SyncNoteForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    note_on: str
    body: str = Field(min_length=1, max_length=500)
    person_id: int = Field(ge=1)

    @field_validator("note_on")
    @classmethod
    def dates(cls, value: str) -> str:
        return _iso_date(value)


class CrossTeamForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    impediment: str = Field(min_length=1, max_length=240)
    dependency: str = Field(min_length=1, max_length=240)
    asked_team_id: int = Field(ge=1)
    person_id: int = Field(ge=1)


class RetroForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    iteration_id: int = Field(ge=1)
    body: str = Field(min_length=1, max_length=500)
    person_id: int = Field(ge=1)


class PromoteForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    statement: str = Field(min_length=1, max_length=240)
    person_id: int = Field(ge=1)


class PolicyForm(BaseModel):
    to_stage: StageName
    effect: Literal["block", "warning"]
    from_stage: str = ""

    @field_validator("from_stage")
    @classmethod
    def blank_or_stage(cls, value: str) -> str:
        if value == "":
            return ""
        if value not in ("Discover", "Define", "Build", "Check", "Ship"):
            raise ValueError("stage")
        return value


class PolicyApprovalForm(BaseModel):
    policy_id: int = Field(ge=1)
    person_id: int = Field(ge=1)


class CriterionForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    measure_name: str = Field(min_length=1, max_length=120)
    threshold: str = Field(min_length=1, max_length=120)
    dataset_label: str = Field(min_length=1, max_length=120)
    latency_target: str = Field(min_length=1, max_length=120)


class AgentActionForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    action: str = Field(min_length=1, max_length=120)
    actor_name: str = Field(min_length=1, max_length=120)
    before_text: str = Field(min_length=1, max_length=240)
    after_text: str = Field(min_length=1, max_length=240)
