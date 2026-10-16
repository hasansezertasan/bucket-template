# Render Identity with Copier and Resolve the Bucket Name at Runtime

## Context and Problem Statement

A bucket needs its name, owner, and repository in the README install snippet
(`scoop bucket add <name> <repository URL>`), but a template cannot know them
in advance, and a new bucket should not have to hunt for placeholders before
its first manifest. At the same time, scripts and workflows must keep working
when a bucket is renamed or moved, so nothing may hardcode an owner or
repository name.

## Considered Options

* Keep runtime resolution only, and render nothing from answers
* Render identity from Copier answers, and resolve the repository at runtime
  everywhere else

## Decision Outcome

Chosen option: "Render identity from answers, resolve at runtime elsewhere."
`copier.yml` asks for `bucket_name`, `bucket_description`, `bucket_owner`, and
`bucket_repository`, and only `README.md` and `LICENSE` are rendered from
answers. Everything else stays owner-agnostic: repository identity comes from
the Git remote, the GitHub Actions context, or an explicit environment/CLI
override, and the `scoop-add` scaffolder infers the repository from the
`origin` remote.

### Consequences

* Good, because a generated bucket's install snippet is correct on first render
  with no placeholder hunt.
* Good, because renames and moves do not require editing scripts or workflows.
* Bad, because two identity mechanisms (rendered answers plus runtime
  resolution) must be understood instead of one.

Related research: [0001-homebrew-tap-template-comparison](../research/0001-homebrew-tap-template-comparison.md).
