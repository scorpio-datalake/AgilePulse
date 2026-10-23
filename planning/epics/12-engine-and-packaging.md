# Epic 12 — Engine and packaging

Status: stories written — not started

## Outcome

If a measured path in the Python app is too slow to stay there, that path moves to a small Rust worker. The running app can then be packed as a container.

## Why this epic is separate

An earlier draft started with a Rust database layer, a native extension, and a container that also held a JavaScript build. None of that is required to prove the delivery process on localhost. Rust is justified by a profile, not by a general wish for speed.

## In scope

- A written performance bar before any Rust code: which page or query, on what data size, and what latency is missed.
- One Rust worker for that path, called from Python.
- A container image of the process that actually ships. The size target is set when the contents are known.
- The Python path this epic measures keeps the SQLAlchemy models and Pydantic bodies from epic 08. The Rust worker does not replace that store.

## Out of scope

- Rewriting the domain model in Rust.
- A JavaScript build stage.
- MySQL, unless a later story names a real consumer.

## Depends on

- Epic 01
- Epic 08, for the SQLAlchemy models and Pydantic models
- Epic 09, because measurement is the first place a slow path is likely to show up

## Local proof

A test or bench shows the Python path missing the bar, the Rust path meeting it, and the UI returning the same numbers either way. The image starts with one command and serves the local login.

## Stories

Check a box when that story can be exercised on localhost. Order is the build order. A later story can assume the earlier ones exist.

- [ ] **12.1 Performance bar.** Before any Rust code, a note names one page, the data size, and the latency that page must meet. The page is the delivery-group flow page from epic 09. A bench builds that data size in a temporary SQLite file through the SQLAlchemy models and times the Python path. If that size still meets the latency, the note raises the size until the Python path misses it. The bench does not add a worker.

  Done when: the note names the flow page, a data size, and a latency, and the bench on a clean machine records a Python time slower than that latency.

- [ ] **12.2 Rust worker.** One Rust worker computes the measures for the path in 12.1. Python loads the rows through the SQLAlchemy models and passes the numbers in. The worker does not open the database and does not replace those models. The bench shows the worker meeting the latency the Python path missed, and both paths returning the same measures for the same fixture.

  Done when: the bench records a Rust time inside the latency from 12.1, and the measures match the Python path.

- [ ] **12.3 Same numbers on the page.** The delivery-group flow page can answer from the Python path or from the worker. For the same fixture, the page shows the same throughput, lead time, and work in progress either way.

  Done when: open the flow page both ways on the fixture from 12.1 and read the same three numbers.

- [ ] **12.4 Container image.** The process that ships is packed as one image: the Python app and the worker from 12.2. The image has no JavaScript build stage. One command starts it, and the local login answers. The note from 12.1 then records the image size and the size target. The built image is within that target.

  Done when: start the image with one command, open the local login, and read a size target in the note that the image meets.

- [ ] **12.5 Engine test.** An automated test boots the app against a temporary SQLite file and walks the measured path: the Python time misses the bar from 12.1, the worker meets it, and both return the same measures. It does not open a browser, it does not call a network service, and it does not start the image from 12.4.

  Done when: the suite passes that test on a clean machine with only the local process and a temp file.
