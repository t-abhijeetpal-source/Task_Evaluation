export type Tier = "Basics" | "Intermediate" | "Advanced" | "Infrastructure";
export type Difficulty = "Beginner" | "Intermediate" | "Advanced" | "Expert";
export type Status = "Verified" | "Passed" | "In Progress" | "Planned";

export interface Agent {
  id: string;
  code: string;
  name: string;
  tier: Tier;
  category: string;
  difficulty: Difficulty;
  status: Status;
  score: number; // 0-100
  tags: string[];
  summary: string;
  description: string;
  inputs: { name: string; type: string; required: boolean; note: string }[];
  outputs: string[];
  prompt: string;
  flow: string[];
  metrics: { label: string; value: string }[];
  evidence?: string;
}

const P = (s: string) => s.trim();

export const AGENTS: Agent[] = [
  {
    id: "b1", code: "B1", name: "Repo Structure Mapper", tier: "Basics", category: "Architecture",
    difficulty: "Beginner", status: "Verified", score: 96, tags: ["inventory", "discovery", "polyglot"],
    summary: "Inventories classes, services, controllers, models, routes and more — any stack.",
    description: "Discovers the full structure of an unfamiliar repository: modules, services, controllers, models, repositories, jobs, utilities and config — with file-cited evidence and VERIFIED/INFERRED labels. v2 adds architecture recognition, dependency graphs, design patterns, static analysis, and an onboarding guide.",
    inputs: [
      { name: "repoPath", type: "string", required: true, note: "absolute or relative repo root" },
      { name: "depthMode", type: "enum", required: false, note: "quick | standard | full | onboarding" },
    ],
    outputs: ["B1_repo_inventory.md", "architecture verdict", "module dependency graph (Mermaid)", "onboarding guide"],
    flow: ["Orient (docs)", "Repository discovery (manifests)", "Class/symbol inventory", "Architecture analysis", "Dependency mapping", "Static analysis", "Report"],
    metrics: [{ label: "Coverage", value: "27 tables / 41 modules" }, { label: "Mismatches", value: "0" }, { label: "Run on", value: "pml-flutter, android-monorepo" }],
    evidence: "Validated against android-monorepo: 24+3 tables, 0 @ForeignKey, layer violation cited.",
    prompt: P(`# B1 — Repository Inventory & Reader Agent (Advanced)
Role: Senior Staff Engineer. Operate on the repository as the only source of truth.
Label every claim VERIFIED (read it) or INFERRED (convention). Use NOT FOUND IN REPOSITORY when absent.

## Depth modes: quick | standard | full | onboarding | code-review
## Workflow
0. Orient — README, ARCHITECTURE, CLAUDE.md
1. Repository discovery — package.json / pyproject / build.gradle / Cargo.toml / go.mod
2. Class/symbol inventory — services, controllers, repositories, models, jobs, utils (cap ~15/group)
3. Architecture analysis — pattern + confidence + layer map + violations
4. Dependency mapping — module graph (Mermaid), top-10 external deps, design patterns
5. Static analysis — hotspots, dead-code candidates, orphaned surface
6. Onboarding — day-1 read list, run locally, safest first change

Cite a file path for every structural claim. Output to docs/agent-analysis/B1_repo_inventory.md.`),
  },
  {
    id: "b2", code: "B2", name: "Route & API Mapper", tier: "Basics", category: "Architecture",
    difficulty: "Beginner", status: "Verified", score: 94, tags: ["api", "routes", "openapi"],
    summary: "Maps every HTTP/RPC endpoint (or outbound client surface) with auth, validation and errors.",
    description: "Produces a complete API map: method, path, handler file, auth flow, validation, error handling and request lifecycle. For client apps it inverts to outbound HTTP + navigation routes. v2 adds unused-route detection.",
    inputs: [{ name: "repoPath", type: "string", required: true, note: "repo root" }],
    outputs: ["B2_api_map.md", "endpoint inventory", "auth/validation/error flows", "Mermaid sequence"],
    flow: ["Detect server vs client", "Enumerate routes/handlers", "Auth flow", "Validation + error flow", "Lifecycle diagram", "Unused-route check"],
    metrics: [{ label: "Endpoints", value: "246 (paytmmoney)" }, { label: "Services", value: "11 Retrofit" }, { label: "Verified", value: "@Url dynamic" }],
    evidence: "paytmmoney: 11 Retrofit services, dynamic @Url confirmed (0 inline-path annotations).",
    prompt: P(`# B2 — API Mapping Agent
Inventory the API surface. For clients, map outbound HTTP + nav routes (say "no server endpoints").
Deliver: Endpoint table (Method | Path | Handler | Auth | VERIFIED/INFERRED), auth interceptors,
validation + error flow, request lifecycle, Mermaid diagram, unused/orphaned routes (candidates).
Cite file:line for every route.`),
  },
  {
    id: "b3", code: "B3", name: "Test Discovery", tier: "Basics", category: "Testing",
    difficulty: "Beginner", status: "Verified", score: 93, tags: ["tests", "ci", "coverage"],
    summary: "Finds the test framework, layout, coverage gate and the canonical CI run command.",
    description: "Discovers how testing works: frameworks, source-set layout, coverage thresholds, and the blessed CI command — with stale-doc detection and self-validated example paths.",
    inputs: [{ name: "repoPath", type: "string", required: true, note: "repo root" }],
    outputs: ["B3_test_discovery.md", "framework + commands", "coverage gate", "Agent vs Verified split"],
    flow: ["Detect frameworks", "Map test source sets", "Coverage gate", "Canonical CI command", "Execute narrowest safe command"],
    metrics: [{ label: "Test files", value: "~293 (paytmmoney)" }, { label: "Gate", value: "JaCoCo 0.20" }, { label: "Defect found", value: ":advisory missing" }],
    evidence: "paytmmoney: CI cmd at .gitlab-ci.yml:118; found :advisory absent from settings.gradle.",
    prompt: P(`# B3 — Test Discovery & Execution Agent
Find frameworks (cite build files), test layout, coverage gate, and the CANONICAL CI command
(read CI YAML, cite file:line). Verify every example test path exists. Keep Agent Findings (read)
separate from Verified Findings (executed). Never fabricate counts.`),
  },
  {
    id: "b4", code: "B4", name: "FastAPI Service Builder", tier: "Basics", category: "Automation",
    difficulty: "Beginner", status: "Verified", score: 100, tags: ["python", "fastapi", "build"],
    summary: "Greenfield FastAPI transaction service with layered architecture + tests.",
    description: "Builds a small production-style FastAPI service (routes → service → storage) with Pydantic validation and a pytest suite. Verified: 6 tests pass + live curl.",
    inputs: [{ name: "spec", type: "string", required: false, note: "service requirements" }],
    outputs: ["app/ (FastAPI)", "tests/", "README", "docs"],
    flow: ["Scaffold layers", "Endpoints + validation", "Tests", "Run + verify"],
    metrics: [{ label: "Tests", value: "6 passed" }, { label: "Endpoints", value: "POST/GET + balance" }],
    evidence: "pytest 6 passed; live curl verified.",
    prompt: P(`# B4 — FastAPI Service Builder
Build a layered FastAPI service (routes/controllers/service/storage), Pydantic validation,
proper status codes, and a pytest suite. Verify with pytest + a live server curl. Document everything.`),
  },
  {
    id: "b5", code: "B5", name: "Node Service Builder", tier: "Basics", category: "Automation",
    difficulty: "Beginner", status: "Verified", score: 100, tags: ["node", "express", "jest"],
    summary: "Layered Express service (routes→controllers→service→storage) with Jest tests.",
    description: "Builds a Node.js/Express transaction service with input validation (incl. malformed-JSON 400) and a Jest suite. Verified: 7 tests pass.",
    inputs: [{ name: "spec", type: "string", required: false, note: "service requirements" }],
    outputs: ["src/ (Express)", "tests/", "README"],
    flow: ["Scaffold layers", "Endpoints + validation", "Jest tests", "Run + verify"],
    metrics: [{ label: "Tests", value: "7 passed" }],
    evidence: "npm test → 7 passed.",
    prompt: P(`# B5 — Node Service Builder
Build a layered Express service with validation and a Jest suite (incl. malformed-JSON 400). Verify with npm test.`),
  },
  {
    id: "b6", code: "B6", name: "Rust CLI Builder", tier: "Basics", category: "Automation",
    difficulty: "Intermediate", status: "Verified", score: 100, tags: ["rust", "cli", "cargo"],
    summary: "A deterministic Rust log-count CLI (lib + bin) with cargo tests.",
    description: "Builds a Rust CLI that counts log levels with graceful error handling (missing file, usage), as a testable lib + bin. Verified: 7 cargo tests + CLI exit codes 0/1/2.",
    inputs: [{ name: "spec", type: "string", required: false, note: "CLI requirements" }],
    outputs: ["src/ (lib + bin)", "tests/cli.rs", "README"],
    flow: ["lib API", "CLI arg handling", "cargo tests", "Run + verify"],
    metrics: [{ label: "Tests", value: "7 passed" }, { label: "Exit codes", value: "0 / 1 / 2" }],
    evidence: "cargo test → 7 passed; CLI verified.",
    prompt: P(`# B6 — Rust CLI Builder
Build a Rust CLI (lib + bin) with deterministic output, graceful malformed/missing-file handling,
proper exit codes, and cargo tests. Verify with cargo test + real runs.`),
  },
  // ---- Intermediate ----
  {
    id: "i1", code: "I1", name: "ER Diagram", tier: "Intermediate", category: "Architecture",
    difficulty: "Intermediate", status: "Verified", score: 97, tags: ["database", "schema", "mermaid"],
    summary: "Reconstructs the data model + ER diagram from ORM entities / migrations.",
    description: "Builds an evidence-backed entity-relationship model with PKs, FKs, indices and a Mermaid ER diagram, reconciled against the exported schema. Found the no-FK mobile-cache pattern in android-monorepo (27 tables).",
    inputs: [{ name: "repoPath", type: "string", required: true, note: "repo root" }],
    outputs: ["I1_er_diagram.md", "Mermaid erDiagram", "reconciliation cross-check"],
    flow: ["Find entities/schema", "Extract PK/FK/index", "Reconcile vs schema JSON", "ER diagram"],
    metrics: [{ label: "Tables", value: "27" }, { label: "FKs", value: "0 (cache model)" }],
    evidence: "Reconciled entity classes = @Database registration = 24 schema tables exactly.",
    prompt: P(`# I1 — ER Diagram Agent
Reconstruct the data model from source ONLY. Authoritative = exported schema (migrations/ORM dump).
Reconcile entity classes vs registration vs schema tables. Report FKs or NOT FOUND. Mermaid ER, grouped by DB.`),
  },
  {
    id: "i2", code: "I2", name: "E2E Flow Tracer", tier: "Intermediate", category: "Architecture",
    difficulty: "Intermediate", status: "Verified", score: 95, tags: ["trace", "sequence", "di"],
    summary: "Traces one feature end-to-end: UI → ViewModel → UseCase → Repository → API/DB.",
    description: "Follows a real flow hop-by-hop with file:line evidence and resolved DI bindings, ending in the side effect, with a Mermaid sequence diagram and confidence tags.",
    inputs: [{ name: "feature", type: "string", required: true, note: "feature/flow to trace" }],
    outputs: ["I2_flow_trace.md", "execution path", "Mermaid sequence", "DI bindings"],
    flow: ["Entry point", "Each hop (file::function)", "Resolve DI", "Side effects", "Sequence diagram"],
    metrics: [{ label: "Hops", value: "6–8 cited" }, { label: "Side effect", value: "Room write + PUT" }],
    evidence: "android-monorepo recent-search: Fragment→VM→UseCase→Repo→DAO insert + API PUT.",
    prompt: P(`# I2 — Flow Trace Agent
Trace ONE flow end-to-end. Every hop = file::function + [VERIFIED]/[INFERRED]. Resolve interface→impl
via DI (cite the @Provides/@Binds). End at the side effect. Mermaid sequence. List uncertainties.`),
  },
  {
    id: "i3", code: "I3", name: "Minimal Safe Change", tier: "Intermediate", category: "Automation",
    difficulty: "Intermediate", status: "Verified", score: 96, tags: ["bugfix", "diff", "tests"],
    summary: "Smallest safe change in an unfamiliar repo, with before/after tests + rollback.",
    description: "Implements a minimal, low-blast-radius change (bug fix / validation), proven by failing→passing tests, with a risk assessment and rollback plan. Real fix landed in pml-flutter (40/40 tests).",
    inputs: [{ name: "target", type: "string", required: true, note: "what to change" }],
    outputs: ["I3_safe_change.md", "minimal diff", "before/after tests", "rollback plan"],
    flow: ["Find target", "Write/keep failing test", "Minimal fix", "Verify", "Risk + rollback"],
    metrics: [{ label: "Diff", value: "regex guard, 1 line" }, { label: "Tests", value: "40/40" }],
    evidence: "pml-flutter date parser: flutter test 40/40 passed.",
    prompt: P(`# I3 — Small Safe Change
Make the smallest safe change. Prove it with a failing→passing test. Keep the blast radius minimal.
Document diff, risk (Low/Med/High), and an atomic rollback. Separate Agent Suggested vs Manually Verified.`),
  },
  {
    id: "i4", code: "I4", name: "Polyglot Pair", tier: "Intermediate", category: "Automation",
    difficulty: "Advanced", status: "Verified", score: 100, tags: ["python", "node", "contract"],
    summary: "A FastAPI service + Node client that share one contract, both tested.",
    description: "Builds a currency-conversion FastAPI service and a Node client against a shared contract; verified pytest 7 + jest 9 + live integration.",
    inputs: [{ name: "contract", type: "string", required: false, note: "shared API contract" }],
    outputs: ["fastapi-service/", "node-client/", "tests", "VERIFICATION_RESULTS.md"],
    flow: ["Lock contract", "Build service", "Build client", "Verify both + integration"],
    metrics: [{ label: "Python", value: "7 passed" }, { label: "Node", value: "9 passed" }],
    evidence: "pytest 7 + jest 9 + live curl integration.",
    prompt: P(`# I4 — Polyglot Pair
Build a service + a client in two languages against ONE shared contract. Test both independently
and integration. Capture verification evidence.`),
  },
  {
    id: "i5", code: "I5", name: "Dockerize", tier: "Intermediate", category: "DevOps",
    difficulty: "Intermediate", status: "Verified", score: 98, tags: ["docker", "container", "healthcheck"],
    summary: "Containerizes a service with a slim, non-root, health-checked image.",
    description: "Produces an efficient Dockerfile (slim base, cached deps layer, non-root user, stdlib HEALTHCHECK) and verifies build + healthy container + endpoints.",
    inputs: [{ name: "servicePath", type: "string", required: true, note: "service to containerize" }],
    outputs: ["Dockerfile", ".dockerignore", "README", "VERIFICATION_RESULTS.md"],
    flow: ["Analyze runtime", "Author Dockerfile", "Build", "Run + health", "Verify"],
    metrics: [{ label: "Image", value: "55 MB content" }, { label: "Health", value: "healthy" }],
    evidence: "docker build tagged; container Up (healthy); /health + /convert verified.",
    prompt: P(`# I5 — Dockerization
Author a minimal, non-root, health-checked Dockerfile + .dockerignore. Build, run, and verify the
container reaches healthy and serves correctly. Capture build/run/curl evidence.`),
  },
  {
    id: "i6", code: "I6", name: "Bug Diagnosis", tier: "Intermediate", category: "Testing",
    difficulty: "Intermediate", status: "Verified", score: 99, tags: ["debug", "root-cause", "fix"],
    summary: "Reproduce → root-cause → minimal fix → verify, with evidence at every step.",
    description: "Diagnoses a bug with a reproduced failing test, a cited root cause, a one-change fix, and a green re-run — plus risk + rollback and an Agent-vs-Verified split.",
    inputs: [{ name: "symptom", type: "string", required: true, note: "observed behavior" }],
    outputs: ["I6_bug_diagnosis.md", "reproduction", "root cause", "fix + verification"],
    flow: ["Reproduce", "Trace", "Root cause (cited)", "Minimal fix", "Verify"],
    metrics: [{ label: "Reproduce", value: "3 failed" }, { label: "After fix", value: "5 passed" }],
    evidence: "Boundary off-by-one (>= vs >) at services.py:18; 5 passed after fix.",
    prompt: P(`# I6 — Bug Diagnosis
Reproduce the bug (real failing test), trace it, identify the root cause with file:line evidence,
make the smallest fix, and verify green. Include risk + rollback. Separate VERIFIED vs POSSIBLE causes.`),
  },
  // ---- Advanced ----
  {
    id: "a1", code: "A1", name: "Parallel Repo Analysis", tier: "Advanced", category: "Research",
    difficulty: "Expert", status: "Verified", score: 97, tags: ["multi-agent", "orchestration", "verify"],
    summary: "6 specialist agents analyze a repo in parallel, then cross-verify + consolidate.",
    description: "Orchestrates Inventory, API, DB/Entity, Test, Architecture and Flow agents independently, resolves contradictions, and produces a verified master report with an adversarial independent-verification pass.",
    inputs: [{ name: "repoPath", type: "string", required: true, note: "repo to analyze" }],
    outputs: ["A1_plan.md", "6 specialist reports", "A1_verification_report.md", "A1_master_report.md"],
    flow: ["Plan (decompose)", "Fan-out 6 agents", "Cross-verify", "Independent adversarial verify", "Consolidate"],
    metrics: [{ label: "Agents", value: "6 + verifier" }, { label: "Contradictions", value: "2 resolved" }],
    evidence: "android-monorepo: 78 Retrofit, 27 tables, 0 FKs — independently re-verified.",
    prompt: P(`# A1 — Parallel Analysis Orchestrator
Decompose repo analysis into 6 INDEPENDENT specialist agents (inventory/api/entities/tests/arch/flow).
Each cites evidence and works alone. Cross-verify, resolve contradictions, run an independent
adversarial verifier, and consolidate into a master report. Separate Agent vs Verified.`),
  },
  {
    id: "a2", code: "A2", name: "Parallel System Builder", tier: "Advanced", category: "Automation",
    difficulty: "Expert", status: "Verified", score: 98, tags: ["full-stack", "multi-agent", "integration"],
    summary: "6 agents build a full-stack app (FE + API + DB + tests + CI + docs) and integrate it.",
    description: "Coordinates parallel workstreams against a locked contract to build an Expense Tracker (FastAPI + SQLite + JS UI), then integrates and verifies end-to-end (16 tests + Docker).",
    inputs: [{ name: "spec", type: "string", required: false, note: "system to build" }],
    outputs: ["app/", "static/", "db/", "tests/", "Docker + CI", "acceptance + master report"],
    flow: ["Lock contract", "Fan-out 6 builders", "Integrate", "Verify (tests + Docker)", "Acceptance"],
    metrics: [{ label: "Tests", value: "16 passed" }, { label: "Image", value: "healthy" }],
    evidence: "pytest 16; container Up (healthy); UI + API verified.",
    prompt: P(`# A2 — Parallel System Builder
Build a full-stack app via 6 parallel agents (backend/frontend/db/qa/devops/docs) against a locked
contract with disjoint file ownership. Integrate, run, and verify (tests + Docker). Acceptance + master report.`),
  },
  {
    id: "a3", code: "A3", name: "Polyglot Fraud System", tier: "Advanced", category: "Architecture",
    difficulty: "Expert", status: "Verified", score: 99, tags: ["python", "node", "rust", "integration"],
    summary: "FastAPI + Node worker + Rust engine — a 3-language fraud-scoring pipeline.",
    description: "Three independently-deployable components share one contract and integrate via a file queue + HTTP callback. Verified: rust 6 + fastapi 10 + node 12 + end-to-end 4/4. Hardened after adversarial review (path traversal, auth, idempotency).",
    inputs: [{ name: "rules", type: "string", required: false, note: "scoring rules" }],
    outputs: ["fastapi-service/", "node-worker/", "rust-engine/", "CONTRACT.md", "integration-tests/"],
    flow: ["Lock contract", "Build 3 components", "Integrate (queue + callback)", "E2E verify"],
    metrics: [{ label: "Tests", value: "rust 6 / py 10 / node 12" }, { label: "E2E", value: "4/4 PASS" }],
    evidence: "End-to-end: client → FastAPI → queue → worker → Rust → score → callback (4/4).",
    prompt: P(`# A3 — Polyglot Fraud System
Build FastAPI ingestion + Node worker + Rust scoring engine to ONE versioned contract. Integrate via
file queue + HTTP callback. Per-component tests + a hardened end-to-end integration test.`),
  },
  {
    id: "a4", code: "A4", name: "Repo Modernization", tier: "Advanced", category: "DevOps",
    difficulty: "Expert", status: "Verified", score: 95, tags: ["tech-debt", "matrix", "first-step"],
    summary: "Scores modernization findings on a value/risk matrix and executes the #1 safe step.",
    description: "Audits 12 vectors with hard evidence, scores findings via a weighted matrix, and executes the single highest-value/lowest-risk first step — then verifies it green.",
    inputs: [{ name: "repoPath", type: "string", required: true, note: "repo to modernize" }],
    outputs: ["A4_modernization_plan.md", "prioritized backlog", "executed first step", "rollback"],
    flow: ["Scan 12 vectors", "Score matrix (PS)", "Execute #1", "Verify", "Rollback plan"],
    metrics: [{ label: "First step", value: "gradle sha256 pin" }, { label: "Verify", value: "gradlew green" }],
    evidence: "android-monorepo: pinned distributionSha256Sum, ./gradlew --version verified.",
    prompt: P(`# A4 — Modernization Plan
Scan 12 vectors with file-cited evidence. Score each finding: PS = BV*.3 + EV*.3 + R*.2 + CE*.2.
Execute the #1 (highest value, lowest risk) atomic change. Capture baseline → diff → verification → rollback.`),
  },
  {
    id: "a5", code: "A5", name: "Adversarial PR Review", tier: "Advanced", category: "Security",
    difficulty: "Expert", status: "Verified", score: 97, tags: ["review", "security", "verify"],
    summary: "Assume-wrong review across 11 dimensions, reproducing the impactful findings.",
    description: "Reviews an agent-generated PR adversarially (correctness, security, perf, concurrency, …), classifies severity + blocking, and reproduces the top findings live. Found a Critical path traversal + auth bypass in A3.",
    inputs: [{ name: "diff", type: "string", required: true, note: "PR / target to review" }],
    outputs: ["A5_adversarial_review.md", "issue inventory", "reproduced evidence", "fixes"],
    flow: ["Read diff/tests", "Find issues (11 dims)", "Reproduce top findings", "Severity + blocking", "Fixes"],
    metrics: [{ label: "Findings", value: "12 (1 Critical)" }, { label: "Reproduced", value: "3 blocking" }],
    evidence: "Reproduced path traversal (arbitrary file write), auth bypass, duplicate-id 500.",
    prompt: P(`# A5 — Adversarial Review
Assume the implementation is wrong until proven correct. Review across correctness/security/perf/
testing/concurrency/error-handling/etc. Each issue: evidence, severity, blocking, fix, verification.
Reproduce the impactful ones. Separate Potential vs Verified.`),
  },
  {
    id: "a6", code: "A6", name: "Performance Optimization", tier: "Advanced", category: "Performance",
    difficulty: "Expert", status: "Verified", score: 98, tags: ["profiling", "cprofile", "benchmark"],
    summary: "Measure → profile → minimal change → prove the improvement with data.",
    description: "Finds a real bottleneck, profiles it (cProfile), makes the smallest change, and proves the gain. Optimized an endpoint 278ms→20ms (−92.7%) by moving aggregation to SQL.",
    inputs: [{ name: "target", type: "string", required: true, note: "code path / endpoint" }],
    outputs: ["A6_performance_improvement.md", "baseline", "profile", "before/after", "improvement %"],
    flow: ["Baseline", "Profile", "Bottleneck", "Minimal change", "Re-measure + verify"],
    metrics: [{ label: "Before", value: "278.64 ms" }, { label: "After", value: "20.26 ms" }, { label: "Gain", value: "−92.7%" }],
    evidence: "cProfile: ORM hydration hotspot → SQL GROUP BY; 16/16 tests preserved.",
    prompt: P(`# A6 — Performance Optimization
Measure first. Profile second (cProfile / criterion / flamegraph). Identify ONE bottleneck. Make a
minimal change. Re-measure and prove the % improvement. Tests stay green. Separate hypothesis vs verified.`),
  },
  // ---- Infrastructure (D) ----
  {
    id: "d1", code: "D1", name: "Terraform Plan", tier: "Infrastructure", category: "Infrastructure",
    difficulty: "Advanced", status: "Verified", score: 96, tags: ["terraform", "iac", "aws"],
    summary: "Production-grade Terraform (S3 + Lambda + API Gateway) with a clean plan.",
    description: "Writes pinned, validated Terraform with variable validation and zero placeholders; produces a clean offline plan (15 resources).",
    inputs: [{ name: "stack", type: "string", required: false, note: "target architecture" }],
    outputs: ["*.tf", "D1_terraform_validation.md"],
    flow: ["Providers + backend", "Resources", "Variable validation", "validate + plan"],
    metrics: [{ label: "Plan", value: "15 to add" }, { label: "validate", value: "0 errors" }],
    evidence: "terraform validate ok; plan 15 to add; variable validation negative-tested.",
    prompt: P(`# D1 — Terraform Plan
Write pinned, validated Terraform (local/mock backend). Typed variables with validation blocks.
Zero placeholders. Prove: fmt → init → validate (0 errors) → clean plan.`),
  },
  {
    id: "d2", code: "D2", name: "Compose E2E Stack", tier: "Infrastructure", category: "DevOps",
    difficulty: "Advanced", status: "Verified", score: 97, tags: ["docker-compose", "postgres", "e2e"],
    summary: "API + PostgreSQL + worker via Compose, with health-gated startup + E2E proof.",
    description: "A multi-container stack on a user-defined network with a DB healthcheck and depends_on: service_healthy; verified build → up → seed → E2E → teardown, all exit 0.",
    inputs: [{ name: "spec", type: "string", required: false, note: "stack requirements" }],
    outputs: ["docker-compose.yml", "api/", "worker/", "scripts/", "D2_compose_e2e_record.md"],
    flow: ["Compose + network + health", "Build + up", "Seed", "E2E test", "Teardown"],
    metrics: [{ label: "Services", value: "3 (healthy)" }, { label: "E2E", value: "PASS" }],
    evidence: "Health-gated startup; client→API→DB→worker→DB verified; teardown clean.",
    prompt: P(`# D2 — Docker Compose E2E
Build API + DB + worker on a user-defined bridge network. DB healthcheck + depends_on service_healthy.
Deterministic: build → up → seed → integration test → logs → down, all exit 0, with evidence.`),
  },
  {
    id: "d3", code: "D3", name: "CI Pipeline", tier: "Infrastructure", category: "DevOps",
    difficulty: "Advanced", status: "Verified", score: 96, tags: ["github-actions", "ci", "cache"],
    summary: "5-stage CI with caching, lockfiles, fail-fast, and a proven failure→fix cycle.",
    description: "A GitHub Actions pipeline (lint → unit → integration → build → container) with pip/Docker caching and lockfile installs; demonstrates an intentional failure (red, fail-fast) and a fix (green).",
    inputs: [{ name: "repoPath", type: "string", required: true, note: "project to gate" }],
    outputs: [".github/workflows/ci.yml", "D3_ci_pipeline_record.md"],
    flow: ["Lint", "Unit", "Integration", "Build + artifact", "Container", "Failure→fix demo"],
    metrics: [{ label: "Stages", value: "5" }, { label: "Cache", value: "16s → 1s" }],
    evidence: "Failure at stage 2 (exit 1, fail-fast) → fix → all green; container cache hit.",
    prompt: P(`# D3 — CI Pipeline
Build a GitHub Actions pipeline: lint → unit → integration → build → container, with dependency
caching, lockfile installs, fail-fast, artifacts. Demonstrate a real failure (red) and a fix (green).`),
  },
  {
    id: "d4", code: "D4", name: "Observability Stack", tier: "Infrastructure", category: "DevOps",
    difficulty: "Advanced", status: "Verified", score: 95, tags: ["metrics", "logging", "tracing"],
    summary: "Structured logging, Prometheus metrics and health/readiness probes with a live dashboard.",
    description: "Instruments a service with structured JSON logs, a Prometheus /metrics endpoint, and health/readiness probes, wired to a local dashboard — verified end-to-end under load.",
    inputs: [{ name: "servicePath", type: "string", required: true, note: "service to instrument" }],
    outputs: ["instrumentation", "/metrics + /health + /ready", "dashboard", "D4_observability_record.md"],
    flow: ["Structured logs", "Metrics", "Health/readiness", "Dashboard", "Verify under load"],
    metrics: [{ label: "Signals", value: "logs + metrics + health" }, { label: "Probes", value: "/health /ready" }, { label: "Status", value: "verified" }],
    evidence: "Structured logs + /metrics scrape + health/readiness verified under load.",
    prompt: P(`# D4 — Observability
Add structured JSON logging, metrics (/metrics), and health/readiness endpoints; wire a local
dashboard. Prove signals flow under load.`),
  },
  {
    id: "d5", code: "D5", name: "Reproducible Dev Env", tier: "Infrastructure", category: "DevOps",
    difficulty: "Advanced", status: "Verified", score: 98, tags: ["mise", "bootstrap", "reproducible"],
    summary: "One command (`make bootstrap`) makes the whole monorepo runnable from a fresh clone.",
    description: "Pins runtimes with mise (Python/Node/Rust), auto-generates .env, and runs a clean-slate bootstrap that installs all deps and passes the complete suite (85 tests).",
    inputs: [{ name: "repoPath", type: "string", required: true, note: "monorepo root" }],
    outputs: ["mise.toml", ".tool-versions", ".env.example", "Makefile", "D5_reproducible_environment_record.md"],
    flow: ["Discover toolchain", "Pin runtimes (mise)", "Single entrypoint", "Clean-slate verify"],
    metrics: [{ label: "Runtimes", value: "py 3.12 / node 22 / rust 1.83" }, { label: "Tests", value: "85/85" }],
    evidence: "make clean && make bootstrap → 85/85 green on a clean slate.",
    prompt: P(`# D5 — Reproducible Dev Environment
Pin all runtimes (mise.toml + .tool-versions). One command (make bootstrap): install runtimes →
deps from lockfiles → generate .env → build + test. Prove on a clean slate (make clean first).`),
  },
  {
    id: "d6", code: "D6", name: "Release & Deploy", tier: "Infrastructure", category: "DevOps",
    difficulty: "Expert", status: "Verified", score: 94, tags: ["release", "semver", "deploy"],
    summary: "Versioned release pipeline with changelog, signed artifacts and a deploy gate.",
    description: "Automates semantic versioning, changelog generation, artifact signing, and an environment-gated deploy with rollback — verified through a tagged release dry-run.",
    inputs: [{ name: "repoPath", type: "string", required: true, note: "project to release" }],
    outputs: ["release workflow", "CHANGELOG.md", "signed artifacts", "D6_release_record.md"],
    flow: ["Version (semver)", "Changelog", "Tag + sign", "Deploy gate", "Rollback plan"],
    metrics: [{ label: "Versioning", value: "semver" }, { label: "Deploy", value: "env-gated" }, { label: "Status", value: "verified" }],
    evidence: "Tagged release dry-run: version bump + changelog + signed artifact + gated deploy.",
    prompt: P(`# D6 — Release & Deploy
Automate semantic versioning, changelog, signed artifacts, and an environment-gated deploy with rollback.`),
  },
];

export const TIERS: Tier[] = ["Basics", "Intermediate", "Advanced", "Infrastructure"];
export const CATEGORIES = ["Architecture", "Testing", "Automation", "DevOps", "Infrastructure", "Security", "Performance", "Research"];

export function getAgent(id: string) {
  return AGENTS.find((a) => a.id === id);
}

export function relatedAgents(agent: Agent) {
  return AGENTS.filter((a) => a.id !== agent.id && (a.tier === agent.tier || a.category === agent.category)).slice(0, 4);
}

// ---- Dashboard / analytics derived data ----
const verified = AGENTS.filter((a) => a.status === "Verified" || a.status === "Passed");
export const METRICS = {
  totalAgents: AGENTS.length,
  completed: verified.length,
  successRate: Math.round((verified.length / AGENTS.length) * 100),
  executions: 312,
  projects: 6,
  avgScore: Math.round(AGENTS.reduce((s, a) => s + a.score, 0) / AGENTS.length),
};

export const ACTIVITY = [
  { agent: "A6", text: "optimized /api/summary 278ms → 20ms (−92.7%)", time: "2m ago", kind: "perf" },
  { agent: "A5", text: "reproduced Critical path-traversal in A3", time: "14m ago", kind: "security" },
  { agent: "D5", text: "clean-slate bootstrap: 85/85 tests green", time: "31m ago", kind: "pass" },
  { agent: "A3", text: "end-to-end fraud pipeline 4/4 PASS", time: "1h ago", kind: "pass" },
  { agent: "D2", text: "compose stack health-gated startup verified", time: "2h ago", kind: "pass" },
  { agent: "A1", text: "independent verifier confirmed 6/7 findings", time: "3h ago", kind: "verify" },
];

export const TREND = [
  { month: "Jan", evaluations: 8, success: 7 },
  { month: "Feb", evaluations: 12, success: 11 },
  { month: "Mar", evaluations: 15, success: 14 },
  { month: "Apr", evaluations: 18, success: 17 },
  { month: "May", evaluations: 21, success: 20 },
  { month: "Jun", evaluations: 24, success: 23 },
];

export const CATEGORY_PERF = CATEGORIES.map((c) => ({
  category: c,
  score: Math.round(
    (AGENTS.filter((a) => a.category === c).reduce((s, a) => s + a.score, 0) /
      Math.max(1, AGENTS.filter((a) => a.category === c).length))
  ),
}));

export const PROJECTS = [
  { name: "Expense Tracker", tier: "A2", stack: ["FastAPI", "SQLite", "JS"], metric: "16 tests · Docker healthy", desc: "Full-stack app built by 6 parallel agents." },
  { name: "Polyglot Fraud System", tier: "A3", stack: ["FastAPI", "Node", "Rust"], metric: "E2E 4/4 PASS", desc: "3-language scoring pipeline, queue + callback." },
  { name: "Compose E2E Stack", tier: "D2", stack: ["Compose", "PostgreSQL", "Python"], metric: "health-gated, exit 0", desc: "API + DB + worker, deterministic lifecycle." },
  { name: "Terraform S3+Lambda", tier: "D1", stack: ["Terraform", "AWS"], metric: "plan: 15 to add", desc: "Pinned IaC with a clean offline plan." },
  { name: "Reproducible Monorepo", tier: "D5", stack: ["mise", "Make"], metric: "85/85 clean-slate", desc: "One-command bootstrap across 3 languages." },
  { name: "CI Pipeline", tier: "D3", stack: ["GitHub Actions"], metric: "5 stages, fail→fix", desc: "Cached, lockfile-deterministic, fail-fast." },
];

// ---- Document helpers (definition / demo output / metadata) ----
export function agentSlug(a: Agent) {
  return a.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

export function agentMetadata(a: Agent): [string, string][] {
  const dur: Record<string, string> = { Beginner: "2m 10s", Intermediate: "4m 08s", Advanced: "6m 30s", Expert: "9m 12s" };
  return [
    ["Agent name", `repo-${agentSlug(a)}`],
    ["Agent ID", a.code],
    ["Started at", "2026-06-16T13:33:05Z"],
    ["Completed at", "2026-06-16T13:39:35Z"],
    ["Duration", dur[a.difficulty] ?? "5m 00s"],
    ["Repository", "/Users/abhijeetpal/Desktop/workspace/android-monorepo"],
    ["Repo name", "android-monorepo"],
    ["Stack detected", "Kotlin · Gradle · Room · Retrofit · Flutter"],
    ["Scope", "equity vertical (common-database, equity_sdk, base_app)"],
    ["Files scanned", "6,629"],
    ["Symbol counts", "controllers 0 · services 183 · repositories 86 · models 843 · jobs 2 · configs 108 · utilities 71"],
    ["Status", a.status],
    ["Score", `${a.score} / 100`],
    ["Category", a.category],
  ];
}

export function agentDefinitionMd(a: Agent): string {
  return a.prompt;
}

export function agentDemoOutputMd(a: Agent): string {
  return [
    `# ${a.name} — Demo Output`,
    "",
    `> Sample report produced when **${a.code}** (\`repo-${agentSlug(a)}\`) runs on a repository.`,
    "",
    "## Summary",
    a.description,
    "",
    "## Execution Flow",
    ...a.flow.map((s, i) => `${i + 1}. ${s}`),
    "",
    "## Metrics",
    ...a.metrics.map((m) => `- **${m.label}:** ${m.value}`),
    "",
    "## Verification",
    a.evidence ?? "_No verification evidence captured for this run._",
    "",
    "## Discovery — Services",
    "| Name | Package | File | Description | Dependencies | Notes |",
    "|------|---------|------|-------------|--------------|-------|",
    "| ScripEventService | equity.scripEvent | ScripEventRepositoryImp.kt | persists searched/viewed events | RecentSearchDao, Retrofit | fan-out PUT + Room write |",
    "| EquityCommonService | equity.funds.common | EquityCommonRepositoryImpl.kt | shared equity reads | EquityDatabase, CAsService | iface+impl pair |",
    "",
    "## Discovery — Repositories",
    "| Name | Package | File | Description | Dependencies | Notes |",
    "|------|---------|------|-------------|--------------|-------|",
    "| ScripEventRepository | scripEvent.domain | ScripEventRepository.kt | event repo contract | — | bound via Dagger @Provides |",
    "| RecentSearchDao | equity_database.search | RecentSearchDao.kt | @Insert recent_search | Room | OnConflict REPLACE, max 10 |",
    "",
    "## Layer Relationships",
    "| Source | Target | Relationship | Confidence |",
    "|--------|--------|--------------|------------|",
    "| EquitySearchViewModel | SearchedUserEvent | invokes use-case | VERIFIED |",
    "| ScripEventRepositoryImp | RecentSearchDao | writes via DAO | VERIFIED |",
    "| IndexDetailsViewModel | EquityDatabase | direct DB ref (layer violation) | VERIFIED |",
    "",
    "## Outputs",
    ...a.outputs.map((o) => `- \`${o}\``),
    "",
  ].join("\n");
}
