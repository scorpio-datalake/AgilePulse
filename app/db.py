from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, event, func, inspect, or_, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from sqlalchemy.pool import NullPool

from app.models import (
    Base,
    BoardStatus,
    CapacityNote,
    ConfidenceVote,
    CrossTeamNote,
    DeliveryGroup,
    Dependency,
    DependentWork,
    DoneCheck,
    Evidence,
    Feature,
    Goal,
    GroupDecision,
    Guardrail,
    Initiative,
    Iteration,
    IterationStory,
    Membership,
    Milestone,
    Organization,
    Outcome,
    OutcomeLink,
    Person,
    PlanningCycle,
    Policy,
    PolicyApproval,
    Portfolio,
    PromotedLearning,
    RetroNote,
    Review,
    Risk,
    RoleAssignment,
    SchemaMigration,
    StageChange,
    Story,
    SyncNote,
    Team,
    User,
    ValueStream,
    WipException,
    Workshop,
    WorkshopAllocation,
    WorkshopParticipant,
)
from app.passwords import hash_password
from app.rows import (
    BoardItem,
    BoardStatusRow,
    CapacityRow,
    CrossNoteRow,
    CycleListRow,
    DecisionRow,
    DependencyRow,
    DependentWorkRow,
    EvidenceRow,
    ExceptionRow,
    FlowWorkRow,
    GroupChoice,
    IterationBoardRow,
    IterationListRow,
    LearningRow,
    MemberRow,
    MilestoneRow,
    NamedRef,
    OutcomeLinkRow,
    OutcomeRow,
    PolicyMoveRow,
    PersonListRow,
    PublicUser,
    RetroNoteRow,
    ReviewRow,
    RiskRow,
    RoleListRow,
    SizingTeamRow,
    StageChangeRow,
    StageStampRow,
    StreamChoice,
    StreamFeature,
    SyncNoteRow,
    TeamChoice,
    VoteRow,
    WorkshopRow,
    dump,
    dump_all,
    dump_maps,
    row_model,
)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
ADMIN_DISPLAY_NAME = "Admin"
ORG_NAME = "Local"
SCHEMA_VERSIONS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

PolicyRow = row_model(Policy, "PolicyRow")
GuardrailRow = row_model(Guardrail, "GuardrailRow")

UserRow = row_model(User, "UserRow")
OrganizationRow = row_model(Organization, "OrganizationRow")
PersonRow = row_model(Person, "PersonRow")
PortfolioRow = row_model(Portfolio, "PortfolioRow")
ValueStreamRow = row_model(ValueStream, "ValueStreamRow")
DeliveryGroupRow = row_model(DeliveryGroup, "DeliveryGroupRow")
TeamRow = row_model(Team, "TeamRow")
MembershipRow = row_model(Membership, "MembershipRow")
RoleRow = row_model(RoleAssignment, "RoleRow")
GoalRow = row_model(Goal, "GoalRow")
InitiativeRow = row_model(Initiative, "InitiativeRow")
FeatureRow = row_model(Feature, "FeatureRow")
StoryRow = row_model(Story, "StoryRow")
CycleRow = row_model(PlanningCycle, "CycleRow")
IterationRow = row_model(Iteration, "IterationRow")
RetroStoreRow = row_model(RetroNote, "RetroStoreRow")
RiskStoreRow = row_model(Risk, "RiskStoreRow")

_engines: dict[str, Engine] = {}


def _engine(path: Path) -> Engine:
    key = str(path)
    engine = _engines.get(key)
    if engine is not None:
        return engine
    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    _engines[key] = engine
    return engine


def connect(path: Path) -> Session:
    path.parent.mkdir(parents=True, exist_ok=True)
    return Session(_engine(path), expire_on_commit=False)


def _ensure_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            present = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                column_type = column.type.compile(dialect=engine.dialect)
                null_sql = "" if column.nullable else " NOT NULL"
                default_sql = ""
                if column.server_default is not None:
                    default_sql = " DEFAULT " + str(column.server_default.arg)
                connection.exec_driver_sql(
                    f"ALTER TABLE {table.name} ADD COLUMN {column.name} {column_type}{null_sql}{default_sql}"
                )


def migrate(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = _engine(path)
    Base.metadata.create_all(engine)
    _ensure_columns(engine)
    session = connect(path)
    try:
        applied = set(session.scalars(select(SchemaMigration.version)))
        stamp = datetime.now(timezone.utc).isoformat()
        for version in SCHEMA_VERSIONS:
            if version not in applied:
                session.add(SchemaMigration(version=version, applied_at=stamp))
        _adopt_admin(session)
        _seed_admin(session)
        _seed_organization(session)
        session.commit()
    finally:
        session.close()


def _adopt_admin(session: Session) -> None:
    admin = session.scalar(select(User).where(User.username == ADMIN_USERNAME))
    if admin is not None:
        return
    previous = session.scalar(select(User).where(User.username == "dev"))
    if previous is None:
        return
    previous.username = ADMIN_USERNAME
    previous.password_hash = hash_password(ADMIN_PASSWORD)
    previous.display_name = ADMIN_DISPLAY_NAME
    previous.must_change_password = 1
    person = session.scalar(select(Person).where(Person.user_id == previous.id, Person.name == "Dev"))
    if person is not None:
        person.name = ADMIN_DISPLAY_NAME


def _seed_admin(session: Session) -> None:
    existing = session.scalar(select(User).where(User.username == ADMIN_USERNAME))
    if existing is not None:
        return
    session.add(
        User(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            display_name=ADMIN_DISPLAY_NAME,
            must_change_password=1,
        )
    )


def _seed_organization(session: Session) -> None:
    session.flush()
    existing = session.scalars(select(Organization).order_by(Organization.id)).first()
    if existing is None:
        existing = Organization(name=ORG_NAME)
        session.add(existing)
        session.flush()
    session.execute(
        update(User).where(User.organization_id.is_(None)).values(organization_id=existing.id)
    )
    user = session.scalar(select(User).where(User.username == ADMIN_USERNAME))
    if user is None:
        return
    person = session.scalar(select(Person).where(Person.user_id == user.id))
    if person is None:
        session.add(
            Person(
                organization_id=existing.id,
                user_id=user.id,
                name=user.display_name,
                account_access="admin",
            )
        )


def attach_login(session: Session, person_id: int, username: str, password: str) -> None:
    person = session.get(Person, int(person_id))
    user = User(
        username=username,
        password_hash=hash_password(password),
        display_name=username,
        organization_id=person.organization_id,
        must_change_password=0,
    )
    session.add(user)
    session.flush()
    person.user_id = user.id
    session.commit()


def _save(session: Session, row) -> int:
    session.add(row)
    session.flush()
    row_id = int(row.id)
    session.commit()
    return row_id


def _changed(session: Session, statement) -> bool:
    result = session.execute(statement)
    session.commit()
    return result.rowcount == 1


def _work(kind: str):
    return Feature if kind == "feature" else Story


def user_by_username(session: Session, username: str) -> dict | None:
    return dump(session.scalar(select(User).where(User.username == username)), UserRow)


def user_by_id(session: Session, user_id: int) -> dict | None:
    return dump(session.get(User, user_id), PublicUser)


def set_password(session: Session, user_id: int, password: str) -> None:
    session.execute(
        update(User)
        .where(User.id == user_id)
        .values(password_hash=hash_password(password), must_change_password=0)
    )
    session.commit()


def has_added_user(session: Session, organization_id: int) -> bool:
    count = session.scalar(
        select(func.count())
        .select_from(Person)
        .where(Person.organization_id == organization_id, Person.user_id.is_(None))
    )
    return int(count or 0) > 0


def organization_tree(session: Session, organization_id: int) -> list[dict]:
    portfolios = list_portfolios(session, organization_id)
    streams = dump_all(
        session.scalars(
            select(ValueStream)
            .where(ValueStream.organization_id == organization_id)
            .order_by(ValueStream.name, ValueStream.id)
        ).all(),
        ValueStreamRow,
    )
    groups = dump_all(
        session.scalars(
            select(DeliveryGroup)
            .where(DeliveryGroup.organization_id == organization_id)
            .order_by(DeliveryGroup.name, DeliveryGroup.id)
        ).all(),
        DeliveryGroupRow,
    )
    teams = dump_all(
        session.scalars(
            select(Team).where(Team.organization_id == organization_id).order_by(Team.name, Team.id)
        ).all(),
        TeamRow,
    )
    teams_by_group: dict[int, list[dict]] = {}
    for team in teams:
        teams_by_group.setdefault(team["delivery_group_id"], []).append(
            {"id": team["id"], "delivery_group_id": team["delivery_group_id"], "name": team["name"]}
        )
    groups_by_stream: dict[int, list[dict]] = {}
    for group in groups:
        group = {
            "id": group["id"],
            "value_stream_id": group["value_stream_id"],
            "name": group["name"],
            "teams": teams_by_group.get(group["id"], []),
        }
        groups_by_stream.setdefault(group["value_stream_id"], []).append(group)
    streams_by_portfolio: dict[int, list[dict]] = {}
    for stream in streams:
        stream = {
            "id": stream["id"],
            "portfolio_id": stream["portfolio_id"],
            "name": stream["name"],
            "groups": groups_by_stream.get(stream["id"], []),
        }
        streams_by_portfolio.setdefault(stream["portfolio_id"], []).append(stream)
    for portfolio in portfolios:
        portfolio["streams"] = streams_by_portfolio.get(portfolio["id"], [])
    return portfolios


def list_portfolios(session: Session, organization_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(Portfolio)
            .where(Portfolio.organization_id == organization_id)
            .order_by(Portfolio.name, Portfolio.id)
        ).all(),
        PortfolioRow,
    )


def get_portfolio(session: Session, organization_id: int, portfolio_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(Portfolio).where(
                Portfolio.id == portfolio_id, Portfolio.organization_id == organization_id
            )
        ),
        PortfolioRow,
    )


def create_portfolio(session: Session, organization_id: int, name: str) -> int:
    return _save(session, Portfolio(organization_id=organization_id, name=name))


def rename_portfolio(session: Session, organization_id: int, portfolio_id: int, name: str) -> bool:
    return _changed(
        session,
        update(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.organization_id == organization_id)
        .values(name=name),
    )


def list_value_streams(session: Session, portfolio_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(ValueStream)
            .where(ValueStream.portfolio_id == portfolio_id)
            .order_by(ValueStream.name, ValueStream.id)
        ).all(),
        ValueStreamRow,
    )


def get_value_stream(session: Session, organization_id: int, value_stream_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(ValueStream).where(
                ValueStream.id == value_stream_id, ValueStream.organization_id == organization_id
            )
        ),
        ValueStreamRow,
    )


def create_value_stream(session: Session, organization_id: int, portfolio_id: int, name: str) -> int | None:
    if get_portfolio(session, organization_id, portfolio_id) is None:
        return None
    return _save(session, ValueStream(organization_id=organization_id, portfolio_id=portfolio_id, name=name))


def rename_value_stream(session: Session, organization_id: int, value_stream_id: int, name: str) -> bool:
    return _changed(
        session,
        update(ValueStream)
        .where(ValueStream.id == value_stream_id, ValueStream.organization_id == organization_id)
        .values(name=name),
    )


def list_delivery_groups(session: Session, value_stream_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(DeliveryGroup)
            .where(DeliveryGroup.value_stream_id == value_stream_id)
            .order_by(DeliveryGroup.name, DeliveryGroup.id)
        ).all(),
        DeliveryGroupRow,
    )


def get_delivery_group(session: Session, organization_id: int, delivery_group_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(DeliveryGroup).where(
                DeliveryGroup.id == delivery_group_id,
                DeliveryGroup.organization_id == organization_id,
            )
        ),
        DeliveryGroupRow,
    )


def create_delivery_group(
    session: Session, organization_id: int, value_stream_id: int, name: str
) -> int | None:
    if get_value_stream(session, organization_id, value_stream_id) is None:
        return None
    return _save(
        session,
        DeliveryGroup(organization_id=organization_id, value_stream_id=value_stream_id, name=name),
    )


def rename_delivery_group(
    session: Session, organization_id: int, delivery_group_id: int, name: str
) -> bool:
    return _changed(
        session,
        update(DeliveryGroup)
        .where(
            DeliveryGroup.id == delivery_group_id,
            DeliveryGroup.organization_id == organization_id,
        )
        .values(name=name),
    )


def list_teams(session: Session, delivery_group_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(Team)
            .where(Team.delivery_group_id == delivery_group_id)
            .order_by(Team.name, Team.id)
        ).all(),
        TeamRow,
    )


def get_team(session: Session, organization_id: int, team_id: int) -> dict | None:
    return dump(
        session.scalar(select(Team).where(Team.id == team_id, Team.organization_id == organization_id)),
        TeamRow,
    )


DEFAULT_BOARD_STATUSES = (
    ("To do", "#6b6e76"),
    ("In progress", "#0c66e4"),
    ("Ready for testing", "#8270db"),
    ("Ready for review", "#e56910"),
    ("Deployed", "#1d7afc"),
    ("Done", "#22a06b"),
)


def _seed_board_statuses(session: Session, organization_id: int, team_id: int) -> None:
    existing = session.scalar(
        select(func.count()).select_from(BoardStatus).where(BoardStatus.team_id == team_id)
    )
    if existing:
        return
    for position, (name, color) in enumerate(DEFAULT_BOARD_STATUSES, start=1):
        session.add(
            BoardStatus(
                organization_id=organization_id,
                team_id=team_id,
                name=name,
                color=color,
                position=position,
            )
        )
    session.commit()


def create_team(session: Session, organization_id: int, delivery_group_id: int, name: str) -> int | None:
    if get_delivery_group(session, organization_id, delivery_group_id) is None:
        return None
    team_id = _save(session, Team(organization_id=organization_id, delivery_group_id=delivery_group_id, name=name))
    _seed_board_statuses(session, organization_id, team_id)
    return team_id


def rename_team(session: Session, organization_id: int, team_id: int, name: str) -> bool:
    return _changed(
        session,
        update(Team)
        .where(Team.id == team_id, Team.organization_id == organization_id)
        .values(name=name),
    )


def list_people(session: Session, organization_id: int) -> list[dict]:
    rows = session.execute(
        select(
            Person.id,
            Person.organization_id,
            Person.user_id,
            Person.name,
            Person.account_access,
            RoleAssignment.role,
        )
        .outerjoin(RoleAssignment, RoleAssignment.person_id == Person.id)
        .where(Person.organization_id == organization_id)
        .order_by(Person.name, Person.id)
    ).mappings()
    return dump_maps(rows, PersonListRow)


def get_person(session: Session, organization_id: int, person_id: int) -> dict | None:
    return dump(
        session.scalar(select(Person).where(Person.id == person_id, Person.organization_id == organization_id)),
        PersonRow,
    )


def create_person(session: Session, organization_id: int, name: str) -> int:
    return _save(session, Person(organization_id=organization_id, name=name, account_access="member"))


def person_by_user_id(session: Session, user_id: int) -> dict | None:
    return dump(session.scalar(select(Person).where(Person.user_id == user_id)), PersonRow)


def membership_scope(session: Session, person_id: int) -> dict:
    memberships = session.scalars(select(Membership).where(Membership.person_id == person_id)).all()
    team_ids = {row.team_id for row in memberships if row.team_id is not None}
    direct_group_ids = {
        row.delivery_group_id for row in memberships if row.delivery_group_id is not None
    }
    group_ids = set(direct_group_ids)
    if team_ids:
        group_ids.update(
            session.scalars(select(Team.delivery_group_id).where(Team.id.in_(team_ids))).all()
        )
    if direct_group_ids:
        team_ids.update(
            session.scalars(select(Team.id).where(Team.delivery_group_id.in_(direct_group_ids))).all()
        )
    stream_ids: set[int] = set()
    if group_ids:
        stream_ids.update(
            session.scalars(
                select(DeliveryGroup.value_stream_id).where(DeliveryGroup.id.in_(group_ids))
            ).all()
        )
    portfolio_ids: set[int] = set()
    if stream_ids:
        portfolio_ids.update(
            session.scalars(select(ValueStream.portfolio_id).where(ValueStream.id.in_(stream_ids))).all()
        )
    return {
        "portfolio": portfolio_ids,
        "stream": stream_ids,
        "group": group_ids,
        "team": team_ids,
    }


def role_for_person(session: Session, person_id: int) -> dict | None:
    return dump(session.scalar(select(RoleAssignment).where(RoleAssignment.person_id == person_id)), RoleRow)


def list_streams_for_roles(session: Session, organization_id: int) -> list[dict]:
    rows = session.execute(
        select(ValueStream.id, ValueStream.name, Portfolio.name.label("portfolio_name"))
        .join(Portfolio, Portfolio.id == ValueStream.portfolio_id)
        .where(ValueStream.organization_id == organization_id)
        .order_by(Portfolio.name, ValueStream.name, ValueStream.id)
    ).mappings()
    return dump_maps(rows, StreamChoice)


def list_teams_for_assignment(session: Session, organization_id: int) -> list[dict]:
    rows = session.execute(
        select(Team.id, Team.name, DeliveryGroup.name.label("group_name"))
        .join(DeliveryGroup, DeliveryGroup.id == Team.delivery_group_id)
        .where(Team.organization_id == organization_id)
        .order_by(DeliveryGroup.name, Team.name, Team.id)
    ).mappings()
    return dump_maps(rows, TeamChoice)


def list_groups_for_roles(session: Session, organization_id: int) -> list[dict]:
    rows = session.execute(
        select(DeliveryGroup.id, DeliveryGroup.name, ValueStream.name.label("stream_name"))
        .join(ValueStream, ValueStream.id == DeliveryGroup.value_stream_id)
        .where(DeliveryGroup.organization_id == organization_id)
        .order_by(ValueStream.name, DeliveryGroup.name, DeliveryGroup.id)
    ).mappings()
    return dump_maps(rows, GroupChoice)


def create_person_with_role(
    session: Session,
    organization_id: int,
    name: str,
    role: str,
    *,
    value_stream_id: int | None = None,
    delivery_group_id: int | None = None,
    team_id: int | None = None,
) -> tuple[int | None, str | None]:
    person = Person(organization_id=organization_id, name=name, account_access="member")
    session.add(person)
    session.flush()
    message = assign_role(
        session,
        organization_id,
        person.id,
        role,
        value_stream_id=value_stream_id,
        delivery_group_id=delivery_group_id,
        team_id=None,
        commit=False,
    )
    if message is not None:
        session.rollback()
        return None, message
    if team_id is not None:
        if get_team(session, organization_id, team_id) is None:
            session.rollback()
            return None, "That team was not found."
        session.add(
            Membership(
                organization_id=organization_id,
                person_id=person.id,
                delivery_group_id=None,
                team_id=team_id,
            )
        )
    session.commit()
    return int(person.id), None


def set_account_access(
    session: Session, organization_id: int, person_id: int, account_access: str
) -> str | None:
    if account_access not in {"member", "viewer"}:
        return "That access was refused."
    person = get_person(session, organization_id, person_id)
    if person is None:
        return "That person was not found."
    if person["account_access"] == "admin":
        return "That access was refused."
    session.execute(
        update(Person)
        .where(Person.id == person_id, Person.organization_id == organization_id)
        .values(account_access=account_access)
    )
    session.commit()
    return None


def rename_person(session: Session, organization_id: int, person_id: int, name: str) -> bool:
    person = get_person(session, organization_id, person_id)
    if person is None:
        return False
    session.execute(
        update(Person)
        .where(Person.id == person_id, Person.organization_id == organization_id)
        .values(name=name)
    )
    if person["user_id"] is not None:
        session.execute(update(User).where(User.id == person["user_id"]).values(display_name=name))
    session.commit()
    return True


def list_members(
    session: Session,
    organization_id: int,
    *,
    delivery_group_id: int | None = None,
    team_id: int | None = None,
) -> list[dict]:
    statement = (
        select(Membership.id, Person.id.label("person_id"), Person.name, RoleAssignment.role)
        .join(Person, Person.id == Membership.person_id)
        .outerjoin(RoleAssignment, RoleAssignment.person_id == Person.id)
        .where(Membership.organization_id == organization_id)
        .order_by(Person.name, Membership.id)
    )
    if delivery_group_id is not None:
        statement = statement.where(Membership.delivery_group_id == delivery_group_id)
    else:
        statement = statement.where(Membership.team_id == team_id)
    return dump_maps(session.execute(statement).mappings(), MemberRow)


def add_membership(
    session: Session,
    organization_id: int,
    person_id: int,
    *,
    delivery_group_id: int | None = None,
    team_id: int | None = None,
) -> str | None:
    if get_person(session, organization_id, person_id) is None:
        return "That person was not found."
    if delivery_group_id is not None:
        if get_delivery_group(session, organization_id, delivery_group_id) is None:
            return "That delivery group was not found."
    elif team_id is not None:
        if get_team(session, organization_id, team_id) is None:
            return "That team was not found."
    else:
        return "That membership was refused."
    try:
        session.add(
            Membership(
                organization_id=organization_id,
                person_id=person_id,
                delivery_group_id=delivery_group_id,
                team_id=team_id,
            )
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        return "That person is already a member."
    return None


def get_membership(session: Session, organization_id: int, membership_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(Membership).where(
                Membership.id == membership_id, Membership.organization_id == organization_id
            )
        ),
        MembershipRow,
    )


def remove_membership(session: Session, organization_id: int, membership_id: int) -> dict | None:
    membership = get_membership(session, organization_id, membership_id)
    if membership is None:
        return None
    row = session.get(Membership, membership_id)
    session.delete(row)
    session.commit()
    return membership


def list_role_assignments(
    session: Session,
    organization_id: int,
    *,
    value_stream_id: int | None = None,
    delivery_group_id: int | None = None,
    team_id: int | None = None,
) -> list[dict]:
    statement = (
        select(
            RoleAssignment.id,
            RoleAssignment.role,
            Person.id.label("person_id"),
            Person.name,
        )
        .join(Person, Person.id == RoleAssignment.person_id)
        .where(RoleAssignment.organization_id == organization_id)
        .order_by(RoleAssignment.role, Person.name)
    )
    if value_stream_id is not None:
        statement = statement.where(RoleAssignment.value_stream_id == value_stream_id)
    elif delivery_group_id is not None:
        statement = statement.where(RoleAssignment.delivery_group_id == delivery_group_id)
    else:
        statement = statement.where(RoleAssignment.team_id == team_id)
    return dump_maps(session.execute(statement).mappings(), RoleListRow)


def assign_role(
    session: Session,
    organization_id: int,
    person_id: int,
    role: str,
    *,
    value_stream_id: int | None = None,
    delivery_group_id: int | None = None,
    team_id: int | None = None,
    commit: bool = True,
) -> str | None:
    if get_person(session, organization_id, person_id) is None:
        return "That role was refused."
    expected = _role_record(role)
    if expected is None:
        return "That role does not belong on this record."
    if expected == "value_stream" and (
        value_stream_id is None or delivery_group_id is not None or team_id is not None
    ):
        return "That role does not belong on this record."
    if expected == "delivery_group" and (
        delivery_group_id is None or value_stream_id is not None or team_id is not None
    ):
        return "That role does not belong on this record."
    if expected == "team" and (value_stream_id is not None or delivery_group_id is not None):
        return "That role does not belong on this record."
    if expected == "value_stream" and get_value_stream(session, organization_id, value_stream_id) is None:
        return "That role does not belong on this record."
    if expected == "delivery_group" and get_delivery_group(session, organization_id, delivery_group_id) is None:
        return "That role does not belong on this record."
    if expected == "team" and team_id is not None and get_team(session, organization_id, team_id) is None:
        return "That role does not belong on this record."
    existing = session.scalar(select(RoleAssignment.id).where(RoleAssignment.person_id == person_id))
    if existing is not None:
        return "That person already has a role."
    try:
        session.add(
            RoleAssignment(
                organization_id=organization_id,
                person_id=person_id,
                role=role,
                value_stream_id=value_stream_id,
                delivery_group_id=delivery_group_id,
                team_id=team_id,
            )
        )
        if commit:
            session.commit()
        else:
            session.flush()
    except IntegrityError:
        session.rollback()
        return "That person already has a role."
    return None


def _role_record(role: str) -> str | None:
    if role == "stream_owner":
        return "value_stream"
    if role in {"group_facilitator", "product_manager", "business_stakeholder"}:
        return "delivery_group"
    if role in {"product_owner", "scrum_master", "technical_lead", "team_member"}:
        return "team"
    return None


def list_goals(session: Session, value_stream_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(Goal).where(Goal.value_stream_id == value_stream_id).order_by(Goal.name, Goal.id)
        ).all(),
        GoalRow,
    )


def get_goal(session: Session, organization_id: int, goal_id: int) -> dict | None:
    return dump(
        session.scalar(select(Goal).where(Goal.id == goal_id, Goal.organization_id == organization_id)),
        GoalRow,
    )


def create_goal(session: Session, organization_id: int, value_stream_id: int, name: str) -> int | None:
    if get_value_stream(session, organization_id, value_stream_id) is None:
        return None
    return _save(session, Goal(organization_id=organization_id, value_stream_id=value_stream_id, name=name))


def rename_goal(session: Session, organization_id: int, goal_id: int, name: str) -> bool:
    return _changed(
        session,
        update(Goal).where(Goal.id == goal_id, Goal.organization_id == organization_id).values(name=name),
    )


def list_initiatives(session: Session, goal_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(Initiative).where(Initiative.goal_id == goal_id).order_by(Initiative.name, Initiative.id)
        ).all(),
        InitiativeRow,
    )


def get_initiative(session: Session, organization_id: int, initiative_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(Initiative).where(
                Initiative.id == initiative_id, Initiative.organization_id == organization_id
            )
        ),
        InitiativeRow,
    )


def create_initiative(session: Session, organization_id: int, goal_id: int, name: str) -> int | None:
    if get_goal(session, organization_id, goal_id) is None:
        return None
    return _save(session, Initiative(organization_id=organization_id, goal_id=goal_id, name=name))


def rename_initiative(session: Session, organization_id: int, initiative_id: int, name: str) -> bool:
    return _changed(
        session,
        update(Initiative)
        .where(Initiative.id == initiative_id, Initiative.organization_id == organization_id)
        .values(name=name),
    )


def set_initiative_state(session: Session, organization_id: int, initiative_id: int, state: str) -> bool:
    return _changed(
        session,
        update(Initiative)
        .where(Initiative.id == initiative_id, Initiative.organization_id == organization_id)
        .values(state=state),
    )


def list_features(session: Session, initiative_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(Feature).where(Feature.initiative_id == initiative_id).order_by(Feature.name, Feature.id)
        ).all(),
        FeatureRow,
    )


def get_feature(session: Session, organization_id: int, feature_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(Feature).where(Feature.id == feature_id, Feature.organization_id == organization_id)
        ),
        FeatureRow,
    )


def create_feature(
    session: Session, organization_id: int, initiative_id: int, name: str, kind: str
) -> int | None:
    if get_initiative(session, organization_id, initiative_id) is None:
        return None
    return _save(
        session,
        Feature(
            organization_id=organization_id,
            initiative_id=initiative_id,
            name=name,
            kind=kind,
            changes_production=0 if kind in {"prototype", "experiment"} else 1,
        ),
    )


def update_feature(session: Session, organization_id: int, feature_id: int, name: str, kind: str) -> bool:
    return _changed(
        session,
        update(Feature)
        .where(Feature.id == feature_id, Feature.organization_id == organization_id)
        .values(name=name, kind=kind),
    )


def set_feature_priority(
    session: Session,
    organization_id: int,
    feature_id: int,
    value_sooner: int,
    urgency: int,
    risk: int,
    economic_size: int,
) -> bool:
    return _changed(
        session,
        update(Feature)
        .where(Feature.id == feature_id, Feature.organization_id == organization_id)
        .values(
            value_sooner=value_sooner,
            urgency=urgency,
            risk=risk,
            economic_size=economic_size,
        ),
    )


def list_stories(session: Session, feature_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(Story).where(Story.feature_id == feature_id).order_by(Story.name, Story.id)
        ).all(),
        StoryRow,
    )


def get_story(session: Session, organization_id: int, story_id: int) -> dict | None:
    return dump(
        session.scalar(select(Story).where(Story.id == story_id, Story.organization_id == organization_id)),
        StoryRow,
    )


def create_story(session: Session, organization_id: int, feature_id: int, name: str, kind: str) -> int | None:
    if get_feature(session, organization_id, feature_id) is None:
        return None
    return _save(session, Story(organization_id=organization_id, feature_id=feature_id, name=name, kind=kind))


def update_story(session: Session, organization_id: int, story_id: int, name: str, kind: str) -> bool:
    return _changed(
        session,
        update(Story)
        .where(Story.id == story_id, Story.organization_id == organization_id)
        .values(name=name, kind=kind),
    )


def set_story_feature(session: Session, organization_id: int, story_id: int, feature_id: int) -> bool:
    if get_story(session, organization_id, story_id) is None:
        return False
    if get_feature(session, organization_id, feature_id) is None:
        return False
    return _changed(
        session,
        update(Story)
        .where(Story.id == story_id, Story.organization_id == organization_id)
        .values(feature_id=feature_id),
    )


def set_story_estimate(
    session: Session,
    organization_id: int,
    story_id: int,
    team_id: int,
    label: str | None,
    value: int,
) -> bool:
    return _changed(
        session,
        update(Story)
        .where(Story.id == story_id, Story.organization_id == organization_id)
        .values(team_id=team_id, estimate_label=label, estimate_value=value),
    )


def list_teams_for_sizing(session: Session, organization_id: int) -> list[dict]:
    rows = session.execute(
        select(
            Team.id,
            Team.name,
            Team.sizing_method,
            Team.size_xs,
            Team.size_s,
            Team.size_m,
            Team.size_l,
            Team.size_xl,
            DeliveryGroup.name.label("group_name"),
        )
        .join(DeliveryGroup, DeliveryGroup.id == Team.delivery_group_id)
        .where(Team.organization_id == organization_id)
        .order_by(DeliveryGroup.name, Team.name, Team.id)
    ).mappings()
    return dump_maps(rows, SizingTeamRow)


def save_team_sizing(
    session: Session,
    organization_id: int,
    team_id: int,
    method: str,
    size_xs: int,
    size_s: int,
    size_m: int,
    size_l: int,
    size_xl: int,
) -> bool:
    return _changed(
        session,
        update(Team)
        .where(Team.id == team_id, Team.organization_id == organization_id)
        .values(
            sizing_method=method,
            size_xs=size_xs,
            size_s=size_s,
            size_m=size_m,
            size_l=size_l,
            size_xl=size_xl,
        ),
    )


def list_stage_changes(session: Session, target_kind: str, target_id: int) -> list[dict]:
    rows = session.execute(
        select(
            StageChange.from_stage,
            StageChange.to_stage,
            StageChange.changed_at,
            Person.name.label("person_name"),
        )
        .join(Person, Person.id == StageChange.person_id)
        .where(StageChange.target_kind == target_kind, StageChange.target_id == target_id)
        .order_by(StageChange.id)
    ).mappings()
    return dump_maps(rows, StageChangeRow)


def latest_builder_id(session: Session, target_kind: str, target_id: int) -> int | None:
    person_id = session.scalar(
        select(StageChange.person_id)
        .where(
            StageChange.target_kind == target_kind,
            StageChange.target_id == target_id,
            StageChange.to_stage == "Build",
        )
        .order_by(StageChange.id.desc())
        .limit(1)
    )
    return None if person_id is None else int(person_id)


def record_stage(
    session: Session,
    organization_id: int,
    target_kind: str,
    target_id: int,
    from_stage: str,
    to_stage: str,
    person_id: int,
    changed_at: str,
) -> None:
    model = _work(target_kind)
    session.execute(
        update(model)
        .where(model.id == target_id, model.organization_id == organization_id)
        .values(stage=to_stage)
    )
    session.add(
        StageChange(
            organization_id=organization_id,
            target_kind=target_kind,
            target_id=target_id,
            from_stage=from_stage,
            to_stage=to_stage,
            person_id=person_id,
            changed_at=changed_at,
        )
    )
    person = session.get(Person, person_id)
    _write_evidence(
        session,
        organization_id=organization_id,
        target_kind=target_kind,
        target_id=target_id,
        action="stage",
        actor_kind="person",
        actor_name="" if person is None else person.name,
        happened_at=changed_at,
        before_text=from_stage,
        after_text=to_stage,
    )
    session.commit()


def approve_definition(
    session: Session,
    organization_id: int,
    target_kind: str,
    target_id: int,
    person_id: int,
    definition: str,
) -> bool:
    model = _work(target_kind)
    return _changed(
        session,
        update(model)
        .where(model.id == target_id, model.organization_id == organization_id)
        .values(approved_by_person_id=person_id, approved_definition=definition),
    )


def clear_approval(session: Session, organization_id: int, target_kind: str, target_id: int) -> None:
    model = _work(target_kind)
    session.execute(
        update(model)
        .where(model.id == target_id, model.organization_id == organization_id)
        .values(approved_by_person_id=None, approved_definition="")
    )
    session.commit()


def done_check_map(session: Session, target_kind: str, target_id: int) -> dict[str, int]:
    rows = session.scalars(
        select(DoneCheck).where(DoneCheck.target_kind == target_kind, DoneCheck.target_id == target_id)
    ).all()
    return {row.item: int(row.done) for row in rows}


def save_done_checks(
    session: Session,
    organization_id: int,
    target_kind: str,
    target_id: int,
    done_items: set[str],
) -> None:
    for item in ("integrated", "acceptance", "dependency", "rollback", "architecture", "pii"):
        statement = sqlite_insert(DoneCheck).values(
            organization_id=organization_id,
            target_kind=target_kind,
            target_id=target_id,
            item=item,
            done=1 if item in done_items else 0,
        )
        session.execute(
            statement.on_conflict_do_update(
                index_elements=["target_kind", "target_id", "item"],
                set_={"done": statement.excluded.done},
            )
        )
    session.commit()


def set_feature_path_flags(
    session: Session,
    organization_id: int,
    feature_id: int,
    changes_production: int,
    architecture_applies: int,
    pii_applies: int,
) -> bool:
    return _changed(
        session,
        update(Feature)
        .where(Feature.id == feature_id, Feature.organization_id == organization_id)
        .values(
            changes_production=changes_production,
            architecture_applies=architecture_applies,
            pii_applies=pii_applies,
        ),
    )


def set_story_production(
    session: Session, organization_id: int, story_id: int, changes_production: int
) -> bool:
    return _changed(
        session,
        update(Story)
        .where(Story.id == story_id, Story.organization_id == organization_id)
        .values(changes_production=changes_production),
    )


def person_role(session: Session, organization_id: int, person_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(RoleAssignment).where(
                RoleAssignment.organization_id == organization_id,
                RoleAssignment.person_id == person_id,
            )
        ),
        RoleRow,
    )


def person_on_team(session: Session, person_id: int, team_id: int) -> bool:
    found = session.scalar(
        select(Membership.id).where(Membership.person_id == person_id, Membership.team_id == team_id)
    )
    return found is not None


def stories_for_team(session: Session, team_id: int) -> list[dict]:
    rows = session.execute(
        select(Story.id, Story.name, Story.stage)
        .where(Story.team_id == team_id)
        .order_by(Story.name, Story.id)
    ).mappings()
    return dump_maps(rows, BoardItem)


def features_for_stream(session: Session, value_stream_id: int) -> list[dict]:
    rows = session.execute(
        select(
            Feature.id,
            Feature.name,
            Feature.stage,
            Feature.architecture_applies,
            Feature.pii_applies,
        )
        .join(Initiative, Initiative.id == Feature.initiative_id)
        .join(Goal, Goal.id == Initiative.goal_id)
        .where(Goal.value_stream_id == value_stream_id)
        .order_by(Feature.name, Feature.id)
    ).mappings()
    return dump_maps(rows, StreamFeature)


def stories_for_group(session: Session, delivery_group_id: int) -> list[dict]:
    rows = session.execute(
        select(Story.id, Story.name, Story.stage)
        .join(Team, Team.id == Story.team_id)
        .where(Team.delivery_group_id == delivery_group_id)
        .order_by(Story.name, Story.id)
    ).mappings()
    return dump_maps(rows, BoardItem)


def set_wip_limit(session: Session, organization_id: int, team_id: int, limit: int) -> bool:
    return _changed(
        session,
        update(Team)
        .where(Team.id == team_id, Team.organization_id == organization_id)
        .values(wip_limit=limit),
    )


def iteration_id_for_story(session: Session, story_id: int) -> int | None:
    iteration_id = session.scalar(
        select(IterationStory.iteration_id).where(IterationStory.story_id == story_id)
    )
    return None if iteration_id is None else int(iteration_id)


def build_count(session: Session, iteration_id: int) -> int:
    total = session.scalar(
        select(func.count())
        .select_from(IterationStory)
        .join(Story, Story.id == IterationStory.story_id)
        .where(IterationStory.iteration_id == iteration_id, Story.stage == "Build")
    )
    return int(total or 0)


def take_wip_exception(session: Session, iteration_id: int, story_id: int) -> int | None:
    row = session.scalar(
        select(WipException)
        .where(WipException.iteration_id == iteration_id, WipException.story_id == story_id)
        .order_by(WipException.id)
        .limit(1)
    )
    if row is None:
        return None
    row_id = int(row.id)
    session.delete(row)
    return row_id


def create_cycle(
    session: Session,
    organization_id: int,
    delivery_group_id: int,
    name: str,
    starts_on: str,
    ends_on: str,
) -> int | None:
    if get_delivery_group(session, organization_id, delivery_group_id) is None:
        return None
    return _save(
        session,
        PlanningCycle(
            organization_id=organization_id,
            delivery_group_id=delivery_group_id,
            name=name,
            starts_on=starts_on,
            ends_on=ends_on,
        ),
    )


def list_cycles(session: Session, delivery_group_id: int) -> list[dict]:
    rows = session.execute(
        select(PlanningCycle.id, PlanningCycle.name, PlanningCycle.starts_on, PlanningCycle.ends_on)
        .where(PlanningCycle.delivery_group_id == delivery_group_id)
        .order_by(PlanningCycle.starts_on, PlanningCycle.id)
    ).mappings()
    return dump_maps(rows, CycleListRow)


def get_cycle(session: Session, organization_id: int, cycle_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(PlanningCycle).where(
                PlanningCycle.id == cycle_id, PlanningCycle.organization_id == organization_id
            )
        ),
        CycleRow,
    )


def create_iteration(
    session: Session,
    organization_id: int,
    team_id: int,
    cycle_id: int,
    name: str,
    starts_on: str,
    ends_on: str,
) -> int | None:
    return _save(
        session,
        Iteration(
            organization_id=organization_id,
            team_id=team_id,
            cycle_id=cycle_id,
            name=name,
            starts_on=starts_on,
            ends_on=ends_on,
        ),
    )


def list_iterations(session: Session, team_id: int) -> list[dict]:
    rows = session.execute(
        select(Iteration.id, Iteration.name, Iteration.starts_on, Iteration.ends_on, Iteration.cycle_id)
        .where(Iteration.team_id == team_id)
        .order_by(Iteration.starts_on, Iteration.id)
    ).mappings()
    return dump_maps(rows, IterationListRow)


def get_iteration(session: Session, organization_id: int, iteration_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(Iteration).where(Iteration.id == iteration_id, Iteration.organization_id == organization_id)
        ),
        IterationRow,
    )


def facilitator_person_id(session: Session, organization_id: int, delivery_group_id: int) -> int | None:
    person_id = session.scalar(
        select(RoleAssignment.person_id).where(
            RoleAssignment.organization_id == organization_id,
            RoleAssignment.delivery_group_id == delivery_group_id,
            RoleAssignment.role == "group_facilitator",
        )
    )
    return None if person_id is None else int(person_id)


def list_cycle_outcomes(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(
            Outcome.id,
            Outcome.description,
            Outcome.planned_signal,
            Outcome.actual_signal,
            Outcome.team_id,
            Team.name.label("team_name"),
        )
        .outerjoin(Team, Team.id == Outcome.team_id)
        .where(Outcome.cycle_id == cycle_id)
        .order_by(Outcome.id)
    ).mappings()
    return dump_maps(rows, OutcomeRow)


def list_outcome_links(session: Session, outcome_id: int) -> list[dict]:
    rows = session.execute(
        select(
            OutcomeLink.id,
            Feature.name.label("feature_name"),
            Story.name.label("story_name"),
        )
        .outerjoin(Feature, Feature.id == OutcomeLink.feature_id)
        .outerjoin(Story, Story.id == OutcomeLink.story_id)
        .where(OutcomeLink.outcome_id == outcome_id)
        .order_by(OutcomeLink.id)
    ).mappings()
    return dump_maps(rows, OutcomeLinkRow)


def list_cycle_reviews(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(
            Review.kind,
            Review.result,
            Review.reviewed_on,
            Feature.name.label("feature_name"),
            Person.name.label("reviewer_name"),
        )
        .join(Feature, Feature.id == Review.feature_id)
        .join(Person, Person.id == Review.reviewer_person_id)
        .where(Review.cycle_id == cycle_id)
        .order_by(Review.id)
    ).mappings()
    return dump_maps(rows, ReviewRow)


def list_cycle_votes(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(ConfidenceVote.score, Person.name)
        .join(Person, Person.id == ConfidenceVote.person_id)
        .where(ConfidenceVote.cycle_id == cycle_id)
        .order_by(Person.name)
    ).mappings()
    return dump_maps(rows, VoteRow)


def list_milestones(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(Milestone.id, Milestone.name, Milestone.happens_on)
        .where(Milestone.cycle_id == cycle_id)
        .order_by(Milestone.happens_on, Milestone.id)
    ).mappings()
    return dump_maps(rows, MilestoneRow)


def list_dependencies(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(
            Dependency.description,
            Dependency.needed_by,
            Dependency.status,
            Dependency.opened_on,
            Person.name.label("owner_name"),
            Team.name.label("team_name"),
        )
        .join(Person, Person.id == Dependency.owner_person_id)
        .outerjoin(Team, Team.id == Dependency.providing_team_id)
        .where(Dependency.cycle_id == cycle_id)
        .order_by(Dependency.id)
    ).mappings()
    return dump_maps(rows, DependencyRow)


def list_dependent_work(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(
            DependentWork.needed,
            DependentWork.done_looks_like,
            DependentWork.needed_by,
            DependentWork.status,
            Feature.name.label("feature_name"),
            Team.name.label("team_name"),
        )
        .join(Feature, Feature.id == DependentWork.feature_id)
        .outerjoin(Team, Team.id == DependentWork.providing_team_id)
        .where(DependentWork.cycle_id == cycle_id)
        .order_by(DependentWork.id)
    ).mappings()
    return dump_maps(rows, DependentWorkRow)


def list_risks(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(Risk.id, Risk.description, Risk.state).where(Risk.cycle_id == cycle_id).order_by(Risk.id)
    ).mappings()
    return dump_maps(rows, RiskRow)


def list_capacities(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(CapacityNote.note, Team.name.label("team_name"))
        .join(Team, Team.id == CapacityNote.team_id)
        .where(CapacityNote.cycle_id == cycle_id)
        .order_by(Team.name)
    ).mappings()
    return dump_maps(rows, CapacityRow)


def list_decisions(session: Session, cycle_id: int) -> list[dict]:
    rows = session.execute(
        select(GroupDecision.statement, GroupDecision.acting_role, Person.name)
        .join(Person, Person.id == GroupDecision.person_id)
        .where(GroupDecision.cycle_id == cycle_id)
        .order_by(GroupDecision.id)
    ).mappings()
    return dump_maps(rows, DecisionRow)


def add_outcome(
    session: Session,
    organization_id: int,
    cycle_id: int,
    team_id: int | None,
    description: str,
    planned_signal: str,
) -> None:
    _save(
        session,
        Outcome(
            organization_id=organization_id,
            cycle_id=cycle_id,
            team_id=team_id,
            description=description,
            planned_signal=planned_signal,
        ),
    )


def outcome_cycle_id(session: Session, organization_id: int, outcome_id: int) -> int | None:
    cycle_id = session.scalar(
        select(Outcome.cycle_id).where(Outcome.id == outcome_id, Outcome.organization_id == organization_id)
    )
    return None if cycle_id is None else int(cycle_id)


def set_outcome_actual(session: Session, outcome_id: int, actual_signal: str) -> None:
    session.execute(update(Outcome).where(Outcome.id == outcome_id).values(actual_signal=actual_signal))
    session.commit()


def add_milestone(session: Session, organization_id: int, cycle_id: int, name: str, happens_on: str) -> None:
    _save(
        session,
        Milestone(organization_id=organization_id, cycle_id=cycle_id, name=name, happens_on=happens_on),
    )


def add_dependency(session: Session, organization_id: int, cycle_id: int, **values) -> None:
    _save(session, Dependency(organization_id=organization_id, cycle_id=cycle_id, **values))


def add_dependent_work(session: Session, organization_id: int, cycle_id: int, **values) -> None:
    _save(session, DependentWork(organization_id=organization_id, cycle_id=cycle_id, **values))


def save_review(session: Session, organization_id: int, cycle_id: int, **values) -> None:
    statement = sqlite_insert(Review).values(organization_id=organization_id, cycle_id=cycle_id, **values)
    session.execute(
        statement.on_conflict_do_update(
            index_elements=["cycle_id", "feature_id", "kind"],
            set_={
                "reviewer_person_id": statement.excluded.reviewer_person_id,
                "reviewed_on": statement.excluded.reviewed_on,
                "result": statement.excluded.result,
            },
        )
    )
    session.commit()


def add_risk(session: Session, organization_id: int, cycle_id: int, description: str, state: str) -> None:
    _save(session, Risk(organization_id=organization_id, cycle_id=cycle_id, description=description, state=state))


def get_risk(session: Session, organization_id: int, risk_id: int) -> dict | None:
    return dump(
        session.scalar(select(Risk).where(Risk.id == risk_id, Risk.organization_id == organization_id)),
        RiskStoreRow,
    )


def set_risk_state(session: Session, risk_id: int, state: str) -> None:
    session.execute(update(Risk).where(Risk.id == risk_id).values(state=state))
    session.commit()


def save_confidence(session: Session, organization_id: int, cycle_id: int, person_id: int, score: int) -> None:
    statement = sqlite_insert(ConfidenceVote).values(
        organization_id=organization_id, cycle_id=cycle_id, person_id=person_id, score=score
    )
    session.execute(
        statement.on_conflict_do_update(
            index_elements=["cycle_id", "person_id"],
            set_={"score": statement.excluded.score},
        )
    )
    session.commit()


def save_capacity(session: Session, organization_id: int, cycle_id: int, team_id: int, note: str) -> None:
    statement = sqlite_insert(CapacityNote).values(
        organization_id=organization_id, cycle_id=cycle_id, team_id=team_id, note=note
    )
    session.execute(
        statement.on_conflict_do_update(
            index_elements=["cycle_id", "team_id"],
            set_={"note": statement.excluded.note},
        )
    )
    session.commit()


def outcome_in_cycle(session: Session, outcome_id: int, cycle_id: int) -> bool:
    found = session.scalar(
        select(Outcome.id).where(Outcome.id == outcome_id, Outcome.cycle_id == cycle_id)
    )
    return found is not None


def add_outcome_link(
    session: Session,
    organization_id: int,
    outcome_id: int,
    feature_id: int | None,
    story_id: int | None,
) -> None:
    _save(
        session,
        OutcomeLink(
            organization_id=organization_id,
            outcome_id=outcome_id,
            feature_id=feature_id,
            story_id=story_id,
        ),
    )


def add_group_decision(
    session: Session, organization_id: int, cycle_id: int, statement: str, person_id: int
) -> None:
    _save(
        session,
        GroupDecision(
            organization_id=organization_id,
            cycle_id=cycle_id,
            statement=statement,
            person_id=person_id,
            acting_role="group_facilitator",
        ),
    )


def list_iteration_board(session: Session, iteration_id: int) -> list[dict]:
    rows = session.execute(
        select(
            Story.id,
            Story.name,
            Story.stage,
            Story.kind,
            Story.estimate_label,
            Story.estimate_value,
            IterationStory.position,
            IterationStory.accepted,
            IterationStory.board_status_id,
            IterationStory.board_rank,
        )
        .join(IterationStory, IterationStory.story_id == Story.id)
        .where(IterationStory.iteration_id == iteration_id)
        .order_by(IterationStory.board_rank, IterationStory.position, Story.id)
    ).mappings()
    return dump_maps(rows, IterationBoardRow)


def place_open_cards(session: Session, iteration_id: int, status_id: int) -> None:
    session.execute(
        update(IterationStory)
        .where(IterationStory.iteration_id == iteration_id, IterationStory.board_status_id.is_(None))
        .values(board_status_id=status_id)
    )
    session.commit()


def list_board_statuses(session: Session, organization_id: int, team_id: int) -> list[dict]:
    _seed_board_statuses(session, organization_id, team_id)
    rows = session.scalars(
        select(BoardStatus)
        .where(BoardStatus.team_id == team_id, BoardStatus.organization_id == organization_id)
        .order_by(BoardStatus.position, BoardStatus.id)
    ).all()
    return dump_all(rows, BoardStatusRow)


def add_board_status(
    session: Session, organization_id: int, team_id: int, name: str, color: str
) -> str | None:
    if get_team(session, organization_id, team_id) is None:
        return "missing"
    taken = session.scalar(
        select(BoardStatus.id).where(BoardStatus.team_id == team_id, BoardStatus.name == name)
    )
    if taken is not None:
        return "duplicate"
    position = session.scalar(
        select(func.coalesce(func.max(BoardStatus.position), 0) + 1).where(BoardStatus.team_id == team_id)
    )
    _save(
        session,
        BoardStatus(
            organization_id=organization_id,
            team_id=team_id,
            name=name,
            color=color,
            position=int(position or 1),
        ),
    )
    return None


def update_board_status(
    session: Session,
    organization_id: int,
    team_id: int,
    status_id: int,
    name: str,
    color: str,
    position: int,
) -> str | None:
    status = session.scalar(
        select(BoardStatus).where(
            BoardStatus.id == status_id,
            BoardStatus.team_id == team_id,
            BoardStatus.organization_id == organization_id,
        )
    )
    if status is None:
        return "missing"
    taken = session.scalar(
        select(BoardStatus.id).where(
            BoardStatus.team_id == team_id,
            BoardStatus.name == name,
            BoardStatus.id != status_id,
        )
    )
    if taken is not None:
        return "duplicate"
    rows = list(
        session.scalars(
            select(BoardStatus)
            .where(BoardStatus.team_id == team_id)
            .order_by(BoardStatus.position, BoardStatus.id)
        ).all()
    )
    rows = [row for row in rows if row.id != status_id]
    index = min(max(position, 1), len(rows) + 1) - 1
    rows.insert(index, status)
    status.name = name
    status.color = color
    for index, row in enumerate(rows, start=1):
        row.position = index
    session.commit()
    return None


def delete_board_status(session: Session, organization_id: int, team_id: int, status_id: int) -> str | None:
    status = session.scalar(
        select(BoardStatus).where(
            BoardStatus.id == status_id,
            BoardStatus.team_id == team_id,
            BoardStatus.organization_id == organization_id,
        )
    )
    if status is None:
        return "missing"
    count = session.scalar(
        select(func.count()).select_from(BoardStatus).where(BoardStatus.team_id == team_id)
    )
    if count is not None and count <= 1:
        return "last"
    used = session.scalar(
        select(func.count()).select_from(IterationStory).where(IterationStory.board_status_id == status_id)
    )
    if used:
        return "in_use"
    session.delete(status)
    session.flush()
    rows = session.scalars(
        select(BoardStatus).where(BoardStatus.team_id == team_id).order_by(BoardStatus.position, BoardStatus.id)
    ).all()
    for index, row in enumerate(rows, start=1):
        row.position = index
    session.commit()
    return None


def move_board_card(
    session: Session,
    iteration_id: int,
    story_id: int,
    status_id: int,
    before_story_id: int | None,
) -> bool:
    iteration = session.get(Iteration, iteration_id)
    status = session.get(BoardStatus, status_id)
    if iteration is None or status is None or status.team_id != iteration.team_id:
        return False
    card = session.scalar(
        select(IterationStory).where(
            IterationStory.iteration_id == iteration_id,
            IterationStory.story_id == story_id,
        )
    )
    if card is None:
        return False
    if before_story_id == story_id:
        return True
    first = session.scalar(
        select(BoardStatus)
        .where(BoardStatus.team_id == iteration.team_id)
        .order_by(BoardStatus.position, BoardStatus.id)
    )
    in_column = [IterationStory.board_status_id == status_id]
    if first is not None and status.id == first.id:
        in_column.append(IterationStory.board_status_id.is_(None))
    target = list(
        session.scalars(
            select(IterationStory)
            .where(
                IterationStory.iteration_id == iteration_id,
                IterationStory.story_id != story_id,
                or_(*in_column),
            )
            .order_by(IterationStory.board_rank, IterationStory.position, IterationStory.id)
        ).all()
    )
    insert_at = len(target)
    if before_story_id is not None:
        ids = [row.story_id for row in target]
        if before_story_id not in ids:
            return False
        insert_at = ids.index(before_story_id)
    target.insert(insert_at, card)
    for index, row in enumerate(target, start=1):
        row.board_status_id = status_id
        row.board_rank = index
    session.commit()
    return True


def list_stories_not_on_iteration(session: Session, team_id: int) -> list[dict]:
    placed = select(IterationStory.story_id)
    rows = session.execute(
        select(Story.id, Story.name)
        .where(Story.team_id == team_id, Story.id.not_in(placed))
        .order_by(Story.name, Story.id)
    ).mappings()
    return dump_maps(rows, NamedRef)


def list_iteration_exceptions(session: Session, iteration_id: int) -> list[dict]:
    rows = session.execute(
        select(WipException.reason, Story.name)
        .join(Story, Story.id == WipException.story_id)
        .where(WipException.iteration_id == iteration_id)
        .order_by(WipException.id)
    ).mappings()
    return dump_maps(rows, ExceptionRow)


def add_iteration_story(
    session: Session, organization_id: int, iteration_id: int, story_id: int
) -> bool:
    position = session.scalar(
        select(func.coalesce(func.max(IterationStory.position), 0) + 1).where(
            IterationStory.iteration_id == iteration_id
        )
    )
    try:
        _save(
            session,
            IterationStory(
                organization_id=organization_id,
                iteration_id=iteration_id,
                story_id=story_id,
                position=int(position or 1),
                accepted=0,
            ),
        )
    except IntegrityError:
        session.rollback()
        return False
    return True


def set_iteration_position(session: Session, iteration_id: int, story_id: int, position: int) -> None:
    session.execute(
        update(IterationStory)
        .where(IterationStory.iteration_id == iteration_id, IterationStory.story_id == story_id)
        .values(position=position)
    )
    session.commit()


def set_iteration_accepted(session: Session, iteration_id: int, story_id: int, accepted: int) -> None:
    session.execute(
        update(IterationStory)
        .where(IterationStory.iteration_id == iteration_id, IterationStory.story_id == story_id)
        .values(accepted=accepted)
    )
    session.commit()


def add_wip_exception_row(
    session: Session, organization_id: int, iteration_id: int, story_id: int, person_id: int, reason: str
) -> None:
    _save(
        session,
        WipException(
            organization_id=organization_id,
            iteration_id=iteration_id,
            story_id=story_id,
            person_id=person_id,
            reason=reason,
        ),
    )


def add_sync_note(
    session: Session, organization_id: int, team_id: int, note_on: str, body: str, person_id: int
) -> None:
    _save(
        session,
        SyncNote(
            organization_id=organization_id,
            team_id=team_id,
            note_on=note_on,
            body=body,
            person_id=person_id,
            acting_role="scrum_master",
        ),
    )


def add_cross_note(
    session: Session,
    organization_id: int,
    team_id: int,
    impediment: str,
    dependency: str,
    asked_team_id: int,
    person_id: int,
) -> None:
    _save(
        session,
        CrossTeamNote(
            organization_id=organization_id,
            team_id=team_id,
            impediment=impediment,
            dependency=dependency,
            asked_team_id=asked_team_id,
            person_id=person_id,
            acting_role="scrum_master",
        ),
    )


def add_retro_note(
    session: Session, organization_id: int, team_id: int, iteration_id: int, body: str, person_id: int
) -> None:
    _save(
        session,
        RetroNote(
            organization_id=organization_id,
            team_id=team_id,
            iteration_id=iteration_id,
            body=body,
            person_id=person_id,
            acting_role="scrum_master",
        ),
    )


def get_retro_note(session: Session, organization_id: int, note_id: int) -> dict | None:
    return dump(
        session.scalar(
            select(RetroNote).where(RetroNote.id == note_id, RetroNote.organization_id == organization_id)
        ),
        RetroStoreRow,
    )


def add_promoted_learning(
    session: Session, organization_id: int, team_id: int, retro_note_id: int, statement: str
) -> None:
    _save(
        session,
        PromotedLearning(
            organization_id=organization_id,
            team_id=team_id,
            retro_note_id=retro_note_id,
            statement=statement,
        ),
    )


def list_group_sync_notes(session: Session, delivery_group_id: int) -> list[dict]:
    rows = session.execute(
        select(SyncNote.note_on, SyncNote.body, Team.name.label("team_name"), Person.name)
        .join(Team, Team.id == SyncNote.team_id)
        .join(Person, Person.id == SyncNote.person_id)
        .where(Team.delivery_group_id == delivery_group_id)
        .order_by(SyncNote.id)
    ).mappings()
    return dump_maps(rows, SyncNoteRow)


def list_group_cross_notes(session: Session, delivery_group_id: int) -> list[dict]:
    asking = aliased(Team)
    asked = aliased(Team)
    rows = session.execute(
        select(
            CrossTeamNote.impediment,
            CrossTeamNote.dependency,
            asking.name.label("asking_name"),
            asked.name.label("asked_name"),
        )
        .join(asking, asking.id == CrossTeamNote.team_id)
        .join(asked, asked.id == CrossTeamNote.asked_team_id)
        .where(
            (asking.delivery_group_id == delivery_group_id) | (asked.delivery_group_id == delivery_group_id)
        )
        .order_by(CrossTeamNote.id)
    ).mappings()
    return dump_maps(rows, CrossNoteRow)


def list_team_retro_notes(session: Session, team_id: int) -> list[dict]:
    rows = session.execute(
        select(RetroNote.id, RetroNote.body, Iteration.name.label("iteration_name"))
        .join(Iteration, Iteration.id == RetroNote.iteration_id)
        .where(RetroNote.team_id == team_id)
        .order_by(RetroNote.id)
    ).mappings()
    return dump_maps(rows, RetroNoteRow)


def list_group_learnings(session: Session, delivery_group_id: int) -> list[dict]:
    rows = session.execute(
        select(PromotedLearning.statement, Team.name.label("team_name"))
        .join(Team, Team.id == PromotedLearning.team_id)
        .where(Team.delivery_group_id == delivery_group_id)
        .order_by(PromotedLearning.id)
    ).mappings()
    return dump_maps(rows, LearningRow)


def list_group_flow_items(session: Session, delivery_group_id: int) -> list[dict]:
    group = session.get(DeliveryGroup, delivery_group_id)
    if group is None:
        return []
    features = session.execute(
        select(
            Feature.id,
            Feature.name,
            Feature.stage,
            Feature.kind,
        )
        .join(Initiative, Initiative.id == Feature.initiative_id)
        .join(Goal, Goal.id == Initiative.goal_id)
        .where(Goal.value_stream_id == group.value_stream_id)
        .order_by(Feature.id)
    ).mappings()
    stories = session.execute(
        select(Story.id, Story.name, Story.stage, Story.kind)
        .join(Team, Team.id == Story.team_id)
        .where(Team.delivery_group_id == delivery_group_id)
        .order_by(Story.id)
    ).mappings()
    items = [
        {"target_kind": "feature", **dict(row)}
        for row in features
    ]
    items.extend({"target_kind": "story", **dict(row)} for row in stories)
    return dump_maps(items, FlowWorkRow)


def list_stage_stamps(session: Session, target_kind: str, target_ids: list[int]) -> list[dict]:
    if not target_ids:
        return []
    rows = session.execute(
        select(
            StageChange.id,
            StageChange.target_kind,
            StageChange.target_id,
            StageChange.from_stage,
            StageChange.to_stage,
            StageChange.changed_at,
        )
        .where(StageChange.target_kind == target_kind, StageChange.target_id.in_(target_ids))
        .order_by(StageChange.id)
    ).mappings()
    return dump_maps(rows, StageStampRow)


def list_policies(session: Session, delivery_group_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(Policy).where(Policy.delivery_group_id == delivery_group_id).order_by(Policy.id)
        ).all(),
        PolicyRow,
    )


def add_policy(
    session: Session,
    organization_id: int,
    delivery_group_id: int,
    from_stage: str,
    to_stage: str,
    effect: str,
) -> int | None:
    if get_delivery_group(session, organization_id, delivery_group_id) is None:
        return None
    return _save(
        session,
        Policy(
            organization_id=organization_id,
            delivery_group_id=delivery_group_id,
            from_stage=from_stage,
            to_stage=to_stage,
            effect=effect,
        ),
    )


def policies_for_move(
    session: Session,
    organization_id: int,
    target_kind: str,
    target_id: int,
    from_stage: str,
    to_stage: str,
) -> list[dict]:
    matched = []
    for group_id in _groups_for_work(session, target_kind, target_id):
        for policy in list_policies(session, group_id):
            if policy["organization_id"] != organization_id:
                continue
            if policy["to_stage"] != to_stage:
                continue
            if policy["from_stage"] and policy["from_stage"] != from_stage:
                continue
            matched.append(
                {
                    "id": policy["id"],
                    "from_stage": policy["from_stage"],
                    "to_stage": policy["to_stage"],
                    "effect": policy["effect"],
                    "approved": 1 if _policy_is_approved(session, policy["id"], target_kind, target_id) else 0,
                }
            )
    return dump_maps(matched, PolicyMoveRow)


def open_blocks(
    session: Session,
    organization_id: int,
    target_kind: str,
    target_id: int,
    from_stage: str,
) -> list[dict]:
    found = []
    seen: set[int] = set()
    for stage in ("Discover", "Define", "Build", "Check", "Ship"):
        for policy in policies_for_move(
            session, organization_id, target_kind, target_id, from_stage, stage
        ):
            if policy["effect"] != "block" or policy["approved"] or policy["id"] in seen:
                continue
            seen.add(policy["id"])
            found.append(policy)
    return found


def approve_policy(
    session: Session,
    organization_id: int,
    policy_id: int,
    target_kind: str,
    target_id: int,
    person_id: int,
    approved_at: str,
) -> bool:
    policy = session.get(Policy, policy_id)
    person = session.get(Person, person_id)
    item = session.get(_work(target_kind), target_id)
    if (
        policy is None
        or policy.organization_id != organization_id
        or policy.effect != "block"
        or person is None
        or person.organization_id != organization_id
        or item is None
        or item.organization_id != organization_id
    ):
        return False
    if not _policy_is_approved(session, policy_id, target_kind, target_id):
        session.add(
            PolicyApproval(
                organization_id=organization_id,
                policy_id=policy_id,
                target_kind=target_kind,
                target_id=target_id,
                person_id=person_id,
                approved_at=approved_at,
            )
        )
    _write_evidence(
        session,
        organization_id=organization_id,
        target_kind=target_kind,
        target_id=target_id,
        action="approve",
        actor_kind="person",
        actor_name=person.name,
        happened_at=approved_at,
        before_text=policy.to_stage,
        after_text="approved",
    )
    session.commit()
    return True


def list_evidence(session: Session, target_kind: str, target_id: int) -> list[dict]:
    rows = session.execute(
        select(
            Evidence.action,
            Evidence.actor_kind,
            Evidence.actor_name,
            Evidence.happened_at,
            Evidence.before_text,
            Evidence.after_text,
        )
        .where(Evidence.target_kind == target_kind, Evidence.target_id == target_id)
        .order_by(Evidence.id)
    ).mappings()
    return dump_maps(rows, EvidenceRow)


def add_evidence(
    session: Session,
    organization_id: int,
    target_kind: str,
    target_id: int,
    action: str,
    actor_kind: str,
    actor_name: str,
    happened_at: str,
    before_text: str,
    after_text: str,
) -> None:
    item = session.get(_work(target_kind), target_id)
    if item is None or item.organization_id != organization_id:
        return
    _write_evidence(
        session,
        organization_id=organization_id,
        target_kind=target_kind,
        target_id=target_id,
        action=action,
        actor_kind=actor_kind,
        actor_name=actor_name,
        happened_at=happened_at,
        before_text=before_text,
        after_text=after_text,
    )
    session.commit()


def set_criteria(
    session: Session,
    organization_id: int,
    target_kind: str,
    target_id: int,
    measure_name: str,
    threshold: str,
    dataset_label: str,
    latency_target: str,
) -> bool:
    model = _work(target_kind)
    return _changed(
        session,
        update(model)
        .where(model.id == target_id, model.organization_id == organization_id)
        .values(
            measure_name=measure_name,
            threshold=threshold,
            dataset_label=dataset_label,
            latency_target=latency_target,
        ),
    )


def get_guardrail(session: Session, value_stream_id: int) -> dict | None:
    return dump(
        session.scalar(select(Guardrail).where(Guardrail.value_stream_id == value_stream_id)),
        GuardrailRow,
    )


def save_guardrail(
    session: Session,
    organization_id: int,
    value_stream_id: int,
    kind: str,
    amount: int,
) -> bool:
    if get_value_stream(session, organization_id, value_stream_id) is None:
        return False
    existing = session.scalar(select(Guardrail).where(Guardrail.value_stream_id == value_stream_id))
    if existing is None:
        session.add(
            Guardrail(
                organization_id=organization_id,
                value_stream_id=value_stream_id,
                kind=kind,
                amount=amount,
            )
        )
    else:
        existing.kind = kind
        existing.amount = amount
    session.commit()
    return True


def initiatives_on_stream(session: Session, value_stream_id: int) -> list[dict]:
    return dump_all(
        session.scalars(
            select(Initiative)
            .join(Goal, Initiative.goal_id == Goal.id)
            .where(Goal.value_stream_id == value_stream_id)
            .order_by(Initiative.name, Initiative.id)
        ).all(),
        InitiativeRow,
    )


def open_initiative_count(session: Session, value_stream_id: int) -> int:
    count = session.scalar(
        select(func.count())
        .select_from(Initiative)
        .join(Goal, Initiative.goal_id == Goal.id)
        .where(Goal.value_stream_id == value_stream_id, Initiative.state != "Done")
    )
    return int(count or 0)


def list_workshops(session: Session, value_stream_id: int) -> list[dict]:
    workshops = session.scalars(
        select(Workshop).where(Workshop.value_stream_id == value_stream_id).order_by(Workshop.id)
    ).all()
    return [_workshop_view(session, workshop) for workshop in workshops]


def latest_workshop(session: Session, value_stream_id: int) -> dict | None:
    workshop = session.scalar(
        select(Workshop)
        .where(Workshop.value_stream_id == value_stream_id)
        .order_by(Workshop.id.desc())
    )
    if workshop is None:
        return None
    return _workshop_view(session, workshop)


def save_workshop(
    session: Session,
    organization_id: int,
    value_stream_id: int,
    person_ids: list[int],
    allocations: list[dict],
    recommendation: str,
) -> str | None:
    if get_value_stream(session, organization_id, value_stream_id) is None:
        return "stream"
    seen_people: list[int] = []
    for person_id in person_ids:
        if person_id in seen_people:
            continue
        person = session.get(Person, person_id)
        if person is None or person.organization_id != organization_id:
            return "person"
        seen_people.append(person_id)
    seen_initiatives: set[int] = set()
    checked: list[tuple[int, int]] = []
    for item in allocations:
        initiative_id = int(item["initiative_id"])
        if initiative_id in seen_initiatives:
            return "initiative"
        initiative = session.get(Initiative, initiative_id)
        goal = None if initiative is None else session.get(Goal, initiative.goal_id)
        if (
            initiative is None
            or initiative.organization_id != organization_id
            or goal is None
            or goal.value_stream_id != value_stream_id
        ):
            return "initiative"
        seen_initiatives.add(initiative_id)
        checked.append((initiative_id, int(item["amount"])))
    workshop = Workshop(
        organization_id=organization_id,
        value_stream_id=value_stream_id,
        recommendation=recommendation,
    )
    session.add(workshop)
    session.flush()
    for person_id in seen_people:
        session.add(
            WorkshopParticipant(
                organization_id=organization_id,
                workshop_id=workshop.id,
                person_id=person_id,
            )
        )
    for initiative_id, amount in checked:
        session.add(
            WorkshopAllocation(
                organization_id=organization_id,
                workshop_id=workshop.id,
                initiative_id=initiative_id,
                amount=amount,
            )
        )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return "initiative"
    return None


def _workshop_view(session: Session, workshop: Workshop) -> dict:
    participants = session.execute(
        select(Person.id, Person.name)
        .join(WorkshopParticipant, WorkshopParticipant.person_id == Person.id)
        .where(WorkshopParticipant.workshop_id == workshop.id)
        .order_by(Person.name, Person.id)
    ).mappings()
    allocations = session.execute(
        select(
            Initiative.id.label("initiative_id"),
            Initiative.name,
            WorkshopAllocation.amount,
        )
        .join(WorkshopAllocation, WorkshopAllocation.initiative_id == Initiative.id)
        .where(WorkshopAllocation.workshop_id == workshop.id)
        .order_by(Initiative.name, Initiative.id)
    ).mappings()
    return WorkshopRow.model_validate(
        {
            "id": workshop.id,
            "value_stream_id": workshop.value_stream_id,
            "recommendation": workshop.recommendation,
            "participants": list(participants),
            "allocations": list(allocations),
        }
    ).model_dump()


def _groups_for_work(session: Session, target_kind: str, target_id: int) -> list[int]:
    if target_kind == "story":
        story = session.get(Story, target_id)
        if story is None or story.team_id is None:
            return []
        team = session.get(Team, story.team_id)
        return [] if team is None else [int(team.delivery_group_id)]
    feature = session.get(Feature, target_id)
    if feature is None:
        return []
    initiative = session.get(Initiative, feature.initiative_id)
    if initiative is None:
        return []
    goal = session.get(Goal, initiative.goal_id)
    if goal is None:
        return []
    return [
        int(group_id)
        for group_id in session.scalars(
            select(DeliveryGroup.id).where(DeliveryGroup.value_stream_id == goal.value_stream_id)
        ).all()
    ]


def _policy_is_approved(session: Session, policy_id: int, target_kind: str, target_id: int) -> bool:
    found = session.scalar(
        select(PolicyApproval.id).where(
            PolicyApproval.policy_id == policy_id,
            PolicyApproval.target_kind == target_kind,
            PolicyApproval.target_id == target_id,
        )
    )
    return found is not None


def _write_evidence(session: Session, **values) -> None:
    session.add(Evidence(**values))
