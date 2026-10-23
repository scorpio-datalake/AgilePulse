from datetime import date, datetime, timedelta, timezone

KINDS = ("feature", "platform", "prototype", "experiment")
WAIT_STAGES = {"Discover", "Define", "Check"}


def delay_cost(feature: dict) -> float | None:
    values = (
        feature.get("value_sooner"),
        feature.get("urgency"),
        feature.get("risk"),
        feature.get("economic_size"),
    )
    if any(value is None for value in values):
        return None
    return (values[0] + values[1] + values[2]) / values[3]


def format_number(value: float | None) -> str | None:
    if value is None:
        return None
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    if text in {"", "-0"}:
        return "0"
    return text


def with_delay_cost(features: list[dict]) -> list[dict]:
    scored = []
    for feature in features:
        row = dict(feature)
        row["delay_cost"] = format_number(delay_cost(feature))
        scored.append(row)
    scored.sort(
        key=lambda row: (
            row["delay_cost"] is None,
            -(delay_cost(row) or 0),
            row["name"],
            row["id"],
        )
    )
    return scored


def signal_ratio(planned: str, actual: str) -> str:
    try:
        planned_number = float(planned)
        actual_number = float(actual)
    except ValueError:
        return "not a number"
    if planned_number == 0:
        return "not a number"
    return format_number(actual_number / planned_number) or "not a number"


def velocity_of(stories: list[dict]) -> int:
    total = 0
    for story in stories:
        if story["stage"] == "Ship" and story.get("estimate_value") is not None:
            total += int(story["estimate_value"])
    return total


def flow_measures(items: list[dict], stamps: list[dict], starts_on: str, ends_on: str) -> dict:
    span_start, span_end = _span(starts_on, ends_on)
    grouped: dict[tuple[str, int], list[dict]] = {}
    for stamp in stamps:
        grouped.setdefault((stamp["target_kind"], stamp["target_id"]), []).append(stamp)
    leads: list[float] = []
    throughput = 0
    wip = 0
    active = 0.0
    wait = 0.0
    for item in items:
        changes = sorted(
            grouped.get((item["target_kind"], item["id"]), []),
            key=lambda change: (change["changed_at"], change["id"]),
        )
        if _shipped_in_span(changes, span_start, span_end):
            throughput += 1
            lead = _lead_days(changes)
            if lead is not None:
                leads.append(lead)
        if _in_progress(changes, span_end):
            wip += 1
        item_active, item_wait = _time_in_span(changes, span_start, span_end)
        active += item_active
        wait += item_wait
    mix = {kind: 0 for kind in KINDS}
    for item in items:
        if item["kind"] in mix:
            mix[item["kind"]] += 1
    lead_time = format_number(sum(leads) / len(leads)) if leads else None
    return {
        "throughput": throughput,
        "lead_time": lead_time or "none",
        "wip": wip,
        "active": format_number(active) or "0",
        "wait": format_number(wait) or "0",
        "mix": mix,
    }


def _span(starts_on: str, ends_on: str) -> tuple[datetime, datetime]:
    start = datetime.combine(date.fromisoformat(starts_on), datetime.min.time(), timezone.utc)
    end = datetime.combine(
        date.fromisoformat(ends_on) + timedelta(days=1),
        datetime.min.time(),
        timezone.utc,
    )
    return start, end


def _stamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _shipped_in_span(changes: list[dict], span_start: datetime, span_end: datetime) -> bool:
    return any(
        change["to_stage"] == "Ship" and span_start <= _stamp(change["changed_at"]) < span_end
        for change in changes
    )


def _lead_days(changes: list[dict]) -> float | None:
    builds = [_stamp(change["changed_at"]) for change in changes if change["to_stage"] == "Build"]
    ships = [_stamp(change["changed_at"]) for change in changes if change["to_stage"] == "Ship"]
    if not builds or not ships:
        return None
    return (min(ships) - min(builds)).total_seconds() / 86400


def _in_progress(changes: list[dict], span_end: datetime) -> bool:
    started = False
    done = False
    for change in changes:
        if _stamp(change["changed_at"]) >= span_end:
            continue
        if change["to_stage"] == "Build":
            started = True
        if change["to_stage"] == "Ship":
            done = True
    return started and not done


def _time_in_span(
    changes: list[dict], span_start: datetime, span_end: datetime
) -> tuple[float, float]:
    active = 0.0
    wait = 0.0
    for index, change in enumerate(changes):
        start = _stamp(change["changed_at"])
        end = _stamp(changes[index + 1]["changed_at"]) if index + 1 < len(changes) else span_end
        if change["to_stage"] == "Ship":
            continue
        seconds = _overlap_seconds(start, end, span_start, span_end)
        days = seconds / 86400
        if change["to_stage"] == "Build":
            active += days
        elif change["to_stage"] in WAIT_STAGES:
            wait += days
    return active, wait


def _overlap_seconds(
    start: datetime, end: datetime, span_start: datetime, span_end: datetime
) -> float:
    lower = max(start, span_start)
    upper = min(end, span_end)
    if upper <= lower:
        return 0.0
    return (upper - lower).total_seconds()
