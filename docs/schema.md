# Result schema v1

`benchpub` consumes benchmark results; it does not execute benchmarks.

Schema v1 describes one result/variant of an experiment. Comparison semantics are deliberately outside this contract and are implemented by the comparison slice.

## Required fields

| Field | Meaning |
| --- | --- |
| `schema_version` | Must be the integer `1`. Booleans or strings are not coerced. |
| `experiment.id` | Stable identifier used to relate results from the same experiment. |
| `metrics` | Non-empty list of scalar numeric metrics. |
| `metrics[].name` | Metric identifier. Names must be unique within one manifest. |
| `metrics[].value` | Finite JSON number. Numeric strings are rejected. |

## Optional fields

| Field | Meaning |
| --- | --- |
| `experiment.name` | Human-readable experiment name. |
| `experiment.hypothesis` | Hypothesis being tested, when one exists. |
| `experiment.variant` | Human-readable arm/variant label. |
| `dataset` | Dataset/corpus identity and optional revision. |
| `controlled_variables` | Values declared as controlled by the experiment author. |
| `configuration` | Configuration that describes the result/variant. |
| `environment` | Relevant environment facts supplied by the producer. |
| `provenance` | ISO 8601 timestamp string and basic Git provenance. |
| `artifacts` | Opaque artifact references. v0.1 validation does not fetch them. |
| `notes` | Free-form notes. |

Git `dirty` must be a JSON boolean; strings such as `"false"` are rejected. Provenance timestamps must be ISO 8601 strings rather than Unix numbers.

## Metric metadata

A metric can additionally declare:

- `unit`: for example `ms`, `requests/s`, `ratio`;
- `direction`: `higher`, `lower`, or `none`.

`direction` is descriptive input for later comparison. It does not imply statistical significance.

## Extensibility

Typed envelopes are strict: unknown fields are rejected so spelling mistakes do not silently become evidence.

The maps `controlled_variables`, `configuration`, and `environment` accept arbitrary JSON values. Domain-specific data belongs there until a concrete need justifies evolving the public schema.

Schema evolution must happen through an explicit `schema_version`; v0.1 accepts only version `1`.

## Minimal example

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

## Evidence-rich example

```json
{
  "schema_version": 1,
  "experiment": {
    "id": "retrieval-001",
    "name": "Lexical vs hybrid retrieval",
    "hypothesis": "Hybrid retrieval improves recall without materially increasing latency.",
    "variant": "baseline"
  },
  "dataset": {
    "name": "sample-code-corpus",
    "revision": "v1"
  },
  "metrics": [
    {
      "name": "recall_at_20",
      "value": 0.71,
      "unit": "ratio",
      "direction": "higher"
    },
    {
      "name": "latency_ms",
      "value": 124.2,
      "unit": "ms",
      "direction": "lower"
    }
  ],
  "controlled_variables": {
    "top_k": 20,
    "context_budget": 8000,
    "temperature": 0
  },
  "configuration": {
    "retrieval": "lexical"
  },
  "environment": {
    "python": "3.13"
  },
  "provenance": {
    "timestamp": "2026-09-07T18:00:00Z",
    "git": {
      "commit": "abc1234",
      "dirty": false
    }
  },
  "artifacts": [
    "raw/results.json"
  ]
}
```

## Validation behavior

```bash
benchpub validate result.json
benchpub validate baseline.json treatment.json
```

The command exits `0` only when every supplied file is valid. Invalid files produce path-aware errors such as:

```text
✗ result.json
  metrics.0.value: Input should be a valid number
```

The machine-readable JSON Schema is committed at `schema/v1.json` and tested against the public Pydantic model to prevent drift.
