"""T7 IFC consistency.

Pass criterion: Fault F1 is detected.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): IFC GUID mapping.
"""

import pytest


@pytest.mark.skip(reason="T7 is implemented in milestone PR 3")
def test_ifc_consistency():
    raise NotImplementedError
