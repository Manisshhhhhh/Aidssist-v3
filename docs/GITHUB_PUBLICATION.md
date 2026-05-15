# GitHub Publication Guide

Target owner: `Manisshhhhhh`
Target repository: `Aidssist-v3`
Project title: Aidssist v3

## Files That Must Not Be Committed

- `.env`
- `.env.*` except `.env.example` and `.env.docker.example`
- real API keys, Gemini keys, JWT secrets, GitHub tokens, or passwords
- `*.db`, `*.sqlite`, `*.sqlite3`
- `datasets/`
- `reports/`
- `backups/`
- `*.zip`
- `.venv/`, `venv/`
- `node_modules/`
- `web/dist/`
- caches and logs

## Secret Scan

Run before every first push or release tag:

```bash
grep -RInE "(AIza|sk-|ghp_|github_pat_|GEMINI_API_KEY=.+|JWT_SECRET|AIDSSIST_API_KEY=.+)" . \
  --exclude-dir=.git \
  --exclude-dir=node_modules \
  --exclude-dir=.venv \
  --exclude-dir=dist \
  --exclude="*.lock" || true
```

Optional tools:

```bash
git secrets --scan || true
trufflehog filesystem . --no-update || true
```

If any real secret appears, remove it, rotate it, and rerun the scan before committing.

## GitHub CLI Flow

If `gh` is installed and authenticated:

```bash
gh auth status
gh repo create Manisshhhhhh/Aidssist-v3 \
  --private \
  --source=. \
  --remote=origin \
  --push
```

If the repository already exists:

```bash
git remote add origin https://github.com/Manisshhhhhh/Aidssist-v3.git || true
git push -u origin main
```

Keep the repository private until Docker runtime verification passes.

To make public later:

```bash
gh repo edit Manisshhhhhh/Aidssist-v3 --visibility public
```

## Manual Browser Flow

If `gh` is unavailable:

1. Open <https://github.com/new>.
2. Owner: `Manisshhhhhh`.
3. Repository name: `Aidssist-v3`.
4. Visibility: Private recommended for RC1.
5. Do not initialize with README, `.gitignore`, or license because the local repo already has them.
6. Create repository.
7. Push:

```bash
git remote add origin https://github.com/Manisshhhhhh/Aidssist-v3.git
git push -u origin main
```

## Tag RC1

After the first push:

```bash
git tag -a v3.0.0-rc1 -m "Aidssist V3 RC1"
git push origin v3.0.0-rc1
```

## GitHub Actions

Expected workflow:

- backend dependency install and pytest
- frontend npm install/typecheck/build

Check runs:

```bash
gh run list --repo Manisshhhhhh/Aidssist-v3 --limit 5
```

If a run fails, inspect logs and fix only CI/release bugs, not new features.
