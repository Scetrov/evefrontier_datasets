# Threat Model

## Scope and assets

This repository contains a Python package, Jupyter notebooks, dependency
metadata (`pyproject.toml` and `poetry.lock`), and GitHub configuration. The
integrity of source code, dependency definitions, workflow configuration, and
any data processed by notebooks or scripts are security-relevant assets.

## Trust boundaries

- Data supplied to notebooks and scripts can be untrusted.
- Dependencies resolved from package registries and their transitive
  dependencies are outside repository control.
- Pull requests, GitHub Actions runners, and third-party GitHub Actions cross
  contributor and automation trust boundaries.
- Local environment configuration must not be committed with credentials.

## Primary threats and mitigations

| Threat | Mitigation |
| --- | --- |
| A malicious dependency or dependency update changes runtime behavior. | Review dependency changes, keep the lockfile under review, and use Dependabot updates for the detected devcontainer ecosystem. |
| A pull request changes automation or dependency metadata to gain broader access. | Require maintainer review through `CODEOWNERS`; the CodeQL workflow uses pinned GitHub Actions and least-privilege permissions. |
| Crafted data or notebooks cause unsafe execution or excessive resource use. | Treat external data and notebooks as untrusted; review sources and avoid executing unreviewed notebook code in privileged environments. |
| Credentials are committed in source or local configuration. | Keep real `.env` files ignored, use repository secret scanning and push protection, and rotate any credential that is exposed. |

## Operational follow-up

Repository administrators must configure branch protection, required reviews,
secret scanning, push protection, and alert triage in GitHub settings. These
controls are outside source control and are not changed by this repository
file documentation.
