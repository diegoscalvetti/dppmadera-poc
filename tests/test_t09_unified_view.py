"""T9 Unified view.

Pass criterion: GET /assets/{id} returns DPP + EPM + DBL + DTw links for each component.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): Table 14.
"""

import pytest


@pytest.mark.skip(reason="T9 is implemented in milestone PR 3")
def test_unified_view():
    raise NotImplementedError
