# bucket-template

A [Copier](https://copier.readthedocs.io) template for a [Scoop](https://scoop.sh)
bucket that publishes Windows applications and Python command-line tools. A
generated bucket includes manifest scaffolding, scheduled and release-triggered
updates, Windows install tests, and a generated package catalog.

## Create a bucket

```sh
uvx copier copy gh:hasansezertasan/bucket-template my-bucket
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

## License

MIT. See `LICENSE`.
