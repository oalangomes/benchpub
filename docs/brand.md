# benchpub brand and product positioning

## Product name

The official product and CLI name is **`benchpub`**.

Use lowercase `benchpub` consistently in prose, commands, documentation, release notes, and visual assets.

## Story

**Benchmarks produce numbers. Engineering decisions need evidence.**

A benchmark result on its own rarely explains enough. To evaluate a claim, an engineer needs to know what was compared, which controls were declared, where the result came from, and which source evidence supports the reported delta.

`benchpub` sits **after** the benchmark runner. It consumes structured benchmark results, validates their contract, checks comparability under declared evidence and controls, computes simple metric deltas, preserves source evidence and provenance, and renders a static bundle that humans and machines can inspect.

The product deliberately remains local-first and infrastructure-free. It does not execute benchmarks, require a tracking server or database, infer statistical significance, or claim to make an experiment scientifically reproducible.

The value proposition is simple: make benchmark claims easier to inspect, compare, trace, and publish responsibly.

## Tagline

> **Publish benchmark evidence, not just benchmark numbers.**

This is the primary public tagline.

A supporting line may be used when more context is needed:

> **Turn benchmark results into traceable evidence.**

## Short GitHub description

> **Local-first CLI to validate comparability, preserve provenance, and render benchmark evidence.**

## Message hierarchy

When explaining benchpub, prefer this order:

1. benchmark numbers are weaker without inspectable evidence;
2. benchpub validates structured result contracts;
3. it evaluates comparability under declared evidence and controls;
4. it preserves provenance and exact source evidence;
5. it renders static, human- and machine-readable evidence bundles;
6. it does this locally without owning benchmark execution or infrastructure.

## Public claim guardrails

Do **not** describe benchpub as if it:

- runs or schedules benchmarks;
- proves or guarantees reproducibility;
- captures an environment automatically unless an input explicitly provides it;
- performs statistical significance testing;
- converts units implicitly;
- publishes to a remote destination in v0.1.x;
- generates PDF reports in v0.1.x.

Prefer **“compatible under declared evidence/controls”** over claims of scientific equivalence.

## Visual identity

The visual identity is dark, technical, and evidence-oriented. Purple is the primary brand family; green is reserved for semantic success states rather than the core brand.

| Role | Color |
| --- | --- |
| Night | `#0B0714` |
| Surface | `#171027` |
| Primary violet | `#A855F7` |
| Deep violet | `#7C3AED` |
| Glow violet | `#C084FC` |
| Primary text | `#F8F7FC` |
| Muted text | `#C8B7DE` |
| Success semantic | `#5EE6A8` |

The canonical repository hero is [`docs/assets/benchpub-brand.svg`](assets/benchpub-brand.svg).

For GitHub social preview, export the same composition at **1280×640** and keep the message limited to verified product claims.
