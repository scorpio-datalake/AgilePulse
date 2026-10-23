# Epic 03 — Navigation

Status: done

## Outcome

A signed-in user can move from a portfolio to a team in one or two clicks, see where they are, and add the next record in the chain without hunting for the form. The page looks like a space in Jira or a board in Monday: a fixed sidebar, a header, and the record filling the rest of the width. Job seats stay labels for who holds the work. A separate access check decides who may see a record and who may change it.

## Why this epic is separate

Epic 02 stores the structure. Walking it means a parent link on each page and a long form under that. After a portfolio, a stream, a group, and two teams exist, the way back is a series of single parent links.

Public navigation in Jira, Linear, Azure DevOps, and Shortcut converges on a few habits:

- A persistent sidebar holds the places a person returns to. Jira keeps recent projects there and opens a project's boards from that project. Linear puts each team in the sidebar and opens that team's home, members, and cycles in one click. Shortcut groups Stories, Epics, and Iterations, and can pin a team so that team's views stay together.
- The full parent chain stays visible. Jira's breadcrumb stops at a fixed depth, and people ask for the epic while they are on a task. Azure DevOps puts the team selector in the breadcrumb and, after an early redesign, keeps the same team when you move between board, backlog, and sprint.
- The first setup is a short path. Jira's team-managed projects land in one place. Shortcut's own notes say a first visit is overwhelming when the sidebar lists everything. Most people never rearrange that sidebar, so a small fixed list beats a customizable one.
- Create stays next to the thing it creates. The header is where Shortcut puts create, search, and recent work.

Jira's 2025 navigation and Monday's board chrome add the part the first pass missed. Both products are full-width. The sidebar is a quiet list with the current row filled, not bold. The record name and one primary action sit in a header. Monday leads with rows (person, status, owner). Settings and rename sit after that list, not as the page itself. Color is reserved for the primary button and for status. Atlassian uses a small status lozenge. Monday fills the status cell. This epic has no work items yet, so it uses that shell for the records that exist: the tree, the members, and the seats.

The two public articles that prompted this pass are process guides, not layout specs. The Atlassian community post "What is the Scaled Agile Framework" maps portfolio epics, features, stories, the release train, and the planning interval onto Jira work types, boards, and versions. The Monday post "Agile workflow" (22 Oct 2025) describes sprints, backlogs, and dashboards. Boards, columns, and status cells arrive with later epics. This epic copies the shell those pages will sit in.

References for the shell, copied into the existing Jinja pages. None of these become a dependency:

- Atlassian Design System: neutral page, one blue primary button, compact rows, a sidebar around 240px wide.
- shadcn's Sidebar Kanban and Sidebar Project Management blocks: grouped sidebar, filled selection, a view switch. They are React references. The pages stay server-rendered.
- shadcn-kanban-board and Taskara (`atlassian-jira-ui`): card and issue-panel density for later epics.
- forge-tailwind-theme: Atlassian color and type tokens, if a stylesheet is added. Not the Forge host.
- Monday's board basics: a header of views, then a table of people and seats. Their template gallery is inside the product.

Seats and access are different objects. Epic 02 stores stream owner, group facilitator, product manager, product owner, scrum master, technical lead, business stakeholder, and team member. Jira does not grant access from those titles. A permission scheme grants actions to a space role such as Administrators, Developers, or Users. A person in two roles receives the union of those grants. Admin does not imply "can edit the work." Monday stacks account, workspace, board, and column, and the strictest layer wins. Account types are Admin, Member, Viewer, and Guest. A board owner can set edit everything, edit content only, edit assigned items, or view and comment. On Enterprise the board roles are Owner, Editor, Contributor, Assigned contributor, and Viewer, and a role is a ceiling. Monday's own example makes the project manager an owner, task managers contributors, and stakeholders viewers. A product owner who cannot edit the backlog is a normal setup in both products.

This tool has one organization, so a reusable permission scheme has nothing to reuse. Copy Monday's strictest-layer rule. Three layers are enough. Epic 15 still owns login, JWT, and the extension point. When those checks land, they read the layers in this epic. They do not treat a job seat as a grant. A second seat on one person stays in epic 16.

## In scope

- A sidebar on every signed-in page: Home, People, and each portfolio with its value streams, delivery groups, and teams nested in that order.
- The current record is marked in the sidebar with a filled row. Children are indented under their parent.
- A breadcrumb on a record page. Every ancestor is a link. The current name is text. The chain is portfolio, value stream, delivery group, team, as far as that record sits. The breadcrumb sits in the page header with the record name and its type.
- After a record is saved, its page opens and the sidebar lists it.
- An empty portfolio offers a value stream. An empty value stream offers a delivery group. An empty delivery group offers a team. That offer is the primary button in the header. The form for that next record is on the page.
- The signed-in page uses the width beside the sidebar. The sign-in page stays narrow and has no sidebar. The "Static shell" line is gone.
- One filled button for the primary action on a page. Other buttons are plain.
- People stays one click away. Adding a person asks for the name and the job seat in one form. A stream owner also picks the value stream. A group seat also picks the delivery group. When a team already exists, the same form can put the person on one team. That choice can be left blank. If no team exists yet, membership stays a later step on the team or the delivery group, because some people are not on a delivery team.
- On a team and a delivery group, members are a table: person, the seat they already hold, and remove. Rename sits after that table. A value stream lists the stream owner and has no member list.
- Account access on a person: admin, member, or viewer. The local user is admin. A new person is a member.
- Record access from membership already stored in epic 02. An admin sees every record. Anyone else sees a team they belong to and that team's ancestors, and a delivery group they belong to plus that group's ancestors and teams. A sibling portfolio stays hidden.
- Action access: view, edit content (rename), change structure (create the next record), and add or remove a member. A viewer may view and may not submit those forms. A member may do them on records they can see. Creating a portfolio stays with the admin. The strictest layer wins. A job seat never grants or removes an action.
- The sign-in page has no sidebar.

## Out of scope

- Boards, backlogs, cycles, search, status columns, and kanban cards (later epics).
- A customizable sidebar, favorites, and a collapsed icon rail.
- Keyboard shortcuts.
- Login, JWT, and a shop-written authenticator (epic 15). This epic stores the access layers those checks will read.
- A second seat on one person (epic 16).
- New fields on the portfolio, value stream, delivery group, or team records from epic 02. Account access is a field on the person.
- Guest accounts, column locks, and a reusable permission scheme.

## Depends on

- Epic 02

## Local proof

Sign in and create Supply chain, Warehouse fulfillment, Optimization of the warehouse, and Build crew from the header action on the page you just opened. The sidebar shows that chain, with Build crew filled and indented. The Build crew header links back to the group, the stream, and the portfolio, and the members are a table above the rename form. Add a person and their seat on the People page, without choosing a team. Reload, click Build crew in the sidebar, and land on that table. Mark a second person as a viewer, open the app as that person in the test client, and see a rename refused. Give that person membership only on Build crew and see the sibling portfolio omitted from the sidebar.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **03.1 Sidebar.** Every signed-in page shows a sidebar with Home and People. The sign-in page does not. The item for the page you are on is marked.

  Done when: sign in, open Home and People from the sidebar, and see the current one marked. Sign out and see the sign-in page without the sidebar.

- [x] **03.2 Tree.** The sidebar lists each portfolio and, under it, its value streams, delivery groups, and teams. Choosing a name opens that record. Saving a new record puts it in the tree.

  Done when: create a portfolio, a value stream, a delivery group, and a team, and see all four in the sidebar. Click the team and land on its page.

- [x] **03.3 Breadcrumb.** A value stream, delivery group, and team page show the chain from the portfolio down to the current record. Each ancestor is a link. The current name is text. Home and People have no breadcrumb.

  Done when: open a team and use the breadcrumb to open its delivery group, then its value stream, then its portfolio.

- [x] **03.4 Next record.** A portfolio with no value stream shows the form to add one. A value stream with no delivery group shows the form to add one. A delivery group with no team shows the form to add one. Saving opens the new record.

  Done when: starting from an empty portfolio, add the stream, the group, and the team by using the form on the page you just opened.

- [x] **03.5 Members before rename.** On a team page and a delivery group page, the member list and the role form come before the form that renames the record. People remains in the sidebar.

  Done when: open a team from the sidebar and see its members and role form without passing the rename form. Open People from the sidebar in one click.

- [x] **03.6 Navigation test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, creates a portfolio, a value stream, a delivery group, and a team, and reads the sidebar and the breadcrumb on the team page. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.

- [x] **03.7 Full-width shell.** A signed-in page uses the width beside a fixed sidebar. The content column is not capped at 36rem. The "Static shell" line is not rendered. The sign-in page stays a narrow page without the sidebar. One button on a page is filled, for the primary action. The other buttons are plain.

  Done when: sign in, see Home fill the width beside the sidebar, and see Create portfolio as the filled button. Open sign-in and see no sidebar and no "Static shell" text.

- [x] **03.8 Record header.** A portfolio, value stream, delivery group, and team page open with a header: the record name, the record type, and the breadcrumb. The primary action in that header is the next record when the page has none, and is absent when the next record already exists. Home and People have a header and no breadcrumb.

  Done when: open an empty portfolio and use the header action to add the stream. Open a team and see its name, the type Team, and the breadcrumb in the header.

- [x] **03.9 Filled selection.** The sidebar row for the current page has a filled background. Value streams indent under the portfolio, delivery groups under the stream, and teams under the group. Bold text is not the only marker.

  Done when: open a team and see that row filled and indented beneath its group. Open Home and see Home filled at the top level.

- [x] **03.10 Members table.** A team and a delivery group list members in a table: person, the seat chosen when the person was added, and remove. Adding a member does not ask for a seat. Rename sits after the table. A value stream lists the stream owner and has no member list.

  Done when: open a team, see each member on one row with a seat or an empty seat, remove a member from that row, and reach rename only after the table.

- [x] **03.11 Person and seat together.** The People form asks for a name and a job seat. A stream owner also chooses a value stream. A group facilitator, product manager, or business stakeholder also chooses a delivery group. Product owner, scrum master, technical lead, and team member do not choose a team. Account access is a separate control on the person: admin, member, or viewer. The local user is admin. A new person is a member. An admin can set another person to viewer or back to member. The eight job seats are not choices in that control.

  Done when: add a product owner with no team, reload, and see that seat on the person. Add a stream owner only after choosing a value stream. Set the product owner to viewer, reload, and see viewer.

- [x] **03.12 Strictest action.** A viewer can open a record they are allowed to see and cannot rename it, create the next record, add or remove a member, or assign a seat. A member can do those four on a record they can see. An admin can do them on every record. Holding a job seat does not change the result.

  Done when: add a person as product owner with no team, then add them to the team. As that member, rename the team and see the new name. Set them to viewer and see the next rename refused, with the name unchanged.

- [x] **03.13 Branch visibility.** An admin sees every portfolio in the sidebar. Another person sees a team they belong to and that team's delivery group, value stream, and portfolio, and sees a delivery group they belong to with that group's ancestors and teams. A portfolio they do not belong to, through a team or a group, is omitted. Job seats do not reveal a branch.

  Done when: with two portfolios, put a member only on a team in the first. Open the app as that member and see the first portfolio and that team, and not the second portfolio. Assign them stream owner on the second portfolio's stream, without membership, and still see the second portfolio omitted.

- [x] **03.14 Shell and access test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, and reads the full-width shell, the team header, the filled sidebar row, and the members table. It sets a second person to viewer, acts as that person, and reads a refused rename. It gives that person one team membership and reads a sidebar that omits the other portfolio. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
