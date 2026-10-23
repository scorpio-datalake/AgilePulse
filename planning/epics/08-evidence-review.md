# Epic 08 — Evidence review

Status: stack stories done; product stories not written yet

## Outcome

Once each iteration, a delivery group can look at what happened and write down what it will change.

## Why this epic is separate

A planning cycle that cannot bend until the next alignment session is too slow for work that includes agents and experiments. Public agent-delivery notes treat evidence as part of the loop, not as a slide at the end of the quarter. The team retro in epic 07 is a different meeting, with a different audience.

The session has two parts:

- Observe: a count or metric note, a customer comment, and a demo note.
- Decide: continue, drop, reshape, or resize something, written as a decision.

When the facilitator seat is filled, the person who runs the session acts as group facilitator. Product owners, scrum masters, technical leads, and business stakeholders attend under their own acting roles. While the seat is empty, the session still happens and no facilitator step is required. The group can open an extra session when new evidence cannot wait for the iteration boundary.

## In scope

- One evidence review per iteration boundary for the delivery group, plus optional extra sessions.
- Observation entries: a metric note, a customer comment, a demo note.
- Decisions linked to a work item, an outcome, or a team's capacity note.
- Promoted team learnings from epic 07 can be attached. Raw retro text cannot.
- A readable summary after the session is closed.
- SQLAlchemy models for every table this epic reads or writes, including the tables already created in epics 01 through 07.
- Pydantic models for those rows and for every new request body.
- An entity-relationship diagram of the tables that exist when this epic starts.
- The iteration board, the features, and the planning cycle of a delivery group stay visible only to an admin and to a person who belongs to that group.
- A note on the entity diagram for several projects on one delivery group. How a project's board, features, and plan stay off the other projects on that group is not decided here.

## Out of scope

- Computing throughput and lead time (epic 09). This epic can display a number epic 09 already stored.
- Agents that draft the decisions (epic 13).
- A project table, and a choice of how several projects attach to one delivery group. The diagram records that boundary. A later epic builds it.

## Depends on

- Epic 05
- Epic 06
- Epic 07

## Local proof

Open a session at the end of an iteration, add one demo note and one customer comment, record a decision to drop an experiment, close the session, and see the decision on the delivery-group page. Confirm a private retro note from epic 07 is absent until it is promoted.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **08.1 Existing tables on SQLAlchemy and Pydantic.** Tables created in epics 01 through 07 are defined as SQLAlchemy models and are read and written through those models. The rows are Pydantic models at the same boundary that already takes form bodies. Startup still creates a missing SQLite file and migrates it. A database that already has those tables keeps its rows. Hand-written `CREATE TABLE` statements for those tables are gone. Sign-in, organization, work items, the delivery path, cycles, and team execution behave as they do today.

  Tables: users, organizations, people, portfolios, value_streams, delivery_groups, teams, memberships, role_assignments, goals, initiatives, features, stories, stage_changes, done_checks, planning_cycles, outcomes, milestones, dependencies, dependent_work, reviews, risks, confidence_votes, capacity_notes, outcome_links, group_decisions, iterations, iteration_stories, wip_exceptions, sync_notes, cross_team_notes, retro_notes, promoted_learnings.

  Done when: start against the existing SQLite file, sign in, and see the same organizations, work items, cycles, and team notes. Run the suite. A fresh file still boots and seeds the local admin.

- [x] **08.2 Entity diagram.** Add `planning/er_diagram.md` with the entity-relationship diagram for the tables in 08.1, including the relationships those tables already store.

  Done when: the file is in the repo and a reader can see each table from 08.1 and how it links to the others.

- [x] **08.3 Group board, features, and plan.** The iteration boards of a delivery group, the features shown for that group, and that group's planning cycle are visible only to an admin and to a person who belongs to the group. Belonging is a membership on the group or on a team in the group, the same membership epic 03 already uses for the sidebar. Anyone else is refused, including when they open the address directly. A job seat on the stream or the group does not reveal them. Epic 03 still decides which portfolios appear in the sidebar. Epic 07 still shows a team its own iteration, its sync note, and its private retro.

  Done when: as a member of the group, open an iteration board for a team in that group, a feature shown on that group, and the planning cycle. As a member of another group only, open those addresses and see them refused. Give that person a job seat on this group, with no membership, and see the same refusal.

- [x] **08.4 Several projects on one group.** One delivery group may hold more than one project. Each project keeps its own iteration board, its own features, and its own plan. A person who can see one project does not see the others by that fact alone. The tables in 08.1 do not say how. A feature hangs off a goal on the value stream, the planning cycle hangs off the delivery group, and the iteration hangs off a team. `planning/er_diagram.md` records that a project boundary has to keep those three apart inside one group, and that the link from a project to the group is not decided. This story does not add a project table. Epics 05, 06, and 07 still store one stage board, one cycle, and one iteration on the group and its teams.

  Done when: the diagram from 08.2 names the iteration board, the features, and the plan as the records a project must keep to itself, states that one delivery group may contain several projects, and states that the link from project to group is not decided. The app still has one cycle on the group.

Product stories for the evidence review itself will be added below these. They use the SQLAlchemy models and Pydantic models from 08.1.
