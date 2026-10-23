# Epic 07 — Team execution

Status: done

## Outcome

A team can run day-to-day work inside an iteration: a backlog, a short team sync, a cross-team dependency note, and a retrospective whose notes stay on that team.

## Why this epic is separate

Alignment and evidence review are delivery-group sessions. The team board is where work actually moves. Retro notes are for the people in the room. Publishing them upward by default would break that.

A cross-team sync belongs near the team board because that is the public practice: during the iteration, representatives name impediments and dependencies often enough that the other teams can still react. The sync note is short. It is not a second planning event.

## In scope

- An iteration on a team, with start and end, inside a cycle from epic 06.
- Team backlog order for that team's stories. Ordering and story acceptance require the product-owner acting role from epic 16. Each story shows the estimate from epic 04. The completed size of the iteration is the input epic 09 uses for velocity.
- A simple board for the iteration.
- A work-in-progress limit for the team. Starting another item is refused while the board is at the limit. The scrum master can raise the limit for one item by recording a reason.
- Team sync notes for a date. The sync, an impediment, and the retrospective require the scrum-master acting role from epic 16.
- A cross-team sync note: impediment, dependency, and which team is asked to respond.
- A retrospective record visible only to members of that team.
- An explicit action to promote one retro learning into a short statement other epics may attach. The raw retro stays private.

## Out of scope

- The delivery-group evidence review (epic 08).
- Who may see an iteration board outside their delivery group. Epic 08 refuses that board, the group's features, and the group's plan. This epic still shows a sync note to another team in the same group, and still hides the raw retro.
- Flow charts (epic 09).
- Chat or mail import.

## Depends on

- Epic 04
- Epic 06

## Local proof

As a team member, add a story to an iteration, write a sync note and a retro note, and see them on the team page. As a member of another team, see the sync note and do not see the retro. Promote one learning and see only the promoted line available outside the team.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **07.1 Iteration.** From a team, a signed-in user can open an iteration with a name, a start date, and an end date inside a cycle of that team's delivery group. A bad date, an end before the start, or dates outside the cycle are refused. Reload shows the iteration on the team.

  Done when: open an iteration inside the cycle, reload, and see the name and both dates. Submit dates outside the cycle and see them refused.

- [x] **07.2 Backlog and acceptance.** The iteration lists the team's stories in a saved order. Each row shows the estimate from epic 04. Adding, reordering, and accepting a story require a person who holds product owner on that team, and the save stores the product-owner acting role. A person who holds scrum master is refused. The completed size is the sum of the estimates on accepted stories. One person holding both roles is epic 16.

  Done when: add a story estimated as 3, see 3 on the row, accept it as the product owner, and see completed size 3. Save the same add as the scrum master and see it refused.

- [x] **07.3 Iteration board.** The iteration page groups its stories by the delivery-path stage.

  Done when: move a story on the iteration to Define and see it under Define on the iteration page.

- [x] **07.4 Work in progress.** A team stores a work-in-progress limit. Moving another story on the iteration to Build is refused while the number of stories in Build is at that limit. The scrum master can raise the limit for one story by recording a reason. The next story still needs its own reason.

  Done when: set the limit to 1, put one story in Build, and see a second story refused. Record a reason as the scrum master and see that second story enter Build.

- [x] **07.5 Team sync.** A team sync note stores a date and a note. Saving it requires the scrum-master acting role. The product owner is refused. The note is visible on the team page to a member of another team in the same delivery group.

  Done when: save a sync note as the scrum master, reload, and see the date and the note. Save it as the product owner and see it refused.

- [x] **07.6 Cross-team note.** A cross-team note stores an impediment, a dependency, and the team asked to respond. Saving it requires the scrum-master acting role. The asked team can see it.

  Done when: save a note that asks the other team, open that team's page as one of its members, and see the impediment.

- [x] **07.7 Retrospective.** A retro note is stored on an iteration and requires the scrum-master acting role. It is visible to a member of that team. A member of another team does not see the raw note.

  Done when: save a retro note as the scrum master and see it on the team page. As a member of the other team, see the sync note and do not see the retro note.

- [x] **07.8 Promoted learning.** An explicit action copies one retro note into a short statement. The raw note stays on the team. The statement is visible to the other team.

  Done when: promote one learning and, as a member of the other team, see the statement and not the raw note.

- [x] **07.9 Team execution test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, adds a story to an iteration, writes a sync note and a retro note, reads those as a member of another team, and reads only the promoted line outside the team. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
