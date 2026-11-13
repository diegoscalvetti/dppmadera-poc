# Build plan: DPP Madera proof of concept

Version 0.1, 13 November 2026. Source: `PoC_Spec_DPPmadera_v1` (FONDEF IDeA ID27 planning folder).

## Goal

Show, with synthetic data and automated tests, that the federated information architecture in
Calvetti & Méndez (2026, *Buildings* 16:4411) works end to end for one CLT building, from factory
to as-built. The result strengthens the declared entry TRL 2 and is the first step towards TRL 3, which the
project reaches in month 6 by re-running it with associates' data. It
proves information flow, not software quality.

## Stack (decided in this plan)

| Choice | Decision | Reason |
|---|---|---|
| Language | Python 3.11+ | Readable for reviewers, one toolchain for services, generator, tests and figures |
| Services | FastAPI, one router per domain, mounted in one local process | Free OpenAPI 3 spec; one command to run; each domain still has its own store and its own router, so ownership stays separate |
| Stores | One JSON file per domain under `var/` (in memory during tests) | No database to install; stores are human-readable evidence |
| Federation | `/assets/{id}` calls the other domains through their public API only, never their stores | Demonstrates "link, don't copy" (T2, T9) |
| Tests | pytest, one file per test case T1–T11 | Each test is a piece of evidence with a paper reference |
| Figures | matplotlib (assembly-state view) plus a hand-drawn architecture SVG | No external services |

Rule enforced in code review: a service module may import shared models, but never another
domain's store. Cross-domain answers go through the resolver and HTTP-style calls.

## Repository layout

```
src/dppmadera/
  models.py          identifiers, event envelope, shared enums
  generator.py       seeded synthetic CLT building (20 components, 5 faults)
  store.py           tiny JSON store, one instance per domain
  app.py             mounts the domain routers
  services/
    dpp.py           products, custody/transformation events, lineage
    epm.py           observation gateway (envelope + payload as received)
    dbl.py           building occurrences, as-built records
    resolver.py      identifier mappings with validity intervals
    dtw.py           derived assembly state
    federation.py    GET /assets/{id} unified view
    conflicts.py     retained assertions, authority rules, review flags
scripts/replay.py    feeds events in time order, runs queries, writes results
data/synthetic/      generated dataset + ground truth (committed, reproducible)
docs/                build plan, LOIN needs mapping, OpenAPI export, report
tests/               T1–T11
```

## Milestones and pull requests

| # | Dates | Pull request | Content | Done when |
|---|---|---|---|---|
| 0 | 13 Nov | Skeleton (#1, done) | Build plan, layout, data model, seeded generator, LOIN mapping, test stubs, CI | CI green; generator reproducible |
| 1 | 13 Nov | DPP, EPM, DBL services (#2, done) | Stores, POST/GET endpoints, envelope rule | Unit tests for each service |
| 2 | 13 Nov | Resolver, federation, replay (#3, done) | Mappings with validity, `/assets/{id}`, `/conflicts`, `make replay`, OpenAPI export | Replay runs end to end |
| 3 | 13 Nov | Tests and view (#4) | T1–T11 implemented, DTw assembly-state view, five faults detected, indicators, figures; DC runs the replay | All 11 tests pass; figures in `docs/figures/` |
| 4 | 30 Nov–4 Dec | Report | Draft by 1 Dec; DC and DM approve by 3 Dec; tag `v1.0-poc` on 4 Dec | Approved by DC and DM |

Target: **4 December 2026** (decided 13 Nov). Fallback: 18 December. It depends on each PR being
reviewed within about two days and on DM reading the report on 1–3 Dec; if either slips, only the
report moves.

Diego runs the final replay himself.

## Synthetic dataset

One fictional four-storey CLT building with 20 components: 12 CLT panels (walls and floors),
4 glulam members, 4 connector sets. Every component has six identifiers: product (class),
product instance, batch, IFC GUID, building occurrence and process runs. Events follow EPCIS 2.0
style (ObjectEvent, AggregationEvent) for factory, transport, assembly and as-built.

The five deliberate faults, and the test that must catch each one:

| Fault | Injected as | Caught by |
|---|---|---|
| F1 IFC GUID clash | Two as-built records claim the same IFC GUID | T7 |
| F2 Moisture conflict | Factory QA and site check disagree on one panel | T5 |
| F3 Out of sequence | One panel installed before its planned predecessor | T8 |
| F4 Custody gap | One member arrives on site with no dispatch event | T3, T4 |
| F5 Late event | One inspection is recorded after later events | T6 |

All values are fictional. There is no personal data: actors are roles ("factory QA", "site
crane"), never people. Identifiers use the reserved `example` domain.

## LOIN needs (T10)

`docs/loin_needs.json` holds the 14 needs exactly as worded in the paper's Table 8, with their LOIN
codes (Table 9). Each need is marked covered, partial or "not covered in PoC", with the endpoints,
fields and tests that serve it. Current mapping: 3 covered (SC3, MC1, MC2), 3 partial (SC1, TD2, TD4),
8 not covered (design-stage cost, capability, route and MEP needs, outside the factory-to-as-built
scope). T10 checks this mapping against the running services.

## Indicators (illustrative, synthetic)

The replay records, for five typical stakeholder questions, the number of look-ups needed with
and without the resolver, and the query time. Example: "Which level 2 panels are installed but
not inspected?" These feed the productivity argument in the proposal, labelled as synthetic.

## Out of scope

Forest and sawmill stages; operation, maintenance and reuse; real sensors; authentication and
security; production database; any monitoring of workers; performance at scale; real company data.

## Open points for Diego

1. Review the LOIN mapping (6 of 14 needs exercised by tests).
2. Confirm the stack (Python + FastAPI) before milestone 1.
