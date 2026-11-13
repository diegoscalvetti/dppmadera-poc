from dppmadera.replay import run


def test_replay_runs_end_to_end():
    res = run()
    assert sum(res["summary"].values()) == 20
    assert len(res["questions"]) == 5
