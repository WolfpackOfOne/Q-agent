# Security Policy

## Supported code

Security fixes are applied to the current `main` branch and the latest tagged
course release. Older snapshots are not maintained.

## Report privately

Do not open a public issue for a vulnerability, exposed credential, private
dataset, or account identifier. Use the repository's
[private vulnerability reporting form](https://github.com/WolfpackOfOne/Q-agent/security/advisories/new).
Course participants should also notify the instructor through the course's
official private communication channel.

If a credential may have been exposed, revoke or rotate it immediately. Removing
it in a later commit does not remove it from Git history.

Include a concise description, affected file or component, reproduction steps,
impact, and a suggested remediation when possible. Do not include live secrets
in the report.

## Repository security controls

This repository uses:

- protected pull requests with instructor approval and required CI checks;
- GitHub secret scanning and push protection;
- Gitleaks and personal-path scanning across pull requests;
- CodeQL and dependency review;
- automated dependency alerts and security updates;
- minimal GitHub Actions token permissions and immutable action references;
- `.gitignore`, `.dockerignore`, and repository-policy checks for local secrets,
  generated artifacts, and oversized data.

## Never commit

- API keys, tokens, passwords, SSH keys, certificates, or private keys;
- QuantConnect IDs or credentials, WRDS credentials, or brokerage credentials;
- `.env`, `lean.json`, project `config.json`, or credential files;
- proprietary or personally identifiable data;
- personal machine paths, generated backtests, or unreviewed notebook output.
