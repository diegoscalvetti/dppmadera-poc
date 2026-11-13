"""T8 Assembly-state view.

Pass criterion: DTw state matches ground truth for all 20 components; fault F3 flagged.
Paper link (Calvetti & Méndez 2026, Buildings 16:4411): Minimal DTw.
"""

import pytest


@pytest.mark.skip(reason="T8 is implemented in milestone PR 3")
def test_assembly_state():
    raise NotImplementedError
