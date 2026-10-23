# Epic 06 — Cycle alignment

Status: done

## Outcome

A delivery group can commit to a planning cycle: measurable outcomes, milestones, dependencies, risks, and a confidence check, in one short working session rather than a multi-day meeting. When a feature needs another team, an architecture review, or a PII review, that need is written in the same session. When it does not, the session does not ask for it.

## Why this epic is separate

Public accounts of multi-team planning keep coming back to the same useful core: shared outcomes, the dependencies between teams, and the risks worth naming. They also describe the cost of planning every team's internal tasks in one room. This epic stores that core. Each team plans its own iteration in epic 07.

The default cycle length in the docs and in sample data is six weeks, because published teams have moved to a cadence of that order and to a session measured in hours. The stored record is just a start date and an end date, so a group can choose another length.

## In scope

- A planning cycle on a delivery group, with start and end. A placeholder group from epic 16 is a valid parent. An empty facilitator seat does not block the cycle. Decisions that manage the group require the facilitator acting role, and those decisions are off while the seat is empty.
- Group outcomes and team outcomes, each with a description and a planned signal. The actual signal is entered later and read by epic 09.
- Milestones on the cycle.
- Dependencies between work items or teams. Each one has an owner, a needed-by date, a status, and the date it was opened, so an aging dependency is visible in the cross-team sync. The providing team is optional.
- Dependent work, only when a feature needs something from another team before it can finish. The record defines the work: the feature it supports, what change or access is needed, what done looks like, a needed-by date, and a status of open, done, or not needed. The providing team is optional. If the shop names one, it is a team from epic 02, under whatever name that shop uses. One named team may cover firewall access and database access. Two named teams may split them. Saving the work does not require a team name. No row is created for work that does not apply.
- An architecture review on a feature, only when the feature says it applies. The record stores who reviewed it, the date, and the result: approved or changes requested. Not applicable is the default, and then there is no review to fill in.
- A PII compliance review on a feature, only when the feature says it handles personal data. Same record as the architecture review. Work that does not handle personal data does not ask for it.
- Risks with a plain state: open, owned, accepted, mitigated, or closed.
- A confidence check stored as a number from 1 to 5 per voter, with the average visible.
- A capacity note per team for the cycle.
- Work items from epic 04 linked to the outcomes they support.

## Out of scope

- The evidence review that adjusts the plan during the cycle (epic 08).
- Who may see the planning cycle. Epic 08 refuses that plan to a person who is not part of the delivery group. This epic shows it to a person who can already open the group.
- Automatic dependency detection (epic 13).
- A second, multi-day agenda. If a group wants a longer checklist later, it is another story on these same records.

## Depends on

- Epic 02
- Epic 04

## Local proof

Open a six-week cycle, add one group outcome and one team outcome, link a feature, add a dependency and a risk, record two confidence scores, and see the summary after reload. Add dependent work for a firewall change, leave the team blank, and see it saved. Add a second item and attach a team the shop named. Open a cycle with no dependent work, no architecture review, and no PII review, and see those sections empty. Mark one feature for an architecture review and one for a PII review, record both results, and see a third feature with neither review.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **06.1 Planning cycle.** From a delivery group, a signed-in user can open a cycle with a name, a start date, and an end date. The usual length is six weeks, and the record stores the dates that were entered. An empty name, a bad date, or an end before the start is refused. An empty facilitator seat does not block the cycle. Reload shows the cycle on the group.

  Done when: open a cycle that runs six weeks, reload, and see the name and both dates. Open it while the facilitator seat is empty.

- [x] **06.2 Outcomes.** A cycle stores group outcomes and team outcomes. Each has a description and a planned signal. The actual signal can be saved on the same record. An empty description or an empty planned signal is refused.

  Done when: add one group outcome and one team outcome, reload, and see both descriptions and planned signals.

- [x] **06.3 Milestones.** A cycle stores milestones with a name and a date. An empty name or a bad date is refused.

  Done when: add a milestone, reload, and see the name and the date.

- [x] **06.4 Dependencies.** A dependency stores a description, an owner, a needed-by date, a status of open, done, or blocked, the date it was opened, and an optional providing team. An empty description, a missing owner, or a bad date is refused. The opened date stays visible.

  Done when: add a dependency with an owner and a needed-by date, leave the providing team blank, reload, and see the opened date.

- [x] **06.5 Dependent work.** A row is created only when someone saves one. It stores the feature it supports, the change or access needed, what done looks like, a needed-by date, and a status of open, done, or not needed. The providing team may be blank. Saving does not require a team name. An empty need or a bad date is refused.

  Done when: save one item with the team blank and a second item with a team the shop named. Open a cycle, save neither, and see the dependent-work list empty.

- [x] **06.6 Reviews.** A feature says whether an architecture review applies and whether a PII review applies. Both default to not applicable, and then the cycle has no review to fill in. When a review applies, the cycle stores who reviewed it, the date, and the result: approved or changes requested.

  Done when: leave both off and see no review rows. Mark one feature for architecture and one for PII, record both results, and see a third feature in neither review.

- [x] **06.7 Risks.** A risk stores a description and a state: open, owned, accepted, mitigated, or closed. An empty description or a state outside that list is refused.

  Done when: add a risk, set the state to owned, reload, and see owned.

- [x] **06.8 Confidence and capacity.** A person stores a confidence score from 1 to 5. The page shows the average. A score outside that range is refused. Each team on the cycle can store one capacity note.

  Done when: record two scores, reload, and see the average. Save a capacity note and see it on the cycle.

- [x] **06.9 Linked work.** A feature or a story can be linked to an outcome. The outcome lists that work.

  Done when: link a feature to the group outcome, reload, and see the feature under that outcome.

- [x] **06.10 Facilitator decision.** A group decision on the cycle requires a person acting as group facilitator. While the facilitator seat is empty, the decision form is absent and a saved decision is refused. One person holding facilitator together with another role, and switching the acting role, is epic 16.

  Done when: with the seat empty, the cycle has no decision form. After a facilitator is assigned, save a decision as that person and see the statement and the acting role. Save it as someone who holds a different role and see it refused.

- [x] **06.11 Cycle test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, and walks the local proof: a six-week cycle, both outcomes, a linked feature, a dependency, a risk, two confidence scores, dependent work with and without a team, an empty review section, then both reviews on two features and none on a third. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
