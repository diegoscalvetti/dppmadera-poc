# PoC results (seed 4411)

11 of 11 tests pass.

| # | Test | Pass criterion | Paper link | Result |
|---|---|---|---|---|
| T1 | Identity resolution | Any of the identifiers of a component resolves to all the others. | §4, identity resolution | **pass** |
| T2 | No duplication | Each fact is stored once, in its authoritative domain; others hold references only. | Federated ownership | **pass** |
| T3 | Provenance completeness | The lineage of every component runs factory to as-built without gaps, or the gap is flagged. | Need for traceability | **pass** |
| T4 | Custody gap detection | Fault F4 is detected and reported. | Custody events | **pass** |
| T5 | Conflict handling | Fault F2: both assertions retained with source and time; authority rule or review flag. | Conflict rule | **pass** |
| T6 | Out-of-order events | Fault F5: correct state after timestamp-ordered reconciliation. | Timestamp ordering | **pass** |
| T7 | IFC consistency | Fault F1 is detected. | IFC GUID mapping | **pass** |
| T8 | Assembly-state view | DTw state matches the ground truth for all 20 components; fault F3 flagged. | Minimal DTw | **pass** |
| T9 | Unified view | GET /assets/{id} returns DPP + EPM + DBL + DTw links for each component. | Table 14 | **pass** |
| T10 | Needs coverage | Each of the 14 LOIN needs is mapped to the endpoint(s)/fields that serve it, or marked "not covered in PoC". | LOIN needs (§3, Table 8) | **pass** |
| T11 | Reproducibility | A clean checkout plus one command reproduces all results. | None (good practice for the TRL 3 evidence) | **pass** |

## Stakeholder questions (illustrative, synthetic)

| Question | Answer | Client requests | Manual look-ups (est.) |
|---|---|---|---|
| Which level 2 panels are installed but not inspected? | P05 | 1 | 9 |
| Where is the element with IFC GUID of P06, and is its custody chain complete? | instance found; storey 2; inspected; custody complete: True | 1 | 4 |
| Which components reached site without a complete custody chain? | G02 | 1 | 40 |
| Which moisture readings disagree, and who reported them? | values [11.8, 18.5] (needs_review) | 1 | 40 |
| Which components were installed out of the planned sequence? | P11 | 1 | 40 |

Assembly state: {'inspected': 18, 'installed': 1, 'delivered': 1}. Replay ingest: 357 API calls.
