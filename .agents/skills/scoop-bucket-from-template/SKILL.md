---
name: scoop-bucket-from-template
description: "Set up a new Scoop bucket from this template, including repository identity, Actions settings, update tokens, shim noop publication, and the first manifest. Use for template adoption or bootstrap questions about SCOOP_BUCKET_TOKEN versus WORKFLOW_TOKEN; delegate manifest creation and verification to scoop-add and scoop-verify."
# Content-Hash: blake3:4063254069d6dd13f08fad66429f083a3bc44ba62a3acfdb53e7a8f3d66e1e92
# Source-Hash: blake3:9c88dc17b8131f1e678d71fad5c870d461ef72f5cabcc61c164922daeaff86a7
---

# Set Up a Scoop Bucket from the Template

## 1. Establish the destination and outcome

Confirm the template source, intended `owner/repository`, visibility, default
branch, local checkout, and first package/upstream route. Derive known identity
from Git `origin`, GitHub Actions context, or explicit overrides; ask through the
native question tool when these disagree or the destination is unspecified.
Distinguish a setup plan, local preparation, and a published installable bucket.
Follow the user's approval rules for creation, settings, secrets, publication,
PRs, and remote workflow runs.

Read the current `README.md` setup/automation sections, `.github/workflows/`,
`scripts/bucket_repository.py`, `scripts/add_manifest.py` (`noop_source` and CLI
options), and `.config/mise.toml` before acting. Use
[references/setup-cases.md](references/setup-cases.md) for implementation,
documentation, and regression-derived evidence; recheck locators after changes.
Do not redesign workflows, token plumbing, or template infrastructure as an
implicit setup step. Surface unsupported choices and agree their scope first.

## 2. Create or inspect the new repository

Use GitHub's **Use this template → Create a new repository** with the agreed
destination, or the equivalent `gh repo create --template` flow. Normally copy
only the default branch; ask before including unrelated branches. Template
creation copies files/directory structure into a new history, not a fork's
history or a live connection that automatically imports future template fixes.

Treat workflow files, scripts, tool configuration, and generated agent skills as
copied content. Check settings, secrets, labels, rulesets/required checks, and
installed integrations separately; do not infer they were copied or configured.
Repository/organization defaults may apply. Clone the **new bucket** and verify
its `origin`; an existing template clone still points at the template. Preserve
user work when resolving a mismatched checkout.

Replace the LICENSE copyright placeholder and README title/introduction with the
agreed bucket identity/purpose. Retain the generated package-table markers and
setup/install guidance. Do not globally replace owner names: external actions
and dependencies are not bucket identity. Preserve managed `.gitignore` inputs;
use Cobo's managed sync if drift occurs.

Confirm `main` before relying on current branch filters and shim defaults. If a
different branch is requested, inspect every relevant filter and noop ref;
`--bucket-ref` alone does not adapt CI. Agree any branch/workflow adaptation
separately instead of silently claiming support.

## 3. Configure Actions and credentials from actual consumers

In **Settings → Actions → General**, verify Actions is enabled and policy allows
the pinned actions used by this checkout. Check organization/enterprise limits
if settings are unavailable. For automation using `GITHUB_TOKEN`, enable
**Allow GitHub Actions to create and approve pull requests** where permitted.
The README asks for read/write defaults, but these workflows explicitly deny
permissions at workflow level and grant them per job; do not broaden defaults
or all jobs merely to troubleshoot. Inspect effective job permissions and
repository policy instead.

Explain the distinct credentials before requesting any secret:

| Consumer | Current credential and access |
| --- | --- |
| Scheduled/manual and dispatch update PR steps | Optional bucket secret `WORKFLOW_TOKEN`, otherwise built-in `GITHUB_TOKEN`; branch commits/pushes and PR creation need Contents: write and Pull requests: write on the bucket. |
| Upstream GitHub API reads | Workflow `GITHUB_TOKEN`; local helpers accept `GITHUB_TOKEN` or `GH_TOKEN`. These are not shim download credentials. |
| Dispatch failure issue | Built-in `GITHUB_TOKEN` with Issues: write; destination comes from `github.repository`. |
| External release producer calling `POST /dispatches` | A credential authorized for the target bucket; a fine-grained token needs Contents: write for this API. Store it in the producer, not the bucket; PR-write is not needed just to dispatch. |

`SCOOP_BUCKET_TOKEN` is an issue/setup name that **current code does not read**.
Creating it alone has no effect. Use the consumer's actual secret name; do not
invent an alias or edit workflows to consume it without agreed scope.
`GITHUB_TOKEN` is supplied by Actions, not a secret the user must create.

Choose the credential path from the desired update-PR CI behavior. The README
describes follow-on suppression with `GITHUB_TOKEN`; current GitHub documentation
also describes approval-required runs for certain bot-created `pull_request`
events. Inspect the actual banner, events, filters, and latest-head runs instead
of assuming either automatic CI or universal suppression. For automatic runs,
the existing update steps accept a suitable PAT or GitHub App token as
`WORKFLOW_TOKEN`. Verify its target access, expiration/renewal, org approval, and
permissions for the operations above. The workflows consume a secret directly;
they do not mint or refresh an App installation token. Agree additional plumbing
if needed. Job `permissions` do not grant rights to a supplied token. Do not
recommend blanket `repo`, admin, or Actions-write privileges without a specific
operation requiring them.

For the built-in-token path, inspect and approve pending runs when available or
use the existing manual **Tests** workflow on the update branch under the user's
approval rules. A Tests run does not prove separate title/branch/agent/audit
gates ran. `WORKFLOW_TOKEN` is used by the two update PR steps, not every bot
workflow; inspect Cobo and other automation independently.

Configure secrets through Settings → Secrets and variables → Actions or secure
CLI input; never print values, ask for them in chat, commit them, or embed them
in shell source. Check the `automated` and `dependencies` labels requested by
update PRs, and enable Issues if dispatch failure reporting is wanted. Report
policy/ruleset blockers rather than escalating privileges speculatively.

## 4. Prepare the first manifest and its publication

Run `mise install` in the new checkout. Invoke `scoop-add` (read
`.agents/skills/scoop-add/SKILL.md` if not discovered) to select and scaffold the
first package using `mise run add-manifest`; do not hand-write JSON or invent a
demo package. Let `scoop-add` delegate its gate to `scoop-verify` for curated
metadata, hashes/layout, smoke commands, README regeneration, local checks, and
exact-head Windows evidence. Keep one package family per PR.

For a PyPI shim, establish the new bucket identity **before** scaffolding:
`--bucket-repository` takes precedence over `SCOOP_BUCKET_REPOSITORY`, which takes
precedence over GitHub `origin`. Inspect stale overrides even with a correct
remote. For an archive/non-GitHub checkout, use the explicit new repository;
ref selection independently follows `--bucket-ref` → `SCOOP_BUCKET_REF` → `main`.
Inspect stale ref overrides too, and reconcile the effective ref with the agreed
publication ref even when that is `main`. Do not leave permanent shim URLs on a
temporary setup branch that may be deleted.

The scaffolder hashes local `scripts/noop.ps1` bytes normalized CRLF→LF; it does
not fetch the generated raw URL. Ensure the intended file is published at the
**new repository and exact ref**, then have `scoop-verify` compare its response
bytes with concrete and static autoupdate URL/hash values. Uncommitted noop edits
and unpublished refs can produce locally valid but uninstallable manifests.
Keep `.gitattributes` LF behavior. Do not point at the template to conceal a
missing destination file, or bless an unexplained mismatch by replacing a hash.

Verify raw download accessibility for intended installers. The helper's API
token is not sent to raw GitHub; a private bucket/404 is not fixed by adding
`WORKFLOW_TOKEN`. Ask about a supported publication/access outcome when private
downloads block shims. CI's local working-tree bucket still downloads remote
noop bytes. Keep first-package install evidence pending until that boundary is
verified; preserve seeded binary install skips until a real asset/hash exists.

## 5. Report readiness at the requested level

Report the destination/default branch, checkout/override identity, copied and
separately configured items, credential **names and purposes only**, first
manifest route, publication/noop status, local checks, and latest-head Windows
install/smoke evidence from `scoop-verify`. Include owner-neutral consumer
commands with the established values:

```powershell
scoop bucket add <bucket-name> https://github.com/<owner>/<repository>
scoop install <bucket-name>/<package>
```

Keep passed, pending, and skipped evidence distinct. Empty-bucket checks or an
update dry-run do not exercise installability or branch/PR publication. A
scheduled/manual update `dry_run` skips PR creation but can modify runner files.
Schedules and repository dispatch depend on default-branch workflow publication;
check actual runs before claiming automation works. Hand update failures to
`scoop-update-triage` and manifest repair to `scoop-fix-manifest`.


## Resources

This skill bundles supporting files. Read them on demand when the task calls for them — don't bulk-load.

### References

- [`references/setup-cases.md`](references/setup-cases.md) — Template Setup Evidence and Cases
