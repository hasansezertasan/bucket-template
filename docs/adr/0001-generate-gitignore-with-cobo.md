# Generate .gitignore with Cobo

## Context and Problem Statement

A bucket checkout accumulates Windows, editor, and Python noise. Hand-curating
a `.gitignore` for five platforms drifts from the upstream `github/gitignore`
templates and nobody can tell which lines were deliberate.

## Considered Options

* Render `.gitignore` from upstream templates with
  [Cobo](https://github.com/hasansezertasan/cobo) and record the inputs in
  `cobo.lock`
* Maintain a hand-written `.gitignore`
* Copy the upstream templates once and let them go stale

## Decision Outcome

Chosen option: "Render `.gitignore` with Cobo." The inputs are the macOS,
Windows, Linux, Visual Studio Code, and Python templates, recorded in
`cobo.lock`. The rendered file is stored as `template/.gitignore.jinja` (under
a `.jinja` name so it does not ignore files inside `template/`, with no Jinja
syntax inside) and must render byte-for-byte identical; `cobo check --strict`
in the generated bucket verifies this. `gitignore-drift.yml` re-renders weekly
and opens a pull request when upstream moved (see
[ADR-0006](0006-open-a-pull-request-for-boilerplate-drift.md)).

### Consequences

* Good, because upstream template fixes arrive as a pull request, not as silent
  drift.
* Good, because the hash seal in `cobo.lock` makes hand edits fail loudly
  instead of rotting quietly.
* Bad, because contributors must learn `cobo sync` instead of editing
  `.gitignore` directly.
