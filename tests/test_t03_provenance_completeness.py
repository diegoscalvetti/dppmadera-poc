"""T3 Provenance completeness.

Pass criterion: Lineage of every component runs factory to as-built without gaps, or the gap is flagged.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): Need for traceability.
"""

import pytest


@pytest.mark.skip(reason="T3 is implemented in milestone PR 3")
def test_provenance_completeness():
    raise NotImplementedError
