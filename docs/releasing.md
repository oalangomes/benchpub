# Releasing benchpub

Releases are deliberately small and tag-driven.

## v0.1 release gate

Before creating `v0.1.0`:

- [ ] package version is `0.1.0`;
- [ ] full CI is green on Python 3.11, 3.12, and 3.13;
- [ ] lint is green;
- [ ] full pytest suite is green;
- [ ] package build is green;
- [ ] example fixtures regenerate byte-for-byte;
- [ ] example passes `validate → compare → render`;
- [ ] README installation and quickstart are current;
- [ ] schema, comparison, and rendering docs are current;
- [ ] changelog contains the release;
- [ ] `docs/releases/v0.1.0.md` is ready.

## Create the release

Create an annotated or lightweight Git tag pointing at the reviewed release commit:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The release workflow then:

1. verifies that the tag matches the package version;
2. reruns lint and tests;
3. builds wheel and source distribution;
4. installs the wheel in a clean environment and runs a CLI smoke;
5. creates the GitHub Release with the built artifacts and versioned notes.

Published tags must be treated as immutable.
