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

Implemented so far:

- CLI/package foundation;
- JSON result contract v1;
- `benchpub validate`.

Comparison and rendering are intentionally separate follow-up slices.

## Result manifest

The smallest valid manifest is:

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

A richer result can record a hypothesis, dataset revision, controlled variables, configuration, environment, Git provenance, artifacts, and notes.

See [docs/schema.md](docs/schema.md) and the machine-readable [schema/v1.json](schema/v1.json).

## Development

Requires Python 3.11+.

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --dev
uv run benchpub --help
uv run pytest
uv run ruff check .
```

Validate one or more result manifests:

```bash
uv run benchpub validate result.json
uv run benchpub validate baseline.json treatment.json
```

Validation is CI-friendly:

- exit `0`: every supplied manifest is valid;
- exit `1`: at least one manifest is invalid or unreadable.

## Design principles

- small explicit contracts;
- deterministic behavior;
- useful path-aware CLI errors;
- comparability under declared controls;
- provenance without pretending to guarantee reproducibility;
- static-first output;
- no infrastructure requirement;
- no abstractions without a concrete need.

## Roadmap

### v0.1.0 — Evidence

- [x] JSON result schema;
- [x] validation;
- [ ] baseline/treatment comparison;
- [ ] simple metric deltas;
- [ ] comparability checks;
- [ ] Markdown report;
- [ ] self-contained HTML report;
- [ ] provenance and input hashes in the evidence bundle;
- [ ] reproducible end-to-end example.

### Later

Publication destinations and optional notifications may be added after the core evidence flow is stable. They must remain outside the benchmark domain core.

## License

MIT.
