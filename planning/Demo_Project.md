# Demo project — Optimization of the warehouse

The work is an optimization model that schedules package picks from where each package sits in the warehouse.

## What epic 2 includes

Sign in as `admin` / `admin`. That user creates every record below. The People page stores a name. It does not store a username or a password, and nobody except `admin` can sign in. Testing keeps that password. A final install makes the first sign-in replace it and add a user before the home page.

You can create and edit:

- One portfolio, then a value stream on it, a delivery group on that stream, and a team on that group.
- People. `Admin` is already on the list.
- Membership of a person on a team or on a delivery group.
- One role per person, on the record that role belongs to.

Roles you can assign: stream owner, group facilitator, product manager, product owner, scrum master, technical lead, business stakeholder, team member. Product owner and scrum master are two different people. A delivery group saves with the facilitator seat empty.

Developer, tester, SRE, MLE, warehouse manager, and production support are jobs. They are not roles in the product. Those people get one of the roles above, usually team member.

## What you are testing

1. Sign in as `admin` / `admin`.
2. Create the portfolio, the value stream, the delivery group, and both teams, in that order.
3. Add each person by the name in the roster.
4. Add the memberships.
5. Assign each role on the page named in the roster.
6. Leave the facilitator seat empty on the first save, reload, and see "Facilitator seat is empty." Then assign the facilitator.
7. Reload the browser. The same portfolio, stream, group, teams, members, and roles are still there.
8. On the Build crew, assign Scrum master to `po1`. That is refused. `po1` already has Product owner.
9. On the Build crew, assign Stream owner to `dev1` and send it with the team. That is refused. Stream owner sits on the value stream.

You are not testing a second sign-in, a password, Azure AD, or a rule that blocks a developer from creating a portfolio. Those are epic 15. This build lets `admin` create all of it.

## What to create

One portfolio. Supply chain is the set of value streams this organization funds. A second portfolio named Supply chain dev, or Supply chain business, would split one funded outcome into departments. Developers, warehouse managers, SREs, and production support who serve this outcome sit under this portfolio.

| Record | Name to type | Where it sits |
| --- | --- | --- |
| Portfolio | Supply chain | Home |
| Value stream | Warehouse fulfillment | On Supply chain |
| Delivery group | Optimization of the warehouse | On Warehouse fulfillment |
| Team | Build crew | On Optimization of the warehouse |
| Team | Model crew | On Optimization of the warehouse |

Warehouse fulfillment is the customer outcome: the model chooses which package to pick, and when, from the location in the warehouse. Optimization of the warehouse is the project name. It is the delivery group because these teams share that product and one planning cycle.

One delivery group. Do not add a group for SREs, a group for warehouse managers, or a group for production support. A separate team is for a crew that pulls its own iteration. Here the app changes and the model changes are two crews. The SREs and the production-support person ship with the Build crew, so they are members of that team. The warehouse manager attends the delivery group as a business stakeholder and does not need a team.

## Roster

Type the name on People. Assign the role on the page in the last column. Add the membership on that same team or group.

| Name to type | Job | Role | Assign on | Member of |
| --- | --- | --- | --- | --- |
| stream1 | Stream lead | Stream owner | Warehouse fulfillment | |
| fac1 | Facilitator | Group facilitator | Optimization of the warehouse | Optimization of the warehouse |
| pm1 | Product manager | Product manager | Optimization of the warehouse | |
| wh1 | Warehouse manager | Business stakeholder | Optimization of the warehouse | Optimization of the warehouse |
| po1 | Product owner | Product owner | Build crew | Build crew |
| sm1 | Scrum master | Scrum master | Build crew | Build crew |
| dev1 | Developer | Team member | Build crew | Build crew |
| dev2 | Developer | Team member | Build crew | Build crew |
| dev3 | Developer | Team member | Build crew | Build crew |
| test1 | Tester | Team member | Build crew | Build crew |
| test2 | Tester | Team member | Build crew | Build crew |
| sre1 | SRE | Team member | Build crew | Build crew |
| sre2 | SRE | Team member | Build crew | Build crew |
| ps1 | Production support | Team member | Build crew | Build crew |
| mle1 | MLE | Technical lead | Model crew | Model crew |
| mle2 | MLE | Team member | Model crew | Model crew |

Leave `Admin` with no role. That is the local user who is setting the shop up.

Skip `fac1` on the first save if you want to see the empty facilitator seat. Add that role after the reload.

## Usernames and passwords

Epic 2 will not accept these. Only `admin` / `admin` can sign in during this test. The list is the roster to use when epic 15 adds a login per person. The password is the same as the username.

| Username | Password | Person name in this demo |
| --- | --- | --- |
| admin | admin | Admin |
| stream1 | stream1 | stream1 |
| fac1 | fac1 | fac1 |
| pm1 | pm1 | pm1 |
| wh1 | wh1 | wh1 |
| po1 | po1 | po1 |
| sm1 | sm1 | sm1 |
| dev1 | dev1 | dev1 |
| dev2 | dev2 | dev2 |
| dev3 | dev3 | dev3 |
| test1 | test1 | test1 |
| test2 | test2 | test2 |
| sre1 | sre1 | sre1 |
| sre2 | sre2 | sre2 |
| ps1 | ps1 | ps1 |
| mle1 | mle1 | mle1 |
| mle2 | mle2 | mle2 |

## Later, not this epic

Who may create a portfolio, a delivery group, or a team is a permission. Epic 15 reads that permission from a role stored in this app. A product manager, and a few admins, can hold it. A developer does not, unless an admin grants it. Epic 2 has no such check.

The box ships with one local admin, `admin`. That person creates the portfolio and assigns the product manager and the other admins. The shop types the rest of the people on the People page. A directory is optional and comes later.

Azure AD is not in the product. Epic 15 lets a shop replace sign-in with its own code, including Entra ID or AWS IAM. That code may find or create the person. It does not grant the right to create a portfolio. Those grants stay in our role rows. A modern tool does the same: the first admin is local, sign-in can later move to the company directory, and creating a project stays a permission inside the tool.

## What epic 4 includes

Finish the epic 2 shop first. Sign in as `admin` / `admin`. Restart the app once before this pass so the work tables are created. Stay on that same database.

This pass adds the backlog the warehouse group plans against. The goal lasts longer than one cycle. The initiative is the chunk that gets shaped and then built. Features and stories are the slices. A platform item is technical work under that initiative. An experiment answers a question and is usually not shipped.

You can create and edit:

- A goal on Warehouse fulfillment, and its name.
- An initiative on that goal. A new one is Proposed. The page can move it to Shaping, Ready, Active, or Done.
- A feature on that initiative, with kind Feature, Platform, Prototype, or Experiment.
- A story on a feature, with the same kinds.
- Four priority numbers on a feature: value of doing it sooner, urgency, risk or opportunity, and size. The page stores them. It does not show a score.
- The sizing method on Build crew: T-shirt or Points. T-shirt starts at XS 1, S 2, M 3, L 5, XL 8. A story estimate follows the method the team has when you save it.

## What you are testing

1. Open **Warehouse fulfillment**. Under **Goals**, click **Add goal** with the name left blank. The page says "A name is required."
2. Add the goal **Fewer walking miles**. Open it, change the name, click **Save goal**, reload, and see the new name. Go back to the value stream and see that goal in the list.
3. On the goal, add the initiative **Slot the picks**. The page says **Proposed**. Leave the name blank and click **Save initiative**. The page says "A name is required."
4. Set State to **Shaping** and click **Save state**. Reload. The page still says **Shaping**. The goal lists this initiative with that state.
5. On the initiative, add **Pick path** with kind Feature, **Aisle map** with kind Platform, and **Which aisle first** with kind Experiment. Reload the initiative. All three names are listed with those kinds.
6. On **Pick path**, add the story **Show the next bin** with kind Feature. Change the name, click **Save story**, reload, and see the story still under that feature.
7. On the story, use the breadcrumb. Open **Pick path**, then **Slot the picks**, then **Fewer walking miles**, then **Warehouse fulfillment**, then **Supply chain**. Each parent lists the child you just left.
8. On **Pick path**, under **Priority**, enter value of doing it sooner `5`, urgency `3`, risk or opportunity `2`, and size `4`. Click **Save priority**. Reload and see those four numbers. There is no score on the page. Change size to `0`, save, and see "Those priority numbers were refused."
9. Open **Build crew**. Under **Sizing**, leave Method on **T-shirt** and the numbers at `1`, `2`, `3`, `5`, `8`. Click **Save sizing**.
10. On **Show the next bin**, under **Estimate**, choose **Optimization of the warehouse / Build crew (tshirt)** and T-shirt size **M**. Click **Save estimate**. The story reads **Estimate: M is 3**.
11. On **Build crew**, switch Method to **Points** and click **Save sizing**. The numbers can stay as they are.
12. On **Pick path**, add the story **Confirm the pick**. On that story, choose Build crew, type Points `5`, and click **Save estimate**. The story reads **Estimate: 5**.
13. Reload **Show the next bin**. It still reads **Estimate: M is 3**.

A missing parent, a state outside the list, and a kind outside the list are refused by the server. The forms on these pages always send a parent and only offer the allowed states and kinds, so those three refusals are in `tests/test_work.py`. Run `uv run pytest` when you want that check. It uses a temporary database and does not open a browser.

## What to create

| Record | Name to type | Kind or state | Where it sits |
| --- | --- | --- | --- |
| Goal | Fewer walking miles | | Warehouse fulfillment |
| Initiative | Slot the picks | Shaping, after it starts as Proposed | Fewer walking miles |
| Feature | Pick path | Feature | Slot the picks |
| Feature | Aisle map | Platform | Slot the picks |
| Feature | Which aisle first | Experiment | Slot the picks |
| Story | Show the next bin | Feature, estimate M on Build crew while the team is T-shirt | Pick path |
| Story | Confirm the pick | Feature, estimate 5 after Build crew is Points | Pick path |

Pick path is the picker walking a shorter route. Aisle map is the location data that route needs. Which aisle first is the experiment that asks whether the model should prefer the nearest aisle. Show the next bin is the screen the picker uses. Confirm the pick is the confirmation after the package is in hand.

On Pick path, the priority numbers are 5, 3, 2, and 4. Size here is the economic size of the feature. It is separate from the story estimate.

## What epic 5 includes

Restart the app once so the delivery-path tables exist. Stay signed in as `admin` / `admin`. Use the epic 4 records. Add `dev1` and `test1` on People as team members of Build crew. The stage form asks which person is acting. That person does not sign in.

## What you are testing

1. On **Pick path**, under **Stage**, choose Define and dev1. Click **Save stage**. Reload. The stage is Define, and the history names dev1, Discover, and Define.
2. Choose Build and save. The page says "Build needs an approved definition." Click **Approve definition** as dev1, then save Build. Reload and see Build.
3. Choose Check as dev1 and save. The page says "The person who built this cannot complete Check."
4. Under **Done list**, mark integrated, acceptance, and no open dependency. Leave the rollback note open. Save, then try Check as test1. It is refused. Mark the rollback note too, save, and Check as test1 succeeds.
5. Set **Architecture review** to Applies and save the path flags. Try Check again as test1. It is refused. Set it back to Not applicable when you want Check clear again.
6. On **Which aisle first**, move it to Check the same way, with test1 completing Check. dev1 cannot. Choose Ship on the stage control. The page says "A prototype or experiment stays in Check." Click **Ship this learning item**. The stage is Ship.
7. On **Aisle map**, approve the definition, move it to Build, then change the name and click **Save feature**. The stage is Check, and the history records the return.
8. On **Show the next bin**, save the stage Define. Open Build crew and Optimization of the warehouse. Under **Delivery path**, that story is listed under Define. Pick path is listed under its own stage on the group page.

## What epic 6 includes

The facilitator seat can stay empty. A cycle does not need that seat. A decision on the cycle does.

## What you are testing

1. On **Optimization of the warehouse**, under **Planning cycles**, open **Warehouse cycle** from `2026-10-05` to `2026-11-16`. Reload the group and see the cycle. Open it. There is no **Save decision** button.
2. Add a group outcome **Fewer walking miles** with planned signal **Miles per pick down**. Add a Build crew outcome **Build crew finishes the picker screen** with planned signal **Screen in use**. Link **Pick path** to the group outcome. Reload and see the feature under that outcome.
3. Add milestone **Picker screen ready** on `2026-10-30`.
4. Add a dependency **Slot map from the warehouse**, owner po1, needed `2026-10-20`, opened `2026-10-06`, and leave the providing team blank. Reload and see the opened date.
5. Add dependent work **Firewall change** for Pick path and leave the team blank. Add **Database change** and choose Model crew. The list shows both. A new cycle that you do not add work to has no dependent-work list.
6. On Pick path, set Architecture review to Applies. On Which aisle first, set PII review to Applies. Leave Aisle map on Not applicable. On the cycle, save an architecture review for Pick path and a PII review for Which aisle first. Aisle map is in neither review line.
7. Add risk **Slot data arrives late**, then set its state to owned and save. Reload and see owned.
8. Save confidence 5 for po1 and 3 for Admin. The page says **Average: 4**. Save a capacity note for Build crew and see it on the cycle.
9. Add `fac1` as group facilitator on the delivery group. Save the decision **Keep the picker screen in this cycle** as fac1. The line says acting as group_facilitator. Save the same decision as po1 and see "That action needs the group facilitator."

## What epic 7 includes

Set Build crew back to T-shirt before estimating, so M still means 3. Add `po1` as product owner and `sm1` as scrum master on Build crew, and `mle1` as a team member on Model crew. One person holding both product owner and scrum master is epic 16.

## What you are testing

1. On Build crew, under **Iterations**, open **Picker week** on Warehouse cycle from `2026-10-05` to `2026-10-16`. Try an end date after the cycle and see "That iteration is outside the cycle."
2. Estimate **Show the next bin** and **Confirm the pick** as M on Build crew. On the iteration, add Show the next bin as po1. The row shows 3. Add it as sm1 and see "That action needs the product owner." Accept the story as po1. The page says **Completed size: 3**.
3. Move Show the next bin to Define. On the iteration, under **Board**, it is listed under Define.
4. On Build crew, set the work-in-progress limit to 1. Approve both stories and move Show the next bin to Build. Move Confirm the pick to Build and see "The board is at its limit." On the iteration, raise the limit for Confirm the pick as sm1 with the reason **The dock is blocked**. Move that story to Build. It enters Build.
5. Save a sync note **Labels are still being printed** on `2026-10-06` as sm1. Save it as po1 and see it refused. Save a cross-team note **Need the slot feed** that asks Model crew.
6. Save a retro note **The aisle labels are hard to read** on Picker week as sm1. It is on the Build crew page. Promote **Label the aisles before the next pick test**.
7. Open Model crew. The sync note, the impediment, and the promoted line are there. The raw retro sentence is not. You are still admin on this pass, and admin can see a retro by opening Build crew. The member view is the one in `tests/test_flow.py`.
