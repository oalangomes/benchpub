# Contributing

Thanks for considering a contribution to `benchpub`.

The project is intentionally small. New abstractions or integrations should be justified by a concrete product need rather than by anticipated future flexibility.

## Development setup

Requirements:

- Python 3.11+;
- uv.

Run:

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run benchpub --help
```

## Pull requests

Please keep pull requests focused and include tests for observable behavior.

Before proposing a feature, consider:

1. What real problem does it solve?
2. Who needs it?
3. Does it belong in the current scope?
4. Does it create permanent complexity?
5. Can the same outcome be achieved more simply?

The CLI, result schema, and generated evidence bundle are public contracts. Internal Python modules are not considered stable public API unless explicitly documented otherwise.
