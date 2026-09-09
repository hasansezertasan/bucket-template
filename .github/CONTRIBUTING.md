# Contributing

Add one package family per pull request. A family may contain a binary manifest
and a `-pipx` shim when both routes expose the same application. Use a concise
Conventional Commit title such as `feat: add example manifest` or
`chore(example): update to 1.2.3`.

Before opening a pull request:

1. Generate manifests with `scripts/add_manifest.py`; do not hand-write their
   update metadata unless the upstream layout requires it.
2. Review inferred descriptions, licenses, archive paths, executable names, and
   smoke-test commands.
3. Run `mise run generate-readme`.
4. Run `mise install` and `mise run check`.
5. When possible, add the bucket on Windows, install the package, and run its
   smoke test.

Include the commands and results in the pull request's verification section.
