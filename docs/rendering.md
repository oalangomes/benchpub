# Static evidence bundles

`benchpub render` converts two valid result manifests and their comparison into an inspectable static directory.

```bash
benchpub render baseline.json treatment.json --output ./report
```

## Bundle layout

```text
report/
├── index.html
├── report.md
├── comparison.json
├── manifest.json
└── evidence/
    ├── baseline.json
    └── treatment.json
```

The HTML report is self-contained: no CDN, JavaScript runtime, remote font, analytics, or server is required.

## Evidence preservation

The files under `evidence/` contain the exact bytes validated by `benchpub`.

`manifest.json` records:

- bundle format version;
- benchpub version;
- relative evidence paths;
- SHA-256 of each input;
- byte size of each input;
- locations of the machine-readable comparison and human reports.

The bundle does not add an automatic generation timestamp. That would make identical evidence produce different bundles without adding benchmark provenance. Experiment timestamps belong in each result manifest's `provenance`.

## Determinism

Given the same validated input bytes and the same benchpub version, `render` produces the same file contents.

The output directory name itself is not embedded in the bundle.

## Safe output behavior

The output path must either not exist or be an empty directory.

A non-empty output directory is rejected rather than partially overwritten. Rendering is assembled in a temporary sibling directory and moved into place only after every artifact has been written successfully.

## Publication boundary

A rendered bundle is ready to be uploaded by existing CI/static-hosting mechanisms, but `render` does not publish it.

GitHub Pages, CI artifacts, Telegram notifications, and other side effects remain separate concerns.
