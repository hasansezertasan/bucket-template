# Use MADR for Decision Records

## Context and Problem Statement

Technical decisions need to remain discoverable after their originating
conversation or pull request. Unstructured decision notes do not establish
which context, alternatives, and consequences must be retained.

## Considered Options

* Record decisions using Markdown Architectural Decision Records (MADR)
* Keep unstructured notes in a general decisions directory
* Keep decisions only in research notes and pull requests

## Decision Outcome

Chosen option: "Record decisions using MADR", because it provides a concise,
repeatable structure while keeping decisions versioned beside the bucket they
govern. Records live in `docs/adr/` and use sequential four-digit prefixes.
Research notes use an independent four-digit sequence under `docs/research/`,
and each ADR links its supporting research when such research exists. The first
records exercising this convention are 0001–0007, backfilled from
[0001-homebrew-tap-template-comparison](../research/0001-homebrew-tap-template-comparison.md).

### Consequences

* Good, because each decision preserves its context, alternatives, outcome, and
  consequences.
* Good, because future contributors have one predictable decision log.
* Good, because the rationale for the workflows and scripts the template ships
  travels beside the template, instead of living only in chat history. (Only
  `template/` renders into a generated bucket, so these records document the
  template itself; buckets inherit the files, not this log.)
* Bad, because meaningful decisions require an additional document to maintain.
