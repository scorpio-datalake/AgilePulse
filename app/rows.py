from pydantic import BaseModel, ConfigDict, create_model

from app.models import Base


def row_model(sa_model: type[Base], name: str):
    fields: dict = {}
    for column in sa_model.__table__.columns:
        py_type = column.type.python_type
        if column.nullable:
            fields[column.name] = (py_type | None, None)
        else:
            fields[column.name] = (py_type, ...)
    return create_model(
        name,
        __config__=ConfigDict(from_attributes=True),
        **fields,
    )


def dump(instance, model: type[BaseModel]):
    if instance is None:
        return None
    return model.model_validate(instance, from_attributes=True).model_dump()


def dump_all(instances, model: type[BaseModel]) -> list[dict]:
    return [model.model_validate(item, from_attributes=True).model_dump() for item in instances]


def dump_maps(rows, model: type[BaseModel]) -> list[dict]:
    return [model.model_validate(dict(row)).model_dump() for row in rows]


class PublicUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    organization_id: int | None = None
    must_change_password: int


class NamedRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class StreamChoice(NamedRef):
    portfolio_name: str


class GroupChoice(NamedRef):
    stream_name: str


class TeamChoice(NamedRef):
    group_name: str


class PersonListRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    user_id: int | None = None
    name: str
    account_access: str
    role: str | None = None


class MemberRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    name: str
    role: str | None = None


class RoleListRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    person_id: int
    name: str


class SizingTeamRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sizing_method: str
    size_xs: int
    size_s: int
    size_m: int
    size_l: int
    size_xl: int
    group_name: str


class StageChangeRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_stage: str
    to_stage: str
    changed_at: str
    person_name: str


class BoardItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    stage: str


class StreamFeature(BoardItem):
    architecture_applies: int
    pii_applies: int


class CycleListRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    starts_on: str
    ends_on: str


class IterationListRow(CycleListRow):
    cycle_id: int


class OutcomeRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    planned_signal: str
    actual_signal: str
    team_id: int | None = None
    team_name: str | None = None


class OutcomeLinkRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feature_name: str | None = None
    story_name: str | None = None


class ReviewRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: str
    result: str
    reviewed_on: str
    feature_name: str
    reviewer_name: str


class VoteRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: int
    name: str


class MilestoneRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    happens_on: str


class DependencyRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    description: str
    needed_by: str
    status: str
    opened_on: str
    owner_name: str
    team_name: str | None = None


class DependentWorkRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    needed: str
    done_looks_like: str
    needed_by: str
    status: str
    feature_name: str
    team_name: str | None = None


class RiskRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    state: str


class CapacityRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note: str
    team_name: str


class DecisionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    statement: str
    acting_role: str
    name: str


class IterationBoardRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    stage: str
    kind: str
    estimate_label: str | None = None
    estimate_value: int | None = None
    position: int
    accepted: int
    board_status_id: int | None = None
    board_rank: int = 0


class BoardStatusRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    position: int


class ExceptionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reason: str
    name: str


class SyncNoteRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_on: str
    body: str
    team_name: str
    name: str


class CrossNoteRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    impediment: str
    dependency: str
    asking_name: str
    asked_name: str


class RetroNoteRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    iteration_name: str


class LearningRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    statement: str
    team_name: str


class FlowWorkRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_kind: str
    id: int
    name: str
    stage: str
    kind: str


class StageStampRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_kind: str
    target_id: int
    from_stage: str
    to_stage: str
    changed_at: str


class PolicyMoveRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_stage: str
    to_stage: str
    effect: str
    approved: int


class EvidenceRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str
    actor_kind: str
    actor_name: str
    happened_at: str
    before_text: str
    after_text: str
