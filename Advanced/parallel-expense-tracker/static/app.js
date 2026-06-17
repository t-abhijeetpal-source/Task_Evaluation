// Expense Tracker — vanilla JS frontend.
// Talks to the backend via RELATIVE URLs so it works wherever the app is served.
"use strict";

const API = {
  expenses: "/api/expenses",
  summary: "/api/summary",
};

// --- DOM refs ---
const form = document.getElementById("expense-form");
const amountInput = document.getElementById("amount");
const categoryInput = document.getElementById("category");
const noteInput = document.getElementById("note");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");

const totalEl = document.getElementById("summary-total");
const countEl = document.getElementById("summary-count");
const categoriesEl = document.getElementById("summary-categories");
const rowsEl = document.getElementById("expense-rows");

// --- helpers ---
function setStatus(message, kind) {
  statusEl.textContent = message || "";
  statusEl.className = kind || "";
}

function fmtMoney(n) {
  const num = Number(n);
  return Number.isFinite(num) ? num.toFixed(2) : String(n);
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleString();
}

// Build a text node / element safely (avoids HTML injection from note/category).
function td(text, className) {
  const cell = document.createElement("td");
  cell.textContent = text;
  if (className) cell.className = className;
  return cell;
}

// --- rendering ---
function renderExpenses(list) {
  rowsEl.innerHTML = "";
  if (!Array.isArray(list) || list.length === 0) {
    const tr = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.className = "empty";
    cell.textContent = "No expenses yet. Add one above.";
    tr.appendChild(cell);
    rowsEl.appendChild(tr);
    return;
  }
  for (const e of list) {
    const tr = document.createElement("tr");
    tr.appendChild(td(e.category));
    tr.appendChild(td(fmtMoney(e.amount), "amount"));
    tr.appendChild(td(e.note || ""));
    tr.appendChild(td(fmtDate(e.created_at)));
    rowsEl.appendChild(tr);
  }
}

function renderSummary(summary) {
  const total = summary && summary.total != null ? summary.total : 0;
  const count = summary && summary.count != null ? summary.count : 0;
  totalEl.textContent = fmtMoney(total);
  countEl.textContent = String(count);

  categoriesEl.innerHTML = "";
  const byCat = (summary && summary.by_category) || {};
  const cats = Object.keys(byCat);
  if (cats.length === 0) {
    const span = document.createElement("span");
    span.className = "cat-pill";
    span.textContent = "No categories yet";
    categoriesEl.appendChild(span);
    return;
  }
  for (const cat of cats) {
    const pill = document.createElement("span");
    pill.className = "cat-pill";
    pill.appendChild(document.createTextNode(cat + ": "));
    const strong = document.createElement("strong");
    strong.textContent = fmtMoney(byCat[cat]);
    pill.appendChild(strong);
    categoriesEl.appendChild(pill);
  }
}

// --- data loading ---
async function loadExpenses() {
  const res = await fetch(API.expenses);
  if (!res.ok) throw new Error("Failed to load expenses (HTTP " + res.status + ")");
  return res.json();
}

async function loadSummary() {
  const res = await fetch(API.summary);
  if (!res.ok) throw new Error("Failed to load summary (HTTP " + res.status + ")");
  return res.json();
}

async function refresh() {
  try {
    const [expenses, summary] = await Promise.all([loadExpenses(), loadSummary()]);
    renderExpenses(expenses);
    renderSummary(summary);
  } catch (err) {
    setStatus(err.message || "Failed to load data.", "error");
  }
}

// --- form submit ---
async function handleSubmit(event) {
  event.preventDefault();
  setStatus("", "");

  const amount = parseFloat(amountInput.value);
  const category = categoryInput.value.trim();
  const note = noteInput.value.trim();

  // Client-side validation.
  if (!Number.isFinite(amount) || amount <= 0) {
    setStatus("Amount must be a positive number.", "error");
    amountInput.focus();
    return;
  }
  if (!category) {
    setStatus("Category is required.", "error");
    categoryInput.focus();
    return;
  }

  submitBtn.disabled = true;
  setStatus("Saving…", "");

  try {
    const res = await fetch(API.expenses, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, category, note }),
    });

    if (res.status === 201) {
      form.reset();
      amountInput.focus();
      setStatus("Expense added.", "ok");
      await refresh();
      return;
    }

    // Error path — try to surface the server's message (e.g. 422).
    let serverMsg = "Could not save expense (HTTP " + res.status + ").";
    try {
      const data = await res.json();
      if (data && data.error) serverMsg = data.error;
    } catch (_) {
      // non-JSON body; keep default message
    }
    setStatus(serverMsg, "error");
  } catch (err) {
    setStatus("Network error: " + (err.message || "request failed") + ".", "error");
  } finally {
    submitBtn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  form.addEventListener("submit", handleSubmit);
  refresh();
});
