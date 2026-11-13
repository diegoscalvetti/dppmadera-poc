"""T2 No duplication.

Pass criterion: Each fact is stored once, in its authoritative domain; others hold references only.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): Federated ownership.
"""

import pytest


@pytest.mark.skip(reason="T2 is implemented in milestone PR 3")
def test_no_duplication():
    raise NotImplementedError
