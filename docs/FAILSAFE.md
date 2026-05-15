# Fail-Safe Mode

Aidssist V3 includes a fail-safe layer for local and internal deployments. It keeps diagnostics and downloads available while blocking risky writes during incidents.

## Read-Only Mode

```bash
export AIDSSIST_READ_ONLY_MODE=true
```

Read-only mode allows health, diagnostics, dataset reads, artifact/report downloads, job reads, audit reads, and backup listing/download. It blocks uploads, analysis generation, forecast generation, chat writes, report generation, workspace/member changes, job writes, and registration.

Blocked requests return `423 Locked`:

```json
{
  "detail": "Aidssist is in read-only maintenance mode."
}
```

## Emergency Safe Mode

```bash
export AIDSSIST_SAFE_MODE=true
```

Safe mode blocks the same risky writes and returns `503 Service Unavailable`. Use it when you suspect a bad deployment, corrupted storage, failing migrations, unsafe configuration, or accidental deletion.

## Startup Preflight

Enabled by default:

```text
AIDSSIST_STARTUP_PREFLIGHT_ENABLED=true
AIDSSIST_FAIL_FAST_ON_PREFLIGHT_ERROR=false
```

Startup preflight checks:

- database reachability
- dataset storage writability
- reports storage writability
- backup directory writability
- artifact records pointing to missing files
- stale running jobs
- LLM configuration when enabled
- JWT configuration when user auth is enabled
- CORS safety
- rate-limit settings

Set `AIDSSIST_FAIL_FAST_ON_PREFLIGHT_ERROR=true` only when startup should fail instead of serving a degraded app.

## Diagnostics

```bash
curl http://127.0.0.1:8000/diagnostics/preflight
make preflight
```

When user auth is enabled, preflight is admin-only. When auth is disabled, it is locally available, still behind API-key auth if API-key auth is enabled.

## Incident Flow

1. Enable read-only mode.
2. Run preflight: `make preflight`.
3. Create a backup: `make backup`.
4. Check jobs: `make recover-jobs`.
5. Check artifacts: `make repair-artifacts`.
6. Review logs using request ids.
7. Restore from a known-good backup only after stopping the backend.

Do not run destructive repair flags unless a fresh backup exists.
