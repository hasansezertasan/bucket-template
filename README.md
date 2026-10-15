# copier-scoop-bucket

A [Copier](https://copier.readthedocs.io) template for a [Scoop](https://scoop.sh)
bucket that publishes Windows applications and Python command-line tools. A
generated bucket includes manifest scaffolding, scheduled and release-triggered
updates, Windows install tests, and a generated package catalog.

## Create a bucket

```sh
uvx copier copy gh:hasansezertasan/copier-scoop-bucket my-bucket
cd my-bucket
git init && git remote add origin https://github.com/<owner>/my-bucket
mise install
```

The generated `README.md` lists the remaining setup (Actions permissions, the
first manifest). Pull later template changes into a bucket with:

```sh
uvx copier update
```

## Agent skills

Skills for operating a bucket (add, fix, triage, remove, verify) live in the
[`scoop-bucket-skills`](https://github.com/hasansezertasan/scoop-bucket-skills)
Claude Code plugin, not in this template.

## Layout

| Path | Role |
|---|---|
| `copier.yml` | questions and Copier settings |
| `template/` | files rendered into a bucket; `*.jinja` files are templated, the rest are copied verbatim |
| `.github/workflows/template.yml` | renders the template and runs the bucket's `mise run check` |

`template/.gitignore.jinja` is the Cobo-managed `.gitignore` stored under a
`.jinja` name so it does not ignore files inside `template/`. It contains no
Jinja syntax and must render byte-for-byte identical (`cobo check --strict` in
the rendered bucket verifies this).

## Releases

The template is versioned with [release-please](https://github.com/googleapis/release-please).
Conventional Commits merged to `main` open a release PR; merging it tags the
commit `vX.Y.Z` and creates a GitHub Release with the changelog. Generated
buckets record the tag in `.copier-answers.yml`, and `copier update` walks these
tags. Until 1.0, breaking changes and features bump the minor version and fixes
bump the patch. The first release, `v0.1.0`, is the first Copier version; history
before the conversion is not part of the changelog.

Pin a version when generating a bucket:

```sh
uvx copier copy --vcs-ref v0.1.0 gh:hasansezertasan/copier-scoop-bucket my-bucket
```

The release PR is opened with the workflow's `GITHUB_TOKEN`, so its checks do not
start by themselves; run the **Template** workflow on the release branch from the
Actions tab if you want them before merging.

## License

MIT. See `LICENSE`.
