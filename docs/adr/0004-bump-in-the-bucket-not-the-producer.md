# Bump in the Bucket, Not in the Producer

## Context and Problem Statement

When a packaged project publishes a release, its manifests in this bucket need
a version bump. The work can happen in the producer repository, which then
pushes to the bucket, or in the bucket, which the producer merely signals. The
choice determines how much trust every producer needs and where the bump logic
lives as more producers come online.

## Considered Options

* Producers fire a `repository_dispatch`; the bucket does the bump and opens its
  own pull request
* Producers run the updater themselves and push a branch to the bucket

## Decision Outcome

Chosen option: "Producers signal; the bucket bumps." The weekly
`update-manifests.yml` re-checks every manifest from its declared upstream
source, and a producer can request an immediate bump with a
`repository_dispatch` event of type `update-manifest`
(`{"package":"example","version":"1.2.3"}`, where the version is informational
because the updater re-checks the source). A producer's dispatch token needs
**Contents: write** on the bucket solely for the dispatch API — the bucket
opens the pull request itself. The token lives in the producer repository, not
in the bucket.

### Consequences

* Good, because producers need minimal access and no knowledge of the manifest
  layouts.
* Good, because all bump logic and validation live in one tested place
  (`scripts/update_manifests.py`).
* Bad, because a producer cannot land an urgent fix directly; it waits on the
  bucket's pull request flow.
