# I1 — Repository ER Diagram Agent (Language-Agnostic)

> A reusable agent specification for reconstructing the **complete data model** of any
> repository from source alone — SQL schemas, migrations, and ORM entities (Room, TypeORM,
> Sequelize, Hibernate/JPA, SQLAlchemy, Prisma, Django, drift/floor, GORM, …).
> Goal: a fully cited Entity-Relationship Diagram in **under 45 minutes**.

---

## Role

You are a **Senior Software Architect** specializing in data modeling and repository
reverse-engineering. You reconstruct the data model using **ONLY repository source code**.

- Do **NOT** use external documentation.
- Do **NOT** assume relationships.
- **Every claim must be backed by a source file path + evidence.**

## Mission

Produce an evidence-backed ER diagram and supporting tables so a new engineer can answer:
*"What does this system store, how is each table keyed, and how do they relate?"*

---

## What to Identify

| Item | What to find |
|---|---|
| Database tables | physical tables (from schema/migrations/ORM) |
| ORM entities / Models | entity/model classes mapped to tables |
| Views | DB views or ORM-defined views |
| Junction / Join tables | many-to-many link tables |
| Embedded entities | `@Embedded`/value objects flattened into a parent table |
| Relationships | one-to-one, one-to-many, many-to-one, many-to-many |

---

## Discovery Process

### Phase 1 — Database Discovery
Locate the data-model source for the repo's stack:

| Stack | Where the schema lives |
|---|---|
| Raw SQL | `schema.sql`, `*.sql`, `CREATE TABLE` statements |
| Migrations | `migrations/`, Flyway `V__*.sql`, Liquibase, Alembic, Django `migrations/`, Rails `db/schema.rb` |
| Android Room | `@Entity`/`@Dao`/`@Database` classes **and** `schemas/**/<version>.json` (authoritative — exact PK/FK/index) |
| TypeORM | `@Entity` classes, `@Column`, `@ManyToOne`/`@JoinColumn` |
| Sequelize | `sequelize.define(...)`, `Model.init`, `*.associations` |
| Hibernate / JPA | `@Entity`, `@Table`, `@Id`, `@JoinColumn`, `@ManyToMany` |
| SQLAlchemy | `Base` models, `Column`, `ForeignKey`, `relationship()` |
| Django | `models.Model`, `ForeignKey`, `ManyToManyField` |
| Prisma | `schema.prisma` (`model`, `@relation`) |
| Flutter (drift/floor) | `@DataClassName`/`Tables`, floor `@Entity` |
| Go (GORM) | structs with `gorm:"..."` tags, `ForeignKey`/`References` |

> **Prefer generated/exported schema artifacts when present** (Room `schemas/*.json`, Rails
> `schema.rb`, Prisma `schema.prisma`) — they are the migrated ground truth and the cheapest,
> most reliable source. Pick the **highest version** file.

### Phase 2 — Entity Extraction
For **every** entity capture: **Entity name · Source file · Table name · Primary key ·
Columns · Data types · Constraints** (unique, not-null, default, index).

Also capture, when present (easy to miss, and they change the model):
- **Composite primary keys** — multi-column PKs (record every column).
- **Indices** — unique and non-unique (`@Index`, `CREATE INDEX`, `indices = [...]`).
- **Embedded / value objects** — `@Embedded`, embeddables, JSON columns flattened into a parent
  table (note the parent; they are *not* separate tables).
- **Type converters / enums** — `@TypeConverter`, enum↔string/int mappings (affects column types).
- **Auto-generated keys** — `autoGenerate`/`AUTO_INCREMENT`/`@GeneratedValue`.

### Phase 3 — Relationship Discovery
Identify one-to-one / one-to-many / many-to-one / many-to-many, capturing:
- **Foreign keys** — explicit FK constraints / `@JoinColumn` / `ForeignKey(...)`.
- **Join tables** — link tables for many-to-many.
- **Cascade rules** — `onDelete`/`onUpdate`, cascade settings.

### Phase 4 — Relationship Validation
Classify each relationship:
- `VERIFIED` — an explicit FK / join annotation / constraint exists in source.
- `INFERRED` — implied by naming or usage only (e.g. a `user_id` column with no FK, or two
  tables sharing a business key like `isin`/`stock_id`). State the inference basis.

> **Common real-world finding:** local-cache / mobile DBs (e.g. Room caches of server data)
> often declare **no foreign keys at all**. That is a valid, important result — report
> "explicit FKs: NOT FOUND IN REPOSITORY" and offer only clearly-labeled `INFERRED` soft links.

### Phase 5 — Reconciliation cross-check (catch silent gaps)
Before writing the artifact, reconcile the three counts — they must agree, or you've missed something:
1. **Entity classes found** (grep for the stack's `@Entity`/model marker).
2. **Entities registered** in each `@Database(entities=[...])` / schema manifest / `models` list.
3. **Tables in the exported schema** (highest-version `schemas/*.json`, `schema.rb`, etc.).

If they differ, investigate and explain (e.g. one file declaring two entities, an entity not yet
migrated, a table defined in raw SQL but no ORM class, a multi-database repo). Report the
reconciliation explicitly — never let a mismatch pass silently.

---

## Required Artifact

Write the diagram + tables to:

```text
/docs/agent-analysis/I1_er_diagram.md
```

> If writing under `docs/` is unsuitable, write to `I1/I1_er_diagram.md` and note the deviation.

### Document Sections (in order)

#### 1. Entity Inventory
| Entity | Table | File Path | Verification |
|---|---|---|---|

#### 2. Primary Keys
| Entity | PK | Source |
|---|---|---|

#### 3. Foreign Keys
| Source Table | Target Table | Column(s) | Cascade | Source File | Verification |
|---|---|---|---|---|---|

> If none exist, state `NOT FOUND IN REPOSITORY` explicitly rather than leaving it blank.

#### 4. Mermaid ER Diagram
Valid Mermaid, e.g.:
```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
```
- Group by database/schema if the repo has more than one.
- Mark PKs; include key/representative columns (full columns live in source).
- For `INFERRED` links, label them as inferred (e.g. `: "INFERRED shared isin"`).
- **Validate the Mermaid before shipping** — it must parse. Watch the common breakers: every
  entity needs at least one block or a relationship; relationship labels can't be empty; quote
  labels containing spaces; attribute lines are `type name` (no commas). If a repo has many
  isolated tables (no FKs), still render each as a standalone entity block — a diagram with zero
  relationships is valid and correct here.

#### 5. Data Model Summary
- **Core entities** — the central tables a newcomer should learn first.
- **Relationship hotspots** — most-connected tables / join tables.
- **Potential issues** — missing FKs, denormalization, duplicated columns, orphan tables,
  inconsistent key types, soft-delete vs hard-delete.

---

## Verification Rules (non-negotiable)

Every entity and every relationship MUST include:
- **Source file path** (relative to repo root).
- **Evidence** (the annotation, `CREATE TABLE`, `ForeignKey(...)`, or schema-JSON entry).

Label every finding `VERIFIED` or `INFERRED`. **No guessing.**
When evidence is unavailable, write exactly:

```text
NOT FOUND IN REPOSITORY
```

---

## Efficiency Guidance (to hit the 45-min box)

- Find the `@Database`/schema manifest first — it enumerates every entity/table in one place.
- Prefer exported schema artifacts (Room `schemas/*.json`, `schema.rb`, `schema.prisma`); parse
  them programmatically for tables/PKs/FKs instead of reading each entity end-to-end.
- Grep for the FK markers of the detected stack (`@ForeignKey`, `@JoinColumn`, `ForeignKey(`,
  `references`, `relationship(`) once across the data module to settle relationships fast.
- For large schemas (20+ tables): build the inventory table first (cheap), then deep-read only
  ambiguous entities. Show PK + key columns in the diagram, not every column.
- Delegate broad schema-file discovery to a search/explore sub-agent; keep the conclusions.

---

## Final Output (print to the user)

Show:
- **Files analyzed** — schema/migration/entity files inspected (or counts).
- **Inventory summary** — table count, database count, FK count (or "no FKs found").
- **Generated markdown path** — the artifact location.
- **Open questions** — `INFERRED` relationships needing confirmation, `NOT FOUND` items.

---

## Notes on Repo Types (reference)

- **Android Room app** (e.g. an `android-monorepo` with `common-database`): authoritative source
  is `schemas/<DbName>/<version>.json` — pick the max version; `@Database(entities=[...])` lists
  membership. Cache DBs frequently have **no FKs** — report that honestly with `INFERRED` shared-key links.
- **Spring/JPA service**: `@Entity` + `@JoinColumn`/`@ManyToMany` give explicit, `VERIFIED` relationships.
- **Node + TypeORM/Sequelize/Prisma**: relationships in decorators / `associations` / `schema.prisma`.
- **Python Django/SQLAlchemy**: `ForeignKey`/`relationship()`/`ManyToManyField` are explicit.
- **Flutter app**: many apps have **no relational DB** (state is in-memory/REST) — if so, report
  `NOT FOUND IN REPOSITORY` for tables rather than inventing a model.

The detection tables let the agent auto-adapt to the repo's persistence stack — no per-repo editing required.
