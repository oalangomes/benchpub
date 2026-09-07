# benchpub

> **Publish benchmark evidence, not just benchmark numbers.**

`benchpub` is a local-first CLI for turning structured benchmark results into evidence that can be validated, compared, inspected, and published as static reports.

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

The intended flow is:

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

The project is currently **pre-release**. The first milestone is `v0.1.0`.

The initial public CLI will be:

```bash
benchpub validate result.json
benchpub compare baseline.json treatment.json
benchpub render baseline.json treatment.json --output ./report
```

The current foundation slice only establishes packaging, CLI entry points, tests, linting, and CI. The result schema and comparison semantics land in subsequent slices.

## Development

Requires Python 3.11+.

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --dev
uv run benchpub --help
uv run pytest
uv run ruff check .
```

To install the local checkout as a tool:

```bash
uv tool install .
benchpub --help
```

## Design principles

- small explicit contracts;
- deterministic behavior;
- useful CLI errors;
- comparability under declared controls;
- provenance without pretending to guarantee reproducibility;
- static-first output;
- no infrastructure requirement;
- no abstractions without a concrete need.

## Roadmap

### v0.1.0 — Evidence

- JSON result schema;
- validation;
- baseline/treatment comparison;
- simple metric deltas;
- comparability checks;
- Markdown report;
- self-contained HTML report;
- provenance and input hashes;
- reproducible end-to-end example.

### Later

Publication destinations and optional notifications may be added after the core evidence flow is stable. They must remain outside the benchmark domain core.

## License

MIT.
