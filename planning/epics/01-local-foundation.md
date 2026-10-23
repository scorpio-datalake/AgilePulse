# Epic 01 — Local foundation

Status: stories done

## Outcome

A developer can start one Python process on a laptop, open the app in a browser, and sign in as a local admin. Data survives in a SQLite file. The suite can reset that file and prove the shell without a network service.

## Why this epic is separate

Every later epic needs a running app, a schema boot, and a test seam. Keeping the shell here stops stack work from leaking into delivery-process stories.

## In scope

- FastAPI application, Jinja pages, HTMX, and Alpine.js.
- Pydantic models at the HTTP boundary.
- SQLite, created and migrated on startup.
- One local user and a session.
- A home page that shows the app is up.
- Automated tests that boot the app against a temporary database.

## Out of scope

- JWT, replacement authenticators, and role checks (epic 15).
- PostgreSQL, SQL Server, Oracle, and other SQL adapters (epic 14).
- Rust (epic 12).
- Docker as a requirement for done.
- A JavaScript build step.

## Depends on

Nothing.

## Local proof

Start the process, sign in, restart the process, and see the same empty home state. A test does the same without a browser.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [x] **01.1 Page shell.** One command starts a FastAPI process. Opening it in a browser shows a Jinja page that the app is up. The layout loads HTMX and Alpine.js from static files served by that process. There is no JavaScript build step.

  Done when: start the process, open the page, and see that it is up.

- [x] **01.2 SQLite on startup.** Startup creates the SQLite file if it is missing and runs migrations. A second start keeps the file and does not wipe it. The database path is a local setting so a test can point at its own file.

  Done when: start the process twice against the same path and see the file still there, then start once against a fresh path and see a new file.

- [x] **01.3 Local user and session.** Migrations seed one local admin, username admin and password admin. A sign-in page accepts that password while testing. The request body is a Pydantic model; a malformed body is rejected. A wrong password is rejected. A correct password sets a session cookie. Signing out clears it. No JWT and no role check. When setup is required, the first sign-in cannot keep the password admin: it sets a new password and adds a user before the home page.

  Done when: sign in as that user, reload and stay signed in, sign out, and see the next request ask for a sign-in. Submit an empty form and a wrong password and see both refused.

- [x] **01.4 Empty home across a restart.** A signed-in user sees an empty home page with their name. A signed-out request for that page goes to sign-in. Stop the process, start it again on the same SQLite file, sign in, and the same empty home is there.

  Done when: the local proof's browser half passes: start, sign in, restart, sign in, same empty home.

- [x] **01.5 Temporary-database test.** An automated test boots the app against a temporary SQLite file, signs in through the test client, and reads the empty home. It does not open a browser and it does not call a network service.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
