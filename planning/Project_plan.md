# AgilePulse

Working name for a local-first project tool. The product name can change later. The delivery process below is ours. It is informed by practices teams publish and use in the open. It is not an implementation of a licensed scaling framework, and the docs do not use that framework's names, events, or roles.

Stories are not written yet. Each epic has its own file under `epics/`. Those files are the only place its stories will go.

A reader overview, with the process steps and what a shop can skip, is in [docs/scaled-engine-overview.pdf](docs/scaled-engine-overview.pdf).

## What people are actually doing

Public write-ups of multi-team delivery and of agent-built software converge on a few habits. AgilePulse keeps those habits and leaves the ceremony light enough to test on a laptop.

Multi-team delivery, from public accounts rather than a licensed manual:

- Organize people around a value stream, the path from request to customer outcome, and keep teams long-lived inside it.
- Align on outcomes before the cycle starts. A published enterprise account describes leaving multi-day quarterly planning for a six-week cycle and a session of a few hours. Other public scaling notes make the same trade: spend the shared meeting on cross-team commitments, dependencies, and risks, and let each team plan its own tasks. Work another team must do is written down only when it applies. The shop names that team, or leaves the name blank.
- Keep a short cross-team sync during the cycle so a dependency found on Tuesday is not a surprise at the next quarterly meeting. The long-standing form is a scrum of scrums: representatives, impediments, and dependencies, often enough that teams can still react inside the iteration.
- Show the queue. Throughput, lead time, work in progress, and active time versus waiting time are ordinary Kanban measures. A team also sizes its stories and reads velocity as completed size per iteration.
- Sort work with delay cost divided by size. That economic idea is older than any one scaling brand: value lost by waiting, divided by how long the job takes.

Agent delivery, from public 2026 descriptions of governed agent workflows:

- Discover the problem, then write a bounded definition. A person approves that definition before implementation starts. The approval is the limit of what an agent may do.
- The producer of a change does not certify it. Check is independent.
- A named person decides to ship. A passing check is evidence for that decision. It is not the decision.
- If the approved definition changes in a material way, the work goes back through Check.
- The record keeps who acted, whether they were a person or an agent, what the policy said, and how the decision came out.

Agent and model work adds three research questions teams already timebox before they commit a feature: whether a prompt can pass a small fixed set of examples, whether a deeper multi-step agent is worth trying after a simpler prompt fails, and whether the data exists, is reachable, and has an owner. Public write-ups treat each as a spike of a few days with a decision at the end: proceed, reshape, or drop. A feature that needs data and has none stays out of build.

A later pass over public agent checklists and ordinary multi-team practice added the gaps those sources repeat and this plan did not yet name. Agent features need a risk tier, a tool allowlist, a held-out eval reference, a named person who can stop the agent, and a rollback drill before Ship. A prompt or model change sends the feature back to Check. An incident puts the agent in an advisory state and adds a case to the eval set. Across teams, a dependency needs an owner and a needed-by date, a shared done list gates Check, and a team work-in-progress limit blocks starting more work. Sources for that pass include the public agent lifecycle at [aisdlc.ai](https://aisdlc.ai/canon/aisdlc.md), published agent deployment checklists, the Scrum.org note on a product-level definition of done, and the long-standing practice of limiting work in progress.

Sources worth rereading when we write stories: the Scrum.org account of shorter outcome alignment, public descriptions of scrum of scrums, Kanban flow measures, cost-of-delay ordering, and the public agent lifecycle notes at [aisdlc.ai](https://aisdlc.ai/canon/aisdlc.md) and [specification-governed agentic development](https://sleepyhollow.io/docs/sgad/).

## Delivery process

Names in this list are AgilePulse words.

| Word | Meaning |
| --- | --- |
| Portfolio | The set of value streams an organization funds. |
| Value stream | The flow of work toward one customer outcome. |
| Delivery group | The teams that share a product and a planning cycle. A shop can leave this as a placeholder instead of staffing a separate group. |
| Team | The people who pull work and ship inside an iteration. The shop chooses the name. One team may cover database access and firewall changes. Two teams may split them. |
| Goal | A longer-lived change the stream is trying to cause. |
| Initiative | A chunk of a goal that can move through shaping into active work. |
| Feature, story | Delivery work. A story belongs to a feature. |
| Platform item | Technical work that makes delivery possible. |
| Prototype, experiment | Learning work. It usually stops once the question is answered. |
| Planning cycle | A dated span, six weeks unless the group chooses otherwise. |
| Alignment | The short shared session at the start of a cycle: outcomes, dependencies, risks, confidence. |
| Evidence review | The session at each iteration boundary: what we observed, what we will change. |
| Delivery path | Discover, Define, Build, Check, Ship. |

Roles a local user can assign: stream owner, group facilitator, product manager, product owner, scrum master, technical lead, business stakeholder, team member. A person can hold more than one at the same time. A small shop can put product owner and scrum master on the same product manager, and can put group facilitator on that person too.

The roles do not merge. Each task requires one acting role. The app asks the person to switch to that role before the task is saved. Backlog acceptance stays a product-owner task. The team sync and the retrospective stay scrum-master tasks. Managing the delivery group stays a facilitator task. Opting out of the group leaves a placeholder and turns the facilitator tasks off. The team process is unchanged. An agent is an actor on a change, not a job title.

Define is not finished until a person approves the bounded intent. Check cannot be signed by the same actor who produced the change. Ship is a separate human decision. Prototypes and experiments stay in Check unless someone deliberately ships them.

## Decisions

| Topic | Earlier draft | This plan |
| --- | --- | --- |
| UI | A React app with separate role dashboards | FastAPI, Jinja, HTMX, and Alpine.js. One local process, no Node build. |
| API | Python FastAPI and Pydantic | Keep. Python owns pages and the domain model. |
| Engine | A Rust sidecar for tokens, tenant walls, and priority math | Defer. Priority math is arithmetic. Rust waits for a measured slow path. |
| Database | PostgreSQL or MySQL through a Rust ORM | SQLite on a laptop. Epic 14 swaps in PostgreSQL, SQL Server, Oracle, or another SQL database through an adapter. |
| Identity | Cloud directories built into the product | Local login and JWT in the product. Roles stay in our database. Azure AD and AWS IAM are adapters a shop writes. Epic 15. |
| Packaging | One image containing a JavaScript build, Python, and Rust | Package later, after there is an app to package. |
| Work hierarchy | Theme, large epic, feature, story, plus a technical type tied to one framework | Goal, initiative, feature, story, platform item, prototype, and experiment. |
| Planning | A multi-day planning event and a branded risk acronym | One alignment session per cycle, a few hours of outcomes, dependencies, and risks. Dependent work, an architecture review, and a PII review are written only when they apply. |
| Learning | A private retro plus a branded train-level workshop | Private team retro. Delivery-group evidence review every iteration. |
| Priority and flow | A branded score and a branded set of six metrics | Delay-cost score, plus throughput, lead time, work in progress, active versus wait, work mix, and outcome reliability. A team sizes stories with t-shirt sizes or points, and velocity is the size completed in an iteration. |
| Agents in the product | Assistants that scan, split, score, and classify | A shop's own tool pushes proposals in and takes stories out. This product does not call the model or open their repository. Epic 19. In-product helpers stay epic 13. |
| Governance | Ethics flags on the side of the workflow | Approval on Define, independent Check, human Ship, and an evidence log. |
| Coordination | A required train and a dedicated coordinator | The delivery group may be a placeholder. Facilitator, product owner, and scrum master can sit on one person. Each task still requires its own acting role. Epic 16. |
| Agent research | Separate research programs and a training course | One timeboxed research item with three questions. No data means the feature does not enter Build. A tutorial and a PDF teach that. Epic 17. |
| Agent release | A runtime that scores agents and hosts their tools | The tool stores the release gates and blocks Ship when they are empty. Epic 18. |

## How to use this plan

1. Read an epic here for outcome and order.
2. Open that epic's file and add stories there when we break the epic down.
3. A story is done only when it can be exercised on localhost, through the UI or an API test, with no cloud account.

Build 01, then 02, then 03, then 04 through 08, then 14, then 16, then 09, then 10, then 17, then 18, then 19, then 15. Epic 08 moves the tables already created onto SQLAlchemy and Pydantic before later epics add rows. Epic 14 then swaps the database through those models, and epic 16 adds dual-role rules on the same models. That order keeps SQLite and a single role available early, makes the structure easy to move through before the cycle, and adds the research gate, the agent release gates, and the outside-tool plugin only after the backlog they write to exists. Epics 11–13 stay written down so they are not mixed into the first build.

## Build epics

### 01 — Local foundation

A single local process serves pages and an API against a SQLite file, with one admin user. Later epics add behavior to this shell.

- File: [epics/01-local-foundation.md](epics/01-local-foundation.md)
- Depends on: nothing

### 02 — Organization and roles

Portfolio, value stream, delivery group, and team exist as records. People can be assigned the roles in the table above.

- File: [epics/02-organization-and-roles.md](epics/02-organization-and-roles.md)
- Depends on: 01

### 03 — Navigation

The portfolio, value stream, delivery group, and team stay on screen in a full-width shell. A breadcrumb shows the full chain, each empty record offers the next record, and job seats stay separate from who may see or change a record.

- File: [epics/03-navigation.md](epics/03-navigation.md)
- Depends on: 02

### 04 — Work model

Goals, initiatives, features, and stories can be created and linked. Initiatives move through Proposed, Shaping, Ready, Active, and Done. Features and stories also record a kind: feature, platform, prototype, or experiment.

- File: [epics/04-work-model.md](epics/04-work-model.md)
- Depends on: 02

### 05 — Delivery path

Each work item sits in Discover, Define, Build, Check, or Ship. Define stores a human approval. Check stores an independent checker. Learning items stay out of Ship unless a person chooses to ship them.

- File: [epics/05-delivery-path.md](epics/05-delivery-path.md)
- Depends on: 04

### 06 — Cycle alignment

A delivery group can open a planning cycle, commit group and team outcomes, and record milestones, dependencies, risks, and a confidence check. Dependent work, an architecture review, and a PII review are added only when that work needs them. The providing team may be left unnamed.

- File: [epics/06-cycle-alignment.md](epics/06-cycle-alignment.md)
- Depends on: 02, 04

### 07 — Team execution

A team can run an iteration board, a short sync, and a retrospective that stays on that team.

- File: [epics/07-team-execution.md](epics/07-team-execution.md)
- Depends on: 04, 06

### 08 — Evidence review

Each iteration boundary has a delivery-group session: observations in, decisions out. Decisions can continue, drop, reshape, or resize work. Private retro text stays out unless the team promotes a learning. The iteration board, the features, and the planning cycle of a group are visible only to someone who belongs to that group. One group may hold several projects. The entity diagram records that those three stay inside one project. It does not yet say how the project attaches to the group.

- File: [epics/08-evidence-review.md](epics/08-evidence-review.md)
- Depends on: 05, 06, 07. The first stories also cover tables from 01 through 07.

### 09 — Flow and priority

A delay-cost score sorts the backlog. Throughput, lead time, work in progress, active versus wait, work mix, and outcome reliability render from dates and states already stored. Team velocity is the story size completed in an iteration.

- File: [epics/09-flow-and-priority.md](epics/09-flow-and-priority.md)
- Depends on: 04, 05, 06, 08

### 10 — Governance and evidence

Policies can block a transition. Every change records a person or an agent. Acceptance criteria can carry a threshold, a dataset label, and a latency target.

- File: [epics/10-governance-and-evidence.md](epics/10-governance-and-evidence.md)
- Depends on: 05, 08

### 14 — Database adapters

The app stores data through one adapter. SQLite is the local default. A shop can switch the connection to PostgreSQL, SQL Server, Oracle, or another SQL database it adds the same way.

- File: [epics/14-database-adapters.md](epics/14-database-adapters.md)
- Depends on: 01, 08

### 15 — Auth extension

Local login and JWT are built in. Permission checks read roles from our database. A shop can overwrite the authenticator, including with its own Azure AD or AWS IAM code. Those directories are not features we ship.

- File: [epics/15-auth-extension.md](epics/15-auth-extension.md)
- Depends on: 01, 02, 08, 16

### 16 — Optional coordination and dual roles

Two small teams can use a placeholder delivery group and leave the facilitator seat empty. A product manager can also be product owner and scrum master. Each task asks them to act as the one role that task belongs to. Operator docs cover the setup.

- File: [epics/16-optional-coordination.md](epics/16-optional-coordination.md)
- Depends on: 02, 08

### 17 — Timeboxed research and the product-manager guide

Prompt trials, deeper-agent trials, and data checks are one research item with a clock and a required decision. A feature that needs data cannot enter Build without a passing data check. A short in-app tutorial and a PDF, from the same guide, show a product manager why.

- File: [epics/17-research-and-guide.md](epics/17-research-and-guide.md)
- Depends on: 04, 05, 07, 08, 16

### 18 — Agent release controls

An agent feature records a risk tier, the tools it may call, a held-out eval reference, who can stop it, and a rollback drill. Ship waits on those. A prompt or model change returns it to Check. An incident marks the agent advisory and adds an eval case.

- File: [epics/18-agent-release-controls.md](epics/18-agent-release-controls.md)
- Depends on: 05, 08, 10, 17

### 19 — Bring your own tool

A shop's own Cursor, Claude, or other tool can submit meeting notes and documents as proposed initiatives. The product owner accepts them. A story pack can be exported for that shop's developers. This product does not call the model, and their code repository stays outside.

- File: [epics/19-bring-your-own-tool.md](epics/19-bring-your-own-tool.md)
- Depends on: 04, 08, 10, 16

## Future epics

These files exist so the scope stays visible. Do not pull their stories into the first build.

### 11 — Portfolio investment

Funding guardrails on a value stream, and a workshop record that feeds an investment review.

- File: [epics/11-portfolio-investment.md](epics/11-portfolio-investment.md)
- Depends on: 02, 04, 08

### 12 — Engine and packaging

A Rust worker only for a path that Python cannot meet, then a container image of whatever the app actually is.

- File: [epics/12-engine-and-packaging.md](epics/12-engine-and-packaging.md)
- Depends on: 01, 08, 09

### 13 — Planning assistants

Helpers that draft dependencies, feature splits, priority inputs, risk states, and flow warnings. A person accepts or discards each draft. Epic 10 records the helper as an agent.

- File: [epics/13-planning-assistants.md](epics/13-planning-assistants.md)
- Depends on: 06, 08, 09, 10
