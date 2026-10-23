# Epic 18 — Agent release controls

Status: stories not written yet

## Outcome

A feature that ships an agent cannot pass Ship on a passing check alone. The record shows the risk, the tools the agent may use, the held-out cases, who can stop it, and that a rollback was drilled.

## Why this epic is separate

Epic 10 records policies, approvals, and evidence. Epic 17 timeboxes research before Build. Public agent-delivery checklists add a later set of controls that those epics do not name. Teams treat them as release gates, not as research spikes.

The controls this tool stores, without running an agent:

- A risk tier on the feature: assistive, read-only, changes data, or high impact. A higher tier requires a named person on Ship and a recorded rollback drill. The labels are ours. Shops can rename them.
- A tool allowlist: the only tools the agent may call. Any other tool is out of bounds. Actions that move money, change production data, or repeat a failed step are marked as needing a person.
- A held-out eval reference: a name, a version, and a note that these cases were not the ones used to write the prompt. Ship is refused for an agent feature when that reference is empty, or when a critical case is marked failed.
- Rollback: the named person who can stop the agent, and a drill note that someone reverted the prompt, the tool list, and the policy, not only the code. Ship is refused until the drill note exists for read-only and higher tiers.
- After Ship, a change to the recorded prompt version or model version sends the feature back to Check.
- An incident note: the agent is advisory until a person closes it, and the note can add a case to the eval reference. The evidence review in epic 08 can link the note. It does not replace it.

The app does not execute the eval, store prompts, or call tools. It stores the gate and blocks Ship when the gate is empty.

## In scope

- Risk tier, tool allowlist, human-trigger list, eval reference, stop person, and rollback drill on an agent feature.
- Ship blocked while a required field for that tier is missing, or while a critical eval case is failed.
- A version field for prompt and model. Changing either returns the feature to Check.
- An incident record linked to the feature, with advisory status and an added eval case.
- A short section in the epic 17 guide that tells a product manager what each gate is for.
- Records this epic stores are SQLAlchemy models. Request bodies are Pydantic models. Both sit on the models from epic 08.

## Out of scope

- Running models, scoring evals, or hosting tool servers.
- Token-cost accounting, penetration tests, and a security program.
- Live agents inside this product (epic 13).

## Depends on

- Epic 05
- Epic 08, for the SQLAlchemy models and Pydantic models
- Epic 10
- Epic 17

## Local proof

Mark a feature as an agent feature at the read-only tier. Try to ship it and see the refusal until an allowlist, a held-out eval reference, a stop person, and a rollback drill are saved. Mark a critical case failed and see Ship refused again. Change the prompt version and see the feature return to Check. Open an incident, mark the agent advisory, add a case, and see that case on the eval reference.

## Stories

Stories for this epic will be added in this file. Each story that stores a row uses a SQLAlchemy model. Each story that accepts a request body uses a Pydantic model.
