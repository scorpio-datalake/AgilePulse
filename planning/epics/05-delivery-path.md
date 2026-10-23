# Epic 05 — Delivery path

Status: done

## Outcome

Every work item has a place on the delivery path, and the app can show how it got there.

## Why this epic is separate

Initiative states in epic 04 answer whether a bet is being shaped or built. The delivery path answers how a single feature or story moves once someone is working on it.

Public descriptions of agent-built software keep three boundaries that a plain task board usually loses. AgilePulse uses them as stage rules:

- Discover records the problem and the outcome.
- Define holds the bounded intent. A person approves it before Build is allowed. That approval is the limit of what a team or an agent may do.
- Build produces the change.
- Check records an independent result. The actor who produced the change cannot be the only one who marks Check complete.
- Ship is a later human decision. Prototypes and experiments stop at Check unless a person explicitly chooses to ship them.
- If the approved definition changes in a material way, the item returns to Check.

## In scope

- A current stage on each work item from epic 04: Discover, Define, Build, Check, or Ship.
- A stored history of stage changes: when, from, to, and who.
- An approval on Define, by a person, required before Build.
- A checker on Check who is not the producing actor.
- The learning-item rule for Ship.
- A return to Check when the approved definition changes.
- A board or list grouped by stage for one team and for one delivery group.
- A shared done list for the delivery group. Check cannot be completed while a required item on that list is open. The list starts with: integrated with the product, acceptance criteria met, no open dependency without an owner, and a rollback note where the work changes production. An architecture review or a PII review is on that list only when the feature says the review applies. A review marked not applicable does not block Check.

## Out of scope

- The policy catalog and the full evidence page (epic 10). Those stories attach to this history.
- Who may see the stage board and the features. Epic 08 refuses them to a person who is not part of the delivery group. This epic shows them to a person who can already open the group.
- Live agents moving cards (epic 13).
- The rule that blocks Build when required data is missing (epic 17).

## Depends on

- Epic 04

## Local proof

Move a feature from Discover to Define, approve it as the dev user, and see Build become available. Try to complete Check as the same person who moved it through Build, and see that refused. Try to ship an experiment through the normal control and see it stay in Check. Ship it only through the explicit action. Change the approved definition and see the feature sent back to Check.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **05.1 Stage and history.** A feature and a story start in Discover. A signed-in user can move either one to Define, Build, Check, or Ship, subject to the rules in the later stories. The page stores each change with when, from, to, and who, and lists that history. A stage outside that list is refused. A signed-out request goes to sign-in.

  Done when: move a feature from Discover to Define, reload, and see Define with a history row that names the person, Discover, and Define.

- [x] **05.2 Define approval.** Build is refused until a person approves the definition. The approval stores that person. After the approval, Build can be saved.

  Done when: move a feature to Build before approval and see it refused. Approve it as a chosen person, move it to Build, reload, and see Build.

- [x] **05.3 Independent check.** The person who moved the item into Build cannot be the person who moves it to Check.

  Done when: that person tries to move it to Check and sees it refused. A different person moves it to Check, and the page shows Check.

- [x] **05.4 Learning items.** A prototype or an experiment stays in Check when Ship is chosen on the stage control. An explicit Ship action moves it to Ship. A feature or a platform item can move to Ship on the stage control.

  Done when: an experiment in Check stays in Check after the stage control is set to Ship. The explicit action moves it to Ship.

- [x] **05.5 Definition change.** After the definition is approved, changing the name or the kind sends the item back to Check and clears that approval. The history records the return.

  Done when: change the approved name and see the stage is Check, with a history row into Check.

- [x] **05.6 Stage board.** A team page groups that team's stories by Discover, Define, Build, Check, and Ship. A delivery group page groups the features on its value stream, and the stories of its teams, the same way.

  Done when: put a story in Define and see it under Define on the team page and the group page. See the feature under its stage on the group page.

- [x] **05.7 Done list.** Check is refused while a required item is open. The list starts with integrated with the product, acceptance criteria met, no open dependency without an owner, and a rollback note when the item changes production. Architecture review and PII review are on the list only when the feature says that review applies. Not applicable does not block. A story uses its feature's review flags.

  Done when: leave one required item open, try Check, and see it refused. Mark the required items done and see Check succeed. Turn on an architecture review, leave it open, and see Check refused again.

- [x] **05.8 Delivery path test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, and walks the local proof: Define, approval, Build, a refused Check by the builder, an experiment that stays in Check until the explicit Ship action, and a definition change that returns the feature to Check. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
