#!/usr/bin/env python3
"""Validate the I1 ER-diagram artifact for internal consistency and (optionally)
against a live schema export.

Stdlib + json only (Python 3.12+). Two modes:

  * OFFLINE (default) — parse the artifact markdown and prove it is internally
    consistent: every count (inventory rows, PK rows, Mermaid entity blocks,
    appendix entity blocks) reconciles to the expected entity count, required
    sections exist, and no truncated `schemas/.../` paths leak into evidence.
    Works even when android-monorepo is NOT checked out.

  * LIVE — `--schema-json <Room .json>` cross-checks artifact tables against an
    exported Room schema; `--prisma <schema.prisma>` parses a Prisma schema and
    counts `@relation` foreign keys as VERIFIED (see W19 / tests/fixtures).

Exit 0 on pass, exit 1 on fail (with a human-readable report).

Usage:
    python scripts/validate_er_diagram.py                 # offline, uses validation.config.json
    python scripts/validate_er_diagram.py --config c.json
    python scripts/validate_er_diagram.py --schema-json common-database/schemas/.../19.json
    python scripts/validate_er_diagram.py --stack prisma --prisma tests/fixtures/prisma-sample/schema.prisma
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # Intermediate/er-diagram/

GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"


# --------------------------------------------------------------------------- #
# Markdown parsing helpers
# --------------------------------------------------------------------------- #
def split_row(line: str) -> list[str]:
    """Split a GFM table row `| a | b |` into ['a', 'b'] (trimmed)."""
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def parse_first_table(section: str) -> list[dict[str, str]]:
    """Parse the first GFM table found in `section` into a list of row dicts."""
    lines = section.splitlines()
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    in_table = False
    for ln in lines:
        s = ln.strip()
        is_row = s.startswith("|") and s.endswith("|")
        if not in_table:
            if is_row:
                header = split_row(s)
                in_table = True
            continue
        if not is_row:
            break  # table ended
        cells = split_row(s)
        if set("".join(cells)) <= set("-: "):  # separator row
            continue
        if header is None:
            continue
        row = {header[i]: (cells[i] if i < len(cells) else "") for i in range(len(header))}
        rows.append(row)
    return rows


def section_text(md: str, header_regex: str, stop_regex: str = r"^#{1,3}\s") -> str:
    """Return the text of the section whose heading matches `header_regex`,
    up to the next heading matching `stop_regex`."""
    lines = md.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.search(header_regex, ln):
            start = i + 1
            break
    if start is None:
        return ""
    out = []
    for ln in lines[start:]:
        if re.match(stop_regex, ln):
            break
        out.append(ln)
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Artifact extractors
# --------------------------------------------------------------------------- #
EQUITY_MARK = "EquityDatabase"
LOGGING_MARK = "LoggingDataBase"


def extract_inventory(md: str) -> list[dict[str, str]]:
    sect = section_text(md, r"^##\s+1\.\s+Entity Inventory", stop_regex=r"^#{2,3}\s")
    rows = parse_first_table(sect)
    # keep only rows that have a backticked Table cell
    out = []
    for r in rows:
        tbl = r.get("Table", "")
        m = re.search(r"`([^`]+)`", tbl)
        if not m:
            continue
        ver = r.get("Verification", "")
        db = EQUITY_MARK if EQUITY_MARK in ver else (LOGGING_MARK if LOGGING_MARK in ver else "?")
        out.append({"entity": r.get("Entity", ""), "table": m.group(1), "db": db,
                    "sensitivity": r.get("Sensitivity", ""), "verification": ver})
    return out


def extract_pk_rows(md: str) -> list[str]:
    sect = section_text(md, r"^##\s+2\.\s+Primary Keys", stop_regex=r"^#{2,3}\s")
    rows = parse_first_table(sect)
    return [r.get("Entity", "") for r in rows if r.get("Entity")]


def extract_mermaid_entities(md: str) -> tuple[bool, list[str]]:
    """Return (has_er_block, [entity names]) from the mermaid erDiagram block."""
    blocks = re.findall(r"```mermaid\s*(.*?)```", md, re.DOTALL)
    er = next((b for b in blocks if "erDiagram" in b), None)
    if er is None:
        return False, []
    entities = re.findall(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\{\s*$", er, re.MULTILINE)
    return True, entities


def extract_appendix_entities(md: str) -> list[str]:
    return re.findall(r"^\*\*([A-Za-z0-9_]+)\*\*\s*(?:→|->)", md, re.MULTILINE)


def find_truncated_paths(md: str) -> list[str]:
    """Lines containing an elided path such as `schemas/.../19.json` or `.../foo`."""
    bad = []
    for i, ln in enumerate(md.splitlines(), 1):
        if re.search(r"schemas/\.\.\.|/\.\.\./|`[^`]*\.\.\.[^`]*\.json", ln):
            bad.append(f"L{i}: {ln.strip()[:120]}")
    return bad


def missing_sections(md: str, required: list[str]) -> list[str]:
    return [s for s in required if s not in md]


# --------------------------------------------------------------------------- #
# Live schema parsers
# --------------------------------------------------------------------------- #
def parse_room_schema_json(path: Path) -> dict:
    data = json.loads(path.read_text())
    db = data["database"]
    entities = db["entities"]
    tables = [e["tableName"] for e in entities]
    fks = []
    for e in entities:
        for fk in e.get("foreignKeys", []) or []:
            fks.append((e["tableName"], fk))
    return {"version": db.get("version"), "tables": tables, "fk_count": len(fks)}


def parse_prisma_schema(path: Path) -> dict:
    """Parse a Prisma schema. Detect `model` blocks and `@relation` foreign keys.

    A field carrying `@relation(... fields: [...] ...)` declares the FK-holding
    side of a relation — that is an explicit, VERIFIED foreign key. The bare
    back-reference side (no `fields:`) is not counted, so a 1:N relation counts once.
    """
    text = path.read_text()
    models = re.findall(r"^\s*model\s+(\w+)\s*\{", text, re.MULTILINE)
    verified_fks = []
    for m in re.finditer(r"@relation\s*\(([^)]*)\)", text):
        args = m.group(1)
        if "fields:" in args:
            verified_fks.append(args.strip())
    return {"models": models, "verified_fks": len(verified_fks), "relations": verified_fks}


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self) -> None:
        self.checks: list[tuple[str, bool, str]] = []

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append((name, ok, detail))

    @property
    def ok(self) -> bool:
        return all(ok for _, ok, _ in self.checks)

    def render(self) -> str:
        lines = []
        for name, ok, detail in self.checks:
            tag = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
            lines.append(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
        verdict = (f"{GREEN}{BOLD}VALIDATION PASSED{RESET}" if self.ok
                   else f"{RED}{BOLD}VALIDATION FAILED{RESET}")
        return "\n".join(lines) + f"\n\n{verdict}"


# --------------------------------------------------------------------------- #
# Validation core
# --------------------------------------------------------------------------- #
def validate_artifact(md: str, cfg: dict, rep: Report) -> None:
    expected = cfg["expected_entity_count"]
    eq_exp = cfg.get("expected_equity_count")
    lg_exp = cfg.get("expected_logging_count")
    required = cfg.get("required_sections", [])

    inv = extract_inventory(md)
    pk = extract_pk_rows(md)
    has_er, mermaid = extract_mermaid_entities(md)
    appendix = extract_appendix_entities(md)

    inv_tables = [r["table"] for r in inv]
    eq = [r for r in inv if r["db"] == EQUITY_MARK]
    lg = [r for r in inv if r["db"] == LOGGING_MARK]

    rep.add(f"Inventory has {expected} entities",
            len(inv) == expected, f"found {len(inv)}")
    rep.add(f"Primary-key table has {expected} rows",
            len(pk) == expected, f"found {len(pk)}")
    rep.add("Mermaid erDiagram block present", has_er)
    rep.add(f"Mermaid renders >= {expected} entities",
            len(mermaid) >= expected, f"found {len(mermaid)}")
    rep.add(f"Appendix lists {expected} entities",
            len(appendix) == expected, f"found {len(appendix)}")

    # Reconciliation: all four counts equal expected
    counts = {"inventory": len(inv), "primary_keys": len(pk),
              "mermaid": len(mermaid), "appendix": len(appendix)}
    distinct = set(counts.values()) | {expected}
    rep.add("Reconciliation: inventory == PK == Mermaid == appendix == expected",
            distinct == {expected}, f"{counts} vs expected {expected}")

    if eq_exp is not None:
        rep.add(f"EquityDatabase entities == {eq_exp}",
                len(eq) == eq_exp, f"found {len(eq)}")
    if lg_exp is not None:
        rep.add(f"LoggingDataBase entities == {lg_exp}",
                len(lg) == lg_exp, f"found {len(lg)}")
    if eq_exp is not None and lg_exp is not None:
        rep.add(f"Per-DB split sums to total ({eq_exp}+{lg_exp})",
                len(eq) + len(lg) == expected, f"{len(eq)}+{len(lg)}={len(eq)+len(lg)}")

    # Cross-check inventory tables appear as mermaid entities
    missing_in_mermaid = sorted(set(inv_tables) - set(mermaid))
    rep.add("Every inventory table appears in the Mermaid diagram",
            not missing_in_mermaid, f"missing: {missing_in_mermaid}" if missing_in_mermaid else "")

    # No truncated paths
    trunc = find_truncated_paths(md)
    rep.add("No truncated `schemas/.../` paths in evidence",
            not trunc, (f"{len(trunc)} offending line(s); first: {trunc[0]}" if trunc else ""))

    # Required sections
    miss = missing_sections(md, required)
    rep.add("Required sections present (Reconciliation / Agent-vs-Verified / Self-Consistency / Uncertainties)",
            not miss, f"missing: {miss}" if miss else "")


def validate_live_schema(md: str, schema_path: Path, rep: Report) -> None:
    parsed = parse_room_schema_json(schema_path)
    inv = extract_inventory(md)
    inv_tables = set(r["table"] for r in inv)
    schema_tables = set(parsed["tables"])
    missing = sorted(schema_tables - inv_tables)
    rep.add(f"Live schema v{parsed['version']}: all {len(schema_tables)} tables documented in artifact",
            not missing, f"undocumented: {missing}" if missing else "")
    rep.add("Live schema declares 0 foreign keys (matches artifact NOT FOUND claim)",
            parsed["fk_count"] == 0, f"schema fk_count={parsed['fk_count']}")


def validate_prisma(prisma_path: Path, rep: Report, expected_fk: int | None) -> None:
    parsed = parse_prisma_schema(prisma_path)
    rep.add(f"Prisma schema parsed: {len(parsed['models'])} model(s) {parsed['models']}",
            len(parsed["models"]) > 0)
    if expected_fk is None:
        sib = prisma_path.parent / "expected_fk_count.json"
        if sib.exists():
            expected_fk = json.loads(sib.read_text()).get("verified_fks")
    if expected_fk is not None:
        rep.add(f"Prisma @relation VERIFIED FK count == {expected_fk}",
                parsed["verified_fks"] == expected_fk,
                f"detected {parsed['verified_fks']}")
    else:
        rep.add(f"Prisma @relation VERIFIED FKs detected: {parsed['verified_fks']}", True)


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate the I1 ER-diagram artifact.")
    ap.add_argument("--config", default=str(ROOT / "validation.config.json"))
    ap.add_argument("--artifact", help="override artifact path from config")
    ap.add_argument("--schema-json", help="live Room schema JSON to cross-check")
    ap.add_argument("--stack", choices=["room", "prisma"], default="room")
    ap.add_argument("--prisma", help="Prisma schema.prisma to validate (W19)")
    ap.add_argument("--expected-fk", type=int, help="expected verified FK count for --prisma")
    args = ap.parse_args(argv)

    rep = Report()

    # Prisma mode can run standalone (no artifact required)
    if args.stack == "prisma" or args.prisma:
        prisma_path = Path(args.prisma) if args.prisma else None
        if not prisma_path or not prisma_path.exists():
            print(f"{RED}error:{RESET} --prisma path required and must exist for prisma stack",
                  file=sys.stderr)
            return 1
        validate_prisma(prisma_path, rep, args.expected_fk)
        print(f"{BOLD}I1 ER-diagram validator — Prisma stack{RESET}\n")
        print(rep.render())
        return 0 if rep.ok else 1

    cfg = json.loads(Path(args.config).read_text())
    artifact = Path(args.artifact) if args.artifact else (ROOT / cfg["artifact"])
    if not artifact.exists():
        print(f"{RED}error:{RESET} artifact not found: {artifact}", file=sys.stderr)
        return 1
    md = artifact.read_text()

    print(f"{BOLD}I1 ER-diagram validator{RESET}  ·  artifact: {artifact.relative_to(ROOT) if artifact.is_relative_to(ROOT) else artifact}")
    mode = "LIVE (schema cross-check)" if args.schema_json else "OFFLINE (internal consistency)"
    print(f"{DIM}mode: {mode}{RESET}\n")

    validate_artifact(md, cfg, rep)

    if args.schema_json:
        sp = Path(args.schema_json)
        if not sp.exists():
            rep.add(f"--schema-json path exists: {sp}", False, "not found")
        else:
            validate_live_schema(md, sp, rep)

    print(rep.render())
    return 0 if rep.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
