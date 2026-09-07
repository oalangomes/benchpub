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

`benchpub` makes those questions part of the evidence instead of leaving them in screenshots or prose.

## What benchpub does

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

`benchpub` **does not execute benchmarks**.

It is intentionally not a benchmark runner, experiment-tracking server, database, dashboard SaaS, or statistical significance engine.

## Install

Python 3.11+ is required.

With uv:

```bash
uv tool install git+https://github.com/oalangomes/benchpub.git@v0.1.0
benchpub --version
```

The GitHub release also contains wheel and source-distribution artifacts.

## Quick start

Given `baseline.json` and `treatment.json`:

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

A compatible result means compatible **under declared evidence**, not proof of scientific equivalence or reproducibility.

## Reproducible example

The repository includes a deterministic linear-search vs binary-search experiment:

```bash
python examples/search-strategies/benchmark.py

benchpub validate \
  examples/search-strategies/results/baseline.json \
  examples/search-strategies/results/treatment.json

benchpub compare \
  examples/search-strategies/results/baseline.json \
  examples/search-strategies/results/treatment.json

benchpub render \
  examples/search-strategies/results/baseline.json \
  examples/search-strategies/results/treatment.json \
  --output ./report
```

The example benchmark is external to benchpub. CI regenerates its result files byte-for-byte and then dogfoods the complete CLI flow.

See [the example](examples/search-strategies/README.md) for the experiment design.

## Result contract

The smallest valid result is:

```json
{
  "schema_version": 1,
  "experiment": {
    "id": "lookup-001"
  },
  "metrics": [
    {
      "name": "latency_ms",
      "value": 12.4
    }
  ]
}
```

Domain-specific details can live in `controlled_variables`, `configuration`, and `environment` without expanding the typed envelope.

## Documentation

- [Result schema](docs/schema.md)
- [Comparison semantics](docs/comparison.md)
- [Static evidence bundles](docs/rendering.md)
- [Release process](docs/releasing.md)
- [Machine-readable JSON Schema](schema/v1.json)

## Development

```bash
uv sync --dev
uv run ruff check .
uv run pytest
uv run benchpub --help
```

CI additionally proves the public example end-to-end on Python 3.11, 3.12, and 3.13.

## Design principles

- small explicit contracts;
- deterministic behavior;
- useful path-aware CLI errors;
- comparability under declared controls;
- provenance without pretending to guarantee reproducibility;
- static-first output;
- no infrastructure requirement;
- no abstractions without a concrete need.

## v0.1.0

- [x] JSON result schema;
- [x] validation;
- [x] baseline/treatment comparison;
- [x] simple metric deltas;
- [x] comparability checks;
- [x] Markdown report;
- [x] self-contained HTML report;
- [x] provenance and input hashes;
- [x] reproducible end-to-end example.

Publication destinations and optional notifications remain post-v0.1 concerns until real usage justifies them.

## License

MIT.
