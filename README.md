# DPP Madera: proof of concept

A small, reproducible proof of concept of a **federated digital product passport** for
industrialised timber construction. One fictional four-storey CLT building with 20 components
flows from factory to transport, assembly and as-built record through mock **DPP**, **EPM** and
**DBL** services, an **identifier resolver** and a minimal **assembly-state view** (DTw).

It tests the architecture proposed in Calvetti & Méndez (2026), *Buildings* 16:4411, and is the
TRL 3 evidence for the FONDEF IDeA ID27 proposal "DPP Madera".

**Synthetic data only.** No real company data and no personal data. Services are mocks, with no
security and no claim about performance at scale.

## Quick start

```bash
make install     # Python 3.11+
make data        # regenerate data/synthetic (seed 4411)
make test        # T1–T11 plus dataset checks
make serve       # services and OpenAPI docs at http://127.0.0.1:8000/docs
make replay      # end-to-end replay (from milestone PR 2)
```

## Status

| Milestone | State |
|---|---|
| Skeleton, data model, generator | done |
| DPP, EPM, DBL services | 16–18 Nov |
| Resolver, federation, replay | planned 30 Nov–4 Dec |
| Tests T1–T11, assembly-state view, figures | 23–27 Nov |
| Technical report, tag `v1.0-poc` | 30 Nov–4 Dec (target 4 Dec) |

See [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md) for the plan, the five injected faults and the test map.

## Use of AI

The code, tests and report draft are written with Claude Code (Anthropic) and reviewed by the
project director, who runs the final replay.
