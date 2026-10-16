# copier-scoop-bucket

A [Copier](https://copier.readthedocs.io) template for a [Scoop](https://scoop.sh)
bucket that publishes Windows applications and Python command-line tools. A
generated bucket includes manifest scaffolding, scheduled and release-triggered
updates, Windows install tests, and a generated package catalog.

## For agents

Your agent is the interface. Copy this prompt into your coding agent:

```text
Install the scoop-bucket-skills skills: pick the best installation method for
you from https://github.com/hasansezertasan/scoop-bucket-skills/blob/main/docs/installation.md

Then use its scoop-bucket-setup skill to set up a new Scoop bucket from
https://github.com/hasansezertasan/copier-scoop-bucket, in a directory named
scoop-bucket. Ask me for what you need (my GitHub owner, the bucket's purpose and
the first package), and ask before you create a repository, change settings or
secrets, or push.
```

The prompt points the agent at the
[installation page](https://github.com/hasansezertasan/scoop-bucket-skills/blob/main/docs/installation.md),
which lists the install routes (Claude Code or Codex plugin, a skills installer,
or a manual clone) and tells the agent how to choose and confirm one. The
Claude Code and Codex plugin routes each have one recorded installation on
macOS; the skills installer route has none.

## For humans

### Create a bucket

```sh
uvx copier copy gh:hasansezertasan/copier-scoop-bucket scoop-bucket
cd scoop-bucket
git init && git remote add origin https://github.com/<owner>/scoop-bucket
mise install
```

The generated `README.md` lists the remaining setup (Actions permissions, the
first manifest). Add manifests with the scaffolder in the plugin's `scoop-add`
skill, which you can also run directly (see the generated README).

### Naming

Scoop does not enforce a repository name. Name the repository `scoop-bucket`, as
the community buckets do with their `scoop-` prefix (for example `scoop-extras`).
The bucket name used in `scoop bucket add <name> <repository URL>` is a separate
choice (see the [Scoop wiki](https://github.com/ScoopInstaller/Scoop/wiki/Buckets)),
and the template asks for it as `bucket_name`, defaulting to the directory name.

### Update a bucket

Pull later template changes into a bucket with:

```sh
uvx copier update
```

## Layout

| Path | Role |
|---|---|
| `copier.yml` | questions and Copier settings |
| `template/` | files rendered into a bucket; `*.jinja` files are templated, the rest are copied verbatim |
| `.github/workflows/template.yml` | renders the template and runs the bucket's `mise run check` |
| `.github/workflows/release.yml` | versions the template with release-please |
| `docs/` | research notes and MADR decision records behind the template's design; paths inside them are relative to this repository, not to a generated bucket |

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
