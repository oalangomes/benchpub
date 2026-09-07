import hashlib
import json
from pathlib import Path

import pytest

from benchpub.comparison import compare_results
from benchpub.models import BenchmarkResult
from benchpub.rendering import RenderError, render_bundle


def _manifest(*, variant: str, score: float) -> BenchmarkResult:
    return BenchmarkResult.model_validate(
        {
            "schema_version": 1,
            "experiment": {
                "id": "render-001",
                "hypothesis": "Treatment improves score.",
                "variant": variant,
            },
            "dataset": {"name": "sample", "revision": "v1"},
            "metrics": [
                {
                    "name": "score",
                    "value": score,
                    "unit": "ratio",
                    "direction": "higher",
                }
            ],
            "controlled_variables": {"seed": 42},
            "provenance": {
                "timestamp": "2026-09-07T18:00:00Z",
                "git": {"commit": "abc123", "dirty": False},
            },
        }
    )


def _render(output: Path) -> tuple[bytes, bytes]:
    baseline_bytes = b'{"source":"baseline","exact":true}\n'
    treatment_bytes = b'{"source":"treatment","exact":true}\n'
    baseline = _manifest(variant="baseline", score=0.7)
    treatment = _manifest(variant="treatment", score=0.8)

    render_bundle(
        baseline=baseline,
        treatment=treatment,
        baseline_bytes=baseline_bytes,
        treatment_bytes=treatment_bytes,
        comparison=compare_results(baseline, treatment),
        output=output,
    )
    return baseline_bytes, treatment_bytes


def test_render_bundle_creates_expected_files(tmp_path: Path) -> None:
    output = tmp_path / "report"

    _render(output)

    assert sorted(
        str(path.relative_to(output))
        for path in output.rglob("*")
        if path.is_file()
    ) == [
        "comparison.json",
        "evidence/baseline.json",
        "evidence/treatment.json",
        "index.html",
        "manifest.json",
        "report.md",
    ]


def test_render_bundle_preserves_exact_input_bytes_and_hashes(tmp_path: Path) -> None:
    output = tmp_path / "report"

    baseline_bytes, treatment_bytes = _render(output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    assert (output / "evidence/baseline.json").read_bytes() == baseline_bytes
    assert (output / "evidence/treatment.json").read_bytes() == treatment_bytes
    assert manifest["inputs"]["baseline"]["sha256"] == hashlib.sha256(baseline_bytes).hexdigest()
    assert manifest["inputs"]["treatment"]["sha256"] == hashlib.sha256(
        treatment_bytes
    ).hexdigest()


def test_render_bundle_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    _render(first)
    _render(second)

    first_files = {
        str(path.relative_to(first)): path.read_bytes()
        for path in first.rglob("*")
        if path.is_file()
    }
    second_files = {
        str(path.relative_to(second)): path.read_bytes()
        for path in second.rglob("*")
        if path.is_file()
    }

    assert first_files == second_files


def test_html_is_self_contained_and_has_no_script_runtime(tmp_path: Path) -> None:
    output = tmp_path / "report"

    _render(output)
    html = (output / "index.html").read_text(encoding="utf-8")

    assert "http://" not in html
    assert "https://" not in html
    assert "<script" not in html
    assert "<style>" in html
    assert "COMPATIBLE" in html


def test_markdown_contains_metrics_and_evidence_links(tmp_path: Path) -> None:
    output = tmp_path / "report"

    _render(output)
    markdown = (output / "report.md").read_text(encoding="utf-8")

    assert "## Metrics" in markdown
    assert "+0.1" in markdown
    assert "evidence/baseline.json" in markdown
    assert "comparison.json" in markdown


def test_non_empty_output_directory_is_rejected_without_mutation(tmp_path: Path) -> None:
    output = tmp_path / "report"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    baseline = _manifest(variant="baseline", score=0.7)
    treatment = _manifest(variant="treatment", score=0.8)

    with pytest.raises(RenderError, match="not empty"):
        render_bundle(
            baseline=baseline,
            treatment=treatment,
            baseline_bytes=b"baseline",
            treatment_bytes=b"treatment",
            comparison=compare_results(baseline, treatment),
            output=output,
        )

    assert marker.read_text(encoding="utf-8") == "keep"
