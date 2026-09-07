# Comparison semantics

`benchpub compare` compares two already-valid result manifests:

```bash
benchpub compare baseline.json treatment.json
benchpub compare baseline.json treatment.json --json
```

The command does not claim statistical significance and does not execute either benchmark.

## Comparability

v0.1 uses three states:

- `compatible`: no contradiction or one-sided omission was found in the evidence benchpub knows how to compare;
- `incompatible`: at least one explicitly declared comparable value differs;
- `indeterminate`: no explicit contradiction exists, but relevant declared evidence is missing from one side.

`incompatible` takes precedence over `indeterminate`.

A `compatible` result means **compatible under declared evidence**. It is not proof that two experiments are scientifically equivalent or reproducible.

## Evidence used for comparability

v0.1 checks only:

- `experiment.id`;
- dataset identity/revision when declared;
- keys under `controlled_variables`.

`configuration` is deliberately not required to match because it may describe the treatment itself.

`environment` and `provenance` are preserved evidence but do not automatically become controlled variables. If an environment fact must remain equal, declare it explicitly in `controlled_variables`.

If both manifests omit an optional piece of evidence, benchpub does not invent a mismatch. If one side declares it and the other does not, the state becomes `indeterminate`.

## Metrics

Metrics are matched by name.

For metrics present in both manifests:

- units must match exactly before a delta is computed;
- absolute delta is `treatment - baseline`;
- relative delta is `(treatment - baseline) / baseline * 100`;
- relative delta is `null` / `N/A` when the baseline is zero.

Missing metrics are warnings rather than comparability findings.

## Direction

When both manifests declare the same direction:

- `higher`: positive delta is `improved`;
- `lower`: negative delta is `improved`;
- equal values are `unchanged`;
- `none` or an omitted direction produces `not_evaluated` for non-zero deltas.

If directions differ, the numeric delta remains available but benchpub does not claim improvement/regression and emits a warning.

This is descriptive arithmetic, not a statistical significance test.

## Exit status

A successful comparison exits `0` even when its comparability state is `incompatible` or `indeterminate`.

Invalid/unreadable input exits `1`.

This keeps scientific/engineering findings separate from command execution failure. A future explicit CI gate can be added if real usage justifies it.

## JSON output

`--json` emits deterministic machine-readable output containing:

- experiment id;
- comparability state;
- structured findings;
- metric comparisons;
- structured warnings.

The JSON output is a public CLI contract for v0.1.
