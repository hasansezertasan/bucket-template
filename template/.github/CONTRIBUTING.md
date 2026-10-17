# Contributing

Add one package family per pull request. A family may contain a binary manifest
and a `-pipx` shim when both routes expose the same application. Use a concise
Conventional Commit title such as `feat: add example manifest` or
`chore(example): update to 1.2.3`.

Before opening a pull request:

1. Generate manifests with the `scoop-add` scaffolder from
   [`scoop-bucket-skills`](https://github.com/hasansezertasan/scoop-bucket-skills);
   do not hand-write their
   update metadata unless the upstream layout requires it.
2. Review inferred descriptions, licenses, archive paths, executable names, and
   smoke-test commands.
3. Run `mise run generate-readme`.
4. Run `mise install` and `mise run check`.
5. When possible, add the bucket on Windows, install the package, and run its
   smoke test.

Include the commands and results in the pull request's verification section.

## Automated pull requests

The update and boilerplate-drift workflows open pull requests with the repository
secret `WORKFLOW_TOKEN` if present, falling back to `GITHUB_TOKEN`. GitHub does
not start workflows for actions performed by `GITHUB_TOKEN`, so maintainers run
the `Tests` workflow manually via `workflow_dispatch` on the update branch
before merging, or push to its branch, or close and reopen such a pull request,
or configure a `WORKFLOW_TOKEN` secret to start applicable checks automatically.
