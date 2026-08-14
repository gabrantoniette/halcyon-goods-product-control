# 5 — Glossary

[← back to the guide](README.md)

Every term this guide uses, in plain language. Ordered by topic rather than
alphabetically, because the ideas build on each other.

---

## Containers and Docker

**Container** — a program running in isolation on your machine, with its own
filesystem, its own network view and its own process list. It is *not* a virtual
machine: it shares the operating system kernel with the host and carries only
the software layered on top. That is why it starts in milliseconds while a
virtual machine takes seconds to boot — there is no second operating system to
start.

**Image** — a frozen filesystem plus the instructions for what to run. The word
comes from "disk image": a snapshot, not a running program. An image is to a
container what a class is to an object. One image can start twenty containers,
and none of them modifies it.

**Layer** — an image is a stack of them, one per build instruction, each holding
only what changed. Docker reuses a layer whenever its input has not changed,
which is why dependencies are copied into the image *before* the source code:
editing code then rebuilds only the last few layers instead of reinstalling
everything.

**Multi-stage build** — building in one image and copying only the finished
result into a second, smaller one. It matters because layers are cumulative:
installing a compiler and then deleting it leaves the compiler's bytes inside
the image, merely hidden. Copying just the result into a fresh stage is the only
way to genuinely leave it behind.

**Volume** — storage that exists independently of any container. A container's
own filesystem is discarded when it is removed, so anything that must survive —
a database — writes to a volume instead.

**Docker Compose** — a tool that reads one YAML file describing several
containers and runs them together as a unit, with a network between them.

**`docker compose up`** — not really "start" but *converge*: compare what is
described in the file with what is currently running, and do the minimum needed
to match. Running it twice does almost nothing the second time.

**Healthcheck** — a command Docker runs inside a container on a schedule to
decide whether it is genuinely working, as opposed to merely running. This
distinction is the whole reason startup ordering works here.

**Publishing a port** — connecting a port inside the container to one on your
machine, so you can reach it from a browser. Without it the container's ports
are private to Docker's network.

**Loopback address** — `127.0.0.1` and `::1`, the addresses that mean "this
machine and nothing else". Publishing a port on the loopback address makes it
reachable from your computer but not from the network around you.

---

## The web

**API** — Application Programming Interface. Here, a program that answers HTTP
requests with data instead of with pages, so that other programs can use it.

**REST** — a convention for designing such an API around *resources* addressed
by URL, where the HTTP verb says what to do with them.

**The verbs**

| | |
|---|---|
| `GET` | read something; changes nothing |
| `POST` | create something new |
| `PUT` | replace something entirely — all fields required |
| `PATCH` | change part of something — only the fields sent |
| `DELETE` | remove it |

**Status codes** — the number in the answer.

| | |
|---|---|
| `200 OK` | it worked |
| `201 Created` | it worked and something new exists |
| `401 Unauthorized` | you sent no credential |
| `403 Forbidden` | you sent one, and it is wrong |
| `404 Not Found` | there is nothing at that address |
| `409 Conflict` | it clashes with something that already exists |
| `422 Unprocessable` | the shape of what you sent is invalid |
| `500 Server Error` | the server broke |

**Header** — a labelled line of metadata attached to a request or response.
`X-API-Key` is where this project's key travels.

**Endpoint** — one address the API answers on, such as `GET /products`.

**Paging** — returning results in chunks rather than all at once. This API
reports the counters in headers (`X-Total-Items`, `X-Total-Pages`) and clamps a
page number that is too large to the last real page, so a client walking through
always lands somewhere valid.

**CORS** — the browser rule that stops a page on one origin from calling another
without permission. This project needs none of it, because the browser never
calls the API — the server does.

---

## The frontend

**Server-side rendering** — building the HTML on the server and sending it
finished, rather than sending an empty page plus JavaScript that fetches the
data afterwards. It is what lets the API key stay on the server.

**Server Component** — in Next.js, a component that runs *only* on the server.
It can read secrets and call internal services, because none of its code is sent
to the browser.

**Server Action** — a function that runs on the server but can be called from a
form in the browser. It is how the dashboard changes data without the browser
ever knowing the API's address or its key.

**Hydration** — the moment the browser attaches interactivity to
server-rendered HTML. A mismatch between what the server rendered and what the
browser then expects produces a visible flicker, which is why the theme in this
project is read from a source both sides agree on.

---

## Data

**Schema** — the shape of the database: which tables exist, and what columns and
types they have.

**Migration** — a script that transforms the schema from one version to the
next, without destroying the data already stored. See
[04-the-database.md](04-the-database.md).

**ORM** — Object-Relational Mapper. A library that lets you work with database
rows as ordinary objects instead of writing SQL by hand. SQLAlchemy here, with
SQLModel on top.

**Primary key** — the column uniquely identifying a row. Here `id`, an integer
that never leaves the API; a separate `uuid` is what the outside world sees.

**Index** — a lookup structure that makes searching a column fast, at the cost
of a little space and slightly slower writes.

**Constraint** — a rule the database itself enforces, such as `name` being
unique. Enforcing it in the database rather than only in code means it holds
even when something writes from outside the application.

**Transaction** — a group of changes that either all take effect or none do.

**Timezone-aware timestamp** — a moment stored with its UTC offset, so it means
the same instant regardless of where it is read. See the last section of
[04-the-database.md](04-the-database.md) for why the alternative causes trouble.

---

## Development practices

**Monorepo** — several applications in one repository, developed together and
deployed separately.

**Linter** — a tool that reads code without running it and reports problems:
unused imports, unreachable branches, suspicious patterns. This project uses
Ruff for Python and ESLint for TypeScript. Ruff's speed matters not because it
makes the program faster — it has no effect on that at all — but because a check
that finishes in milliseconds can run on every keystroke, while one that takes
thirty seconds gets switched off.

**Type checking** — verifying that values are used consistently with their
declared types, before the program ever runs. `tsc` does this for TypeScript.

**CI (Continuous Integration)** — a service that runs the tests automatically on
every push, so a broken change is caught before anyone merges it. GitHub Actions
here.

**Unit test** — a test of one piece of code in isolation, without a network or a
real database. Fast, and blind to everything outside its own process.

**Environment variable** — a value handed to a program by whatever started it,
rather than written into its source. Configuration and secrets travel this way,
so the same image can run in different places without being rebuilt.

**`.env` file** — a file of environment variables for local use. It is never
committed, because it holds real secrets; `.env.example` is committed instead,
with the same keys and placeholder values, so someone cloning the project knows
what to provide.

**Idempotent** — an operation that can be repeated with no additional effect.
The seed script is idempotent: run it ten times and the register still holds one
copy of each product.

---

[← back to the guide](README.md)
