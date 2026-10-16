# Repository instructions

This is a Copier template for a Scoop bucket. The files rendered
into a bucket live under `template/`; `copier.yml` holds the questions. Nothing in
the scripts or workflows hardcodes an owner or repository name: repository identity
comes from the Git remote, the GitHub Actions context, or an explicit
environment/CLI override, so keep new code owner-agnostic.
Only `README.md` and `LICENSE` are rendered from answers.

`template/.gitignore.jinja` is the Cobo-managed `.gitignore` stored under a
`.jinja` name so it does not ignore files inside `template/`. It must render
byte-for-byte identical; `cobo check --strict` in the rendered bucket verifies it.

Skills for operating a generated bucket live in
[`scoop-bucket-skills`](https://github.com/hasansezertasan/scoop-bucket-skills),
not here. Persist research notes in `docs/research/` and decisions as MADR
records in `docs/adr/`. Give both sequential four-digit filename prefixes, link
each ADR to its related research when present, and commit them with the related
work.

Before opening a pull request, render the template and run the generated bucket's
checks (`.github/workflows/template.yml` does the same):

```sh
uvx copier copy --defaults --vcs-ref=HEAD -d bucket_owner=example \
  -d copyright_holder=Example . /tmp/demo-bucket
cd /tmp/demo-bucket && git init -q && git remote add origin https://github.com/example/demo-bucket
git add -A && mise install && mise run check
```
