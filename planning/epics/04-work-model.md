# Epic 04 — Work model

Status: done

## Outcome

A local user can capture the backlog a delivery group actually plans against: goals, initiatives, features, and stories, including learning work and platform work.

## Why this epic is separate

This epic owns what a piece of work is. The delivery path, the planning cycle, and the measures all point at these records.

The shape matches how product groups already talk, without a licensed framework's layer names. A goal lasts longer than one cycle. An initiative is the chunk that gets shaped and then built. Features and stories are the delivery slices. Platform items are the technical work underneath them. Prototypes and experiments answer a question and usually are not shipped.

## In scope

- A goal on a value stream.
- An initiative on a goal, moving through Proposed, Shaping, Ready, Active, and Done.
- A feature linked to an initiative.
- A story linked to a feature.
- Kind on a feature or story: feature, platform, prototype, or experiment.
- Parents and children visible from either side.
- Priority inputs stored on a feature: value of doing it sooner, urgency, risk or opportunity addressed, and size. The score itself is epic 09. That size is the economic divisor. It is not the story estimate.
- A sizing method on a team: t-shirt or points. T-shirt labels are XS, S, M, L, and XL. Each label has a number, starting at 1, 2, 3, 5, and 8, and the team can change those numbers. Points are a positive number the team enters on the story. A story stores one estimate in the team's method. Velocity in epic 09 sums the numbers on stories completed in an iteration.

## Out of scope

- Stage history along the delivery path (epic 05).
- Cycle outcomes (epic 06).
- Sorting and charts (epic 09).
- A model-training or drift tracker. Thresholds belong on acceptance criteria in epic 10.
- The research timebox and the data gate. Those are epic 17. This epic only needs the experiment kind they attach to.

## Depends on

- Epic 02

## Local proof

Create a goal, an initiative, a feature, and a story under it. Move the initiative from Proposed to Shaping. Create one experiment and one platform item beside the feature. Set the team method to t-shirt, estimate the story as M, and read back 3. Switch the method to points, estimate another story as 5, and read that number back. Reload and see the links.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **04.1 Goal.** From a value stream, a signed-in user can create a goal and edit its name. The goal is stored under that stream. A goal with no stream is refused. An empty name is refused. A signed-out request goes to sign-in.

  Done when: add a goal on the stream, edit the name, reload, and see it still under that stream. Submit an empty name and see it refused.

- [x] **04.2 Initiative.** From a goal, a signed-in user can create an initiative and edit its name. A new initiative is Proposed. The page can move it to Shaping, Ready, Active, or Done. An initiative with no goal is refused. An empty name is refused. A state outside that list is refused.

  Done when: add an initiative, see Proposed, move it to Shaping, reload, and see Shaping.

- [x] **04.3 Feature.** From an initiative, a signed-in user can create a feature and edit its name and kind. The kind is feature, platform, prototype, or experiment. A feature with no initiative is refused. An empty name is refused. A kind outside that list is refused.

  Done when: add a feature, a platform item, and an experiment on the same initiative, reload, and see all three with their kinds.

- [x] **04.4 Story.** From a feature, a signed-in user can create a story and edit its name and kind. The kind is the same list as a feature. A story with no feature is refused. An empty name is refused.

  Done when: add a story under the feature, edit the name, reload, and see it still under that feature.

- [x] **04.5 Parents and children.** A goal lists its initiatives. An initiative lists its features and links to its goal. A feature lists its stories and links to its initiative. A story links to its feature. The breadcrumb on each page links every ancestor back to the portfolio.

  Done when: from a story, open the feature, the initiative, the goal, and the value stream from the breadcrumb, and see the child listed on each parent.

- [x] **04.6 Priority inputs.** A feature stores value of doing it sooner, urgency, risk or opportunity, and size. They are whole numbers. Size is at least 1. The page does not compute a score. An empty or invalid number is refused.

  Done when: save 5, 3, 2, and 4 on a feature, reload, and see those numbers. Save a size of 0 and see it refused.

- [x] **04.7 Team sizing.** A team chooses t-shirt or points. T-shirt sizes are XS, S, M, L, and XL, starting at 1, 2, 3, 5, and 8, and the team can change those numbers. A story estimate uses the team's current method. T-shirt stores the team's number for the chosen size. Points stores the positive number entered on the story. Switching the method does not change an estimate already stored.

  Done when: leave the team on t-shirt, estimate a story as M, and read 3. Switch the team to points, estimate another story as 5, and read 5. Reload the first story and still read 3.

- [x] **04.8 Work model test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, creates the chain in the local proof, and reads the links, the state, the kinds, the priority numbers, and both estimates. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
