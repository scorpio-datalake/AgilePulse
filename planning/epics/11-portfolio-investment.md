# Epic 11 — Portfolio investment

Status: stories written — not started

## Outcome

Portfolio leadership can record a funding guardrail per value stream and can keep the notes from a workshop that recommends how to apply it.

## Why this epic is separate

Stream-level funding is a real portfolio habit. It is a poor first milestone: the delivery loop in epics 02–09 is testable without money. The workshop here is our own record, a recommendation a later review can accept. It is not a licensed portfolio ceremony.

## In scope

- A budget or capacity guardrail on a value stream.
- A workshop record: proposed allocations, participants, and the resulting recommendation.
- A view that compares current initiative load, from epic 04, with the guardrail.
- Records this epic stores are SQLAlchemy models. Request bodies are Pydantic models. Both sit on the models from epic 08.

## Out of scope

- A general ledger, invoicing, or payroll.
- Automatic reallocation.

## Depends on

- Epic 02
- Epic 04
- Epic 08, for the SQLAlchemy models and Pydantic models

## Local proof

Set a guardrail on a value stream, record a workshop recommendation, and see both on the portfolio page after reload.


story 0.1

research this and create or change our epics based on this. 


look at the /home/vihang/work/projects/pm_tools/taiga-front frontend and see what we are missing. We are a clean room but we I do feel that we are missing tooling and navigation. 


Lets figure out how we can create the same stuff. 





Let the board columns be data, and leave the delivery path fixed. Taiga stores each column as a status on the project, with a name, a color, an order, and an is_closed flag. Discover, Define, Build, Check, and Ship should stay the gates. The iteration board inside Build can let a team name its own columns.

Swimlanes, not a second project. Taiga groups a Kanban horizontally with swimlanes. On a delivery-group board that is a cleaner way to show several teams, or several features, than Taiga’s “open another project.”

Do not copy their epic link. An epic connects to stories through a join table, so one story can sit on many epics and epics do not nest. That is how they fake cross-cutting work without a portfolio. AgilePulse already has a stricter parent (story under feature) and a dependency with an owner and a needed-by date. Keep that. A many-to-many epic would blur the tree.

A short ref on each story. Taiga gives every story a project ref, so notes say #42 instead of a long URL. A ref scoped to the value stream would make cross-team sync notes easier to write.

Paste a list into the backlog. Their bulk-create endpoint turns one title per line into stories. That fits the alignment session, when someone already has a list and should not create each story by hand.

Turn pieces off per group. A Taiga project enables Scrum, Kanban, issues, and the wiki independently. The same switch fits a delivery group that is only a placeholder: board on, alignment off, evidence review off, without a second product mode.



## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [ ] **11.1 Stream guardrail.** A value stream stores one guardrail: a kind of budget or capacity, and a whole number of at least 1. The number is the most initiatives that stream may carry. The kind records how leadership reads that number. A guardrail with no stream is refused. A kind outside that list is refused. A number below 1 is refused. The guardrail is a SQLAlchemy model. The request body is a Pydantic model.

  Done when: save capacity and 4 on a stream, reload, and see them. Save a budget of 0 and see it refused.

- [ ] **11.2 Workshop record.** A value stream stores a workshop: the people who attended, a proposed allocation for each initiative named, and the recommendation. Each participant is a person already in the organization. Each allocation names an initiative on that stream and a whole number of at least 1. The recommendation is text. An empty recommendation is refused. A person who is not in the organization is refused. An initiative on another stream is refused. Saving the workshop does not change the guardrail and does not change an initiative. The workshop and its allocations are SQLAlchemy models. The request body is a Pydantic model.

  Done when: record two people, an allocation of 2 on one initiative and 3 on another, and a recommendation, reload, and see them. Submit an empty recommendation and see it refused.

- [ ] **11.3 Portfolio comparison.** The portfolio page lists each stream’s guardrail beside its load. Load is the count of initiatives on that stream whose state is not Done. A stream with no guardrail shows the load and no guardrail. A stream whose load is greater than its guardrail shows over. The page also shows the recommendation from the latest workshop on that stream. The page does not move initiatives.

  Done when: with a guardrail of 4 and five initiatives that are not Done, see load 5 and over. Mark one Done, reload, and see load 4. See the recommendation from 11.2 on that stream.

- [ ] **11.4 Portfolio investment test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, and walks the local proof: a guardrail on a value stream, a workshop recommendation, and both visible on the portfolio page. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
