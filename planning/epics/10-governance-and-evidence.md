# Epic 10 — Governance and evidence

Status: done

## Outcome

The app can show who changed a work item, can require a person to approve a blocked transition, and can store acceptance criteria that are thresholds rather than yes-or-no checks.

## Why this epic is separate

Epic 05 already enforces the three boundaries on the main path: a person approves Define, someone else completes Check, and a person decides to Ship. This epic is the record around those boundaries. Public agent-delivery write-ups treat that record as part of the work: identity, policy, and disposition have to be readable later, including when the actor was an agent.

A person can record an agent action by hand, so the log is testable before any model is connected.

Threshold fields cover probabilistic work without turning the tool into a training platform: measure name, threshold, dataset label, and latency target, stored on the work item.

## In scope

- Policy records attached to a delivery-path transition, with a block or a warning.
- An evidence list: action, actor kind (person or agent), actor name, time, before, and after.
- A page that shows the evidence for one work item.
- Acceptance-criteria fields for a threshold, a dataset label, and a latency target.
- A test or form that creates an agent actor without calling a model.
- Records this epic stores are SQLAlchemy models. Request bodies are Pydantic models. Both sit on the models from epic 08.

## Out of scope

- Token validation and tenant sandboxes (epics 10 and 12).
- Calling a model to score accuracy.
- Live agent runners (epic 13).

## Depends on

- Epic 05
- Epic 08, for the SQLAlchemy models and Pydantic models

## Local proof

Put a blocking policy on the move into Ship. See the move refused until the dev user approves it. Record one action as an agent and see both actor kinds on the evidence page. Save a threshold and a latency target on that feature and read them back.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **10.1 Transition policy.** A delivery group stores a policy on a move into a stage, from one stage or from any stage, with a block or a warning. A block refuses the move until a person approves it for that work item. A warning lets the move through. The policy is a SQLAlchemy model. The request body is a Pydantic model.

  Done when: put a warning on the move into Check and see Check saved. Put a block on the move into Ship and see Ship refused. Approve it as Dev and see Ship.

- [x] **10.2 Evidence record.** A stage change stores an evidence row: action, actor kind, actor name, time, before, and after. The actor kind for that row is person. A warning on the move stores a row whose action is warning. The row is a SQLAlchemy model.

  Done when: the Check move from 10.1 is stored as a person, and the warning is stored on that feature too.

- [x] **10.3 Evidence page.** A page lists the evidence for one feature or one story.

  Done when: open the evidence page for the feature from 10.1 and see the person rows.

- [x] **10.4 Threshold criteria.** A feature or a story stores a measure name, a threshold, a dataset label, and a latency target. An empty field is refused. The request body is a Pydantic model.

  Done when: save accuracy, 0.9, held-out, and 200ms, reload, and see those four.

- [x] **10.5 Agent actor.** A form records an action with actor kind agent and an actor name. It does not call a model. The request body is a Pydantic model.

  Done when: record picker-agent on the feature and see both person and agent on the evidence page.

- [x] **10.6 Governance test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, and walks the local proof: a block on Ship until Dev approves it, a warning that does not refuse Check, an agent row beside the person rows, and a threshold with a latency target read back. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
