# Epic 09 — Flow and priority

Status: done

## Outcome

A local user can sort features by delay cost, can read a small set of flow measures for a team or a delivery group, and can read team velocity from story estimates already stored.

## Why this epic is separate

Priority math does not belong in a second language runtime. The score is a division of numbers epic 04 already stores. This epic computes it in Python and keeps the charts off the boards that capture the raw events.

Delay-cost score = (value of doing it sooner + urgency + risk or opportunity addressed) / size.

Measures, using words teams already use for Kanban and outcome tracking:

- Throughput: items finished in the cycle.
- Lead time: elapsed time from commitment to done.
- Work in progress: items started and not done.
- Active versus wait: time in Build compared with time sitting in earlier or later stages, using history from epic 05.
- Work mix: counts of feature, platform, prototype, and experiment.
- Outcome reliability: actual signal divided by the planned signal on outcomes from epic 06.
- Velocity: the sum of the numeric estimate on stories completed in one iteration. T-shirt labels use the team's numbers. Points use the number entered on the story. The team page shows the last three iterations. Velocity is a record of what finished. It is not a target the tool enforces.

## In scope

- A computed delay-cost score and a backlog sorted by it.
- Pages or sections for the six measures over a selected cycle or iteration.
- Velocity for a team over a selected iteration, and the three-iteration history beside it.
- Entry of the actual signal on an outcome.
- Tests that build a small fixture and assert the numbers.
- Records this epic stores are SQLAlchemy models. Request bodies are Pydantic models. Both sit on the models from epic 08.

## Out of scope

- A Rust analytics crate (epic 12), unless a story here records a measured limit Python cannot meet.
- Predictive overload alerts (epic 13).
- Editing the economic inputs. Those fields are created in epic 04.

## Depends on

- Epic 04
- Epic 05
- Epic 06
- Epic 08, for the SQLAlchemy models and Pydantic models

## Local proof

Set priority inputs on three features and see them sort in score order. Complete two items with known dates and see lead time and work in progress match the fixture. Enter an actual signal and see outcome reliability as actual divided by planned. Complete one M story and one 5-point story in an iteration and see velocity equal the team's number for M plus 5.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **09.1 Delay-cost score.** A feature that has value of doing it sooner, urgency, risk or opportunity, and size shows the score: those first three added, divided by size. A feature missing any of the four has no score. The initiative lists scored features first, highest score first, and lists the rest after them in name order. This story does not add a way to edit the four numbers.

  Done when: save 8, 2, 0, and 2 on one feature and 1, 1, 0, and 4 on another, leave a third blank, and see them listed as 5, then 0.5, then the blank one.

- [x] **09.2 Throughput, lead time, and work in progress.** The delivery-group flow page takes a cycle. The team flow page takes an iteration. Throughput counts items whose history reaches Ship inside that span. Lead time is the average elapsed time from the first move into Build to the move into Ship, for those items. Work in progress counts items that entered Build before the span ended and had not reached Ship by then.

  Done when: ship two features inside a cycle on known dates, leave one in Build, and see throughput 2, lead time 2, and work in progress 1.

- [x] **09.3 Active versus wait.** On that same page, active is the time the history shows in Build during the span. Wait is the time it shows in Discover, Define, or Check during the span. Time before the first recorded change is not counted. Time in Ship is neither.

  Done when: the fixture from 09.2 shows active 7 and wait 4.

- [x] **09.4 Work mix.** The same page counts feature, platform, prototype, and experiment among the items in the selected cycle or iteration.

  Done when: the fixture from 09.2 shows 3 features and 0 for the other three kinds.

- [x] **09.5 Outcome reliability.** The group flow page reads each outcome on the selected cycle. Reliability is the numeric actual signal divided by the numeric planned signal. A signal that is not a number is shown as not a number. The actual signal is still saved on the cycle page.

  Done when: save an actual signal of 8 against a planned signal of 10 and see 0.8. Save a planned signal that is not a number and see not a number.

- [x] **09.6 Velocity.** The team page lists velocity for the three iterations with the latest end dates. Velocity is the sum of the stored estimate on stories in Ship on that iteration. A t-shirt estimate uses the number already stored for that label. A points estimate uses the number entered on the story. Fewer than three iterations lists the ones that exist.

  Done when: finish one M story and one 5-point story in the latest of three iterations and see 8, then 0, then 0.

- [x] **09.7 Flow and priority test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, and walks the local proof: three features sort by score, the cycle measures match the dated fixture, outcome reliability is actual divided by planned, and velocity is the team's number for M plus 5. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
