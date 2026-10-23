# Epic 17 — Timeboxed research and the product-manager guide

Status: stories not written yet

## Outcome

A product manager can run a short research item, get a recorded decision, and see a feature stay out of Build when the data is not there. The same lesson is available as an in-app tutorial and as a PDF.

## Why this epic is separate

Prompt trials, deeper-agent trials, and data checks are real. Public practice runs them as timeboxes: a few days, one question, a decision of proceed, reshape, or drop. They are not three new delivery paths, and they are not a course platform.

AgilePulse already has an experiment. This epic gives an experiment a clock and one of three questions:

- Prompt: can a fixed set of examples pass with a written instruction, before anyone builds a feature around it?
- Deeper agent: after a prompt trial fails the question, is a multi-step agent worth another timebox? The deeper trial does not start while the prompt question is still open.
- Data: does the data exist, can the team read a sample, and is there a named owner? This is the check that gates a feature.

The deliverable is the decision, not a feature. When the clock ends, the item cannot stay open. The product owner records proceed, reshape, or drop. Drop leaves a note on the parent initiative and does not create stories.

A feature that declares it needs data cannot move from Define to Build until a linked data research item has a proceed decision. Missing data is the reason the feature waits. The team does not fill the gap by writing stories. Reshape means the outcome changes to match the data that exists. Proceed means a sample, access, and an owner are named on the research item.

## In scope

- A research flag on an experiment: question type, start, timebox end, linked feature or initiative, and a decision.
- A default timebox of five days, editable before the item starts.
- At the end, the only actions are proceed, reshape, and drop. The screen explains that the timebox protects the calendar and the decision is the result.
- The Define-to-Build block for a feature that needs data, with the blocking research item linked on the feature.
- An exception a product owner can record, with a reason, when they move that feature anyway. The exception is visible on the feature.
- One guide, stored as the source for both the tutorial and the PDF. The PDF is produced from that source so the two cannot drift.
- An in-app tutorial a product manager can finish on the local sample: create a data research item, let it end, record drop, try to move the linked feature into Build, and see the block. The tutorial also asks them to switch acting role where epic 16 requires it.
- The guide's explanation, in plain language: research is timeboxed because an open investigation will consume the cycle; a feature with no data has nothing for a person or an agent to check, so it stays in Define.
- Records this epic stores are SQLAlchemy models. Request bodies are Pydantic models. Both sit on the models from epic 08.

## Out of scope

- Running a model, hosting prompts, or storing training sets. The research item records the question, the sample reference, and the decision.
- A learning-management system, quizzes, or certificates.
- Three separate boards for the three questions.

## Depends on

- Epic 04
- Epic 05
- Epic 07
- Epic 08, for the SQLAlchemy models and Pydantic models
- Epic 16

## Local proof

Create a feature that needs data and an experiment linked to it with the data question and a five-day timebox. Mark the timebox ended, choose drop, and see Build refused for that feature. Record proceed on a second item that names a sample and an owner, and see Build become available. Open the tutorial and finish those steps as the product owner. Export the PDF and see the same explanation as the guide page.

## Stories

Stories for this epic will be added in this file. Each story that stores a row uses a SQLAlchemy model. Each story that accepts a request body uses a Pydantic model.
