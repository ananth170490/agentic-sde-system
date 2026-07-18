# Demo Mode and Production Readiness Guide

## Purpose

This guide has two goals:

1. Provide a stable, deterministic demo flow by hardcoding orchestrator responses for sample prompts.
2. Provide a clear path to evolve this project from assignment/demo quality to production quality.

## Part A: Hardcoded Demo Mode

### What Demo Mode Does

When `DEMO_MODE=true`, the API:

- bypasses live model generation for `POST /requirements`
- returns deterministic `plan_review` payloads for supported prompts
- advances deterministically on `POST /runs/{run_id}/approve`
- completes after the second approval (plan review -> merge review -> completed)

This avoids flaky model output during demos.

### Supported Sample Prompts

Use one of these in Swagger `POST /requirements` request body `text`:

1. Build a scalable URL shortener service with APIs, persistence, and analytics.
2. Create a task management REST API with authentication, PostgreSQL persistence, and activity audit logs.
3. Build an inventory service with CRUD APIs, low-stock alerts, and daily summary analytics.

### Enable Demo Mode

1. Open `.env` in project root.
2. Set:

```env
DEMO_MODE=true
MODEL_PROVIDER=anthropic
```

Notes:

- In demo mode, model provider is not used for deterministic responses.
- Keep provider variables configured anyway for easy switching back.

### Restart API

Using Docker:

```bash
docker compose up -d --build
```

Using local uvicorn:

```bash
uvicorn orchestrator.api.main:app --reload
```

### Demo Script (Swagger UI)

1. `POST /requirements`
- Click `Try it out`.
- Body:
```json
{
  "text": "Build a scalable URL shortener service with APIs, persistence, and analytics."
}
```
- Click `Execute`.
- Capture `run_id`.

2. `GET /runs/{run_id}`
- Fill `run_id`.
- Click `Execute`.
- Expect: `status=awaiting_human`, `current_phase=plan_review`.

3. `POST /runs/{run_id}/approve`
- Fill `run_id`.
- Body:
```json
{
  "feedback": "approved"
}
```
- Click `Execute`.
- Expect: `status=awaiting_human` with merge review payload.

4. `POST /runs/{run_id}/approve` again
- Same `run_id` and body.
- Click `Execute`.
- Expect: `status=completed`.

5. `GET /runs/{run_id}`
- Verify `status=completed`, `current_phase=completed`.

### Disable Demo Mode

Set `DEMO_MODE=false` and restart API.

---

## Part B: Production Readiness Plan

## 1. Runtime and API Reliability

### Required Improvements

- Add strict request/response contracts for all endpoints.
- Return stable error codes and machine-readable error bodies.
- Add request id propagation and correlation ids.
- Add timeout policies for all model and tool calls.
- Add retry with backoff and idempotency keys where safe.

### Action Checklist

1. Add global exception handlers in FastAPI for expected error classes.
2. Define a uniform error schema (`code`, `message`, `details`, `request_id`).
3. Add middleware for request ids.
4. Set hard timeouts for provider calls and subprocess tools.
5. Add health endpoints: `/health/live`, `/health/ready`.

## 2. Security Hardening

### Required Improvements

- Add authentication/authorization for all mutating endpoints.
- Move secrets to a secret manager.
- Add input size/rate limits and abuse controls.
- Add dependency and image vulnerability scanning.

### Action Checklist

1. Protect API with OAuth2/JWT or mTLS depending on environment.
2. Replace plaintext `.env` secrets with managed secret stores.
3. Add rate limiting and payload size constraints.
4. Enable dependency scanning in CI.
5. Generate and scan SBOM for container images.

## 3. Data and State Management

### Required Improvements

- Replace SQLite for multi-instance production usage.
- Add migration framework and schema versioning.
- Add archival/retention strategy for run states.

### Action Checklist

1. Move to managed PostgreSQL.
2. Add Alembic migrations.
3. Add indexes for run lookup and phase/status queries.
4. Define retention policy and scheduled cleanup jobs.
5. Add backup and restore drills.

## 4. Observability

### Required Improvements

- Add structured logging and tracing.
- Add metrics for latency, failures, retries, queue depth.
- Add alerting and SLO dashboards.

### Action Checklist

1. Emit JSON logs with request_id and run_id.
2. Add OpenTelemetry tracing.
3. Export metrics (Prometheus/OpenTelemetry metrics).
4. Build dashboards for endpoint and orchestration phases.
5. Add alert rules for elevated error rates and latency.

## 5. Orchestration Robustness

### Required Improvements

- Guard against malformed model outputs at every stage.
- Add deterministic fallbacks for critical workflow stages.
- Add dead-letter handling for persistent task failures.

### Action Checklist

1. Keep strict schema validation with coercion where safe.
2. Add explicit fallback policies per agent node.
3. Persist failure reason taxonomy (parse, timeout, validation, execution).
4. Add run resume/retry endpoints for operators.
5. Add operator-facing run diagnostics endpoint.

## 6. Testing Strategy

### Required Improvements

- Increase unit/integration/contract coverage.
- Add non-flaky E2E tests with deterministic providers.
- Add load and chaos testing.

### Action Checklist

1. Add API contract tests for every endpoint.
2. Add regression tests for approval gates and retries.
3. Add provider mock tests for malformed payloads.
4. Add load tests for create/poll/approve cycles.
5. Add failure-injection tests for subprocess and provider outages.

## 7. Delivery and Operations

### Required Improvements

- Introduce environment promotion with quality gates.
- Add canary or blue/green deployment pattern.
- Add rollback and runbook documentation.

### Action Checklist

1. Define CI pipeline gates (lint, test, security scan, image scan).
2. Define CD strategy with progressive rollout.
3. Add rollback automation and version pinning.
4. Create incident response runbooks.
5. Run game days for failure scenarios.

## 8. Recommended Rollout Plan

1. Phase 1 (1-2 weeks): API reliability, auth, health checks, structured errors.
2. Phase 2 (1-2 weeks): PostgreSQL migration, observability, CI security scans.
3. Phase 3 (1-2 weeks): orchestration resilience, run diagnostics, operator controls.
4. Phase 4 (ongoing): load testing, cost optimization, governance and compliance.

## Production Exit Criteria

Before go-live, verify all are true:

- No unauthenticated write endpoints.
- SLO dashboards and alerts are active.
- Database backups and restore tested.
- CI/CD gates and rollback validated.
- End-to-end tests pass in a production-like environment.
- On-call runbooks and ownership are documented.
