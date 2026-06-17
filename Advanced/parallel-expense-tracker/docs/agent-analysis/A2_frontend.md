# A2 — Frontend Workstream Report

> Role: Frontend Engineer (A2). Owns only `static/index.html` and `static/app.js`.
> Stack: vanilla JavaScript, no framework, no build step. Talks to the backend via **relative** URLs.
> Date: 2026-06-17.

---

## What the UI does

A single-page Expense Tracker (`static/index.html`) served at site root. It contains:

- A **heading** and short subtitle.
- An **add-expense form** with a number input `amount`, text inputs `category` and `note`, and a submit button.
- A **Summary** card showing **total**, **count**, and a per-category breakdown (one pill per category).
- An **expenses table** listing each expense's category, amount, note, and created-at timestamp (newest first, as returned by the API).
- A small **status/error message area** below the form (`#status`, `aria-live="polite"`).

Styling is minimal inline CSS for a tidy, responsive look. `app.js` is linked with `<script src="/app.js" defer></script>` (files are served at site root).

On `DOMContentLoaded` the page loads expenses and summary in parallel and renders them. The form is wired to the submit handler. Rendering uses `textContent`/DOM nodes (not `innerHTML`) for user-supplied fields to avoid HTML injection.

---

## Exact API calls (method + path + payload)

All paths are **relative** (no host) so the UI works wherever the backend serves it.

| When | Method | Path | Payload | Handling |
|---|---|---|---|---|
| On load + after a successful add | GET | `/api/expenses` | — | Expects `[{id,amount,category,note,created_at}, …]` newest first; renders table rows. |
| On load + after a successful add | GET | `/api/summary` | — | Expects `{total, count, by_category:{cat:sum}}`; renders total, count, and category pills. |
| On form submit (valid input) | POST | `/api/expenses` | `{ "amount": <number>, "category": <string>, "note": <string> }` with header `Content-Type: application/json` | `201` → reset form, show "Expense added.", refresh list + summary. Non-201 → show server error. |

The two GETs are issued together via `Promise.all` in `refresh()`.

---

## Error handling

- **Client-side validation (before any request):**
  - `amount` parsed with `parseFloat`; rejected unless finite and `> 0` → status "Amount must be a positive number."
  - empty `category` → status "Category is required."
  - Invalid input focuses the offending field and aborts the POST.
- **Server 422 (and any non-201):** the response body is parsed as JSON and, if it contains `{"error": "..."}` (e.g. `"amount must be positive"`), that exact message is shown in the status area. If the body is missing/non-JSON, a generic `Could not save expense (HTTP <status>).` message is shown.
- **Network failures:** caught and shown as `Network error: <message>.`.
- **Load failures:** failed GET on `/api/expenses` or `/api/summary` surfaces `Failed to load …` in the status area.
- **UX guards:** submit button is disabled while a POST is in flight and re-enabled in `finally`; a transient "Saving…" status is shown.

---

## Files authored

- `static/index.html` — page structure + inline CSS; links `/app.js`.
- `static/app.js` — load/render logic, form validation, POST + refresh, status/error messaging.

No external libraries; no build step. Adheres to the locked API contract in `A2_architecture.md`.

---

## Agent Generated

This frontend (HTML + JS) and this report were **Agent Generated** by the A2 Frontend Engineer agent against the locked contract. Functional verification (running the backend and exercising the live API) is performed separately by the coordinator in Phase 4; nothing here is claimed as runtime-verified.
