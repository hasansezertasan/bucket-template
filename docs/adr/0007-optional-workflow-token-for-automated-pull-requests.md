# Optional WORKFLOW_TOKEN for Automated Pull Requests

## Context and Problem Statement

The update workflows and the boilerplate-drift workflow open pull requests with
`GITHUB_TOKEN`. GitHub does not start workflows for actions that token performs,
so those pull requests do not run `Tests` or the other checks until a
maintainer intervenes (see
[ADR-0004](0004-bump-in-the-bucket-not-the-producer.md)). A long-lived
credential with more access would fix it but widens the blast radius of an
attacker-influenced dispatch payload.

## Considered Options

* Keep `GITHUB_TOKEN` only and re-trigger each pull request's checks by hand
* Require a privileged token for all automation pull requests
* Accept an optional `WORKFLOW_TOKEN` secret, falling back to `GITHUB_TOKEN`

## Decision Outcome

Chosen option: "Optional `WORKFLOW_TOKEN`, `GITHUB_TOKEN` fallback." The
update, dispatch, and drift workflows open pull requests with
`${{ secrets.WORKFLOW_TOKEN || secrets.GITHUB_TOKEN }}`. A fine-grained
personal access token or GitHub App token with **Contents: write** and **Pull
requests: write** starts the checks automatically; without it, maintainers run
the `Tests` workflow manually via `workflow_dispatch` on the update branch,
push to its branch, or close and reopen the pull request. The secret stays
optional so buckets without one keep working.

### Consequences

* Good, because the default path needs no secret management.
* Good, because buckets that configure the secret get fully automatic checks.
* Bad, because two token paths mean two behaviors to document and understand.

Related research: [0001-homebrew-tap-template-comparison](../research/0001-homebrew-tap-template-comparison.md).
