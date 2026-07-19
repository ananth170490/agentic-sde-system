# Demo Mode

## Purpose

This document defines two operating modes:

1. Real-provider mode (OpenAI-first) for realistic live demonstrations.
2. Deterministic demo mode for stable fallback demonstrations.

It also captures the production-readiness path from assignment prototype to operational service.

## Part A: Real-Provider Demo Mode (Recommended)

Use this mode when you want to show authentic model behavior and full orchestration semantics.

## OpenAI Configuration

Set `.env`:

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=<your_openai_key>
OPENAI_MODEL=gpt-4o-mini
DEMO_MODE=false
```

Important: provider model selection belongs in `OPENAI_MODEL`. Keep the API endpoint in `OPENAI_BASE_URL`.

Optional endpoint override:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
```

Start runtime:

```bash
docker compose up -d --build orchestrator
```

## Real-Provider Operational Behavior

- The orchestrator performs structured-output calls via OpenAI.
- If provider response parsing fails, schema-safe fallback is applied.
- If provider request fails (for example quota/billing block), run completion still remains controlled.
- Reviewer-facing summaries use sanitized, humanized failure text.

Sanitized summary example:

```text
Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.
```

## Part B: Deterministic Demo Mode

Use this mode when internet/provider access is unstable or unavailable.

Set `.env`:

```env
DEMO_MODE=true
MODEL_PROVIDER=anthropic
```

Behavior:

- deterministic `POST /requirements` responses for supported prompts
- controlled plan-review and merge-review transitions
- repeatable gate behavior for live interviews

## Quick API Demo Sequence

1. Submit requirement:

```bash
curl -s -X POST http://127.0.0.1:8000/requirements \
  -H "Content-Type: application/json" \
  -d '{"text":"Build a scalable URL shortener service with APIs, persistence, and analytics."}'
```

2. Inspect run:

```bash
curl -s http://127.0.0.1:8000/runs/<RUN_ID>
```

3. Approve gate:

```bash
curl -s -X POST http://127.0.0.1:8000/runs/<RUN_ID>/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback":"approved"}'
```

Repeat approval at next gate until completion.

## Production Readiness Plan

This plan supports the assignment expectation of production-grade engineering quality: reliability, safety, observability, and defensible operational behavior.

## 1. Reliability and API Contracts

- standardize error schema (`code`, `message`, `details`, `request_id`)
- enforce provider and subprocess timeouts
- add idempotency for approval/resume endpoints
- add readiness/liveness probes

## 2. Security

- require authN/authZ for mutating endpoints
- move secrets to managed secret store
- add request-size and rate limits
- run dependency and image vulnerability scans in CI

## 3. Data and Persistence

- migrate from SQLite to PostgreSQL for multi-instance operation
- add schema migrations and backup/restore drills
- define retention policy for run history and artifacts

## 4. Observability

- structured logs keyed by `run_id` and `request_id`
- tracing across API, provider, and validator steps
- metrics for phase latency, failure rates, and retry counts
- alerts for elevated provider failure and task rejection rates

## 5. Orchestration Hardening

- maintain schema-validated structured outputs at each node
- keep fallback paths domain-safe and phase-safe
- keep terminal rejection summaries explicit and actionable

## 6. Test and Delivery Discipline

- preserve deterministic tests for graph and API contracts
- add provider fault-injection tests
- add load and chaos tests for resume/retry behavior
- enforce CI quality gates before deployment

## Production Exit Criteria

Before go-live:

- no unauthenticated write endpoints
- health probes and dashboards are active
- backup and restore tested
- CI/CD gates and rollback verified
- E2E smoke run passes in production-like environment
- incident runbooks and ownership are documented
