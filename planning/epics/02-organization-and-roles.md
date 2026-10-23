# Epic 02 — Organization and roles

Status: done

## Outcome

A local user can create one portfolio, at least one value stream, one delivery group, and one team, then assign people to the roles those groups need.

## Why this epic is separate

Work items, alignment, and evidence reviews all hang off the delivery group and the team. Building boards before that structure exists makes later stories invent owners as they go.

A delivery group is the set of teams that share a product and a planning cycle. A value stream is the customer outcome those teams serve. Both words are ordinary Lean and product language. This epic does not import role titles from a licensed framework.

## In scope

- Portfolio, value stream, delivery group, and team records, linked in that order. A team name is whatever the shop calls that group of people. The tool does not require a site-reliability team, a database team, a network team, or a firewall team. One team may do more than one of those jobs.
- People, and membership of a person on a team or a delivery group.
- Roles: stream owner, group facilitator, product manager, product owner, scrum master, technical lead, business stakeholder, and team member. Product owner and scrum master are separate roles. One person holding both is epic 16.
- Pages to create and edit these records.
- A delivery group can be saved with no facilitator. Placeholder groups, dual roles, and the operator guide for a two-team shop are epic 16.

## Out of scope

- Funding guardrails and investment reviews (epic 11).
- Several isolated enterprises. Store an organization id so a later boundary is possible, and test only one organization.
- JWT and shop-written directory adapters (epic 15). Roles created here stay in our database either way.
- A special job title for agents. Agent is an actor type, added in epic 10.

## Depends on

- Epic 01

## Local proof

Create a portfolio, a value stream, a delivery group, and a team in the browser. Assign a product owner and a scrum master. Reload and see the same structure.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **02.1 One organization.** Migrations create one organization and store its id on the local user. There is no page to add a second organization. Portfolio, value stream, delivery group, team, and person records in this epic store that same id.

  Done when: start the app, and a test reads exactly one organization with the local user on it. Start again and see that a second organization was not added.

- [x] **02.2 Portfolio.** A signed-in user can create a portfolio and edit its name. The home page lists the portfolios for that organization. The request body is a Pydantic model. An empty name is refused. A signed-out request for these pages goes to sign-in.

  Done when: create a portfolio, edit the name, reload, and see the new name. Submit an empty name and see it refused.

- [x] **02.3 Value stream.** From a portfolio, a signed-in user can create a value stream and edit its name. The stream is stored under that portfolio. A stream with no portfolio is refused. An empty name is refused.

  Done when: add a stream to the portfolio, edit the name, reload, and see the stream still under that portfolio.

- [x] **02.4 Delivery group.** From a value stream, a signed-in user can create a delivery group and edit its name. The group is stored under that stream. The group saves when the facilitator seat is empty. An empty name is refused. A placeholder flag, and one person holding more than one role, are epic 16.

  Done when: add a group with no facilitator, edit the name, reload, and see the group still under that stream.

- [x] **02.5 Team.** From a delivery group, a signed-in user can create a team and edit its name. The name is whatever the shop calls that group of people. The page does not require a site-reliability team, a database team, a network team, or a firewall team. The team is stored under that group. An empty name is refused.

  Done when: add one team with a shop name, edit the name, reload, and see the team still under that group.

- [x] **02.6 People.** A signed-in user can add a person and edit their name. The local admin is already a person. An empty name is refused. A people page lists them. These records stay in our database. Sign-in for anyone but the local user is epic 15.

  Done when: add a person, edit the name, reload, and see both that person and the local admin.

- [x] **02.7 Membership.** A signed-in user can add a person to a team or to a delivery group, and can remove them. The team page and the group page list their members.

  Done when: add a person to the team and to the group, reload, and see them listed on both. Remove them from the team and see them gone from the team and still on the group.

- [x] **02.8 Roles.** A signed-in user can assign one role to a person. The assignment is a row in our database. Stream owner sits on a value stream. Group facilitator, product manager, and business stakeholder sit on a delivery group. Product owner, scrum master, technical lead, and team member sit on a team. Product owner and scrum master are separate choices. A role saved on the wrong record is refused. A person who already has a role cannot take a second one in this epic; that is epic 16. The delivery group still saves with no facilitator. There is no agent job title.

  Done when: assign a product owner and a different person as scrum master, assign each other role on its record, reload, and see the same assignments. Give the product owner the scrum master role as well and see it refused.

- [x] **02.9 Structure test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, creates a portfolio, a value stream, a delivery group with no facilitator, and a team, assigns a product owner and a different scrum master, and reads that structure back. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
