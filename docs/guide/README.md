# Halcyon Goods — Internal Product Control

**A guide to the project, for someone seeing it for the first time.**

Repository: https://github.com/gabrantoniette/halcyon-goods-product-control

---

## What this folder is

Five short documents and three diagrams. Read them in order and you will
understand what the system does, how it is put together, how to run it, and why
the less obvious decisions were made the way they were.

No prior knowledge of the project is assumed. Docker, containers, migrations and
the other terms are explained where they first matter, and again in the
glossary.

| File | What it covers | Read it if you want to know… |
|---|---|---|
| [01-what-this-is.md](01-what-this-is.md) | The problem, the three applications, the technology | …what was built and why |
| [02-architecture.md](02-architecture.md) | How the pieces fit and where the boundaries are | …how it is organised |
| [03-running-it.md](03-running-it.md) | Every step from starting it to shutting it down | …how to actually use it |
| [04-the-database.md](04-the-database.md) | Migrations, example data, inspecting the data | …how the data is managed |
| [05-glossary.md](05-glossary.md) | Every term used, in plain language | …what a word means |

### Diagrams

| | |
|---|---|
| ![Architecture](diagrams/01-architecture.png) | **[01-architecture.png](diagrams/01-architecture.png)** — the four moving parts and the only paths between them |
| ![Lifecycle](diagrams/02-lifecycle.png) | **[02-lifecycle.png](diagrams/02-lifecycle.png)** — from one command to a running system, and back to nothing |
| ![Write path](diagrams/03-write-path.png) | **[03-write-path.png](diagrams/03-write-path.png)** — one click, followed through every layer |

---

## The 60-second version

**Halcyon Goods is a fictional company. This is the back-office tool its
warehouse staff would use** to see what is registered, how much is on hand, what
is running low and what needs restocking. It is not a shop: there is no cart, no
checkout and no customer-facing page.

It is built as three separate applications that share one HTTP contract:

- a **records API** that owns the data and the rules,
- a **web dashboard** that people use in a browser,
- a **terminal client** for the same operations from a command line.

All three run in containers. One command starts everything:

```
docker compose up --build
```

Then open **http://localhost:3000**.

To stop it:

```
docker compose down
```

---

## Why the project exists

It is a study of a specific question: **how do a REST API and the clients that
consume it actually fit together, once you stop cutting corners?**

That framing explains most of what you will find in the code. There is one
authoritative source of the rules — the API — and two independent interfaces
over it, neither of which is allowed to reimplement a rule locally. Wherever
that principle was inconvenient, the inconvenience was accepted rather than
worked around, and the reasoning was written down next to the code.

---

## What to look at if you only have five minutes

1. **[diagrams/02-lifecycle.png](diagrams/02-lifecycle.png)** — the whole
   operational story on one page.
2. **The `docker-compose.yml`** in the repository. It is heavily commented, and
   every comment explains a decision rather than restating the line below it.
3. **The screenshots** in `docs/screenshots/` in the repository, which show the
   system running: the same create, update and delete operations captured from
   the browser, from the database and from the container logs.
