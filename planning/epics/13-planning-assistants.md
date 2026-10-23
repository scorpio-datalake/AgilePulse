# Epic 13 — Planning assistants

Status: future — stories not written yet

## Outcome

Optional helpers draft planning inputs a person can accept or ignore. Accepted drafts are normal records. The evidence log from epic 10 shows an agent as the actor.

## Why this epic is separate

Useful drafts show up only after the records exist: dependencies across teams, a split of an initiative into features, suggested priority inputs, a risk state drawn from a promoted learning, and a warning when work in progress crosses a limit. Building the helpers first would invent the delivery process inside a prompt.

Shops that already have Cursor, Claude, or another tool do not need these helpers. They push proposals in and take stories out through epic 19. This epic is only for a later, in-product helper. It is not the plugin seam.

Each helper is a client of the local API. None of them get a private write path. A helper does not approve Define, complete Check, or decide Ship.

## In scope

- A dependency draft across teams, which a person confirms before it is saved.
- A draft split of an initiative into features and platform items.
- Suggested priority inputs, stored only after a person accepts them.
- A risk-state suggestion that reads promoted learnings, not raw team retros.
- A warning when work in progress crosses a limit the team set.
- Accepted drafts are written through the SQLAlchemy models from epic 08. Request bodies are Pydantic models. A helper has no private write path.

## Out of scope

- An agent shipping its own work.
- Reading chat tools or mail.
- Hiding agent actions from the evidence log.

## Depends on

- Epic 06
- Epic 08, including the SQLAlchemy models and Pydantic models
- Epic 09
- Epic 10

## Local proof

Each helper can be run against fixture data with a fake model client. A person accepts one draft and rejects one. Only the accepted draft is stored, and the evidence page names the agent.

## Stories

Stories for this epic will be added in this file when the epic leaves future scope. Each story that stores a row uses a SQLAlchemy model. Each story that accepts a request body uses a Pydantic model.
