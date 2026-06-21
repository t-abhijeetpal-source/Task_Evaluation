"""Tests for scripts/validate_er_diagram.py (stdlib + pytest only)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_er_diagram as v  # noqa: E402

CONFIG = json.loads((ROOT / "validation.config.json").read_text())
ARTIFACT = ROOT / CONFIG["artifact"]
ARTIFACT_MD = ARTIFACT.read_text()
PRISMA = ROOT / "tests" / "fixtures" / "prisma-sample" / "schema.prisma"
MINI = ROOT / "tests" / "fixtures" / "mini_schema.json"


def run_artifact(md: str, cfg: dict | None = None) -> v.Report:
    rep = v.Report()
    v.validate_artifact(md, cfg or CONFIG, rep)
    return rep


# --------------------------------------------------------------------------- #
# 1. Happy path
# --------------------------------------------------------------------------- #
def test_happy_path_current_artifact_passes():
    rep = run_artifact(ARTIFACT_MD)
    failed = [(n, d) for n, ok, d in rep.checks if not ok]
    assert rep.ok, f"unexpected failures: {failed}"


def test_cli_offline_exit_zero():
    assert v.main([]) == 0


# --------------------------------------------------------------------------- #
# 2. Counts parsed correctly
# --------------------------------------------------------------------------- #
def test_inventory_has_27_entities():
    inv = v.extract_inventory(ARTIFACT_MD)
    assert len(inv) == 27
    eq = [r for r in inv if r["db"] == v.EQUITY_MARK]
    lg = [r for r in inv if r["db"] == v.LOGGING_MARK]
    assert len(eq) == 24 and len(lg) == 3


def test_mermaid_has_27_entities():
    has_er, ents = v.extract_mermaid_entities(ARTIFACT_MD)
    assert has_er
    assert len(ents) == 27, ents


def test_pk_and_appendix_counts():
    assert len(v.extract_pk_rows(ARTIFACT_MD)) == 27
    assert len(v.extract_appendix_entities(ARTIFACT_MD)) == 27


# --------------------------------------------------------------------------- #
# 3. Failure cases
# --------------------------------------------------------------------------- #
def test_missing_entity_in_inventory_fails():
    # Drop the first inventory data row (PersonalDetails line ends with PII...).
    lines = ARTIFACT_MD.splitlines()
    out, dropped = [], False
    for ln in lines:
        if not dropped and ln.startswith("| PopularSearch |"):
            dropped = True
            continue
        out.append(ln)
    rep = run_artifact("\n".join(out))
    assert not rep.ok


def test_count_mismatch_fails():
    cfg = dict(CONFIG, expected_entity_count=99)
    rep = run_artifact(ARTIFACT_MD, cfg)
    assert not rep.ok


def test_missing_mermaid_block_fails():
    import re
    md = re.sub(r"```mermaid.*?```", "(diagram removed)", ARTIFACT_MD, flags=re.DOTALL)
    rep = run_artifact(md)
    names = {n: ok for n, ok, _ in rep.checks}
    assert not rep.ok
    assert any("Mermaid erDiagram block present" in n and not ok for n, ok, _ in rep.checks)


def test_invalid_mermaid_too_few_entities_fails():
    import re
    block = re.search(r"```mermaid.*?```", ARTIFACT_MD, re.DOTALL).group(0)
    tiny = "```mermaid\nerDiagram\n    only_one {\n        INTEGER id PK\n    }\n```"
    rep = run_artifact(ARTIFACT_MD.replace(block, tiny))
    assert not rep.ok


def test_truncated_path_detected():
    bad = ARTIFACT_MD + "\n| X | `x` | None | `schemas/.../19.json` | VERIFIED |\n"
    assert v.find_truncated_paths(bad), "should flag schemas/.../ ellipsis"
    rep = run_artifact(bad)
    assert not rep.ok


def test_current_artifact_has_no_truncated_paths():
    assert v.find_truncated_paths(ARTIFACT_MD) == []


def test_missing_required_section_fails():
    md = ARTIFACT_MD.replace("Self-Consistency Check", "Removed Heading")
    rep = run_artifact(md)
    assert not rep.ok
    assert v.missing_sections(md, CONFIG["required_sections"]) == ["Self-Consistency Check"]


# --------------------------------------------------------------------------- #
# 4. Reconciliation logic unit test
# --------------------------------------------------------------------------- #
def test_reconciliation_all_sources_agree():
    inv = len(v.extract_inventory(ARTIFACT_MD))
    pk = len(v.extract_pk_rows(ARTIFACT_MD))
    _, mer = v.extract_mermaid_entities(ARTIFACT_MD)
    app = len(v.extract_appendix_entities(ARTIFACT_MD))
    assert inv == pk == len(mer) == app == CONFIG["expected_entity_count"]


def test_required_sections_all_present_in_artifact():
    assert v.missing_sections(ARTIFACT_MD, CONFIG["required_sections"]) == []


# --------------------------------------------------------------------------- #
# 5. Live Room schema cross-check (offline fixture)
# --------------------------------------------------------------------------- #
def test_parse_room_schema_mini_fixture():
    parsed = v.parse_room_schema_json(MINI)
    assert parsed["version"] == 2
    assert set(parsed["tables"]) == {"widget", "gadget"}
    assert parsed["fk_count"] == 0


def test_live_schema_cross_check_reports_undocumented(tmp_path):
    # mini fixture tables are NOT in the real artifact -> should fail the doc check
    rep = v.Report()
    v.validate_live_schema(ARTIFACT_MD, MINI, rep)
    assert not rep.ok  # widget/gadget undocumented in the android artifact


# --------------------------------------------------------------------------- #
# 6. Prisma generalizability (W19)
# --------------------------------------------------------------------------- #
def test_prisma_detects_exactly_one_fk():
    parsed = v.parse_prisma_schema(PRISMA)
    assert parsed["models"] == ["User", "Post", "Tag"]
    assert parsed["verified_fks"] == 1


def test_prisma_fk_matches_expected_json():
    rep = v.Report()
    v.validate_prisma(PRISMA, rep, expected_fk=None)  # reads sibling expected_fk_count.json
    assert rep.ok


def test_prisma_cli_exit_zero():
    assert v.main(["--stack", "prisma", "--prisma", str(PRISMA)]) == 0
