# Epic 15 — Auth extension

Status: stories not written yet

## Outcome

A shop can keep local login, switch the app to JWT, or replace the authenticator with its own code. Role checks always read roles stored in AgilePulse's database.

## Why this epic is separate

Login and permissions are different seams. Login answers who the caller is. Permissions answer what that person may do, from role rows we own. A shop that already runs Azure AD or AWS IAM overwrites the authenticator with its own implementation. AgilePulse does not ship those integrations. Their adapter may find or create the person. It does not become the role store. Grants stay in our tables and are edited in our screens.

Role-based checks are the default permission model. A shop extends them by adding a role or a permission the check already knows how to read, or by replacing the permission function documented in this epic. Replacing that function is an extension. Bypassing the role tables is not.

## In scope

- Local username and session login from epic 01, still available when no other authenticator is configured.
- A built-in JWT authenticator: validate a token, map the subject to a person row, then load that person's roles from the database.
- A small authenticator interface with a documented method a shop implements to overwrite login. The docs include a worked sketch of where an Azure AD or AWS IAM adapter would sit. The sketch is not a working cloud integration.
- Permission checks that accept a person only when the required role is in the database for that person.
- A way to register the replacement authenticator without editing feature code.
- Operator documentation: turn on JWT, assign roles in the app, and replace the authenticator. The doc states that directory groups do not grant permissions unless the shop's own code writes our role rows.
- Role rows stay on the SQLAlchemy models from epic 08. Login and token bodies are Pydantic models. Any new auth record is a SQLAlchemy model.

## Out of scope

- Shipping Azure AD, AWS IAM, or any other hosted directory.
- Putting role membership only in the token and skipping the database.
- A Rust token parser (epic 12).

## Depends on

- Epic 01
- Epic 02
- Epic 08, for the SQLAlchemy models and Pydantic models
- Epic 16, so checks understand a person who holds more than one role

## Local proof

Sign in as the dev user and call a route that requires a role stored on that user. Switch configuration to the JWT authenticator, present a locally signed token for the same person, and see the same role check pass. Load a test authenticator that returns that person without a password, and see the role check still read the database. Remove the role row and see the same call refused. The operator doc shows the Azure AD and AWS IAM sketches as customer code, not as features of the app.

## Stories

Stories for this epic will be added in this file. Each story that stores a row uses a SQLAlchemy model. Each story that accepts a request body uses a Pydantic model.
