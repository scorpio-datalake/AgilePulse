# How to create the sample organization

This walkthrough builds the same organization the sample script loads: two portfolios, the warehouse and checkout value streams, three teams, and the people who work on them. You can click through it, or load it in one step.

An admin opens portfolios and value streams. A product manager, product owner, or scrum master places people from the organization onto a team and chooses their seat. A developer lands on the projects and sprints they belong to.

## Load it with the script

From the project directory, with the app's virtualenv active:

```bash
python -m app.sample_data
```

That writes `data/scaled_engine.sqlite`, which is the database the app uses when `SCALED_ENGINE_DB` is unset. To write a different file:

```bash
python -m app.sample_data path/to/scaled_engine.sqlite
```

Run it once. If **Supply chain** is already in that file, the script stops so it does not add the same people again.

Start the app, then sign in with one of these accounts.

| Person | Username | Password | What the home page is for |
| --- | --- | --- | --- |
| Admin | `admin` | `admin` | Every portfolio, with its value streams. Create portfolio is on this page. |
| Nia Chen | `nia` | `sample` | Product manager. Crew page for both warehouse teams. |
| Owen Park | `owen` | `sample` | Product owner. Crew page for Build crew. |
| Sam Reed | `sam` | `sample` | Scrum master. Crew page for Build crew. |
| Dev Patel | `dev` | `sample` | Developer. Build crew is the current project. Model crew is a past project. |
| Lea Ortiz | `lea` | `sample` | Developer. Checkout crew only. |

Rio Alvarez is in the organization and has no seat yet. Owen, Nia, or Sam can put Rio on a team.

The script dates sprints from the day you run it:

| Record | When |
| --- | --- |
| Discovery of the AI models, on Optimization of the warehouse | 80 days ago through 36 days ago |
| Sprint 1, on Model crew, inside that cycle | 80 days ago through 50 days ago |
| Warehouse pick optimization, on Optimization of the warehouse | 28 days ago through 28 days from today |
| Picker week, on Build crew | 28 days ago through 8 days ago |
| Sprint 2, on Build crew | 4 days ago through 10 days from today |
| Checkout cycle and Lane week | 90 days ago through 40 days from today, and yesterday through 10 days from today |

## Or create the same records yourself

Sign in as `admin` / `admin`. The home page is the portfolio list. **Create portfolio** is only on that page for an admin.

### 1. Portfolios and value streams

1. Create portfolio **Supply chain**.
2. On that portfolio, **Add value stream** **Warehouse fulfillment**.
3. Back on Home, create portfolio **Storefront**.
4. Add value stream **Checkout experience**.

A product owner, product manager, scrum master, or developer does not get **Add value stream**. If they post one anyway, the app refuses it.

### 2. Delivery groups and teams

Open **Warehouse fulfillment**.

1. **Add delivery group** **Optimization of the warehouse**.
2. On that group, **Add team** **Build crew**.
3. Add a second team, **Model crew**.

Open **Checkout experience**.

1. Add delivery group **Lane redesign**.
2. Add team **Checkout crew**.

### 3. People and seats

Open **People**. For each person, set the name, the role, and the team or delivery group in the table below, then **Add person**.

| Name | Role | Place |
| --- | --- | --- |
| Nia Chen | Product manager | Delivery group Optimization of the warehouse. Also add Nia on that group's Overview tab with **Add to delivery group**. |
| Owen Park | Product owner | Team Build crew |
| Sam Reed | Scrum master | Team Build crew |
| Dev Patel | Team member | Team Build crew. Then open Model crew and **Add to team** Dev Patel, so Dev belongs to both projects. |
| Lea Ortiz | Technical lead | Team Checkout crew |
| Rio Alvarez | Team member | Leave the team as **None**. Rio stays unseated until a product owner, product manager, or scrum master places them. |

The People form creates the person and the seat. It does not create a sign-in. The sample script does. Hand-built people are visible to an admin and to the crew leads who share a team or group with them. To sign in as those people you need the script, which attaches the usernames in the table above.

### 4. The work the board will show

The team **Board** stays at 0 until a story is estimated for that team. The delivery-group **Board** is the warehouse optimization board: it lists features for the value stream and stories for the teams in **Optimization of the warehouse**.

Open **Warehouse fulfillment**.

1. **Add goal** **Fewer walking miles**.
2. On that goal, **Add initiative** **Slot the picks**. Set the state to **Active** and **Save state**.
3. Add a second initiative, **Choose the pick model**, and set it to **Active**.
4. On **Slot the picks**, add three features:
   - **Pick path**, kind Feature
   - **Aisle map**, kind Platform
   - **Which aisle first**, kind Experiment
5. On **Choose the pick model**, add **Travel-time model**, kind Experiment.

Move the features along the delivery path. On each feature, **Stage**, choose the person and **Save stage**. Use a developer for Discover and Define. **Build** is refused until you **Approve definition** as that same person. **Check** is refused for the person who moved it into Build, so choose someone else, such as a tester. Before Check, open **Done list**, mark every box, and **Save done list**.

| Feature | Stop at |
| --- | --- |
| Which aisle first | Discover |
| Aisle map | Define |
| Pick path | Build |
| Travel-time model | Check |

On **Pick path**, under **Acceptance criteria**, type the measure **Miles per pick**, the threshold **Lower than the week before the cycle**, the dataset **A full picker shift**, and the latency target **Route chosen before the picker walks**. **Save acceptance criteria**.

Add the stories below. On each story, **Estimate** for the team in the table, T-shirt size **M**, and **Save estimate**. That is what places the story on that team's board. Then save the acceptance criteria from the table, and move the stage the same way as a feature. A story that is still in Discover does not need an approval.

| Story | Feature | Team | Stage |
| --- | --- | --- | --- |
| Write the model card | Travel-time model | Model crew | Discover |
| Label a week of pick paths | Travel-time model | Model crew | Define |
| Score the nearest-aisle baseline | Travel-time model | Model crew | Build |
| Compare travel-time models | Travel-time model | Model crew | Check |
| Print the slot label | Pick path | Build crew | Discover |
| Show the next bin | Pick path | Build crew | Define |
| Confirm the pick | Pick path | Build crew | Build |
| Warn when the aisle is blocked | Pick path | Build crew | Check |
| Record the walking miles | Pick path | Build crew | Ship |

Acceptance criteria to type on each story:

| Story | Measure | Threshold | Dataset | Latency target |
| --- | --- | --- | --- | --- |
| Write the model card | Model card sections | Data, metric, and limit filled in | The chosen model | Not timed |
| Label a week of pick paths | Labeled routes | At least 200 routes | Pick paths from last week | Not timed |
| Score the nearest-aisle baseline | Baseline miles per pick | Recorded for the same week | Completed picks | Batch finishes overnight |
| Compare travel-time models | Walk-time error | Under 0.4 minutes | One week of completed picks | Score a route in under 50 ms |
| Print the slot label | Label reads the slot | Matches the bin the model chose | A test pick | Shown before the picker walks |
| Show the next bin | Next bin on the screen | The bin the model named | One pick | Under 1 second |
| Confirm the pick | Confirmed picks | The package in hand matches the bin | A test aisle | Under 1 second |
| Warn when the aisle is blocked | Blocked-aisle warning | Shown before the picker enters | A closed aisle | Under 1 second |
| Record the walking miles | Miles per pick | Lower than last week | A full shift | Recorded at the end of the pick |

**Compare travel-time models** is kind Experiment. Leave it in Check. An experiment does not use the normal Ship stage. **Record the walking miles** is kind Feature, so after Check you can choose Ship.

Open **Model crew**, **Board**. Write the model card is under Discover, Label a week of pick paths under Define, Score the nearest-aisle baseline under Build, and Compare travel-time models under Check.

Open **Build crew**, **Board**. One story sits in each column: Print the slot label, Show the next bin, Confirm the pick, Warn when the aisle is blocked, and Record the walking miles.

Open **Optimization of the warehouse**, **Board**. That is the warehouse optimization board. Pick path is under Build, Aisle map under Define, Which aisle first under Discover, and Travel-time model under Check. The stories from both teams are in those same columns.

### 5. Two cycles and Sprint 1

A cycle is opened on the delivery group, not on the team. Until that exists, the **Cycle** menu on a team Planning tab is empty. An iteration's start and end have to fall inside the cycle you select.

Open **Optimization of the warehouse**, **Planning**.

1. **Open cycle** **Discovery of the AI models**. Start 80 days ago. End 36 days ago.
2. **Open cycle** **Warehouse pick optimization**. Start 28 days ago. End 28 days from today.

Open the discovery cycle.

1. **Add outcome** **A pick model is chosen**. Planned signal **One model card accepted**. Choose Model crew when the form asks for a team.
2. On **Warehouse pick optimization**, **Add outcome** **Fewer walking miles**. Planned signal **Miles per pick down**. Leave the team blank if the form allows it. This outcome is for the whole group.
3. **Add milestone** **Picker screen ready** on the day Sprint 2 ends, 10 days from today.

Open **Model crew**, **Planning**. The Cycle menu now lists **Discovery of the AI models**. **Open iteration** **Sprint 1**. Start 80 days ago. End 50 days ago. On Sprint 1, **Add to iteration** as the product owner: Compare travel-time models, Label a week of pick paths, and Score the nearest-aisle baseline.

Open **Build crew**, **Planning**.

1. Set the work-in-progress limit to **3** and **Save limit**.
2. **Save sizing** with Method **T-shirt** and XS 1, S 2, M 3, L 5, XL 8.
3. **Open iteration** **Picker week** on **Warehouse pick optimization**. Start 28 days ago. End 8 days ago. Add **Record the walking miles**.
4. **Open iteration** **Sprint 2** on the same cycle. Start 4 days ago. End 10 days from today. Add **Show the next bin**, **Confirm the pick**, and **Warn when the aisle is blocked**.

If you also have the checkout group, open **Lane redesign**, **Planning**, **Open cycle** **Checkout cycle** from 90 days ago through 40 days from today, then on **Checkout crew** open **Lane week** from yesterday through 10 days from today.

### Sprint columns, a backlog, and later sprints

The sample script does not create these. You add them on the sprint page. No one seat can do every step. Sign in as `admin` / `admin` so you can open the pages, and choose the person named below in each form.

| Step | Person you select | Seat |
| --- | --- | --- |
| Add a story, estimate it, and open an iteration | Anyone who can edit. Admin can. | No seat on the team |
| Add a story to a sprint | Owen Park | Product owner on that team |
| Add, rename, reorder, or remove a column | Nia Chen, Owen Park, or Sam Reed | Product manager for the delivery group, or product owner or scrum master on that team |
| Drag a story into a column, or use **Move** | Anyone who can edit. Admin can. | No seat |

A developer such as Dev can move cards on a sprint he can open. He cannot add a story to the sprint, and he cannot change the columns, unless the form is signed as Owen, Nia, or Sam. One person cannot hold product manager, product owner, and scrum master at the same time.

Open **Build crew**, **Planning**, **Sprint 2**. That sprint includes today. Under **Columns**, change the six starting columns to these five. For each save or remove, set **Editor** to Owen Park. Remove a column only after its stories have been moved out.

| Order | Name | Color |
| --- | --- | --- |
| 1 | Ready | `#6b6e76` |
| 2 | Building | `#0c66e4` |
| 3 | Review | `#e56910` |
| 4 | Testing | `#8270db` |
| 5 | Done | `#22a06b` |

**Add column** uses the same editor. **Save column** keeps a rename. The same five columns then appear on every Build crew sprint, including ones that have not started.

On **Pick path**, **Add story** for each name below, then on the story **Estimate** for **Build crew**, T-shirt **M**, **Save estimate**. Back on Sprint 2, **Add to iteration** and choose Owen Park as the product owner. Drag the card into the column, or choose the column and **Move**.

| Story | Column on Sprint 2 |
| --- | --- |
| Show the next bin | Ready |
| Scan the bin barcode | Ready |
| Confirm the pick | Building |
| Skip a damaged slot | Building |
| Warn when the aisle is blocked | Review |
| Show the picker their pace | Testing |
| Mark the pick complete | Done |

Each column should have at least one card. The card shows the story name, the estimate, and the delivery-path stage. It does not show a person. The sprint board does not store who the story is assigned to.

Leave these three estimated for Build crew and do not add them to a sprint: **Reprint a torn label**, **Count empty slots at end of shift**, and **Flag a short pick**. There is no backlog page. They stay in the **Story** menu under **Add to iteration** until a product owner adds one.

Later sprints are more iterations inside the same cycle. On **Build crew**, **Planning**, **Open iteration** on **Warehouse pick optimization**:

| Iteration | Start | End | Stories, left in Ready |
| --- | --- | --- | --- |
| Sprint 3 | The day after Sprint 2 ends | Eight days later | Highlight the next aisle, Confirm the tote is closed |
| Sprint 4 | The day after Sprint 3 ends | The day the cycle ends | Log a missed scan, Show yesterday's miles |

Add those four stories the same way, estimate them for Build crew, and add them to the matching sprint as Owen Park. A sprint that has not started is only another row on **Planning**. The home page for a developer still calls the sprint that contains today the current sprint.

On the delivery group **Board** tab you can save a policy: from **Define**, into **Build**, effect **Warning**. That does not add a card. It only warns when something moves between those stages.

### 6. Coordination notes

Open Build crew, **Coordination**. Sign the notes as Sam Reed, the scrum master.

1. **Save sync note**. Date two days ago. Note: `Labels are still being printed`.
2. **Save cross-team note**. Impediment: `Need the slot feed`. Dependency: `Model crew publishes the feed`. Asked team: Model crew.
3. **Save retro note** on Picker week: `The aisle labels are hard to read`.

## What each home page shows

Sign out between accounts.

**Admin.** Home lists Supply chain and Storefront. Under Supply chain is Warehouse fulfillment. Under Storefront is Checkout experience. **Create portfolio** is on this page. Open a portfolio to add another value stream.

**Nia, Owen, or Sam.** Home is **Crew**. Pick a person, a team they are allowed to staff, and a seat: team member, product owner, scrum master, or technical lead. **Add to team**. They do not get **Create portfolio** or **Add value stream**.

Try it: sign in as `owen` / `sample`, choose Rio Alvarez, Build crew, and Team member.

Nia can staff Build crew and Model crew. Owen and Sam can staff Build crew.

**Dev.** Home is **Your work**: 2 projects and 3 sprints. The current project is Build crew, the current sprint is Sprint 2, the past sprint on that project is Picker week, and the past project is Model crew. Sprint 1 is the discovery sprint on Model crew.

**Lea.** Home is Checkout crew, current sprint Lane week, and no other project.

Open Build crew after loading the sample and switch **Overview**, **Board**, **Planning**, and **Coordination**. Each tab is one kind of work instead of one long page.
