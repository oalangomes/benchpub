"""Static evidence bundle rendering."""

from __future__ import annotations

import hashlib
import html
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchpub import __version__
from benchpub.comparison import ComparisonResult
from benchpub.models import BenchmarkResult


class RenderError(ValueError):
    """Raised when an evidence bundle cannot be rendered safely."""


@dataclass(frozen=True)
class EvidenceDigest:
    role: str
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class RenderedBundle:
    output: Path
    manifest: dict[str, Any]


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_file(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _format_number(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "N/A"
    prefix = "+" if signed and value > 0 else ""
    return f"{prefix}{value:.6g}"


def _format_change(value: float | None) -> str:
    if value is None:
        return "N/A"
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.2f}%"


def _markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _variant(manifest: BenchmarkResult, fallback: str) -> str:
    return manifest.experiment.variant or fallback


def _dataset(manifest: BenchmarkResult) -> str:
    if manifest.dataset is None:
        return "not declared"
    if manifest.dataset.revision:
        return f"{manifest.dataset.name} @ {manifest.dataset.revision}"
    return manifest.dataset.name


def _git_commit(manifest: BenchmarkResult) -> str:
    if manifest.provenance is None or manifest.provenance.git is None:
        return "not declared"
    suffix = ""
    if manifest.provenance.git.dirty is True:
        suffix = " (dirty)"
    elif manifest.provenance.git.dirty is False:
        suffix = " (clean)"
    return f"{manifest.provenance.git.commit}{suffix}"


def _timestamp(manifest: BenchmarkResult) -> str:
    if manifest.provenance is None or manifest.provenance.timestamp is None:
        return "not declared"
    return manifest.provenance.timestamp.isoformat()


def _metric_rows(comparison: ComparisonResult) -> list[tuple[str, str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for metric in comparison.metrics:
        name = f"{metric.name} [{metric.unit}]" if metric.unit else metric.name
        rows.append(
            (
                name,
                _format_number(metric.baseline),
                _format_number(metric.treatment),
                _format_number(metric.delta, signed=True),
                _format_change(metric.relative_delta_percent),
                metric.outcome.value,
            )
        )
    return rows


def _report_markdown(
    baseline: BenchmarkResult,
    treatment: BenchmarkResult,
    comparison: ComparisonResult,
    baseline_digest: EvidenceDigest,
    treatment_digest: EvidenceDigest,
) -> str:
    lines = [
        f"# Benchmark evidence: {comparison.experiment_id}",
        "",
        f"**Comparability:** {comparison.comparability.value.upper()}",
        "",
        (
            "> Comparability is evaluated under declared evidence. "
            "It is not proof of scientific equivalence or reproducibility."
        ),
        "",
        "## Experiment",
        "",
        "| Evidence | Baseline | Treatment |",
        "| --- | --- | --- |",
        (
            f"| Variant | {_markdown_cell(_variant(baseline, 'baseline'))} | "
            f"{_markdown_cell(_variant(treatment, 'treatment'))} |"
        ),
        (
            f"| Dataset | {_markdown_cell(_dataset(baseline))} | "
            f"{_markdown_cell(_dataset(treatment))} |"
        ),
        (
            f"| Git revision | {_markdown_cell(_git_commit(baseline))} | "
            f"{_markdown_cell(_git_commit(treatment))} |"
        ),
        (
            f"| Timestamp | {_markdown_cell(_timestamp(baseline))} | "
            f"{_markdown_cell(_timestamp(treatment))} |"
        ),
    ]

    hypothesis = baseline.experiment.hypothesis or treatment.experiment.hypothesis
    if hypothesis:
        lines.extend(["", "### Hypothesis", "", hypothesis])

    lines.extend(["", "## Metrics", ""])
    rows = _metric_rows(comparison)
    if rows:
        lines.extend(
            [
                "| Metric | Baseline | Treatment | Delta | Change | Outcome |",
                "| --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in rows:
            lines.append(
                "| "
                + " | ".join(_markdown_cell(value) for value in row)
                + " |"
            )
    else:
        lines.append("No metrics were comparable by name.")

    lines.extend(["", "## Comparability findings", ""])
    if comparison.findings:
        for finding in comparison.findings:
            lines.append(
                f"- `{finding.path}` — **{finding.kind.value}**: "
                f"baseline={_json_text(finding.baseline)}, "
                f"treatment={_json_text(finding.treatment)}"
            )
    else:
        lines.append("No comparability findings.")

    lines.extend(["", "## Warnings", ""])
    if comparison.warnings:
        for warning in comparison.warnings:
            lines.append(f"- `{warning.code}` — {warning.message}")
    else:
        lines.append("No warnings.")

    lines.extend(
        [
            "",
            "## Evidence",
            "",
            "| Role | File | SHA-256 | Size |",
            "| --- | --- | --- | ---: |",
            (
                f"| Baseline | [{baseline_digest.path}]({baseline_digest.path}) | "
                f"`{baseline_digest.sha256}` | {baseline_digest.size_bytes} bytes |"
            ),
            (
                f"| Treatment | [{treatment_digest.path}]({treatment_digest.path}) | "
                f"`{treatment_digest.sha256}` | {treatment_digest.size_bytes} bytes |"
            ),
            "",
            "Machine-readable comparison: [comparison.json](comparison.json)",
            "",
            "Bundle manifest: [manifest.json](manifest.json)",
            "",
            f"Generated by `benchpub {__version__}`.",
            "",
        ]
    )

    return "\n".join(lines)


def _html_escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _report_html(
    baseline: BenchmarkResult,
    treatment: BenchmarkResult,
    comparison: ComparisonResult,
    baseline_digest: EvidenceDigest,
    treatment_digest: EvidenceDigest,
) -> str:
    metric_rows = ""
    for row in _metric_rows(comparison):
        metric_rows += (
            "<tr>"
            + "".join(f"<td>{_html_escape(value)}</td>" for value in row)
            + "</tr>"
        )
    if not metric_rows:
        metric_rows = '<tr><td colspan="6">No metrics were comparable by name.</td></tr>'

    findings = "".join(
        (
            "<li><code>"
            + _html_escape(finding.path)
            + "</code> — <strong>"
            + _html_escape(finding.kind.value)
            + "</strong>: baseline=<code>"
            + _html_escape(_json_text(finding.baseline))
            + "</code>, treatment=<code>"
            + _html_escape(_json_text(finding.treatment))
            + "</code></li>"
        )
        for finding in comparison.findings
    )
    if not findings:
        findings = "<li>No comparability findings.</li>"

    warnings = "".join(
        (
            "<li><code>"
            + _html_escape(warning.code)
            + "</code> — "
            + _html_escape(warning.message)
            + "</li>"
        )
        for warning in comparison.warnings
    )
    if not warnings:
        warnings = "<li>No warnings.</li>"

    hypothesis = baseline.experiment.hypothesis or treatment.experiment.hypothesis
    hypothesis_html = ""
    if hypothesis:
        hypothesis_html = (
            "<h3>Hypothesis</h3><p>"
            + _html_escape(hypothesis)
            + "</p>"
        )

    status = comparison.comparability.value
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Benchmark evidence: {_html_escape(comparison.experiment_id)}</title>
<style>
:root {{
  color-scheme: light dark;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,\n    "Segoe UI", sans-serif;
  line-height: 1.5;
}}
body {{ margin: 0; background: #0b1020; color: #e8ecf4; }}
main {{ max-width: 1080px; margin: 0 auto; padding: 48px 24px 72px; }}
h1, h2, h3 {{ line-height: 1.2; }}
h1 {{ margin-bottom: 8px; }}
section {{ margin-top: 36px; }}
.card {{ background: #121a2d; border: 1px solid #26324d; border-radius: 14px; padding: 20px; }}
.status {{ display: inline-block; padding: 6px 10px; border-radius: 999px; font-weight: 700; }}
.status-compatible {{ background: #123d2d; color: #8ff0bf; }}
.status-incompatible {{ background: #4a1f27; color: #ffb4bd; }}
.status-indeterminate {{ background: #4a3815; color: #ffd58a; }}
.note {{ color: #aeb8ca; max-width: 800px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #26324d; }}
th {{ color: #aeb8ca; font-size: 0.9rem; }}
code {{ overflow-wrap: anywhere; }}
a {{ color: #8db9ff; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }}
.kv strong {{ display: block; color: #aeb8ca; font-size: 0.82rem; margin-bottom: 4px; }}
footer {{ margin-top: 48px; color: #8591a6; font-size: 0.9rem; }}
@media (max-width: 720px) {{
  main {{ padding: 28px 14px 48px; }}
  .table-wrap {{ overflow-x: auto; }}
}}
</style>
</head>
<body>
<main>
  <header>
    <p class="note">benchpub static evidence bundle</p>
    <h1>Benchmark evidence: {_html_escape(comparison.experiment_id)}</h1>
    <span class="status status-{_html_escape(status)}">{_html_escape(status.upper())}</span>
    <p class="note">
      Comparability is evaluated under declared evidence. It is not proof of scientific
      equivalence or reproducibility.
    </p>
  </header>

  <section>
    <h2>Experiment</h2>
    <div class="grid">
      <div class="card kv">\n        <strong>Baseline variant</strong>{_html_escape(_variant(baseline, "baseline"))}\n      </div>
      <div class="card kv">\n        <strong>Treatment variant</strong>{_html_escape(_variant(treatment, "treatment"))}\n      </div>
      <div class="card kv"><strong>Baseline dataset</strong>{_html_escape(_dataset(baseline))}</div>
      <div class="card kv">\n        <strong>Treatment dataset</strong>{_html_escape(_dataset(treatment))}\n      </div>
      <div class="card kv"><strong>Baseline Git</strong>{_html_escape(_git_commit(baseline))}</div>
      <div class="card kv">\n        <strong>Treatment Git</strong>{_html_escape(_git_commit(treatment))}\n      </div>
      <div class="card kv">\n        <strong>Baseline timestamp</strong>{_html_escape(_timestamp(baseline))}\n      </div>
      <div class="card kv">\n        <strong>Treatment timestamp</strong>{_html_escape(_timestamp(treatment))}\n      </div>
    </div>
    {hypothesis_html}
  </section>

  <section>
    <h2>Metrics</h2>
    <div class="card table-wrap">
      <table>
        <thead>
          <tr><th>Metric</th><th>Baseline</th><th>Treatment</th><th>Delta</th><th>Change</th><th>Outcome</th></tr>
        </thead>
        <tbody>{metric_rows}</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Comparability findings</h2>
    <div class="card"><ul>{findings}</ul></div>
  </section>

  <section>
    <h2>Warnings</h2>
    <div class="card"><ul>{warnings}</ul></div>
  </section>

  <section>
    <h2>Evidence</h2>
    <div class="card table-wrap">
      <table>
        <thead><tr><th>Role</th><th>File</th><th>SHA-256</th><th>Size</th></tr></thead>
        <tbody>
          <tr>
            <td>Baseline</td>
            <td>\n              <a href="{_html_escape(baseline_digest.path)}">\n                {_html_escape(baseline_digest.path)}\n              </a>\n            </td>
            <td><code>{_html_escape(baseline_digest.sha256)}</code></td>
            <td>{baseline_digest.size_bytes} bytes</td>
          </tr>
          <tr>
            <td>Treatment</td>
            <td>\n              <a href="{_html_escape(treatment_digest.path)}">\n                {_html_escape(treatment_digest.path)}\n              </a>\n            </td>
            <td><code>{_html_escape(treatment_digest.sha256)}</code></td>
            <td>{treatment_digest.size_bytes} bytes</td>
          </tr>
        </tbody>
      </table>
      <p>
        <a href="comparison.json">comparison.json</a> ·
        <a href="manifest.json">manifest.json</a> ·
        <a href="report.md">report.md</a>
      </p>
    </div>
  </section>

  <footer>Generated by benchpub {_html_escape(__version__)}.</footer>
</main>
</body>
</html>
"""


def _bundle_manifest(
    baseline_digest: EvidenceDigest,
    treatment_digest: EvidenceDigest,
) -> dict[str, Any]:
    return {
        "bundle_version": 1,
        "generated_by": {
            "name": "benchpub",
            "version": __version__,
        },
        "inputs": {
            "baseline": {
                "path": baseline_digest.path,
                "sha256": baseline_digest.sha256,
                "size_bytes": baseline_digest.size_bytes,
            },
            "treatment": {
                "path": treatment_digest.path,
                "sha256": treatment_digest.sha256,
                "size_bytes": treatment_digest.size_bytes,
            },
        },
        "comparison": "comparison.json",
        "reports": {
            "html": "index.html",
            "markdown": "report.md",
        },
    }


def _validate_output_path(output: Path) -> None:
    if not output.exists():
        return
    if not output.is_dir():
        raise RenderError(f"output path exists and is not a directory: {output}")
    if any(output.iterdir()):
        raise RenderError(f"output directory is not empty: {output}")


def render_bundle(
    *,
    baseline: BenchmarkResult,
    treatment: BenchmarkResult,
    baseline_bytes: bytes,
    treatment_bytes: bytes,
    comparison: ComparisonResult,
    output: Path,
) -> RenderedBundle:
    """Render a deterministic static evidence bundle."""

    _validate_output_path(output)
    output_parent = output.parent
    output_parent.mkdir(parents=True, exist_ok=True)

    baseline_digest = EvidenceDigest(
        role="baseline",
        path="evidence/baseline.json",
        sha256=_sha256(baseline_bytes),
        size_bytes=len(baseline_bytes),
    )
    treatment_digest = EvidenceDigest(
        role="treatment",
        path="evidence/treatment.json",
        sha256=_sha256(treatment_bytes),
        size_bytes=len(treatment_bytes),
    )
    manifest = _bundle_manifest(baseline_digest, treatment_digest)

    temp_path = Path(
        tempfile.mkdtemp(
            prefix=f".{output.name}.tmp-",
            dir=output_parent,
        )
    )

    try:
        evidence_dir = temp_path / "evidence"
        evidence_dir.mkdir()
        (evidence_dir / "baseline.json").write_bytes(baseline_bytes)
        (evidence_dir / "treatment.json").write_bytes(treatment_bytes)

        (temp_path / "comparison.json").write_text(
            _json_file(comparison.to_dict()),
            encoding="utf-8",
        )
        (temp_path / "manifest.json").write_text(
            _json_file(manifest),
            encoding="utf-8",
        )
        (temp_path / "report.md").write_text(
            _report_markdown(
                baseline,
                treatment,
                comparison,
                baseline_digest,
                treatment_digest,
            ),
            encoding="utf-8",
        )
        (temp_path / "index.html").write_text(
            _report_html(
                baseline,
                treatment,
                comparison,
                baseline_digest,
                treatment_digest,
            ),
            encoding="utf-8",
        )

        if output.exists():
            output.rmdir()
        temp_path.replace(output)
    except Exception:
        shutil.rmtree(temp_path, ignore_errors=True)
        raise

    return RenderedBundle(output=output, manifest=manifest)
