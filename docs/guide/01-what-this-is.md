# 1 — What this is

[← back to the guide](README.md)

---

## The problem it solves

A warehouse holds stock. Someone needs to answer five questions, quickly and
without arguing about which spreadsheet is current:

- What items are registered?
- How many of each are on hand?
- What is running low?
- What has run out, and what have we withdrawn? (Not the same question —
  see [the database](04-the-database.md#two-fields-four-states).)
- How old is each of those quantities?

**Halcyon Goods is a fictional company**, invented so the project has a concrete
shape rather than being an abstract CRUD exercise. The system is the internal
tool its staff would use.

It is deliberately **not a storefront**. There is no cart, no checkout, no
customer. That constraint changes the design in ways that are visible: the
default view is a dense table rather than a grid of product cards, because a
register is read like a ledger, not browsed like a catalogue.

---

## The three applications

The project is a **monorepo** — one repository holding several applications that
are developed together but deployed separately.

```
apps/
├── api/     the records service — owns the data and the rules
├── web/     the dashboard people use in a browser
└── cli/     a terminal client for the same operations
```

### `api` — the records service

The authority. It holds the products, enforces the rules, and is the only thing
that talks to the database. Everything else is a client.

Written in **Python** with **FastAPI**. Its endpoints are ordinary REST:

| Method | Path | Needs the key? | What it does |
|---|---|---|---|
| `GET` | `/health` | no | says whether it is alive and reachable |
| `GET` | `/products` | no | one page of registered items |
| `GET` | `/products/{name}` | no | find one item by name |
| `POST` | `/products/{name}` | **yes** | register a new item |
| `PUT` | `/products/{name}` | **yes** | replace an item entirely |
| `PATCH` | `/products/{name}` | **yes** | change only the fields sent |
| `DELETE` | `/products/{name}` | **yes** | remove an item |

Reads are open, writes need a key. That split is deliberate: a dashboard can be
pointed at the API without handing it a secret, while nothing can change the
register without one.

### `web` — the dashboard

What people actually use. Built with **Next.js 16** and **React**. It shows the
summary tiles, the per-category chart, search, filters, sorting, and the dialogs
for creating, editing and removing items.

It has no database of its own. Every number on screen came from the API.

### `cli` — the terminal client

The same operations from a terminal menu, in Python. It exists to prove a point
that is easy to claim and hard to honour: **if the rules genuinely live in the
API, a second interface should be able to sit on top of it without duplicating
any of them.** Writing it was the test.

---

## The technology, and what each piece is for

| | What it is | Why it is here |
|---|---|---|
| **Python** | the language of the API and the terminal client | |
| **FastAPI** | web framework | generates the interactive API documentation at `/docs` for free |
| **SQLModel / SQLAlchemy** | maps Python objects to database rows | lets the same code run on SQLite and Postgres |
| **Pydantic** | validates data shapes | rejects a malformed request before it reaches any logic |
| **Alembic** | database migrations | see [04-the-database.md](04-the-database.md) — this is the important one |
| **PostgreSQL** | the database | handles concurrent writes, which SQLite does poorly |
| **TypeScript** | the language of the dashboard | catches mistakes at build time rather than in the browser |
| **Next.js 16** | React framework | renders pages on the server, which is what keeps the API key out of the browser |
| **Zod** | validates data in the dashboard | mirrors the API's rules so errors are shown before a request is made |
| **Docker / Compose** | packaging and orchestration | see [03-running-it.md](03-running-it.md) |
| **GitHub Actions** | continuous integration | runs every test on every push |

---

## What "finished" means here

The project is verified rather than assumed to work:

- **100 automated tests** — 69 for the API, 31 for the terminal client.
- **Continuous integration** runs on every push: linting, the API suite across
  three Python versions, the terminal client's suite, the migrations applied
  *and rolled back* against a real Postgres, and the dashboard's production
  build.
- **The whole stack was run end to end** from an empty database, and the
  evidence is committed as screenshots in `docs/screenshots/`.

That last point deserves emphasis, because it is where a real lesson lives. The
test suite passed for a long time before the containers were ever started. When
they finally were, three bugs appeared immediately — a broken image build, a
database that refused to start, and a crash on startup caused by an environment
variable no test had ever set.

**None of them were catchable by unit tests, because each one lived outside the
process the tests run in.** Automated tests check logic; running the real thing
checks everything around it. The project needs both, and the commit that fixed
those three is a useful thing to read.

---

**Next:** [02-architecture.md](02-architecture.md) — how the pieces fit together.
