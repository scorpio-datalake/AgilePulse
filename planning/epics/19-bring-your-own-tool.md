# Epic 19 — Bring your own tool

Status: stories not written yet

## Outcome

A shop can use Cursor, Claude, or any other tool it already runs to turn meeting notes, documents, and other artifacts into backlog items in AgilePulse, and to take stories back out for its own developers. AgilePulse does not call a model and does not open their code repository.

## Why this epic is separate

The conversion is theirs. Their prompts, their operational model, and their coding tool stay outside this product. What we provide is a plugin seam: a documented way for their tool to push work in, and a documented way to pull stories out.

A shop's tool may call the parent item an epic. In this product that parent is an initiative. The contract uses that word, and the guide shows the mapping so their prompt can keep saying epic.

Inbound items arrive as proposals. The product owner accepts them while acting as product owner, then they are visible to the scrum master and the team. A plugin cannot approve Define, complete Check, or decide Ship.

Stories are for their system. The export is a file their developer can hand to Cursor or another coding tool. The code that tool writes stays in the shop's repository. That repository is out of scope.

## In scope

- A named plugin registration. Each call records the plugin as an agent actor on the evidence log.
- An inbound payload: source note, proposed initiative, optional features, and which audience it is for (product owner, scrum master, or team). Extra fields from their operating model are stored with the proposal and are not interpreted.
- A queue of proposals. Accepting one creates the initiative and features. Rejecting one keeps the note and does not create work.
- An outbound story pack for a feature: title, outcome, acceptance lines, and links back to the initiative. The pack is a file. It is not sent to a model.
- Operator documentation with one example payload and one example story pack. The example says the shop's own Cursor or Claude workflow fills the payload. The example does not include a working connection to those products.
- A local test that posts a payload with no network call and checks the proposal, the accept step, and the exported file.
- Proposals and the work created from them are SQLAlchemy models. The inbound payload is a Pydantic model. Both sit on the models from epic 08.

## Out of scope

- Calling Cursor, Claude, or any other model.
- Writing or reading the shop's source repository.
- Shipping prompt packs that match a shop's process. They write those.
- In-product drafting helpers. Those remain epic 13, and they are not required for this seam.

## Depends on

- Epic 04
- Epic 08, for the SQLAlchemy models and Pydantic models
- Epic 10
- Epic 16

## Local proof

Post a sample payload as a plugin. See a proposal, not a live initiative. Accept it as product owner and see the initiative on the backlog, with the plugin named on the evidence page. Export a story pack for one feature and read the file. Reject a second proposal and see that no initiative was created. Confirm the guide says the shop's tool does the conversion and that their repository is untouched.

## Stories

Stories for this epic will be added in this file. Each story that stores a row uses a SQLAlchemy model. Each story that accepts a request body uses a Pydantic model.
