# Epic 16 — Optional coordination and dual roles

Status: stories not written yet

## Outcome

A shop with one or two small teams can run the same delivery process without hiring a separate person for every seat. One person can hold several roles. Each task is still done as exactly one of those roles.

## Why this epic is separate

Epic 02 creates the structure and the role list. This epic is how a small shop uses that list without inventing a shorter process.

Roles stay distinct when they share a person:

- The group facilitator manages the delivery group. A product manager can hold that role too. Group tasks are still facilitator tasks. The shop can instead opt out and leave the group as a placeholder with the facilitator seat empty.
- The product owner owns the team backlog and acceptance of a story. A product manager, or a scrum master, can hold that role too. Those tasks are still product-owner tasks.
- The scrum master runs the team sync, impediments, and the retrospective. A product owner can hold that role too. Those tasks are still scrum-master tasks.

Holding both product owner and scrum master does not merge them. Before a task is saved, the app asks the person to set their acting role to the role that task requires. The action stores that acting role. A backlog change made while acting as scrum master is refused. A retro note made while acting as product owner is refused.

The delivery group is the coordination container: shared cycle, shared outcomes, dependencies between teams. Opting out means the facilitator steps are off. It does not delete the container. A placeholder keeps one method:

- The value stream still owns the customer outcome.
- The placeholder still owns the cycle, the dependencies, and the evidence review.
- Teams still run the same iteration, backlog, sync, and retro.
- With the facilitator seat empty, no one is asked to act as facilitator. Product-owner steps and scrum-master steps still happen, each under its own acting role.
- When the shop names a facilitator, they add that role. If the person is already a product manager, a developer, a product owner, or a scrum master, they keep those roles. Group tasks then ask them to act as facilitator.
- Marking the group active is an edit on the same record. Work, cycles, and teams stay put.

## In scope

- A delivery group flag: placeholder or active. Creating a value stream can create the placeholder in the same step.
- Saving a delivery group with an empty facilitator seat, which turns facilitator tasks off for that group.
- Opening a planning cycle and an evidence review on a placeholder group.
- Many roles on one person, scoped to the organization, stream, group, or team where the role applies.
- An assignment screen where adding product owner, scrum master, or group facilitator to someone who already has a role is one more choice and a save.
- An acting role on each saved task. The screen asks the person to switch to the required role when they hold it among others.
- Task bindings: team backlog order and story acceptance require product owner; team sync, impediment, and retrospective require scrum master; alignment decisions and other group-management tasks require group facilitator, and those tasks are absent while the seat is empty.
- The stored action records the person and the acting role.
- Guard: the placeholder cannot be removed while a team, cycle, or dependency still points at it.
- Operator documentation: a product manager who is also product owner and scrum master, a facilitator who is the same person as the product manager, opting out of the facilitator seat, and switching acting role for a task.
- Records this epic stores, including the acting role and the placeholder flag, are SQLAlchemy models. Request bodies are Pydantic models. Both sit on the models from epic 08.

## Out of scope

- A different backlog, cycle, or delivery path for small shops.
- A combined role that satisfies both product-owner and scrum-master tasks.
- Automatic promotion from placeholder to active when a third team appears. A person makes that edit.
- Funding guardrails (epic 11).

## Depends on

- Epic 02
- Epic 08, for the SQLAlchemy models and Pydantic models

## Local proof

Create a value stream and accept the placeholder group. Add two teams and leave the facilitator seat empty. Open a cycle and see it attach to the placeholder. Assign one product manager as product owner and as scrum master. Order the backlog and see the app ask for the product-owner acting role. Save a retro note only after switching to scrum master. See the scrum-master role refused for the backlog change. Then add group facilitator to that same person, turn the group active, and save an alignment decision only while acting as facilitator. Read the operator doc and confirm it matches those steps.

## Stories

Stories for this epic will be added in this file. Each story that stores a row uses a SQLAlchemy model. Each story that accepts a request body uses a Pydantic model.
