# Epic 14 — Database adapters

Status: stories not written yet

## Outcome

A shop can point AgilePulse at the SQL database it already runs. The same product behavior works on that database. SQLite remains the zero-config database for local development and for the test suite.

## Why this epic is separate

Epic 01 boots the app on SQLite so every other epic can be clicked through on a laptop. Shops do not standardize on SQLite. The storage boundary has to be a replaceable adapter before features start embedding one dialect.

Supported shop databases for this epic: PostgreSQL, Microsoft SQL Server, and Oracle. Any other SQL database is added by writing an adapter against the same contract and registering it. The app does not ship a driver for every product on the market. The contract is how a shop brings its own.

## In scope

- One repository boundary. Feature code calls that boundary. It does not open vendor-specific clients. The boundary is SQLAlchemy, using the models from epic 08.
- A connection setting, a URL or an equivalent discrete config, chosen at startup.
- Adapters for SQLite, PostgreSQL, SQL Server, and Oracle, as SQLAlchemy dialects.
- Request bodies stay Pydantic models.
- Migrations that run on each supported adapter.
- One test suite parameterized by the connection setting. SQLite always runs. PostgreSQL runs in a local container when Docker is available. SQL Server and Oracle run when a URL is supplied.
- Operator documentation: how to switch the database, which URL form each adapter expects, and how to add an adapter for another SQL database.

## Out of scope

- A Rust database layer (epic 12).
- Graph databases, document stores, and warehouses.
- Moving an existing production dataset between vendors. The docs cover a fresh schema on the chosen database.

## Depends on

- Epic 01
- Epic 08, for the SQLAlchemy models and Pydantic models

## Local proof

Run the foundation tests on SQLite. Start Postgres in a local container, point the app at it, sign in, and see the same home page. Follow the doc and confirm it names SQL Server, Oracle, and the steps to register another SQL adapter.

## Stories

Stories for this epic will be added in this file. Each story that stores a row uses a SQLAlchemy model. Each story that accepts a request body uses a Pydantic model. The adapters are SQLAlchemy dialects.
