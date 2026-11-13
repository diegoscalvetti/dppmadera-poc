"""T10 Needs coverage.

Pass criterion: Each of the 14 LOIN needs is mapped to endpoints/fields, or marked not covered in PoC.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): LOIN needs.
"""

import pytest


@pytest.mark.skip(reason="T10 is implemented in milestone PR 3")
def test_needs_coverage():
    raise NotImplementedError
