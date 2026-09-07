# benchpub

> **Publish benchmark evidence, not just benchmark numbers.**

`benchpub` is a local-first CLI for turning structured benchmark results into evidence that can be validated, compared, inspected, and rendered as static reports.

## Why

Benchmark results often end up fragmented across JSON, CSV, logs, screenshots, and hand-written tables. That makes it hard to answer basic questions:

- What hypothesis was being tested?
- What changed between baseline and treatment?
- Were the controlled variables actually controlled?
- Which dataset or corpus was used?
- Which code revision produced the result?
- Are two runs comparable?
- Where did a reported delta come from?

`benchpub` is designed to make those answers explicit.

## Product boundary

`benchpub` **does not execute benchmarks**.

```text
benchmark / experiment
        ↓
structured results
        ↓
benchpub
        ↓
validate → compare → render
        ↓
static evidence bundle
```

It is intentionally not a benchmark runner, experiment-tracking server, database, dashboard SaaS, or statistical analysis platform.

## Status

The project is **pre-release**. The first milestone is `v0.1.0`.

Implemented:

- JSON result contract v1;
- path-aware validation;
- baseline/treatment comparison;
- `compatible / incompatible / indeterminate`;
- absolute and relative metric deltas;
- human and JSON comparison output;
- deterministic Markdown and self-contained HTML evidence bundles;
- SHA-256 provenance for the exact validated inputs.

## Quick start

```bash
benchpub validate baseline.json treatment.json
benchpub compare baseline.json treatment.json
benchpub render baseline.json treatment.json --output ./report
```

The rendered directory contains:

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

Open `report/index.html` directly or upload the directory using the static hosting/artifact mechanism you already use.

A compatible result means compatible **under declared evidence**, not proof of scientific equivalence.

See [schema semantics](docs/schema.md), [comparison semantics](docs/comparison.md), [rendering semantics](docs/rendering.md), and the machine-readable [JSON Schema](schema/v1.json).

## Development

Requires Python 3.11+.

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run benchpub --help
```

## Design principles

- small explicit contracts;
- deterministic behavior;
- useful path-aware CLI errors;
- comparability under declared controls;
- provenance without pretending to guarantee reproducibility;
- static-first output;
- no infrastructure requirement;
- no abstractions without a concrete need.

## v0.1.0 roadmap

- [x] JSON result schema;
- [x] validation;
- [x] baseline/treatment comparison;
- [x] simple metric deltas;
- [x] comparability checks;
- [x] Markdown report;
- [x] self-contained HTML report;
- [x] provenance and input hashes in the evidence bundle;
- [ ] reproducible end-to-end example.

Publication destinations and optional notifications remain post-v0.1 concerns until the evidence core is stable.

## License

MIT.
