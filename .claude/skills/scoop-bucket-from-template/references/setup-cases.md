# Template Setup Evidence and Cases

## Provenance

Inspected implementation and local history at
`3678296ac0f6521ae834f8df6f83cd9b0b60d72d` (2026-10-08).
Both `bucket/` and `deprecated/` contain only `.gitkeep`; available local history
contains no committed package JSON or observed new-bucket adoption incident.
The cases below are synthetic desk scenarios grounded in implementation and
regressions, not observed failed installations or Windows runtime tests.

Read the existing verification, repair, triage, and lifecycle references for
their separate evidence boundaries. Recorded Cobo CI drift is a managed
boilerplate failure, not proof of a template/token/shim incident.

## Local evidence map

| Evidence | Locator at the inspected base |
| --- | --- |
| Adoption checklist, identity overrides, consumer commands | `README.md`, Start a bucket / Install packages / Add a manifest |
| Token names and producer versus bucket responsibilities | `README.md`, Automated updates; `.github/workflows/update-manifests.yml`, `update` job; `update-manifest-dispatch.yml`, Create Pull Request / Report failure |
| CLI → environment → remote precedence; HTTPS/SSH regressions | `scripts/add_manifest.py`, shim CLI and `main`; `scripts/bucket_repository.py`, `resolve` / `from_remote`; `tests/test_bucket_repository.py` |
| Local LF-normalized hash and raw repository/ref URL | `scripts/add_manifest.py`, `noop_source`; `.gitattributes`; `tests/test_add_manifest.py`, noop tests |
| API-only authorization and redirect stripping | `scripts/url_fetch.py`; `tests/test_url_fetch.py` |
| PyPI updater preserves noop pair | `tests/test_update_manifests.py`, `test_pypi_bump_preserves_shape` |
| First-manifest scaffolder and verification ownership | `.ai-rulez/skills/scoop-add/SKILL.md`; `.ai-rulez/skills/scoop-verify/SKILL.md` |
| Local check coverage and generated files | `.config/mise.toml`, `check` / `agents:generate`; `scripts/gen_agents.py` |
| Install working-tree manifests, skip zero hashes, smoke command | `.github/workflows/tests.yml`, `discover` and `test` jobs, install/smoke steps |
| Branch filters/default-ref assumptions | `.github/workflows/tests.yml`, `readme.yml`, `agents.yml`; shim `--bucket-ref` default |
| Cobo PR token boundary | `.github/workflows/gitignore-drift.yml`; no `WORKFLOW_TOKEN` input |

Recheck code rather than treating comments as authoritative: dispatch comments
describe wildcard family selection, but the updater selects the exact token and
its `-pipx` sibling. No `SCOOP_BUCKET_TOKEN` consumer exists at this base.
All workflows deny permissions by default; each job opts in. Update PR jobs
need Contents/Pull requests write, dispatch failure reporting needs Issues write,
comment gates also declare Pull requests write, and zizmor declares Security
events write. Do not generalize update-token permissions to every workflow.

## External documentation checked

Checked 2026-10-08; recheck current docs and destination policy during adoption.

- [GitHub template creation](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template):
  files/directory structure, default versus all branches, new single-commit
  history rather than fork history. Configure repository settings/secrets
  independently; creation is not evidence those are ready.
- [Actions repository settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository):
  Actions enabled by default but controllable by policy, allowed actions,
  default token permissions versus explicit YAML permissions, and separate
  GitHub Actions PR-creation setting (disabled by default in new personal repos).
- [Token authentication](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token):
  built-in token, job permissions, PAT/App alternatives.
- [Workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow):
  `GITHUB_TOKEN` suppression has exceptions. Current docs describe approval-required
  `pull_request` opened/synchronize/reopened runs; other events remain suppressed
  except workflow/repository dispatch. This is more nuanced than the README's
  summary; inspect actual runs and do not promise all gates run automatically.
- [Events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows):
  default-branch constraints for schedules/repository dispatch/manual workflows.
- [Repository dispatch API](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event):
  dispatch is a producer signal, not PR creation; the local README/workflow
  documents target Contents: write for a fine-grained producer token.
- [Scoop buckets documentation](https://github.com/ScoopInstaller/Scoop/wiki/Buckets):
  custom Git bucket registration and consumer install checks. Its description
  of ScoopInstaller's different template is not this repository's automation.

## Synthetic evaluation cases

### A. Unspecified team destination and first package

Ask for owner/repository, visibility/branch and first upstream/route, and whether
the goal is planning or published readiness. Distinguish copied files from
Actions/secrets/policy configuration. Keep identity neutral and use
`scoop-add` → `scoop-verify`; do not create a fictional manifest.

### B. Correct origin, stale override, unpublished noop

Honor CLI/environment/remote precedence rather than trusting origin alone.
Scaffolding success does not verify remote content. A raw 404 and uncommitted noop
changes block installability until the intended identity/ref publishes matching
LF bytes and static autoupdate values agree. Do not reuse the template's raw URL,
change a hash blindly, or claim a local CI bucket bypasses remote shim downloads.

### C. Wrong secret and empty-bucket automation check

Explain the unused `SCOOP_BUCKET_TOKEN` name versus `WORKFLOW_TOKEN` fallback,
effective permissions, PR settings, and suppression/approval-required CI.
Distinguish a producer's dispatch credential from bucket branch/PR writes and
failure-issue credentials. Empty checks and dry-runs do not prove publishing,
all separate gates, or Windows installs. Never expose secrets or recommend
blanket privileges to mask missing evidence.
