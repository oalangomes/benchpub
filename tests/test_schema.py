import json
from pathlib import Path

from benchpub.models import BenchmarkResult


def test_committed_json_schema_matches_public_model() -> None:
    schema_path = Path(__file__).parents[1] / "schema" / "v1.json"
    committed = json.loads(schema_path.read_text(encoding="utf-8"))

    assert committed == BenchmarkResult.model_json_schema()
