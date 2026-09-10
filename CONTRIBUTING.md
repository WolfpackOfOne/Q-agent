# Contributing to Q-agent

Q-agent is a teaching and research workspace. Contributions should be focused,
reviewable, reproducible, and understandable by another student.

## Contribution model

Students contribute through personal forks. Students should not be granted
write access to the upstream repository. The instructor reviews and merges all
changes to `main`.

Individual trading strategies normally live in their own repositories. The
central Q-agent repository accepts shared infrastructure, reusable signals,
documentation, tests, and explicitly approved example strategies. Open a
feature proposal before adding a new project under `MyProjects/`.
Maintainers use the taxonomy in `.github/labels.md` to keep work discoverable
and consistently prioritized.

## Set up your fork

1. Fork `WolfpackOfOne/Q-agent` on GitHub.
2. Clone your fork and register this repository as `upstream`:

   ```bash
   git clone https://github.com/YOUR-USERNAME/Q-agent.git
   cd Q-agent
   git remote add upstream https://github.com/WolfpackOfOne/Q-agent.git
   git fetch upstream
   ```

3. Create one branch per focused change:

   ```bash
   git switch main
   git pull --ff-only upstream main
   git switch -c feature/short-description
   ```

Never commit directly to `main` in either repository.

## Make and validate a change

Keep architecture modular, prefer pure functions for calculations, document
assumptions, and add tests for new behavior.

Run the checks relevant to the change:

```bash
python -m venv venv
source venv/bin/activate  # Windows PowerShell: venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
pytest -m "not integration"
python scripts/check_repository_policy.py --all
```

Documentation contributors should also run:

```bash
python -m pip install -r docs/requirements-docs.txt
mkdocs build --strict
```

Requirements files apply `constraints-course.txt`. Update that baseline and all
affected requirements together in a dedicated dependency PR.

## Open the pull request

```bash
git push -u origin feature/short-description
```

Open a PR from your fork into `WolfpackOfOne/Q-agent:main` and complete every
section of the PR template. Link the related issue when one exists.

First-time contributors must wait for the instructor to approve the GitHub
Actions run. After CI starts, a PR cannot merge until all required checks pass,
the branch is current with `main`, review conversations are resolved, and the
instructor approves the latest revision. Pushing new commits dismisses an old
approval.

## Data and notebook policy

Do not commit credentials, account identifiers, raw vendor data, proprietary
research, generated backtests, or large notebook outputs.

- Each committed file must be at most 6 MiB.
- CSV and TSV fixtures must contain at most 50,000 rows.
- A previously merged oversized dataset is exempt only while its exact SHA-256
  remains listed in `.github/repository-policy-grandfathered.txt`; contributors
  may not add to that list through ordinary feature PRs.
- Commit only the smallest fixture needed for tests or a reproducible example.
- Include a refresh script and document source, license, date range, and schema.
- Inspect notebook output and metadata before committing.
- Use an approved external store or release asset for larger public datasets.

## Creating a strategy

Render the template; do not copy `_template` directly:

```bash
python scripts/create_strategy.py MyFirstStrategy
cd MyProjects/MyFirstStrategy
git init
```

The generated directory is intentionally ignored by the Q-agent workspace and
should normally become its own repository. Do not edit the workspace
`.gitignore` to add it to Q-agent unless the instructor approved it as a shared
example first.

## Commit style

Use short, imperative messages such as:

```text
Add WRDS sector pipeline
Fix LEAN data timestamp normalization
Document Polymarket fixture provenance
```

## Conduct and security

Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
Report vulnerabilities or
credential exposure through [GitHub's private vulnerability form](https://github.com/WolfpackOfOne/Q-agent/security/advisories/new),
never through a public issue.
