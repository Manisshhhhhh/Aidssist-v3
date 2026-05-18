# Contributing To Aidssist v3

Aidssist v3 uses a deterministic-first backend and a React/Vite frontend. Contributions should stay small, testable, and scoped.

## Local Setup

Install dependencies:

```bash
make install
```

Check your workstation:

```bash
make doctor
```

Run the local dev stack:

```bash
make dev
```

Development URLs:

- Frontend: <http://127.0.0.1:5173>
- Backend: <http://127.0.0.1:8000>
- API docs: <http://127.0.0.1:8000/docs>

## Standard Checks

Before opening a pull request, run:

```bash
make test
make typecheck
make build
```

When Docker Desktop is running, also run:

```bash
make docker-build
make docker-up
make docker-smoke
make docker-down
```

For a release-style local gate:

```bash
make release-check
```

`release-check` requires a clean working tree. It runs tests, frontend checks, Docker Compose validation/build, and Docker smoke when Docker is available.

## CI Expectations

The default CI workflow runs on pushes and pull requests. It verifies:

- backend dependency installation and pytest
- frontend npm install, optional lint, typecheck, and build
- Docker Compose config validation
- Docker image build

The manual Docker smoke workflow can be started from GitHub Actions and verifies:

- Docker Compose build
- Docker Compose startup
- backend health
- frontend nginx
- backend smoke test
- cleanup with `docker compose down -v`

## Repository Hygiene

Do not commit `.env` files, secrets, SQLite databases, uploaded datasets, generated reports, backups, `node_modules`, Python virtual environments, frontend `dist`, or zip archives.

Gemini keys, JWT secrets, API keys, and GitHub tokens must never be committed.
